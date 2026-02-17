"""
AI Resume Optimizer - FastAPI Backend
With polling-based job status updates and file-based job persistence.
"""

from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import uuid
import traceback
import logging
import os
import concurrent.futures
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / 'backend' / '.env')

# Import our modules
from crew import run_crew
from utils.resume_reader import read_resume
from utils.resume_structurer import structure_resume
from services.template_renderer import render_html
from services.pdf_service import html_to_pdf_base64
from utils.job_store import job_store, JobStatus, AgentStatus
from utils.pre_pdf_validator import validate_resume_data
from utils.ats_scorer import analyze_ats_improvement, extract_keywords_from_job_description
from schemas.resume_schema import ResumeSchema, Experience, Project

# Thread pool for background tasks (runs in separate threads, not event loop)
thread_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting AI Resume Optimizer API...")
    logger.info(f"Loaded {len(job_store._cache)} existing jobs from storage")
    
    # Cleanup old jobs on startup
    cleaned = job_store.cleanup_old_jobs(max_age_hours=48)
    if cleaned:
        logger.info(f"Cleaned up {cleaned} old jobs")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Resume Optimizer API...")
    thread_executor.shutdown(wait=False)


app = FastAPI(
    title="AI Resume Optimizer",
    description="Multi-agent resume optimization with polling-based status updates",
    version="2.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def process_resume_job(job_id: str, resume_text: str, job_description: str, template: str, page_count: int = 1, ats_keywords: dict = None):
    """
    Background task to process resume optimization.
    Includes ATS keywords and page count for optimization.
    """
    import threading
    import sys
    
    # Force immediate output
    print(f"[{job_id}] ===== BACKGROUND TASK STARTED (PRINT) =====", flush=True)
    logger.info(f"[{job_id}] ===== BACKGROUND TASK STARTED =====")
    logger.info(f"[{job_id}] Process ID: {os.getpid()}, Thread: {threading.current_thread().name}")
    sys.stdout.flush()
    sys.stderr.flush()
    
    try:
        print(f"[{job_id}] ===== Starting resume optimization (PRINT) =====", flush=True)
        logger.info(f"[{job_id}] ===== Starting resume optimization =====")
        
        logger.info(f"[{job_id}] About to call run_crew()")
        logger.info(f"[{job_id}] Resume length: {len(resume_text)}, Job desc length: {len(job_description)}, Template: {template}")
        logger.info(f"[{job_id}] Page count: {page_count}, ATS keywords: {len(ats_keywords.get('all_keywords', {})) if ats_keywords else 0}")
        
        # Run the crew with callbacks
        agent_output = run_crew(
            resume_text=resume_text,
            job_description=job_description,
            template=template,
            job_id=job_id,
            page_count=page_count,
            ats_keywords=ats_keywords
        )
        
        logger.info(f"[{job_id}] run_crew() completed successfully")
        
        # Process the result
        if "structured_data" in agent_output and agent_output["structured_data"]:
            logger.info(f"[{job_id}] Using direct JSON structure from executor")
            json_data = agent_output["structured_data"]
            
            # Convert experience dicts to Experience objects
            experience_list = []
            for exp in json_data.get("experience", []):
                if isinstance(exp, dict):
                    experience_list.append(Experience(
                        role=exp.get("role", ""),
                        company=exp.get("company", ""),
                        description=exp.get("description", "")
                    ))
            
            # Convert project dicts to Project objects
            projects_list = []
            for proj in json_data.get("projects", []):
                if isinstance(proj, dict):
                    projects_list.append(Project(
                        title=proj.get("title", ""),
                        details=proj.get("details", "")
                    ))
            
            resume_data = ResumeSchema(
                name=json_data.get("name", ""),
                email=json_data.get("email", ""),
                phone=json_data.get("phone", ""),
                linkedin=json_data.get("linkedin", ""),
                github=json_data.get("github", ""),
                summary=json_data.get("summary", ""),
                education=json_data.get("education", ""),
                experience=experience_list,
                projects=projects_list,
                skills=json_data.get("skills", [])
            )
        else:
            logger.warning(f"[{job_id}] Falling back to markdown parsing")
            resume_data = structure_resume(agent_output, original_resume_text=resume_text)
        
        # Pre-PDF validation
        pre_pdf_validation = validate_resume_data(resume_text, resume_data)
        
        # Check for validation warnings
        if pre_pdf_validation.get("warnings"):
            for warning in pre_pdf_validation["warnings"]:
                job_store.add_validation_warning(job_id, warning)
        
        logger.info(f"[{job_id}] Rendering resume template...")
        
        # Generate PDF
        html_content = render_html(resume_data, template)
        pdf_base64 = html_to_pdf_base64(html_content)
        
        # Post-generation page count validation
        try:
            import io
            import base64
            from PyPDF2 import PdfReader
            pdf_bytes = base64.b64decode(pdf_base64)
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            output_pages = len(pdf_reader.pages)
            target_pages = min(page_count, 2)  # Cap target at 2 pages
            
            if output_pages > target_pages:
                page_warning = f"Page bloat: Generated {output_pages} pages vs {target_pages} target. Consider condensing."
                job_store.add_validation_warning(job_id, page_warning)
                logger.warning(f"[{job_id}] {page_warning}")
            else:
                logger.info(f"[{job_id}] Page count OK: {output_pages}/{target_pages} pages")
        except Exception as e:
            logger.warning(f"[{job_id}] Could not validate page count: {e}")
        
        # Generate optimized resume text for ATS comparison
        optimized_resume_text = agent_output.get("executor", "")
        
        # ATS Analysis - compare original vs optimized
        logger.info(f"[{job_id}] Running ATS keyword analysis...")
        ats_analysis = analyze_ats_improvement(
            original_resume=resume_text,
            optimized_resume=optimized_resume_text,
            job_description=job_description
        )
        logger.info(f"[{job_id}] ATS Score: {ats_analysis['summary']['original_score']} -> {ats_analysis['summary']['optimized_score']} (+{ats_analysis['summary']['improvement']}%)")
        
        logger.info(f"[{job_id}] Finalizing...")
        
        # Build final result
        result = {
            "planner": agent_output.get("planner", ""),
            "executor": agent_output.get("executor", ""),
            "critic": agent_output.get("critic", ""),
            "pdf_base64": pdf_base64,
            "template_used": agent_output.get("template_used", template),
            "validation": agent_output.get("validation", {}),
            "pre_pdf_validation": pre_pdf_validation,
            "retry_count": agent_output.get("retry_count", 0),
            "baseline": agent_output.get("baseline", {}),
            "ats_analysis": ats_analysis,
            "original_resume": resume_text,
            "optimized_resume": optimized_resume_text
        }
        
        # Complete the job
        job_store.complete_job(job_id, result)
        
        logger.info(f"[{job_id}] Resume optimization completed successfully")
        
    except Exception as e:
        error_msg = f"Error processing resume: {str(e)}\n{traceback.format_exc()}"
        logger.error(f"[{job_id}] {error_msg}")
        
        job_store.error_job(job_id, error_msg)


@app.get("/api/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Resume Optimizer",
        "version": "2.1.0"
    }


@app.post("/api/optimize-resume")
async def optimize_resume(
    resume: UploadFile,
    job_description: str = Form(...),
    template: str = Form("professional")
):
    """
    Submit resume optimization job.
    Returns job_id immediately, process runs in background.
    Poll /api/status/{job_id} for updates.
    """
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Read resume
    try:
        resume_text, page_count = read_resume(resume)
        logger.info(f"[New Job] Resume extracted: {len(resume_text)} chars, {page_count} page(s)")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read resume: {str(e)}")
    
    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume appears to be empty")
    
    # Extract ATS keywords from job description BEFORE crew runs
    ats_keywords = extract_keywords_from_job_description(job_description)
    logger.info(f"[New Job] Extracted {len(ats_keywords.get('technical_skills', []))} technical skills, {len(ats_keywords.get('soft_skills', []))} soft skills")
    
    # Create job in persistent store
    job_store.create_job(
        job_id=job_id,
        resume_text=resume_text,
        job_description=job_description,
        template=template
    )
    
    logger.info(f"[{job_id}] Created new optimization job")
    
    # Start background processing in a SEPARATE THREAD (not the event loop)
    logger.info(f"[{job_id}] Submitting to thread pool executor...")
    thread_executor.submit(
        process_resume_job,
        job_id,
        resume_text,
        job_description,
        template,
        page_count,
        ats_keywords
    )
    logger.info(f"[{job_id}] Background task submitted successfully")
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Resume optimization started. Poll /api/status/{job_id} for updates."
    }


@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get current status of a resume optimization job.
    Supports both polling and WebSocket approaches.
    Poll this endpoint until status is 'complete' or 'error'.
    """
    job_status = job_store.get_job_status(job_id)
    
    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_status


@app.get("/api/jobs")
async def list_jobs(status: Optional[str] = None, limit: int = 50):
    """List all jobs, optionally filtered by status."""
    jobs = job_store.list_jobs(status=status, limit=limit)
    return {"jobs": jobs, "count": len(jobs)}

@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its data."""
    job_data = job_store.get_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Remove from store
    if job_id in job_store._cache:
        del job_store._cache[job_id]
    
    # Remove file
    job_path = job_store._get_job_path(job_id)
    if job_path.exists():
        job_path.unlink()
    
    return {"message": f"Job {job_id} deleted"}


@app.post("/api/cleanup")
async def cleanup_old_jobs(max_age_hours: int = 24):
    """Manually trigger cleanup of old jobs."""
    cleaned = job_store.cleanup_old_jobs(max_age_hours)
    return {"cleaned": cleaned, "message": f"Removed {cleaned} old jobs"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False  # Disabled for ThreadPoolExecutor stability
    )
