from crewai import Crew, Task
from agents.planner import planner
from agents.executor import executor
from agents.critic import critic
from config.template_contexts import get_template_prompt_context, get_json_structure_prompt
from utils.validation_parser import parse_validation_report
from utils.job_tracker import job_tracker, AgentStatus
from typing import Optional
import json
import re


def run_crew(resume_text: str, job_description: str, template: str = "harvard", job_id: Optional[str] = None):
    # Get template-specific context for agents
    template_context = get_template_prompt_context(template)
    json_structure_prompt = get_json_structure_prompt(template)
    
    # ----- TASKS -----
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

    exec_task = Task(
        description=f"""
        ⚠️ CRITICAL: This is a DATA EXTRACTION and FORMATTING task.
        Your source of truth is the ORIGINAL RESUME below. Extract ALL data from it.
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        ORIGINAL RESUME (YOUR SOURCE OF TRUTH - PRESERVE ALL DATA FROM THIS):
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {resume_text}
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        STRATEGIC IMPROVEMENTS (from Planner - available via context):
        Use these recommendations for STYLE/KEYWORD improvements ONLY.
        Do NOT use these as your data source. Extract data from ORIGINAL RESUME above.
        
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
        • Company names: Use EXACTLY as written (do not abbreviate, rename, or invent)
        • Project titles: Use EXACTLY as written (do not merge into generic categories)
        • If original says "Company Name, City" → JSON must say "Company Name, City"
        • DO NOT invent company names not present in original
        • DO NOT use placeholders like "ABC Corp" or "XYZ Inc"
        
        STEP 4 - PRESERVE ALL CONTENT (enhance formatting only):
        • Every bullet/responsibility from original must appear in JSON
        • DO NOT merge multiple bullets into one
        • DO NOT skip bullets to reduce length
        • DO NOT summarize detailed project descriptions into generic statements
        • Enhance with bold formatting: wrap technologies/metrics/achievements in **term**
        
        STEP 4.5 - ATS-OPTIMIZED BULLET FORMATTING:
        ⛕ CRITICAL FOR ATS SCORING:
        • Each responsibility = ONE separate bullet point with \\n separation
        • DO NOT chain multiple actions with dashes in one line
        • Format: "- Action verb + specific task + technology/result"
        • Each bullet should map to: ONE skill + ONE action + ONE outcome
        
        ❌ WRONG (dash-chaining hurts ATS):
        "- Developed backend services using Django - Designed RESTful APIs - Implemented authentication"
        
        ✅ RIGHT (separate bullets boost ATS):
        "- Developed and maintained backend services using **Django REST Framework**\\n- Designed and consumed **RESTful** and **asynchronous APIs**\\n- Implemented secure **JWT authentication** with role-based access control"
        
        STEP 5 - APPLY BOLD FORMATTING:
        Within descriptions, use **term** to emphasize:
        • Technologies and tools (programming languages, frameworks, databases, cloud services)
        • Quantifiable metrics (percentages, user counts, performance improvements, time savings)
        • Key achievements and outcomes (awards, leadership roles, impact statements)
        • Business results (revenue, cost savings, efficiency gains)
        
        STEP 5.5 - FORMAT SKILLS ARRAY PROPERLY:
        The skills field must be an ARRAY of strings, where each string is a category:
        • Group related skills by category (e.g., "Programming Languages", "Frameworks", "Databases")
        • Each array element = one category with its skills
        • Format: "Category Name: skill1, skill2, skill3"
        • Apply **bold** to skill names for emphasis
        • Keep each category on a separate array element for clean rendering
        • Example structure:
          "skills": [
            "Programming Languages: **Python**, **JavaScript**, **TypeScript**",
            "Frameworks: **Django**, **React**, **Node.js**, **FastAPI**",
            "Databases: **PostgreSQL**, **MySQL**, **MongoDB**"
          ]
        
        STEP 6 - APPLY STRATEGIC IMPROVEMENTS (from Planner context):
        • Add ATS keywords where relevant
        • Improve bullet point phrasing for impact
        • Ensure action verb usage
        • Enhance metrics and quantification
        • BUT: Do this WHILE preserving original content, not replacing it
        
        STEP 8 - FINAL VERIFICATION BEFORE OUTPUT:
        Count your JSON arrays and verify:
        ✓ experience array length = number of job positions in original resume?
        ✓ projects array length = number of projects in original resume?
        ✓ All company names match original exactly (no invented names)?
        ✓ All project titles from original are present?
        ✓ All bullets/responsibilities from original preserved?
        ✓ Bold formatting applied to key terms?
        ✓ Skills formatted as array of category strings (not one long paragraph)?
        ✓ Each bullet is separate (no dash-chaining like "Task A - Task B - Task C")?
        ✓ Summary field populated for ATS top-of-page keywords?
        ✓ No data merged, summarized, or omitted?
        
        If ANY verification fails, STOP and re-extract from original resume.
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        JSON OUTPUT FORMAT REQUIREMENTS:
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        1. Output ONLY valid JSON matching the structure shown above
        2. Do NOT wrap in ```json code blocks or add markdown formatting
        3. Do NOT add explanatory text before or after the JSON
        4. Use \\n for line breaks within descriptions (not actual newlines)
        5. Start each bullet point with "- " prefix
        6. Use **term** for bold emphasis (will be rendered as HTML <strong>)
        7. Escape special characters properly (\\ for backslash, \\" for quotes)
        8. Ensure valid JSON syntax (proper commas, brackets, quotes)
        
        ⚠️  YOUR OUTPUT MUST START WITH {{{{ and END WITH }}}}
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
        
        EXECUTOR OUTPUT (JSON FORMAT):
        The executor should have output valid JSON. Validate the JSON structure and content.
        
        JSON VALIDATION CHECKLIST:
        ✓ Valid JSON format (proper syntax, no parsing errors)
        ✓ All required fields present: name, email, phone, linkedin, github, summary, education, experience, projects, skills
        ✓ experience is an array with objects containing: company, role, description
        ✓ projects is an array with objects containing: title, details
        ✓ skills is an array of strings
        ✓ Descriptions use \\n for line breaks (not actual newlines)
        
        FIELD MAPPING VALIDATION (MANDATORY):
        You MUST verify every field from the ORIGINAL RESUME appears in the JSON:
        
        1. COUNT VALIDATION:
           - Count job positions in original resume
           - Count job positions in JSON experience array
           - MUST MATCH: If original has 3 jobs, JSON MUST have 3 jobs
           
        2. COMPANY NAMES:
           - List all companies from original resume
           - Verify ALL companies appear in JSON experience array
           - Flag any missing companies
           
        3. PROJECT TITLES:
           - List all projects from original resume
           - Verify ALL projects appear in JSON projects array
           - Flag any missing projects
           
        4. CONTACT INFORMATION:
           - Verify email, phone, LinkedIn, GitHub preserved
           - Check that name is spelled exactly the same
           
        5. SKILLS:
           - Verify all key technical skills from original are included
           - New skills can be added, but original skills cannot be removed
           
        6. EDUCATION:
           - Verify degree, university, graduation year preserved
        
        TEMPLATE COMPLIANCE ({template.upper()}):
        ✓ Content matches {template} style and tone
        ✓ Appropriate level of detail for template
        ✓ Professional language consistent with template
        ✓ ATS-friendly keywords present
        ✓ Quantifiable achievements included
        
        OUTPUT REQUIREMENTS:
        Provide a comprehensive validation report:
        
        ---
        VALIDATION REPORT:
        
        JSON Structure: [✓ Valid / ⚠️ Issues: details]
        
        Field Mapping:
        ✓ Jobs Mapped: [X original → X in JSON] ✓
        ✓ Companies: [List all companies] ✓
        ✓ Projects: [X original → X in JSON] ✓
        ✓ Contact Info: [email, phone, linkedin, github] ✓
        ✓ Education: [Preserved] ✓
        ✓ Skills Count: [X original → X in JSON] ✓
        
        Template Compliance: [✓ 100% / ⚠️ Issues]
        Data Integrity: [COMPLETE / ⚠️ INCOMPLETE - details]
        
        If ANY field is missing or JSON is invalid, report:
        ⚠️ WARNING: [Issue description and recommended fix]
        """,
        expected_output=f"Comprehensive validation report for JSON structure and {template} template compliance",
        agent=critic,
        context=[plan_task, exec_task]
    )

    crew = Crew(
        agents=[planner, executor, critic],
        tasks=[plan_task, exec_task, review_task],
        process="sequential",
        verbose=True
    )

    # Update status: Starting planner
    if job_id:
        job_tracker.update_agent_status(job_id, "planner", AgentStatus.RUNNING)
    
    final_result = crew.kickoff()
    
    # Update status: Planner complete
    if job_id:
        job_tracker.update_agent_status(job_id, "planner", AgentStatus.COMPLETE, str(plan_task.output))
        job_tracker.update_agent_status(job_id, "executor", AgentStatus.COMPLETE, str(exec_task.output))
        job_tracker.update_agent_status(job_id, "critic", AgentStatus.COMPLETE)
    
    # Extract executor output
    executor_output = str(exec_task.output.raw) if hasattr(exec_task.output, 'raw') else str(exec_task.output)
    
    # Try to parse JSON from executor output
    structured_data = None
    parse_error = None
    
    try:
        # First attempt: Direct JSON parse
        structured_data = json.loads(executor_output)
        print("✅ Successfully parsed JSON directly from executor output")
    except json.JSONDecodeError as e:
        print(f"⚠️ Direct JSON parse failed: {e}")
        
        try:
            # Second attempt: Extract JSON from markdown code block
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', executor_output, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                structured_data = json.loads(json_str)
                print("✅ Successfully extracted JSON from markdown code block")
            else:
                # Third attempt: Find JSON between first { and last }
                first_brace = executor_output.find('{')
                last_brace = executor_output.rfind('}')
                
                if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                    json_str = executor_output[first_brace:last_brace + 1]
                    structured_data = json.loads(json_str)
                    print("✅ Successfully extracted JSON by finding braces")
                else:
                    raise ValueError("Could not find valid JSON in executor output")
        except (json.JSONDecodeError, ValueError) as e2:
            parse_error = str(e2)
            print(f"❌ All JSON parsing attempts failed: {e2}")
            print("⚠️ Falling back to markdown parsing in main.py")
    
    # Get critic output with validation report
    critic_output = str(review_task.output.raw) if hasattr(review_task.output, 'raw') else str(review_task.output)
    
    # Parse validation report from critic output
    validation_data = parse_validation_report(critic_output)
    
    # Prepare return data
    result = {
        "planner": str(plan_task.output),
        "executor": executor_output,
        "critic": critic_output,
        "template_used": template,
        "validation": validation_data
    }
    
    # Add structured data if JSON parsing succeeded
    if structured_data:
        result["structured_data"] = structured_data
        result["parse_method"] = "json"
        print("📊 Returning structured JSON data")
    else:
        result["parse_method"] = "markdown"
        result["parse_error"] = parse_error
        print("📝 Returning markdown data (will be parsed by resume_structurer)")
        
        # Extract clean resume content for markdown fallback
        if "---" in critic_output and "VALIDATION REPORT:" in critic_output:
            result["final"] = critic_output.split("---")[0].strip()
        else:
            if "---" in executor_output and "This resume is designed" in executor_output:
                result["final"] = executor_output.split("This resume is designed")[0].strip()
            elif "Above is the optimized" in executor_output:
                result["final"] = executor_output.split("Above is the optimized")[0].strip()
            else:
                result["final"] = executor_output

    return result
