"""
Job tracking system for real-time agent status updates.
Tracks progress of multi-agent crew execution.
"""

from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum


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


class JobTracker:
    """In-memory job tracker for agent execution status."""
    
    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
    
    def create_job(self, job_id: str) -> None:
        """Create a new job with initial status."""
        self.jobs[job_id] = {
            "job_id": job_id,
            "status": JobStatus.QUEUED,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "agents": {
                "planner": {"status": AgentStatus.PENDING, "output": None, "started_at": None, "completed_at": None},
                "executor": {"status": AgentStatus.PENDING, "output": None, "started_at": None, "completed_at": None},
                "critic": {"status": AgentStatus.PENDING, "output": None, "started_at": None, "completed_at": None}
            },
            "result": None,
            "error": None,
            "progress": 0  # 0-100
        }
    
    def update_agent_status(self, job_id: str, agent_name: str, status: AgentStatus, output: Optional[str] = None) -> None:
        """Update status of a specific agent."""
        if job_id not in self.jobs:
            return
        
        agent_data = self.jobs[job_id]["agents"][agent_name]
        agent_data["status"] = status
        
        if status == AgentStatus.RUNNING and not agent_data["started_at"]:
            agent_data["started_at"] = datetime.now().isoformat()
        
        if status == AgentStatus.COMPLETE:
            agent_data["completed_at"] = datetime.now().isoformat()
            if output:
                agent_data["output"] = output
        
        # Update job status
        if status == AgentStatus.RUNNING:
            self.jobs[job_id]["status"] = JobStatus.PROCESSING
        
        # Update progress
        self._update_progress(job_id)
        
        self.jobs[job_id]["updated_at"] = datetime.now().isoformat()
    
    def _update_progress(self, job_id: str) -> None:
        """Calculate overall progress based on agent statuses."""
        agents = self.jobs[job_id]["agents"]
        
        # Each agent contributes to progress
        progress = 0
        if agents["planner"]["status"] == AgentStatus.RUNNING:
            progress = 10
        elif agents["planner"]["status"] == AgentStatus.COMPLETE:
            progress = 33
        
        if agents["executor"]["status"] == AgentStatus.RUNNING:
            progress = 40
        elif agents["executor"]["status"] == AgentStatus.COMPLETE:
            progress = 66
        
        if agents["critic"]["status"] == AgentStatus.RUNNING:
            progress = 75
        elif agents["critic"]["status"] == AgentStatus.COMPLETE:
            progress = 100
        
        self.jobs[job_id]["progress"] = progress
    
    def complete_job(self, job_id: str, result: Dict) -> None:
        """Mark job as complete with final result."""
        if job_id not in self.jobs:
            return
        
        self.jobs[job_id]["status"] = JobStatus.COMPLETE
        self.jobs[job_id]["result"] = result
        self.jobs[job_id]["progress"] = 100
        self.jobs[job_id]["updated_at"] = datetime.now().isoformat()
    
    def error_job(self, job_id: str, error: str) -> None:
        """Mark job as failed with error message."""
        if job_id not in self.jobs:
            return
        
        self.jobs[job_id]["status"] = JobStatus.ERROR
        self.jobs[job_id]["error"] = error
        self.jobs[job_id]["updated_at"] = datetime.now().isoformat()
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get current status of a job."""
        return self.jobs.get(job_id)
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> None:
        """Remove jobs older than max_age_hours."""
        current_time = datetime.now()
        to_remove = []
        
        for job_id, job_data in self.jobs.items():
            created_at = datetime.fromisoformat(job_data["created_at"])
            age_hours = (current_time - created_at).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                to_remove.append(job_id)
        
        for job_id in to_remove:
            del self.jobs[job_id]


# Global job tracker instance
job_tracker = JobTracker()
