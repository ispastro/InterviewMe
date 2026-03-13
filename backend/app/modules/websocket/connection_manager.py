"""
WebSocket Connection Manager for InterviewMe Platform
Handles real-time connections, session state, and message routing
"""
from typing import Dict, List, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
import json
import uuid
from datetime import datetime
import asyncio
from enum import Enum

class SessionStatus(str, Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    DISCONNECTED = "disconnected"

class MessageType(str, Enum):
    CONNECT = "connect"
    START_INTERVIEW = "start_interview"
    USER_RESPONSE = "user_response"
    AI_QUESTION = "ai_question"
    AI_FEEDBACK = "ai_feedback"
    SESSION_STATUS = "session_status"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"

class InterviewSession:
    """Represents an active interview session"""
    
    def __init__(self, session_id: str, interview_id: str, user_id: str):
        self.session_id = session_id
        self.interview_id = interview_id
        self.user_id = user_id
        self.status = SessionStatus.WAITING
        self.current_turn = 0
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.context: Dict[str, Any] = {}
        
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "interview_id": self.interview_id,
            "user_id": self.user_id,
            "status": self.status.value,
            "current_turn": self.current_turn,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "context": self.context
        }

class ConnectionManager:
    """Manages WebSocket connections and interview sessions"""
    
    def __init__(self):
        # Active WebSocket connections: {session_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # Active interview sessions: {session_id: InterviewSession}
        self.active_sessions: Dict[str, InterviewSession] = {}
        # User to session mapping: {user_id: session_id}
        self.user_sessions: Dict[str, str] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str, interview_id: str) -> str:
        """Accept WebSocket connection and create session"""
        await websocket.accept()
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Create interview session
        session = InterviewSession(session_id, interview_id, user_id)
        
        # Store connection and session
        self.active_connections[session_id] = websocket
        self.active_sessions[session_id] = session
        self.user_sessions[user_id] = session_id
        
        # Send connection confirmation
        await self.send_message(session_id, {
            "type": MessageType.CONNECT,
            "data": {
                "session_id": session_id,
                "status": "connected",
                "message": "WebSocket connection established"
            }
        })
        
        return session_id
        
    async def disconnect(self, session_id: str):
        """Handle WebSocket disconnection"""
        if session_id in self.active_connections:
            # Update session status
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.status = SessionStatus.DISCONNECTED
                session.update_activity()
                
                # Remove from user mapping
                if session.user_id in self.user_sessions:
                    del self.user_sessions[session.user_id]
            
            # Remove connection
            del self.active_connections[session_id]
            
    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """Send message to specific session"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_text(json.dumps(message))
                
                # Update session activity
                if session_id in self.active_sessions:
                    self.active_sessions[session_id].update_activity()
                    
            except Exception as e:
                print(f"Error sending message to session {session_id}: {e}")
                await self.disconnect(session_id)
                
    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to all sessions of a user"""
        if user_id in self.user_sessions:
            session_id = self.user_sessions[user_id]
            await self.send_message(session_id, message)
            
    async def send_error(self, session_id: str, error_message: str, error_code: str = "GENERAL_ERROR"):
        """Send error message to session"""
        await self.send_message(session_id, {
            "type": MessageType.ERROR,
            "data": {
                "error_code": error_code,
                "message": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        """Get interview session by ID"""
        return self.active_sessions.get(session_id)
        
    def get_user_session(self, user_id: str) -> Optional[InterviewSession]:
        """Get active session for user"""
        if user_id in self.user_sessions:
            session_id = self.user_sessions[user_id]
            return self.active_sessions.get(session_id)
        return None
        
    def update_session_status(self, session_id: str, status: SessionStatus):
        """Update session status"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.status = status
            session.update_activity()
            
    def update_session_context(self, session_id: str, context_update: Dict[str, Any]):
        """Update session context"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.context.update(context_update)
            session.update_activity()
            
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len(self.active_sessions)
        
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        status_counts = {}
        for session in self.active_sessions.values():
            status = session.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
        return {
            "total_sessions": len(self.active_sessions),
            "active_connections": len(self.active_connections),
            "status_breakdown": status_counts
        }

# Global connection manager instance
connection_manager = ConnectionManager()