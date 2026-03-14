"""
WebSocket API Routes for InterviewMe Platform
Real-time communication endpoints for interview sessions
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from typing import Dict, Any, Optional
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...modules.auth.dependencies import get_current_user_websocket
from ...models.user import User
from .connection_manager import connection_manager, MessageType, SessionStatus
from .interview_conductor import interview_conductor
from .interview_engine import InterviewEngine

# Create router
router = APIRouter(prefix="/ws", tags=["websocket"])

# Initialize interview engine
interview_engine = InterviewEngine(connection_manager, interview_conductor)

@router.websocket("/interview/{interview_id}")
async def websocket_interview_endpoint(
    websocket: WebSocket,
    interview_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time interview sessions"""
    
    session_id = None
    print(f"🔵 WebSocket connection attempt for interview {interview_id}")
    
    try:
        # Authenticate user via token
        print(f"🔑 Authenticating user...")
        user = await get_current_user_websocket(token, db)
        if not user:
            print(f"❌ Authentication failed for interview {interview_id}")
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        print(f"✅ User {user.id} authenticated successfully")
            
        # Connect to WebSocket and create session
        print(f"🔌 Accepting WebSocket connection...")
        session_id = await connection_manager.connect(websocket, user.id, interview_id)
        print(f"✅ User {user.id} connected to interview {interview_id} with session {session_id}")
        
        # Main message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Process message based on type
                await handle_websocket_message(session_id, message, db)
                
            except WebSocketDisconnect:
                print(f"WebSocket disconnected for session {session_id}")
                break
            except json.JSONDecodeError as e:
                print(f"Invalid JSON from session {session_id}: {e}")
                # Try to send error, but don't crash if it fails
                try:
                    await connection_manager.send_error(
                        session_id, 
                        "Invalid JSON format", 
                        "INVALID_JSON"
                    )
                except Exception:
                    pass  # Connection might be dead, just continue
            except Exception as e:
                print(f"Error processing message for session {session_id}: {e}")
                # Try to send error, but don't crash if it fails
                try:
                    await connection_manager.send_error(
                        session_id, 
                        f"Error processing message: {str(e)}", 
                        "MESSAGE_PROCESSING_ERROR"
                    )
                except Exception:
                    pass  # Connection might be dead, just continue
                
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        # Only try to send error if we have a valid session_id and connection
        if session_id and session_id in connection_manager.active_connections:
            try:
                await connection_manager.send_error(
                    session_id, 
                    f"Connection error: {str(e)}", 
                    "CONNECTION_ERROR"
                )
            except Exception:
                pass  # Connection is dead, can't send error
        
        # Try to close WebSocket gracefully
        try:
            await websocket.close(code=4000, reason="Connection error")
        except Exception:
            pass  # Already closed or invalid state
    finally:
        if session_id:
            await connection_manager.disconnect(session_id)
            print(f"Session {session_id} disconnected and cleaned up")

async def handle_websocket_message(session_id: str, message: Dict[str, Any], db: AsyncSession):
    """Handle incoming WebSocket messages"""
    
    message_type = message.get("type")
    data = message.get("data", {})
    
    # Verify session still exists
    if session_id not in connection_manager.active_sessions:
        print(f"Cannot handle message: session {session_id} no longer exists")
        return
    
    try:
        if message_type == MessageType.START_INTERVIEW:
            # Start the interview session
            result = await interview_engine.start_interview(session_id, db)
            print(f"Interview started for session {session_id}: {result}")
            
        elif message_type == MessageType.USER_RESPONSE:
            # Process user response
            user_response = data.get("response", "").strip()
            if not user_response:
                await connection_manager.send_error(
                    session_id, 
                    "Response cannot be empty", 
                    "EMPTY_RESPONSE"
                )
                return
                
            result = await interview_engine.process_user_response(session_id, user_response, db)
            print(f"User response processed for session {session_id}")
            
        elif message_type == "pause_interview":
            # Pause the interview
            result = await interview_engine.pause_interview(session_id)
            print(f"Interview paused for session {session_id}")
            
        elif message_type == "resume_interview":
            # Resume the interview
            result = await interview_engine.resume_interview(session_id)
            print(f"Interview resumed for session {session_id}")
            
        elif message_type == "end_interview":
            # End the interview
            result = await interview_engine.end_interview(session_id, db)
            print(f"Interview ended for session {session_id}")
            
        elif message_type == "get_status":
            # Get session status
            status = await interview_engine.get_session_status(session_id)
            await connection_manager.send_message(session_id, {
                "type": "status_response",
                "data": status
            })
            
        elif message_type == MessageType.PING:
            # Handle ping for connection health check
            await connection_manager.send_message(session_id, {
                "type": MessageType.PONG,
                "data": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "session_id": session_id
                }
            })
            
        else:
            await connection_manager.send_error(
                session_id, 
                f"Unknown message type: {message_type}", 
                "UNKNOWN_MESSAGE_TYPE"
            )
            
    except ValueError as e:
        # Try to send error, but don't crash if connection is dead
        try:
            await connection_manager.send_error(
                session_id, 
                str(e), 
                "VALIDATION_ERROR"
            )
        except Exception:
            print(f"Failed to send validation error to session {session_id}")
            pass
    except Exception as e:
        print(f"Error handling message type {message_type} for session {session_id}: {e}")
        import traceback
        traceback.print_exc()  # Print full stack trace for debugging
        # Try to send error, but don't crash if connection is dead
        try:
            await connection_manager.send_error(
                session_id, 
                f"Internal error: {str(e)}", 
                "INTERNAL_ERROR"
            )
        except Exception:
            print(f"Failed to send internal error to session {session_id}")
            pass

# REST endpoints for WebSocket management
@router.get("/sessions/stats")
async def get_session_stats():
    """Get WebSocket session statistics"""
    return connection_manager.get_session_stats()

@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """Get status of a specific session"""
    try:
        status = await interview_engine.get_session_status(session_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/sessions/{session_id}/end")
async def force_end_session(
    session_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """Force end a session (admin/debugging endpoint)"""
    try:
        result = await interview_engine.end_interview(session_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Health check endpoint
@router.get("/health")
async def websocket_health_check():
    """Health check for WebSocket service"""
    stats = connection_manager.get_session_stats()
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_sessions": stats["total_sessions"],
        "active_connections": stats["active_connections"]
    }