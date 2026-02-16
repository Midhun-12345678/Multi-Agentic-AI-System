from fastapi import FastAPI, UploadFile, Form, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from crew import run_crew
from utils.resume_reader import read_resume
from utils.resume_structurer import structure_resume
from services.template_renderer import render_html
from services.pdf_service import html_to_pdf_base64
from utils.job_tracker import job_tracker, JobStatus
from utils.pre_pdf_validator import validate_resume_data
from schemas.resume_schema import ResumeSchema
import uuid
import traceback

app = FastAPI(title="AI Resume Optimizer")


def process_resume_job(job_id: str, resume_text: str, job_description: str, template: str):
    """Background task to process resume optimization."""
    try:
        # Run the crew with job tracking
        agent_output = run_crew(
            resume_text=resume_text,
            job_description=job_description,
            template=template,
            job_id=job_id
        )

        # Check if we have structured JSON data
        if "structured_data" in agent_output and agent_output["structured_data"]:
            print("✅ Using direct JSON structure from executor")
            # Create ResumeSchema directly from JSON
            json_data = agent_output["structured_data"]
            resume_data = ResumeSchema(
                name=json_data.get("name", ""),
                email=json_data.get("email", ""),
                phone=json_data.get("phone", ""),
                linkedin=json_data.get("linkedin", ""),
                github=json_data.get("github", ""),
                summary=json_data.get("summary", ""),
                education=json_data.get("education", ""),
                experience=json_data.get("experience", []),
                projects=json_data.get("projects", []),
                skills=json_data.get("skills", [])
            )
        else:
            print("⚠️ Falling back to markdown parsing")
            # Fallback to markdown parsing
            resume_data = structure_resume(agent_output, original_resume_text=resume_text)
        
        # ===== AUTOMATIC PRE-PDF VALIDATION =====
        pre_pdf_validation = validate_resume_data(resume_text, resume_data)
        
        html_content = render_html(resume_data, template)
        pdf_base64 = html_to_pdf_base64(html_content)

        # Complete the job with results
        result = {
            "planner": agent_output["planner"],
            "executor": agent_output["executor"],
            "critic": agent_output["critic"],
            "pdf_base64": pdf_base64,
            "template_used": agent_output.get("template_used", template),
            "validation": agent_output.get("validation", {}),
            "pre_pdf_validation": pre_pdf_validation  # Automatic data integrity check
        }
        
        job_tracker.complete_job(job_id, result)
        
    except Exception as e:
        error_msg = f"Error processing resume: {str(e)}\n{traceback.format_exc()}"
        job_tracker.error_job(job_id, error_msg)


@app.post("/optimize-resume")
async def optimize_resume(
    background_tasks: BackgroundTasks,
    resume: UploadFile,
    job_description: str = Form(...),
    template: str = Form("professional")
):
    """
    Submit resume optimization job.
    Returns job_id immediately, process runs in background.
    """
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Read resume
    resume_text = read_resume(resume)
    
    # Create job tracker entry
    job_tracker.create_job(job_id)
    
    # Start background processing
    background_tasks.add_task(
        process_resume_job,
        job_id=job_id,
        resume_text=resume_text,
        job_description=job_description,
        template=template
    )
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Resume optimization started. Poll /status/{job_id} for progress."
    }


@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get current status of a resume optimization job.
    Returns agent progress, outputs, and final result when complete.
    """
    job_status = job_tracker.get_job_status(job_id)
    
    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_status
