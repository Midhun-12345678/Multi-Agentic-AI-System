"""
CrewAI orchestration for resume optimization.
Implements sequential agent pipeline with real-time status updates,
field mapping enforcement, and automatic retry on data loss.
"""

from crewai import Crew, Task, Agent
from agents.planner import planner
from agents.executor import executor
from agents.critic import critic
from config.template_contexts import get_template_prompt_context, get_json_structure_prompt
from utils.validation_parser import parse_validation_report
from utils.job_store import job_store, AgentStatus
from utils.field_mapper import extract_baseline, validate_against_baseline, compare_counts
from utils.websocket_manager import JobEventEmitter
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
        on_agent_start: Callback when agent starts
        on_agent_message: Callback for progress messages
        on_agent_complete: Callback when agent completes
        on_validation_warning: Callback for validation warnings
    
    Returns:
        Dict with planner, executor, critic outputs and structured data
    """
    
    # Create event emitter for WebSocket updates
    emitter = JobEventEmitter(job_id) if job_id else None
    
    def emit_start(agent_name: str):
        if emitter:
            emitter.agent_started(agent_name)
        if on_agent_start:
            on_agent_start(agent_name)
        if job_id:
            job_store.update_agent_status(job_id, agent_name, AgentStatus.RUNNING)
        log_agent_event(job_id, agent_name, "started")
    
    def emit_message(agent_name: str, message: str):
        if emitter:
            emitter.agent_message(agent_name, message)
        if on_agent_message:
            on_agent_message(agent_name, message)
        if job_id:
            job_store.add_agent_message(job_id, agent_name, message)
    
    def emit_complete(agent_name: str, output: str = ""):
        output_size = len(output) if output else 0
        if emitter:
            emitter.agent_completed(agent_name, output_size)
        if on_agent_complete:
            on_agent_complete(agent_name, output_size)
        if job_id:
            job_store.update_agent_status(job_id, agent_name, AgentStatus.COMPLETE, output)
        log_agent_event(job_id, agent_name, "completed", {"output_size": output_size})
    
    def emit_warning(warning: str):
        if emitter:
            emitter.validation_warning(warning)
        if on_validation_warning:
            on_validation_warning(warning)
        if job_id:
            job_store.add_validation_warning(job_id, warning)
    
    # Extract baseline BEFORE running agents
    emit_message("planner", "Extracting baseline from original resume...")
    baseline = extract_baseline(resume_text)
    
    logger.info(f"[{job_id}] Baseline: {baseline.experience_count} experiences, "
                f"{baseline.project_count} projects")
    
    # Get template-specific context
    template_context = get_template_prompt_context(template)
    json_structure_prompt = get_json_structure_prompt(template)
    
    # Run crew with retry logic
    retry_count = 0
    corrective_prompt = ""
    structured_data = None
    validation_result = None
    
    while retry_count <= MAX_RETRIES:
        # Build tasks
        plan_task, exec_task, review_task = build_tasks(
            resume_text=resume_text,
            job_description=job_description,
            template=template,
            template_context=template_context,
            json_structure_prompt=json_structure_prompt,
            corrective_prompt=corrective_prompt
        )
        
        crew = Crew(
            agents=[planner, executor, critic],
            tasks=[plan_task, exec_task, review_task],
            process="sequential",
            verbose=True
        )
        
        # === PLANNER PHASE ===
        emit_start("planner")
        emit_message("planner", "Analyzing resume structure and content...")
        emit_message("planner", "Identifying gaps vs job requirements...")
        emit_message("planner", "Building optimization strategy...")
        
        # Run the crew
        try:
            final_result = crew.kickoff()
        except Exception as e:
            logger.error(f"[{job_id}] Crew execution failed: {e}")
            raise
        
        # Get outputs
        planner_output = str(plan_task.output)
        emit_complete("planner", planner_output)
        
        # === EXECUTOR PHASE ===
        emit_start("executor")
        emit_message("executor", "Extracting data from original resume...")
        emit_message("executor", "Applying template formatting...")
        emit_message("executor", "Enhancing with ATS keywords...")
        
        executor_output = str(exec_task.output.raw) if hasattr(exec_task.output, 'raw') else str(exec_task.output)
        emit_complete("executor", executor_output)
        
        # === PARSE JSON ===
        structured_data = parse_executor_json(executor_output)
        
        if not structured_data:
            emit_warning("Failed to parse JSON from executor output")
            logger.warning(f"[{job_id}] JSON parsing failed, retry {retry_count + 1}")
            retry_count += 1
            corrective_prompt = "⚠️ Your output was not valid JSON. Output ONLY valid JSON starting with { and ending with }"
            continue
        
        # === VALIDATE AGAINST BASELINE ===
        emit_message("critic", "Validating field mapping...")
        validation_result = validate_against_baseline(baseline, structured_data)
        
        if not validation_result.passed:
            for issue in validation_result.issues:
                emit_warning(issue)
                logger.warning(f"[{job_id}] Validation issue: {issue}")
            
            if retry_count < MAX_RETRIES:
                emit_message("executor", f"Retry {retry_count + 1}: Correcting data preservation issues...")
                corrective_prompt = validation_result.corrective_prompt
                retry_count += 1
                
                if job_id:
                    job_store.increment_retry(job_id)
                continue
            else:
                emit_warning(f"Max retries ({MAX_RETRIES}) reached. Some data may be missing.")
                logger.warning(f"[{job_id}] Max retries reached, proceeding with partial data")
        
        # Validation passed or max retries reached
        break
    
    # === CRITIC PHASE ===
    emit_start("critic")
    emit_message("critic", "Validating JSON structure...")
    emit_message("critic", "Cross-checking field preservation...")
    emit_message("critic", "Verifying template compliance...")
    
    critic_output = str(review_task.output.raw) if hasattr(review_task.output, 'raw') else str(review_task.output)
    emit_complete("critic", critic_output)
    
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
    corrective_prompt: str = ""
) -> tuple:
    """Build CrewAI tasks with optional corrective prompt for retries."""
    
    plan_task = Task(
        description=f"""
        Analyze the resume and job description.
        Identify gaps, missing keywords, and improvement strategy.
        
        IMPORTANT: The optimized resume will be formatted for the {template.upper()} template.
        Consider this template's style, tone, and structure when making recommendations.

        Resume:
        {resume_text}

        Job Description:
        {job_description}
        """,
        expected_output=f"Structured improvement plan with {template}-specific recommendations",
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
    
    exec_task = Task(
        description=f"""
        ⚠️ CRITICAL: This is a DATA EXTRACTION and FORMATTING task.
        Your source of truth is the ORIGINAL RESUME below. Extract ALL data from it.
        {correction_section}
        
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
