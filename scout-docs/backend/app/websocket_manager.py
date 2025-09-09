import json
import logging
from typing import Dict, List
from datetime import datetime
from fastapi import WebSocket

logger = logging.getLogger(__name__)

def datetime_serializer(obj):
    """Custom JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

class WebSocketManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        # job_id -> list of websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, job_id: str):
        """Accept and track a WebSocket connection"""
        await websocket.accept()
        
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        
        self.active_connections[job_id].append(websocket)
        logger.info(f"WebSocket connected for job {job_id} (total: {len(self.active_connections[job_id])})")
    
    def disconnect(self, job_id: str, websocket: WebSocket = None):
        """Remove WebSocket connection"""
        if job_id in self.active_connections:
            if websocket:
                try:
                    self.active_connections[job_id].remove(websocket)
                except ValueError:
                    pass
            
            # Clean up empty job entries
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
                logger.info(f"All WebSocket connections closed for job {job_id}")
    
    async def send_update(self, job_id: str, data: dict):
        """Send update to all connections for a job"""
        if job_id not in self.active_connections:
            return
        
        message = json.dumps({
            "type": "job_update",
            "job_id": job_id,
            "data": data
        }, default=datetime_serializer)
        
        # Send to all active connections for this job
        connections_to_remove = []
        for websocket in self.active_connections[job_id][:]:  # Copy list to avoid modification during iteration
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message to {job_id}: {e}")
                connections_to_remove.append(websocket)
        
        # Remove failed connections
        for websocket in connections_to_remove:
            self.disconnect(job_id, websocket)
    
    async def broadcast_message(self, message_type: str, data: dict):
        """Broadcast message to all active connections"""
        message = json.dumps({
            "type": message_type,
            "data": data
        }, default=datetime_serializer)
        
        all_connections = []
        for connections in self.active_connections.values():
            all_connections.extend(connections)
        
        for websocket in all_connections:
            try:
                await websocket.send_text(message)
            except Exception:
                # Let disconnect handle cleanup
                pass