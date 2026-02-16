"""
File-based job persistence for the Resume Optimizer.
Stores jobs as JSON files with atomic writes to prevent corruption.
Jobs survive server restarts.
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
import fcntl

logger = logging.getLogger(__name__)

# Storage directory
JOBS_DIR = Path("/app/data/jobs")
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
    """
    Persistent file-based job store with atomic writes.
    Each job is stored as a separate JSON file.
    """
    
    def __init__(self, storage_dir: Path = JOBS_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        # In-memory cache for fast reads
        self._cache: Dict[str, Dict] = {}
        # Load existing jobs on startup
        self._load_existing_jobs()
    
    def _get_job_path(self, job_id: str) -> Path:
        """Get file path for a job."""
        return self.storage_dir / f"{job_id}.json"
    
    def _load_existing_jobs(self) -> None:
        """Load all existing jobs from disk on startup."""
        try:
            for job_file in self.storage_dir.glob("*.json"):
                try:
                    with open(job_file, 'r') as f:
                        job_data = json.load(f)
                        job_id = job_data.get("job_id")
                        if job_id:
                            self._cache[job_id] = job_data
                            logger.info(f"Loaded job {job_id} from disk (status: {job_data.get('status')})")
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to load job file {job_file}: {e}")
        except Exception as e:
            logger.error(f"Error loading existing jobs: {e}")
    
    def _atomic_write(self, job_id: str, data: Dict) -> bool:
        """
        Write job data atomically using temp file + rename.
        This prevents corruption from partial writes or crashes.
        """
        job_path = self._get_job_path(job_id)
        temp_fd = None
        temp_path = None
        
        try:
            # Create temp file in same directory (for atomic rename)
            temp_fd, temp_path = tempfile.mkstemp(
                suffix='.tmp',
                prefix=f'job_{job_id}_',
                dir=self.storage_dir
            )
            
            # Write JSON to temp file
            json_data = json.dumps(data, indent=2, default=str)
            os.write(temp_fd, json_data.encode('utf-8'))
            os.fsync(temp_fd)
            os.close(temp_fd)
            temp_fd = None
            
            # Atomic rename
            shutil.move(temp_path, job_path)
            temp_path = None
            
            logger.debug(f"Atomic write successful for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Atomic write failed for job {job_id}: {e}")
            return False
        finally:
            # Cleanup
            if temp_fd is not None:
                try:
                    os.close(temp_fd)
                except OSError:
                    pass
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
    
    def create_job(self, job_id: str, resume_text: str = "", job_description: str = "", template: str = "professional") -> Dict:
        """Create a new job with initial status."""
        now = datetime.now(timezone.utc).isoformat()
        
        job_data = {
            "job_id": job_id,
            "status": JobStatus.QUEUED.value,
            "created_at": now,
            "updated_at": now,
            "resume_text": resume_text,
            "job_description": job_description,
            "template": template,
            "agents": {
                "planner": {
                    "status": AgentStatus.PENDING.value,
                    "output": None,
                    "started_at": None,
                    "completed_at": None,
                    "messages": []
                },
                "executor": {
                    "status": AgentStatus.PENDING.value,
                    "output": None,
                    "started_at": None,
                    "completed_at": None,
                    "messages": []
                },
                "critic": {
                    "status": AgentStatus.PENDING.value,
                    "output": None,
                    "started_at": None,
                    "completed_at": None,
                    "messages": []
                }
            },
            "result": None,
            "error": None,
            "progress": 0,
            "retry_count": 0,
            "validation_warnings": [],
            "logs": []
        }
        
        # Update cache
        self._cache[job_id] = job_data
        
        # Persist to disk
        self._atomic_write(job_id, job_data)
        
        self._add_log(job_id, "job_created", {"status": "queued"})
        
        return job_data
    
    def _add_log(self, job_id: str, event: str, details: Dict = None) -> None:
        """Add structured log entry to job."""
        if job_id not in self._cache:
            return
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "details": details or {}
        }
        
        self._cache[job_id]["logs"].append(log_entry)
    
    def update_agent_status(
        self, 
        job_id: str, 
        agent_name: str, 
        status: AgentStatus, 
        output: Optional[str] = None,
        message: Optional[str] = None
    ) -> Optional[Dict]:
        """Update status of a specific agent with optional progress message."""
        if job_id not in self._cache:
            # Try to load from disk
            job_path = self._get_job_path(job_id)
            if job_path.exists():
                try:
                    with open(job_path, 'r') as f:
                        self._cache[job_id] = json.load(f)
                except:
                    return None
            else:
                return None
        
        job_data = self._cache[job_id]
        agent_data = job_data["agents"].get(agent_name)
        if not agent_data:
            return None
        
        now = datetime.now(timezone.utc).isoformat()
        
        # Update agent status
        agent_data["status"] = status.value if isinstance(status, AgentStatus) else status
        
        if status == AgentStatus.RUNNING and not agent_data["started_at"]:
            agent_data["started_at"] = now
        
        if status == AgentStatus.COMPLETE:
            agent_data["completed_at"] = now
            if output:
                agent_data["output"] = output
        
        # Add progress message
        if message:
            agent_data["messages"].append({
                "timestamp": now,
                "message": message
            })
        
        # Update job status
        if status == AgentStatus.RUNNING:
            job_data["status"] = JobStatus.PROCESSING.value
        
        # Update progress
        self._update_progress(job_id)
        
        job_data["updated_at"] = now
        
        # Add structured log
        self._add_log(job_id, "agent_status_update", {
            "agent_name": agent_name,
            "status": agent_data["status"],
            "message": message
        })
        
        # Persist to disk
        self._atomic_write(job_id, job_data)
        
        return job_data
    
    def add_agent_message(self, job_id: str, agent_name: str, message: str) -> Optional[Dict]:
        """Add a progress message to an agent without changing status."""
        if job_id not in self._cache:
            return None
        
        job_data = self._cache[job_id]
        agent_data = job_data["agents"].get(agent_name)
        if not agent_data:
            return None
        
        now = datetime.now(timezone.utc).isoformat()
        agent_data["messages"].append({
            "timestamp": now,
            "message": message
        })
        
        job_data["updated_at"] = now
        
        # Persist to disk
        self._atomic_write(job_id, job_data)
        
        return job_data
    
    def _update_progress(self, job_id: str) -> None:
        """Calculate overall progress based on agent statuses."""
        job_data = self._cache.get(job_id)
        if not job_data:
            return
        
        agents = job_data["agents"]
        progress = 0
        
        # Planner: 0-33%
        planner_status = agents["planner"]["status"]
        if planner_status == AgentStatus.RUNNING.value:
            progress = 15
        elif planner_status == AgentStatus.COMPLETE.value:
            progress = 33
        
        # Executor: 33-66%
        executor_status = agents["executor"]["status"]
        if executor_status == AgentStatus.RUNNING.value:
            progress = 50
        elif executor_status == AgentStatus.COMPLETE.value:
            progress = 66
        
        # Critic: 66-100%
        critic_status = agents["critic"]["status"]
        if critic_status == AgentStatus.RUNNING.value:
            progress = 80
        elif critic_status == AgentStatus.COMPLETE.value:
            progress = 100
        
        job_data["progress"] = progress
    
    def complete_job(self, job_id: str, result: Dict) -> Optional[Dict]:
        """Mark job as complete with final result."""
        if job_id not in self._cache:
            return None
        
        job_data = self._cache[job_id]
        now = datetime.now(timezone.utc).isoformat()
        
        job_data["status"] = JobStatus.COMPLETE.value
        job_data["result"] = result
        job_data["progress"] = 100
        job_data["updated_at"] = now
        
        # Calculate total processing time
        created_at = datetime.fromisoformat(job_data["created_at"].replace('Z', '+00:00'))
        completed_at = datetime.fromisoformat(now.replace('Z', '+00:00'))
        processing_time = (completed_at - created_at).total_seconds()
        
        self._add_log(job_id, "job_completed", {
            "processing_time_seconds": processing_time,
            "result_size": len(str(result))
        })
        
        # Persist to disk
        self._atomic_write(job_id, job_data)
        
        return job_data
    
    def error_job(self, job_id: str, error: str) -> Optional[Dict]:
        """Mark job as failed with error message."""
        if job_id not in self._cache:
            return None
        
        job_data = self._cache[job_id]
        now = datetime.now(timezone.utc).isoformat()
        
        job_data["status"] = JobStatus.ERROR.value
        job_data["error"] = error
        job_data["updated_at"] = now
        
        self._add_log(job_id, "job_error", {"error": error[:500]})
        
        # Persist to disk
        self._atomic_write(job_id, job_data)
        
        return job_data
    
    def increment_retry(self, job_id: str) -> int:
        """Increment retry count and return new count."""
        if job_id not in self._cache:
            return -1
        
        job_data = self._cache[job_id]
        job_data["retry_count"] = job_data.get("retry_count", 0) + 1
        
        self._add_log(job_id, "retry_attempted", {"retry_count": job_data["retry_count"]})
        
        # Persist to disk
        self._atomic_write(job_id, job_data)
        
        return job_data["retry_count"]
    
    def add_validation_warning(self, job_id: str, warning: str) -> None:
        """Add a validation warning to the job."""
        if job_id not in self._cache:
            return
        
        job_data = self._cache[job_id]
        job_data["validation_warnings"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "warning": warning
        })
        
        self._add_log(job_id, "validation_warning", {"warning": warning})
        
        # Persist to disk
        self._atomic_write(job_id, job_data)
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job data by ID."""
        # Check cache first
        if job_id in self._cache:
            return self._cache[job_id]
        
        # Try to load from disk
        job_path = self._get_job_path(job_id)
        if job_path.exists():
            try:
                with open(job_path, 'r') as f:
                    job_data = json.load(f)
                    self._cache[job_id] = job_data
                    return job_data
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load job {job_id}: {e}")
        
        return None
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get job status (without large result data for polling)."""
        job_data = self.get_job(job_id)
        if not job_data:
            return None
        
        # Return a lighter version for status polling
        return {
            "job_id": job_data["job_id"],
            "status": job_data["status"],
            "created_at": job_data["created_at"],
            "updated_at": job_data["updated_at"],
            "progress": job_data["progress"],
            "agents": {
                name: {
                    "status": agent["status"],
                    "started_at": agent["started_at"],
                    "completed_at": agent["completed_at"],
                    "messages": agent["messages"][-5:]  # Last 5 messages only
                }
                for name, agent in job_data["agents"].items()
            },
            "error": job_data.get("error"),
            "result": job_data.get("result"),  # Include result when complete
            "validation_warnings": job_data.get("validation_warnings", [])
        }
    
    def list_jobs(self, status: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """List all jobs, optionally filtered by status."""
        jobs = []
        
        for job_id, job_data in self._cache.items():
            if status and job_data.get("status") != status:
                continue
            jobs.append({
                "job_id": job_data["job_id"],
                "status": job_data["status"],
                "created_at": job_data["created_at"],
                "updated_at": job_data["updated_at"],
                "progress": job_data["progress"]
            })
        
        # Sort by created_at descending
        jobs.sort(key=lambda x: x["created_at"], reverse=True)
        
        return jobs[:limit]
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Remove jobs older than max_age_hours. Returns count of removed jobs."""
        current_time = datetime.now(timezone.utc)
        to_remove = []
        
        for job_id, job_data in self._cache.items():
            try:
                created_at_str = job_data["created_at"]
                if created_at_str.endswith('Z'):
                    created_at_str = created_at_str[:-1] + '+00:00'
                created_at = datetime.fromisoformat(created_at_str)
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                
                age_hours = (current_time - created_at).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    to_remove.append(job_id)
            except Exception as e:
                logger.warning(f"Error checking job age for {job_id}: {e}")
        
        for job_id in to_remove:
            try:
                # Remove from cache
                del self._cache[job_id]
                # Remove file
                job_path = self._get_job_path(job_id)
                if job_path.exists():
                    job_path.unlink()
                logger.info(f"Cleaned up old job {job_id}")
            except Exception as e:
                logger.warning(f"Failed to cleanup job {job_id}: {e}")
        
        return len(to_remove)


# Global job store instance
job_store = FileJobStore()
