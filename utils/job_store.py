"""
File-based job persistence for the Resume Optimizer.
Simplified version without complex locking.
"""

import json
import os
import tempfile
import shutil
from typing import Dict, Optional, List
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

JOBS_DIR = Path("data/jobs")
JOBS_DIR.mkdir(parents=True, exist_ok=True)


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"


class FileJobStore:
    """Simple file-based job store."""
    
    def __init__(self, storage_dir: Path = JOBS_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Dict] = {}
        self._load_existing_jobs()
    
    def _get_job_path(self, job_id: str) -> Path:
        return self.storage_dir / f"{job_id}.json"
    
    def _load_existing_jobs(self) -> None:
        try:
            for job_file in self.storage_dir.glob("*.json"):
                try:
                    with open(job_file, 'r', encoding='utf-8') as f:
                        job_data = json.load(f)
                        job_id = job_data.get("job_id")
                        if job_id:
                            self._cache[job_id] = job_data
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to load {job_file}: {e}")
        except Exception as e:
            logger.error(f"Error loading jobs: {e}")
    
    def _save(self, job_id: str, data: Dict) -> bool:
        """Save job to disk with atomic write."""
        job_path = self._get_job_path(job_id)
        try:
            temp_fd, temp_path = tempfile.mkstemp(suffix='.tmp', dir=self.storage_dir)
            os.write(temp_fd, json.dumps(data, indent=2, default=str).encode('utf-8'))
            os.close(temp_fd)
            shutil.move(temp_path, job_path)
            return True
        except Exception as e:
            logger.error(f"Save failed for {job_id}: {e}")
            return False
    
    def create_job(self, job_id: str, resume_text: str, job_description: str, template: str) -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        job_data = {
            "job_id": job_id,
            "status": JobStatus.QUEUED.value,
            "progress": 0,
            "created_at": now,
            "updated_at": now,
            "template": template,
            "resume_text": resume_text,
            "job_description": job_description,
            "agents": {
                "planner": {"status": AgentStatus.PENDING.value, "messages": [], "started_at": None, "completed_at": None, "output": None},
                "executor": {"status": AgentStatus.PENDING.value, "messages": [], "started_at": None, "completed_at": None, "output": None},
                "critic": {"status": AgentStatus.PENDING.value, "messages": [], "started_at": None, "completed_at": None, "output": None}
            },
            "result": None,
            "error": None,
            "validation_warnings": [],
            "logs": [],
            "retry_count": 0
        }
        self._cache[job_id] = job_data
        self._save(job_id, job_data)
        return job_data
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        return self._cache.get(job_id)
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        job = self._cache.get(job_id)
        if not job:
            return None
        return {
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "agents": job["agents"],
            "result": job["result"],
            "error": job["error"],
            "validation_warnings": job["validation_warnings"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"]
        }
    
    def update_agent_status(self, job_id: str, agent_name: str, status: AgentStatus, output: str = None, message: str = None) -> Optional[Dict]:
        job = self._cache.get(job_id)
        if not job:
            return None
        
        now = datetime.now(timezone.utc).isoformat()
        agent = job["agents"].get(agent_name)
        if not agent:
            return None
        
        agent["status"] = status.value if isinstance(status, AgentStatus) else status
        
        if status == AgentStatus.RUNNING and not agent["started_at"]:
            agent["started_at"] = now
            job["status"] = JobStatus.PROCESSING.value
        
        if status == AgentStatus.COMPLETE:
            agent["completed_at"] = now
            if output:
                agent["output"] = output
        
        if message:
            agent["messages"].append({"timestamp": now, "message": message})
        
        # Update progress
        progress = 0
        for i, name in enumerate(["planner", "executor", "critic"]):
            s = job["agents"][name]["status"]
            if s == "running":
                progress = (i * 33) + 15
            elif s == "complete":
                progress = (i + 1) * 33
        job["progress"] = min(progress, 100)
        job["updated_at"] = now
        
        self._save(job_id, job)
        return job
    
    def add_agent_message(self, job_id: str, agent_name: str, message: str) -> Optional[Dict]:
        job = self._cache.get(job_id)
        if not job:
            return None
        
        now = datetime.now(timezone.utc).isoformat()
        agent = job["agents"].get(agent_name)
        if agent:
            agent["messages"].append({"timestamp": now, "message": message})
            job["updated_at"] = now
            self._save(job_id, job)
        return job
    
    def add_validation_warning(self, job_id: str, warning: str) -> None:
        job = self._cache.get(job_id)
        if job:
            job["validation_warnings"].append(warning)
            job["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(job_id, job)
    
    def complete_job(self, job_id: str, result: Dict) -> Optional[Dict]:
        job = self._cache.get(job_id)
        if not job:
            return None
        
        now = datetime.now(timezone.utc).isoformat()
        job["status"] = JobStatus.COMPLETE.value
        job["progress"] = 100
        job["result"] = result
        job["updated_at"] = now
        self._save(job_id, job)
        return job
    
    def error_job(self, job_id: str, error: str) -> Optional[Dict]:
        job = self._cache.get(job_id)
        if not job:
            return None
        
        now = datetime.now(timezone.utc).isoformat()
        job["status"] = JobStatus.ERROR.value
        job["error"] = error
        job["updated_at"] = now
        self._save(job_id, job)
        return job
    
    def list_jobs(self, status: str = None, limit: int = 50) -> List[Dict]:
        jobs = list(self._cache.values())
        if status:
            jobs = [j for j in jobs if j["status"] == status]
        jobs.sort(key=lambda x: x["created_at"], reverse=True)
        return jobs[:limit]
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        removed = 0
        for job_id, job in list(self._cache.items()):
            try:
                created = datetime.fromisoformat(job["created_at"].replace('Z', '+00:00'))
                if created < cutoff:
                    del self._cache[job_id]
                    path = self._get_job_path(job_id)
                    if path.exists():
                        path.unlink()
                    removed += 1
            except:
                pass
        return removed
    
    def increment_retry(self, job_id: str) -> int:
        """Increment retry count for a job. Returns new retry count."""
        job = self._cache.get(job_id)
        if not job:
            return 0
        
        retry_count = job.get("retry_count", 0) + 1
        job["retry_count"] = retry_count
        job["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save(job_id, job)
        return retry_count
    
    def get_retry_count(self, job_id: str) -> int:
        """Get current retry count for a job."""
        job = self._cache.get(job_id)
        if not job:
            return 0
        return job.get("retry_count", 0)


# Global instance
job_store = FileJobStore()
