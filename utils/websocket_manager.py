"""
WebSocket Manager for real-time job updates.
Handles WebSocket connections and event emission.
"""

import asyncio
import logging
from typing import Dict, Set, Optional
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, job_id: str) -> bool:
        """Connect a websocket to a job's update stream."""
        try:
            await websocket.accept()
            async with self._lock:
                if job_id not in self._connections:
                    self._connections[job_id] = set()
                self._connections[job_id].add(websocket)
            logger.info(f"WebSocket connected for job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect websocket for job {job_id}: {e}")
            return False
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect a websocket."""
        async with self._lock:
            for job_id, sockets in list(self._connections.items()):
                if websocket in sockets:
                    sockets.discard(websocket)
                    if not sockets:
                        del self._connections[job_id]
                    break
    
    async def broadcast(self, job_id: str, message: dict):
        """Broadcast a message to all websockets connected to a job."""
        async with self._lock:
            sockets = self._connections.get(job_id, set()).copy()
        
        disconnected = []
        for websocket in sockets:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        
        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    self._connections.get(job_id, set()).discard(ws)


class JobEventEmitter:
    """Emits events for a specific job to connected WebSocket clients."""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
    
    def _emit(self, event_type: str, data: dict):
        """Emit an event (runs async broadcast in background)."""
        message = {"type": event_type, "job_id": self.job_id, "data": data}
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(ws_manager.broadcast(self.job_id, message))
            else:
                loop.run_until_complete(ws_manager.broadcast(self.job_id, message))
        except RuntimeError:
            pass
    
    def progress(self, percent: int, message: str):
        """Emit a progress update."""
        self._emit("progress", {"percent": percent, "message": message})
    
    def agent_status(self, agent: str, status: str, message: Optional[str] = None):
        """Emit an agent status update."""
        data = {"agent": agent, "status": status}
        if message:
            data["message"] = message
        self._emit("agent_status", data)
    
    def validation_warning(self, warning: str):
        """Emit a validation warning."""
        self._emit("validation_warning", {"warning": warning})
    
    def job_completed(self, result: dict):
        """Emit job completion event."""
        self._emit("job_completed", {
            "status": "completed",
            "retry_count": result.get("retry_count", 0),
            "template_used": result.get("template_used", "")
        })
    
    def job_failed(self, error: str):
        """Emit job failure event."""
        self._emit("job_failed", {"status": "failed", "error": error})


# Global instance
ws_manager = WebSocketManager()
