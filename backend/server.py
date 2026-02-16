"""
Backend server entry point.
Imports the main FastAPI app and runs it.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, APIRouter, UploadFile, Form, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import logging
import asyncio
from typing import Optional
import uuid
import traceback

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import from parent modules
from crew import run_crew
from utils.resume_reader import read_resume
from utils.resume_structurer import structure_resume
from services.template_renderer import render_html
from services.pdf_service import html_to_pdf_base64
from utils.job_store import job_store, JobStatus, AgentStatus
from utils.pre_pdf_validator import validate_resume_data
from utils.websocket_manager import ws_manager, JobEventEmitter
from schemas.resume_schema import ResumeSchema, Experience, Project

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Resume Optimizer",
    description="Multi-agent resume optimization with real-time WebSocket updates",
    version="2.0.0"
)

# Create API router
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def process_resume_job(job_id: str, resume_text: str, job_description: str, template: str):
    """Background task to process resume optimization."""
    emitter = JobEventEmitter(job_id)
    
    try:
        logger.info(f"[{job_id}] Starting resume optimization")
        emitter.progress(5, "Starting optimization...")
        
        # Run the crew
        agent_output = run_crew(
            resume_text=resume_text,
            job_description=job_description,
            template=template,
            job_id=job_id
        )
        
        emitter.progress(80, "Generating PDF...")
        
        # Process structured data
        if "structured_data" in agent_output and agent_output["structured_data"]:
            json_data = agent_output["structured_data"]
            
            experience_list = []
            for exp in json_data.get("experience", []):
                if isinstance(exp, dict):
                    experience_list.append(Experience(
                        role=exp.get("role", ""),
                        company=exp.get("company", ""),
                        description=exp.get("description", "")
                    ))
            
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
            resume_data = structure_resume(agent_output, original_resume_text=resume_text)
        
        # Validation
        pre_pdf_validation = validate_resume_data(resume_text, resume_data)
        
        if pre_pdf_validation.get("warnings"):
            for warning in pre_pdf_validation["warnings"]:
                emitter.validation_warning(warning)
        
        emitter.progress(90, "Rendering template...")
        
        # Generate PDF
        html_content = render_html(resume_data, template)
        pdf_base64 = html_to_pdf_base64(html_content)
        
        # Build result
        result = {
            "planner": agent_output.get("planner", ""),
            "executor": agent_output.get("executor", ""),
            "critic": agent_output.get("critic", ""),
            "pdf_base64": pdf_base64,
            "template_used": agent_output.get("template_used", template),
            "validation": agent_output.get("validation", {}),
            "pre_pdf_validation": pre_pdf_validation,
            "retry_count": agent_output.get("retry_count", 0),
            "baseline": agent_output.get("baseline", {})
        }
        
        job_store.complete_job(job_id, result)
        emitter.job_completed(result)
        emitter.progress(100, "Complete!")
        
        logger.info(f"[{job_id}] Completed successfully")
        
    except Exception as e:
        error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
        logger.error(f"[{job_id}] {error_msg}")
        job_store.error_job(job_id, error_msg)
        emitter.job_failed(str(e))


@api_router.get("/")
async def root():
    """Health check."""
    return {
        "status": "healthy",
        "service": "AI Resume Optimizer",
        "version": "2.0.0"
    }


@api_router.post("/optimize-resume")
async def optimize_resume(
    background_tasks: BackgroundTasks,
    resume: UploadFile,
    job_description: str = Form(...),
    template: str = Form("professional")
):
    """Submit resume optimization job."""
    job_id = str(uuid.uuid4())
    
    try:
        resume_text = read_resume(resume)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read resume: {str(e)}")
    
    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume appears to be empty")
    
    job_store.create_job(
        job_id=job_id,
        resume_text=resume_text,
        job_description=job_description,
        template=template
    )
    
    logger.info(f"[{job_id}] Created new job")
    
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
        "message": "Resume optimization started. Connect to WebSocket for real-time updates.",
        "websocket_url": f"/api/ws/{job_id}"
    }


@api_router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Get job status."""
    job_status = job_store.get_job_status(job_id)
    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_status


@api_router.get("/jobs")
async def list_jobs(status: Optional[str] = None, limit: int = 50):
    """List jobs."""
    jobs = job_store.list_jobs(status=status, limit=limit)
    return {"jobs": jobs, "count": len(jobs)}


@app.websocket("/api/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time updates."""
    job_data = job_store.get_job(job_id)
    if not job_data:
        await websocket.close(code=4004, reason="Job not found")
        return
    
    connected = await ws_manager.connect(websocket, job_id)
    if not connected:
        return
    
    try:
        status = job_store.get_job_status(job_id)
        if status:
            await websocket.send_json({
                "type": "initial_status",
                "data": status
            })
        
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                try:
                    await websocket.send_text("ping")
                except:
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket)


@api_router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job."""
    job_data = job_store.get_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_id in job_store._cache:
        del job_store._cache[job_id]
    
    job_path = job_store._get_job_path(job_id)
    if job_path.exists():
        job_path.unlink()
    
    return {"message": f"Job {job_id} deleted"}


@api_router.post("/cleanup")
async def cleanup_old_jobs(max_age_hours: int = 24):
    """Cleanup old jobs."""
    cleaned = job_store.cleanup_old_jobs(max_age_hours)
    return {"cleaned": cleaned}


# Include router
app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting AI Resume Optimizer API...")
    logger.info(f"Loaded {len(job_store._cache)} existing jobs")
    cleaned = job_store.cleanup_old_jobs(max_age_hours=48)
    if cleaned:
        logger.info(f"Cleaned up {cleaned} old jobs")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
