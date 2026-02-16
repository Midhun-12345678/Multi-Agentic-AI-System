"""
WebSocket manager for real-time job status updates.
Replaces polling architecture with push-based updates.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Callable, Any
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

logger = logging.getLogger(__name__)


class WebSocketEventType(str, Enum):
    """Event types for WebSocket messages."""
    CONNECTED = "connected"
    AGENT_STARTED = "agent_started"
    AGENT_MESSAGE = "agent_message"
    AGENT_COMPLETED = "agent_completed"
    VALIDATION_WARNING = "validation_warning"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_PROGRESS = "job_progress"
    ERROR = "error"


class ConnectionManager:
    """
    Manages WebSocket connections for job status updates.
    Clients subscribe to specific job_ids.
    """
    
    def __init__(self):
        # job_id -> set of connected websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> job_id (for cleanup)
        self.websocket_jobs: Dict[WebSocket, str] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, job_id: str) -> bool:
        """Accept WebSocket connection and subscribe to job updates."""
        try:
            await websocket.accept()
            
            async with self._lock:
                if job_id not in self.active_connections:
                    self.active_connections[job_id] = set()
                self.active_connections[job_id].add(websocket)
                self.websocket_jobs[websocket] = job_id
            
            logger.info(f"WebSocket connected for job {job_id}")
            
            # Send connection confirmation
            await self.send_event(
                websocket,
                WebSocketEventType.CONNECTED,
                {"job_id": job_id, "message": "Connected to job updates"}
            )
            
            return True
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            return False
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket from active connections."""
        async with self._lock:
            job_id = self.websocket_jobs.pop(websocket, None)
            if job_id and job_id in self.active_connections:
                self.active_connections[job_id].discard(websocket)
                if not self.active_connections[job_id]:
                    del self.active_connections[job_id]
        
        logger.info(f"WebSocket disconnected for job {job_id}")
    
    async def send_event(
        self, 
        websocket: WebSocket, 
        event_type: WebSocketEventType, 
        data: Dict
    ) -> bool:
        """Send event to a single WebSocket."""
        try:
            message = {
                "type": event_type.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data
            }
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.warning(f"Failed to send WebSocket message: {e}")
            return False
    
    async def broadcast_to_job(
        self, 
        job_id: str, 
        event_type: WebSocketEventType, 
        data: Dict
    ) -> int:
        """Broadcast event to all connections for a job. Returns count of successful sends."""
        async with self._lock:
            connections = self.active_connections.get(job_id, set()).copy()
        
        if not connections:
            return 0
        
        message = {
            "type": event_type.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
        
        success_count = 0
        disconnected = []
        
        for websocket in connections:
            try:
                await websocket.send_json(message)
                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for ws in disconnected:
            await self.disconnect(ws)
        
        return success_count
    
    async def send_agent_started(self, job_id: str, agent_name: str) -> int:
        """Send agent_started event."""
        return await self.broadcast_to_job(
            job_id,
            WebSocketEventType.AGENT_STARTED,
            {
                "job_id": job_id,
                "agent": agent_name,
                "message": f"{agent_name.title()} agent started"
            }
        )
    
    async def send_agent_message(self, job_id: str, agent_name: str, message: str) -> int:
        """Send progress message from agent."""
        return await self.broadcast_to_job(
            job_id,
            WebSocketEventType.AGENT_MESSAGE,
            {
                "job_id": job_id,
                "agent": agent_name,
                "message": message
            }
        )
    
    async def send_agent_completed(
        self, 
        job_id: str, 
        agent_name: str, 
        output_size: int = 0
    ) -> int:
        """Send agent_completed event."""
        return await self.broadcast_to_job(
            job_id,
            WebSocketEventType.AGENT_COMPLETED,
            {
                "job_id": job_id,
                "agent": agent_name,
                "message": f"{agent_name.title()} agent completed",
                "output_size": output_size
            }
        )
    
    async def send_validation_warning(self, job_id: str, warning: str) -> int:
        """Send validation_warning event."""
        return await self.broadcast_to_job(
            job_id,
            WebSocketEventType.VALIDATION_WARNING,
            {
                "job_id": job_id,
                "warning": warning
            }
        )
    
    async def send_job_completed(self, job_id: str, result: Dict) -> int:
        """Send job_completed event with results."""
        return await self.broadcast_to_job(
            job_id,
            WebSocketEventType.JOB_COMPLETED,
            {
                "job_id": job_id,
                "message": "Resume optimization complete",
                "result": result
            }
        )
    
    async def send_job_failed(self, job_id: str, error: str) -> int:
        """Send job_failed event."""
        return await self.broadcast_to_job(
            job_id,
            WebSocketEventType.JOB_FAILED,
            {
                "job_id": job_id,
                "error": error
            }
        )
    
    async def send_progress(self, job_id: str, progress: int, status: str) -> int:
        """Send progress update."""
        return await self.broadcast_to_job(
            job_id,
            WebSocketEventType.JOB_PROGRESS,
            {
                "job_id": job_id,
                "progress": progress,
                "status": status
            }
        )
    
    def has_connections(self, job_id: str) -> bool:
        """Check if any connections exist for a job."""
        return bool(self.active_connections.get(job_id))
    
    def get_connection_count(self, job_id: str) -> int:
        """Get number of connections for a job."""
        return len(self.active_connections.get(job_id, set()))


# Global connection manager instance
ws_manager = ConnectionManager()


class JobEventEmitter:
    """
    Helper class to emit events for a specific job.
    Used in background task to send real-time updates.
    """
    
    def __init__(self, job_id: str, manager: ConnectionManager = None):
        self.job_id = job_id
        self.manager = manager or ws_manager
        self._event_loop = None
    
    def _get_loop(self):
        """Get or create event loop for sync context."""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            if self._event_loop is None:
                self._event_loop = asyncio.new_event_loop()
            return self._event_loop
    
    def _run_async(self, coro):
        """Run coroutine from sync context."""
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, create a task
            asyncio.create_task(coro)
        except RuntimeError:
            # We're in a sync context, use run_until_complete
            loop = self._get_loop()
            try:
                loop.run_until_complete(coro)
            except RuntimeError:
                # Loop already running in another thread
                pass
    
    def agent_started(self, agent_name: str) -> None:
        """Emit agent_started event (sync wrapper)."""
        self._run_async(self.manager.send_agent_started(self.job_id, agent_name))
    
    def agent_message(self, agent_name: str, message: str) -> None:
        """Emit agent progress message (sync wrapper)."""
        self._run_async(self.manager.send_agent_message(self.job_id, agent_name, message))
    
    def agent_completed(self, agent_name: str, output_size: int = 0) -> None:
        """Emit agent_completed event (sync wrapper)."""
        self._run_async(self.manager.send_agent_completed(self.job_id, agent_name, output_size))
    
    def validation_warning(self, warning: str) -> None:
        """Emit validation_warning event (sync wrapper)."""
        self._run_async(self.manager.send_validation_warning(self.job_id, warning))
    
    def job_completed(self, result: Dict) -> None:
        """Emit job_completed event (sync wrapper)."""
        self._run_async(self.manager.send_job_completed(self.job_id, result))
    
    def job_failed(self, error: str) -> None:
        """Emit job_failed event (sync wrapper)."""
        self._run_async(self.manager.send_job_failed(self.job_id, error))
    
    def progress(self, progress: int, status: str) -> None:
        """Emit progress update (sync wrapper)."""
        self._run_async(self.manager.send_progress(self.job_id, progress, status))
