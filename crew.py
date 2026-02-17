"""
CrewAI orchestration for resume optimization.
Implements sequential agent pipeline with real-time status updates,
field mapping enforcement, and automatic retry on data loss.
"""

from crewai import Crew, Task, Agent
from crewai.tasks.task_output import TaskOutput
from agents import planner, executor, critic
from config.template_contexts import get_template_prompt_context, get_json_structure_prompt
from utils.validation_parser import parse_validation_report
from utils.job_store import job_store, AgentStatus
from utils.field_mapper import extract_baseline, validate_against_baseline, compare_counts
from typing import Optional, Dict, Callable
import json
import re
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Maximum retries for field mapping failures
MAX_RETRIES = 2


def run_crew(
    resume_text: str, 
    job_description: str, 
    template: str = "harvard", 
    job_id: Optional[str] = None,
    page_count: int = 1,
    ats_keywords: Optional[Dict] = None,
    on_agent_start: Optional[Callable] = None,
    on_agent_message: Optional[Callable] = None,
    on_agent_complete: Optional[Callable] = None,
    on_validation_warning: Optional[Callable] = None
) -> Dict:
    """
    Run the multi-agent crew for resume optimization.
    
    Args:
        resume_text: Original resume text
        job_description: Target job description
        template: Resume template to use
        job_id: Job ID for status tracking
        page_count: Target page count (preserve original length)
        ats_keywords: Pre-extracted ATS keywords from job description
        on_agent_start: Callback when agent starts
        on_agent_message: Callback for progress messages
        on_agent_complete: Callback when agent completes
        on_validation_warning: Callback for validation warnings
    
    Returns:
        Dict with planner, executor, critic outputs and structured data
    """
    
    # Create event emitter for WebSocket updates
    # Event callbacks removed - using job_store only
    
    # Track current task for real-time callbacks
    current_task_index = [0]  # Use list to allow mutation in nested functions
    task_to_agent = {0: "planner", 1: "executor", 2: "critic"}
    last_step_time = [0]  # Throttle step messages
    
    def emit_start(agent_name: str):
        if on_agent_start:
            on_agent_start(agent_name)
        if job_id:
            job_store.update_agent_status(job_id, agent_name, AgentStatus.RUNNING)
        log_agent_event(job_id, agent_name, "started")
    
    def emit_message(agent_name: str, message: str):
        if on_agent_message:
            on_agent_message(agent_name, message)
        if job_id:
            job_store.add_agent_message(job_id, agent_name, message)
    
    def emit_complete(agent_name: str, output: str = ""):
        output_size = len(output) if output else 0
        if on_agent_complete:
            on_agent_complete(agent_name, output_size)
        if job_id:
            job_store.update_agent_status(job_id, agent_name, AgentStatus.COMPLETE, output)
        log_agent_event(job_id, agent_name, "completed", {"output_size": output_size})
    
    def emit_warning(warning: str):
        if on_validation_warning:
            on_validation_warning(warning)
        if job_id:
            job_store.add_validation_warning(job_id, warning)
    
    # Extract baseline BEFORE running agents
    logger.info(f"[{job_id}] Extracting baseline from original resume...")
    emit_message("planner", "Extracting baseline from original resume...")
    baseline = extract_baseline(resume_text)
    
    logger.info(f"[{job_id}] Baseline: {baseline.experience_count} experiences, "
                f"{baseline.project_count} projects")
    
    # Get template-specific context
    logger.info(f"[{job_id}] Loading template context for: {template}")
    template_context = get_template_prompt_context(template)
    json_structure_prompt = get_json_structure_prompt(template)
    logger.info(f"[{job_id}] Template context loaded")
    
    # Run crew with retry logic
    retry_count = 0
    corrective_prompt = ""
    structured_data = None
    validation_result = None
    
    logger.info(f"[{job_id}] Starting crew execution loop...")
    
    while retry_count <= MAX_RETRIES:
        logger.info(f"[{job_id}] Retry attempt: {retry_count}/{MAX_RETRIES}")
        
        # Build tasks
        logger.info(f"[{job_id}] Building crew tasks...")
        plan_task, exec_task, review_task = build_tasks(
            resume_text=resume_text,
            job_description=job_description,
            template=template,
            template_context=template_context,
            json_structure_prompt=json_structure_prompt,
            corrective_prompt=corrective_prompt,
            page_count=page_count,
            ats_keywords=ats_keywords
        )
        logger.info(f"[{job_id}] Tasks built successfully")
        
        # === CREWAI CALLBACKS FOR REAL-TIME UPDATES ===
        def on_task_complete(output: TaskOutput):
            """Called when each task completes - mark agent complete and start next."""
            agent_name = task_to_agent.get(current_task_index[0], "unknown")
            logger.info(f"[{job_id}] Task completed for {agent_name}")
            
            # Mark this agent as COMPLETE with output
            output_str = str(output.raw) if hasattr(output, 'raw') else str(output)
            emit_complete(agent_name, output_str)
            
            # Move to next task
            current_task_index[0] += 1
            
            # Start next agent if not last task
            next_agent = task_to_agent.get(current_task_index[0])
            if next_agent:
                emit_start(next_agent)
                emit_message(next_agent, f"Starting {next_agent} task...")
        
        def on_step(step_output):
            """Called on each agent step - provides granular progress."""
            import time
            current_time = time.time()
            
            # Convert to string for filtering
            step_str = str(step_output) if step_output else ""
            
            # Skip AgentFinish messages (too noisy/redundant with task_callback)
            if "AgentFinish" in step_str:
                return
            
            # Throttle: only emit every 3 seconds to avoid spam
            if current_time - last_step_time[0] < 3:
                return
            last_step_time[0] = current_time
            
            agent_name = task_to_agent.get(current_task_index[0], "system")
            # Extract meaningful info from step_output (truncate)
            display_str = step_str[:100] if step_str else "Processing..."
            emit_message(agent_name, f"Thinking: {display_str}...")
        
        logger.info(f"[{job_id}] Creating Crew instance with callbacks...")
        crew = Crew(
            agents=[planner, executor, critic],
            tasks=[plan_task, exec_task, review_task],
            process="sequential",
            verbose=True,
            step_callback=on_step,
            task_callback=on_task_complete
        )
        logger.info(f"[{job_id}] Crew instance created with real-time callbacks")
        
        # Mark all agents as pending before kickoff
        if job_id:
            job_store.update_agent_status(job_id, "planner", AgentStatus.PENDING)
            job_store.update_agent_status(job_id, "executor", AgentStatus.PENDING)
            job_store.update_agent_status(job_id, "critic", AgentStatus.PENDING)
        
        # Reset task index for this iteration
        current_task_index[0] = 0
        
        # === RUN CREW WITH REAL-TIME CALLBACKS ===
        logger.info(f"[{job_id}] About to call crew.kickoff()...")
        
        # Mark planner as running - callbacks will handle the rest
        emit_start("planner")
        emit_message("planner", "Analyzing resume structure and content...")
        
        # Run the crew - callbacks fire during execution
        try:
            logger.info(f"[{job_id}] ===== CALLING crew.kickoff() =====")
            crew.kickoff()  # Callbacks fire in real-time during this
            logger.info(f"[{job_id}] ===== crew.kickoff() COMPLETED =====")
        except Exception as e:
            logger.error(f"[{job_id}] Crew execution failed: {e}", exc_info=True)
            raise
        
        # === GET OUTPUTS (callbacks already marked agents complete) ===
        planner_output = str(plan_task.output)
        executor_output = str(exec_task.output.raw) if hasattr(exec_task.output, 'raw') else str(exec_task.output)
        
        # === PARSE JSON ===
        structured_data = parse_executor_json(executor_output)
        
        if not structured_data:
            emit_warning("Failed to parse JSON from executor output")
            emit_message("executor", f"Retry {retry_count + 1}: JSON parsing failed, retrying...")
            logger.warning(f"[{job_id}] JSON parsing failed, retry {retry_count + 1}")
            retry_count += 1
            corrective_prompt = "⚠️ Your output was not valid JSON. Output ONLY valid JSON starting with { and ending with }"
            # Reset statuses for retry
            if job_id:
                job_store.update_agent_status(job_id, "executor", AgentStatus.PENDING)
                job_store.update_agent_status(job_id, "critic", AgentStatus.PENDING)
            continue
        
        # === VALIDATE AGAINST BASELINE ===
        # Note: critic status already set by task_callback, just emit messages
        emit_message("critic", "Validating field mapping...")
        validation_result = validate_against_baseline(baseline, structured_data)
        
        if not validation_result.passed:
            for issue in validation_result.issues:
                emit_warning(issue)
                logger.warning(f"[{job_id}] Validation issue: {issue}")
            
            if retry_count < MAX_RETRIES:
                emit_message("critic", "Data preservation issues detected")
                emit_message("executor", f"Retry {retry_count + 1}: Correcting data preservation issues...")
                corrective_prompt = validation_result.corrective_prompt
                retry_count += 1
                
                if job_id:
                    job_store.increment_retry(job_id)
                    # Reset statuses for retry
                    job_store.update_agent_status(job_id, "planner", AgentStatus.PENDING)
                    job_store.update_agent_status(job_id, "executor", AgentStatus.PENDING)
                    job_store.update_agent_status(job_id, "critic", AgentStatus.PENDING)
                continue
            else:
                emit_warning(f"Max retries ({MAX_RETRIES}) reached. Some data may be missing.")
                logger.warning(f"[{job_id}] Max retries reached, proceeding with partial data")
        
        # Validation passed or max retries reached
        break
    
    # === POST-PROCESSING (callbacks already handled agent statuses) ===
    critic_output = str(review_task.output.raw) if hasattr(review_task.output, 'raw') else str(review_task.output)
    
    # Parse validation report from critic
    validation_data = parse_validation_report(critic_output)
    
    # Add baseline comparison
    if structured_data:
        validation_data["baseline_comparison"] = compare_counts(baseline, structured_data)
    
    # Build result
    result = {
        "planner": planner_output,
        "executor": executor_output,
        "critic": critic_output,
        "template_used": template,
        "validation": validation_data,
        "retry_count": retry_count,
        "baseline": {
            "experience_count": baseline.experience_count,
            "project_count": baseline.project_count,
            "skill_count": baseline.skill_count
        }
    }
    
    if structured_data:
        result["structured_data"] = structured_data
        result["parse_method"] = "json"
        logger.info(f"[{job_id}] Returning structured JSON data")
    else:
        result["parse_method"] = "markdown"
        result["final"] = executor_output
        logger.info(f"[{job_id}] Returning markdown data (JSON parsing failed)")
    
    return result


def build_tasks(
    resume_text: str,
    job_description: str,
    template: str,
    template_context: str,
    json_structure_prompt: str,
    corrective_prompt: str = "",
    page_count: int = 1,
    ats_keywords: Optional[Dict] = None
) -> tuple:
    """Build CrewAI tasks with ATS keywords, page limits, and optional corrective prompt."""
    
    # Build ATS keywords section for planner
    ats_section = ""
    if ats_keywords:
        tech_skills = ats_keywords.get("technical_skills", [])
        soft_skills = ats_keywords.get("soft_skills", [])
        ats_section = f"""
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        🎯 KEY JOB KEYWORDS TO OPTIMIZE FOR:
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Technical Skills: {', '.join(tech_skills[:15]) if tech_skills else 'None identified'}
        Soft Skills: {', '.join(soft_skills[:10]) if soft_skills else 'None identified'}
        
        STRATEGY: Identify which keywords are MISSING from the resume and recommend
        where to naturally incorporate them (without inventing false experience).
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
    
    plan_task = Task(
        description=f"""
        Analyze the resume and job description.
        Identify gaps, missing keywords, and improvement strategy.
        {ats_section}
        
        IMPORTANT: The optimized resume will be formatted for the {template.upper()} template.
        Consider this template's style, tone, and structure when making recommendations.
        
        📄 PAGE CONSTRAINT: Original resume is {page_count} page(s). Keep recommendations concise
        to fit within this page limit.

        Resume:
        {resume_text}

        Job Description:
        {job_description}
        """,
        expected_output=f"Structured improvement plan with {template}-specific recommendations and ATS keyword strategy",
        agent=planner
    )
    
    # Add corrective prompt for retries
    correction_section = ""
    if corrective_prompt:
        correction_section = f"""
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        🚨 RETRY - CORRECTION REQUIRED:
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {corrective_prompt}
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
    
    # Build ATS optimization section for executor
    ats_executor_section = ""
    if ats_keywords:
        tech_skills = ats_keywords.get("technical_skills", [])
        soft_skills = ats_keywords.get("soft_skills", [])
        missing_hint = f"""
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        🎯 ATS KEYWORD OPTIMIZATION:
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Job requires these keywords: {', '.join(tech_skills[:12])}
        Soft skills needed: {', '.join(soft_skills[:8])}
        
        OPTIMIZATION RULES:
        1. Include ALL skills from original resume in the skills array
        2. If candidate used related tech (e.g., "Flask" and job wants "FastAPI"), 
           mention BOTH in descriptions where truthful
        3. Enhance bullet points to naturally include job keywords
        4. Add soft skills to summary if demonstrated by experience
        5. DO NOT fabricate experience - only optimize wording
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        ats_executor_section = missing_hint
    
    # Page constraint section with strict content limits
    if page_count == 1:
        content_limits = "MAX 2 bullets per job, 15-20 skills total, 2-sentence summary"
    elif page_count == 2:
        content_limits = "MAX 3 bullets per job, 25-30 skills total, 3-sentence summary"
    else:
        # 3+ pages indicates bloated resume - target condensing to 2 pages
        content_limits = "TARGET 2 PAGES: MAX 3 bullets per job, 25-35 skills, condense aggressively"
    
    page_constraint = f"""
        
        📄 STRICT PAGE LIMIT: {page_count if page_count <= 2 else 2} page(s) maximum
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        CONTENT LIMITS: {content_limits}
        
        ⚠️ EXCEEDING PAGE LIMIT CREATES POOR IMPRESSION ON RECRUITERS
        
        CONDENSING RULES:
        • Each bullet point: 1-2 lines maximum (not 3-4 lines)
        • Skills: Group by category, remove duplicates, prioritize job-relevant
        • Projects: 2-3 bullet points each, focus on impact/results
        • Education: 2-3 lines maximum
        • Remove generic phrases like "Responsible for..." - use action verbs
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
    
    exec_task = Task(
        description=f"""
        ⚠️ CRITICAL: This is a DATA EXTRACTION and FORMATTING task.
        Your source of truth is the ORIGINAL RESUME below. Extract ALL data from it.
        {correction_section}
        {ats_executor_section}
        {page_constraint}
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        ORIGINAL RESUME (YOUR SOURCE OF TRUTH - PRESERVE ALL DATA FROM THIS):
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {resume_text}
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        {json_structure_prompt}
        
        TEMPLATE STYLE GUIDANCE ({template.upper()}):
        {template_context}
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        🚨 MANDATORY DATA EXTRACTION WORKFLOW:
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        STEP 1 - INVENTORY THE ORIGINAL RESUME:
        Before writing ANY JSON, parse the original resume above and count:
        • How many distinct job positions/work experiences?
        • How many distinct projects/portfolio items?
        • What are the EXACT company names as written?
        • What are the EXACT project titles as written?
        • Extract ALL skills from the original (aim for 80%+ preservation)
        
        STEP 2 - CREATE 1:1 MAPPING (NO CONSOLIDATION):
        • Each job position in original = ONE entry in experience array
        • Each project in original = ONE entry in projects array
        • If original has 5 projects → JSON MUST have 5 project objects
        • If original has 3 jobs → JSON MUST have 3 experience objects
        
        STEP 3 - PRESERVE EXACT NAMES:
        • Company names: Use EXACTLY as written
        • Project titles: Use EXACTLY as written
        • DO NOT invent company names not present in original
        
        STEP 4 - OUTPUT VALID JSON ONLY:
        • Start with {{ and end with }}
        • No markdown code blocks
        • No explanatory text
        
        ⚠️ YOUR OUTPUT MUST START WITH {{ and END WITH }}
        """,
        expected_output=f"Valid JSON object with resume data formatted for {template} template",
        agent=executor,
        context=[plan_task]
    )
    
    review_task = Task(
        description=f"""
        CRITICAL MISSION: Validate JSON structure and field mapping accuracy.
        
        ⚠️ The Executor MUST have extracted data from the ORIGINAL RESUME below.
        Your job is to verify NO data was lost, merged, or invented.
        
        ORIGINAL RESUME TO CROSS-CHECK:
        {resume_text}
        
        VALIDATION CHECKLIST:
        ✓ Valid JSON format
        ✓ All required fields present
        ✓ experience array count matches original job count
        ✓ projects array count matches original project count
        ✓ No hallucinated companies
        ✓ Contact info preserved
        
        OUTPUT A VALIDATION REPORT with:
        - JSON Structure: Valid/Invalid
        - Jobs Mapped: X original → X in JSON
        - Projects Mapped: X original → X in JSON
        - Data Integrity: COMPLETE/INCOMPLETE
        - Any warnings
        """,
        expected_output=f"Comprehensive validation report for JSON structure and {template} template compliance",
        agent=critic,
        context=[plan_task, exec_task]
    )
    
    return plan_task, exec_task, review_task


def parse_executor_json(executor_output: str) -> Optional[Dict]:
    """
    Parse JSON from executor output with multiple strategies.
    Returns parsed dict or None if all strategies fail.
    """
    strategies = [
        ("direct", lambda x: json.loads(x)),
        ("markdown_block", extract_from_markdown),
        ("brace_extraction", extract_from_braces),
        ("cleaned", lambda x: json.loads(clean_json_string(x)))
    ]
    
    for strategy_name, strategy_fn in strategies:
        try:
            result = strategy_fn(executor_output)
            if result and isinstance(result, dict):
                logger.info(f"JSON parsed successfully using {strategy_name} strategy")
                return result
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.debug(f"{strategy_name} strategy failed: {e}")
            continue
    
    logger.error("All JSON parsing strategies failed")
    return None


def extract_from_markdown(text: str) -> Optional[Dict]:
    """Extract JSON from markdown code block."""
    match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if match:
        return json.loads(match.group(1))
    return None


def extract_from_braces(text: str) -> Optional[Dict]:
    """Extract JSON by finding first { and last }."""
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_str = text[first_brace:last_brace + 1]
        return json.loads(json_str)
    return None


def clean_json_string(text: str) -> str:
    """Clean common JSON issues."""
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    # Fix unescaped newlines in strings
    text = re.sub(r'(?<!\\)\n', '\\n', text)
    return text


def log_agent_event(job_id: str, agent_name: str, event: str, details: Dict = None):
    """Log structured agent event."""
    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = {
        "timestamp": timestamp,
        "job_id": job_id,
        "agent_name": agent_name,
        "event": event,
        "details": details or {}
    }
    logger.info(f"[AGENT_EVENT] {json.dumps(log_entry)}")
