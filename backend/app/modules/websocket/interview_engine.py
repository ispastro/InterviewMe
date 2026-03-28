
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...models.interview import Interview, Turn, InterviewPhase
from ...models import InterviewStatus
from ...models.feedback import Feedback
from ...models.user import User
from ..interviews import service as interview_service
from .connection_manager import ConnectionManager, SessionStatus, MessageType, InterviewSession
from .interview_conductor import InterviewConductor
from .conversation_memory import ConversationMemory
import json


def _map_question_type_to_phase(question_type: str) -> str:
    if not question_type:
        return InterviewPhase.TECHNICAL.value

    q = question_type.lower()
    if q in ("opening", "intro", "introduction"):
        return InterviewPhase.INTRO.value
    if q in ("behavioral", "situational"):
        return InterviewPhase.BEHAVIORAL.value
    if q in ("technical", "coding"):
        return InterviewPhase.TECHNICAL.value
    if q in ("deep_dive", "deep-dive"):
        return InterviewPhase.DEEP_DIVE.value
    if q in ("closing", "wrap_up", "wrap-up"):
        return InterviewPhase.CLOSING.value
    return InterviewPhase.TECHNICAL.value

class InterviewEngine:
    
    def __init__(self, connection_manager: ConnectionManager, interview_conductor: InterviewConductor):
        self.connection_manager = connection_manager
        self.interview_conductor = interview_conductor
        self.interview_service = interview_service
        # Memory instances per session: {session_id: ConversationMemory}
        self.session_memories: Dict[str, ConversationMemory] = {}
        
    async def start_interview(self, session_id: str, db: AsyncSession) -> Dict[str, Any]:
        session = self.connection_manager.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
            
        try:
            # Get user from database
            user_stmt = select(User).where(User.id == session.user_id)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            if not user:
                raise ValueError("User not found")
            
            # Get interview data from database
            interview = await interview_service.get_interview_by_id(db, uuid.UUID(session.interview_id), user)
            if not interview:
                raise ValueError("Interview not found")
                
            # Start only when first entering live session; allow reconnects for in-progress interviews.
            if interview.status == InterviewStatus.READY:
                interview = await interview_service.start_interview(db, uuid.UUID(session.interview_id), user)
            elif interview.status != InterviewStatus.IN_PROGRESS:
                raise ValueError(f"Interview is in invalid state for websocket start: {interview.status}")
            
            # Update session status
            self.connection_manager.update_session_status(session_id, SessionStatus.ACTIVE)
            
            # Generate opening question
            strategy = {}
            if isinstance(interview.interview_config, dict):
                strategy = interview.interview_config.get("strategy", {})

            interview_data = {
                "cv_analysis": interview.cv_analysis,
                "jd_analysis": interview.jd_analysis,
                "interview_strategy": strategy
            }
            
            opening_question = await self.interview_conductor.generate_opening_question(interview_data)
            
            # Initialize conversation memory for this session
            memory = ConversationMemory(
                cv_analysis=interview.cv_analysis,
                jd_analysis=interview.jd_analysis
            )
            self.session_memories[session_id] = memory
            
            # Store question in session context
            self.connection_manager.update_session_context(session_id, {
                "current_question": opening_question,
                "interview_data": interview_data,
                "conversation_history": []
            })
            
            # Send opening question to client
            await self.connection_manager.send_message(session_id, {
                "type": MessageType.AI_QUESTION,
                "data": {
                    "question": opening_question["question"],
                    "question_type": opening_question["question_type"],
                    "turn_number": opening_question["turn_number"],
                    "focus_area": opening_question["focus_area"],
                    "expected_duration": opening_question["expected_duration"]
                }
            })
            
            # Send session status update
            await self.connection_manager.send_message(session_id, {
                "type": MessageType.SESSION_STATUS,
                "data": {
                    "status": SessionStatus.ACTIVE.value,
                    "message": "Interview started successfully",
                    "turn_number": 1
                }
            })
            
            return {
                "status": "started",
                "session_id": session_id,
                "opening_question": opening_question
            }
            
        except Exception as e:
            await self.connection_manager.send_error(
                session_id, 
                f"Failed to start interview: {str(e)}", 
                "START_INTERVIEW_ERROR"
            )
            raise
    
    async def process_user_response(
        self,
        session_id: str,
        user_response: str,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        session = self.connection_manager.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
            
        # More graceful handling of non-active states
        if session.status != SessionStatus.ACTIVE:
            # Send informative error instead of raising exception
            await self.connection_manager.send_error(
                session_id,
                f"Cannot process response: interview is {session.status.value}. Please wait for the interview to become active.",
                "SESSION_NOT_ACTIVE"
            )
            return {
                "status": "rejected",
                "reason": f"Session is {session.status.value}",
                "session_status": session.status.value
            }
            
        try:
            # Get session context
            context = session.context
            current_question = context.get("current_question", {})
            interview_data = context.get("interview_data", {})
            conversation_history = context.get("conversation_history", [])
            
            # Evaluate the user response
            evaluation = await self.interview_conductor.evaluate_response(
                current_question, user_response, interview_data
            )
            
            # Create turn record
            turn_data = {
                "turn_number": current_question.get("turn_number", session.current_turn + 1),
                "question": current_question.get("question", ""),
                "question_type": current_question.get("question_type", ""),
                "response": user_response,
                "evaluation": evaluation,
                "timestamp": datetime.utcnow()
            }
            
            # Save turn to database
            await self._save_turn_to_db(session.interview_id, turn_data, db)
            
            # Add to conversation history
            conversation_history.append(turn_data)
            session.current_turn += 1
            
            # Add to conversation memory for agentic behavior
            memory = self.session_memories.get(session_id)
            if memory:
                memory.add_turn(turn_data)
            
            # Send evaluation feedback to client
            try:
                await self.connection_manager.send_message(session_id, {
                    "type": MessageType.AI_FEEDBACK,
                    "data": {
                        "question_id": f"turn-{turn_data['turn_number']}",
                        "turn_number": turn_data["turn_number"],
                        **evaluation,
                    }
                })
            except Exception as e:
                print(f"Failed to send feedback to session {session_id}: {e}")
            
            # Check if we should probe deeper (agentic decision)
            memory = self.session_memories.get(session_id)
            if memory:
                should_probe, probe_reason = memory.should_probe_deeper(turn_data)
                
                if should_probe:
                    # Generate probing follow-up question
                    probe_question = await self.interview_conductor.generate_probe_question(
                        turn_data, probe_reason, interview_data
                    )
                    
                    # Send probe question (doesn't increment turn)
                    try:
                        await self.connection_manager.send_message(session_id, {
                            "type": MessageType.AI_QUESTION,
                            "data": {
                                "question": probe_question["question"],
                                "question_type": "probe",
                                "turn_number": turn_data["turn_number"],
                                "focus_area": turn_data.get("focus_area", ""),
                                "expected_duration": 2,
                                "is_probe": True,
                                "probe_reason": probe_reason
                            }
                        })
                    except Exception as e:
                        print(f"Failed to send probe question to session {session_id}: {e}")
                    
                    # Update context with probe question
                    self.connection_manager.update_session_context(session_id, {
                        "current_question": probe_question
                    })
                    
                    return {
                        "status": "probing",
                        "probe_question": probe_question,
                        "probe_reason": probe_reason,
                        "turn_number": session.current_turn
                    }
            
            # Check if interview should end
            should_end_check = await self.interview_conductor.should_end_interview(
                conversation_history, session.current_turn
            )
            
            if should_end_check["should_end"]:
                return await self.end_interview(session_id, db)
            
            # Get intelligent context from memory
            relevant_context = None
            next_focus_recommendation = None
            if memory:
                # Get recommendation for next focus area
                next_focus_recommendation = memory.get_next_focus_recommendation()
                next_focus_area = next_focus_recommendation.get("priority_topics", [""])[0] if next_focus_recommendation.get("priority_topics") else ""
                
                # Get relevant context for next question
                relevant_context = memory.get_relevant_context(next_focus_area)
            
            # Generate next question with enhanced context
            next_question = await self.interview_conductor.generate_follow_up_question(
                interview_data, 
                conversation_history, 
                session.current_turn + 1,
                memory_context=relevant_context,
                focus_recommendation=next_focus_recommendation
            )
            
            # Update session context
            self.connection_manager.update_session_context(session_id, {
                "current_question": next_question,
                "conversation_history": conversation_history
            })
            
            # Send next question to client
            try:
                await self.connection_manager.send_message(session_id, {
                    "type": MessageType.AI_QUESTION,
                    "data": {
                        "question": next_question["question"],
                        "question_type": next_question["question_type"],
                        "turn_number": next_question["turn_number"],
                        "focus_area": next_question["focus_area"],
                        "expected_duration": next_question["expected_duration"]
                    }
                })
            except Exception as e:
                print(f"Failed to send next question to session {session_id}: {e}")
            
            return {
                "status": "processed",
                "evaluation": evaluation,
                "next_question": next_question,
                "turn_number": session.current_turn
            }
            
        except Exception as e:
            await self.connection_manager.send_error(
                session_id, 
                f"Failed to process response: {str(e)}", 
                "PROCESS_RESPONSE_ERROR"
            )
            raise
    
    async def pause_interview(self, session_id: str) -> Dict[str, Any]:
        session = self.connection_manager.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
            
        if session.status != SessionStatus.ACTIVE:
            raise ValueError("Can only pause active sessions")
            
        # Update session status
        self.connection_manager.update_session_status(session_id, SessionStatus.PAUSED)
        
        # Send status update to client
        await self.connection_manager.send_message(session_id, {
            "type": MessageType.SESSION_STATUS,
            "data": {
                "status": SessionStatus.PAUSED.value,
                "message": "Interview paused",
                "turn_number": session.current_turn
            }
        })
        
        return {
            "status": "paused",
            "session_id": session_id,
            "turn_number": session.current_turn
        }
    
    async def resume_interview(self, session_id: str) -> Dict[str, Any]:
        session = self.connection_manager.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
            
        if session.status != SessionStatus.PAUSED:
            raise ValueError("Can only resume paused sessions")
            
        # Update session status
        self.connection_manager.update_session_status(session_id, SessionStatus.ACTIVE)
        
        # Send current question again
        context = session.context
        current_question = context.get("current_question", {})
        
        if current_question:
            await self.connection_manager.send_message(session_id, {
                "type": MessageType.AI_QUESTION,
                "data": {
                    "question": current_question["question"],
                    "question_type": current_question["question_type"],
                    "turn_number": current_question["turn_number"],
                    "focus_area": current_question["focus_area"],
                    "expected_duration": current_question["expected_duration"]
                }
            })
        
        # Send status update to client
        await self.connection_manager.send_message(session_id, {
            "type": MessageType.SESSION_STATUS,
            "data": {
                "status": SessionStatus.ACTIVE.value,
                "message": "Interview resumed",
                "turn_number": session.current_turn
            }
        })
        
        return {
            "status": "resumed",
            "session_id": session_id,
            "turn_number": session.current_turn
        }
    
    async def end_interview(self, session_id: str, db: AsyncSession) -> Dict[str, Any]:
        session = self.connection_manager.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
            
        try:
            # Get user from database
            user_stmt = select(User).where(User.id == session.user_id)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            if not user:
                raise ValueError("User not found")
            
            # Get conversation history
            context = session.context
            conversation_history = context.get("conversation_history", [])
            interview_data = context.get("interview_data", {})
            
            # Generate interview summary
            summary = await self.interview_conductor.generate_interview_summary(
                interview_data, conversation_history
            )
            
            # Save summary to database
            await self._save_interview_summary(session.interview_id, summary, db)
            
            # Update interview status to completed
            await interview_service.complete_interview(db, uuid.UUID(session.interview_id), user)
            
            # Clean up session memory
            if session_id in self.session_memories:
                del self.session_memories[session_id]
            
            # Update session status
            self.connection_manager.update_session_status(session_id, SessionStatus.COMPLETED)
            
            # Send summary to client
            await self.connection_manager.send_message(session_id, {
                "type": MessageType.SESSION_STATUS,
                "data": {
                    "status": SessionStatus.COMPLETED.value,
                    "message": "Interview completed",
                    "summary": summary,
                    "total_turns": len(conversation_history)
                }
            })
            
            return {
                "status": "completed",
                "session_id": session_id,
                "summary": summary,
                "total_turns": len(conversation_history)
            }
            
        except Exception as e:
            await self.connection_manager.send_error(
                session_id, 
                f"Failed to end interview: {str(e)}", 
                "END_INTERVIEW_ERROR"
            )
            raise
    
    async def _save_turn_to_db(self, interview_id: str, turn_data: Dict[str, Any], db: AsyncSession):
        try:
            # Check if turn already exists
            existing_turn_stmt = select(Turn).where(
                Turn.interview_id == uuid.UUID(interview_id),
                Turn.turn_number == turn_data["turn_number"]
            )
            existing_turn_result = await db.execute(existing_turn_stmt)
            existing_turn = existing_turn_result.scalar_one_or_none()
            
            if existing_turn:
                print(f"Turn {turn_data['turn_number']} already exists for interview {interview_id}, skipping...")
                return
            
            # Create new turn
            turn = Turn(
                id=uuid.uuid4(),
                interview_id=uuid.UUID(interview_id),
                turn_number=turn_data["turn_number"],
                phase=_map_question_type_to_phase(turn_data.get("question_type", "")),
                ai_question=turn_data["question"],
                user_answer=turn_data["response"],
                evaluation=turn_data["evaluation"],
                created_at=turn_data["timestamp"]
            )
            
            db.add(turn)
            await db.flush()
            print(f"✅ Saved turn {turn_data['turn_number']} for interview {interview_id}")
            
        except Exception as e:
            print(f"❌ Error saving turn to database: {e}")
            # Don't raise - allow interview to continue even if turn save fails
            import traceback
            traceback.print_exc()
    
    async def _save_interview_summary(self, interview_id: str, summary: Dict[str, Any], db: AsyncSession):
        strengths = [{"area": s, "score": 75} for s in summary.get("key_strengths", [])]
        weaknesses = [{"area": w, "score": 45} for w in summary.get("key_concerns", [])]
        suggestions = [
            {"action": step, "priority": "medium"}
            for step in summary.get("next_steps", [])
        ]

        feedback = Feedback(
            id=uuid.uuid4(),
            interview_id=uuid.UUID(interview_id),
            overall_score=float(summary.get("overall_score", 0)) * 10,
            summary=summary.get("recommendation_reason") or summary.get("overall_rating"),
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            phase_scores={
                "intro": 0,
                "behavioral": 0,
                "technical": float(summary.get("overall_score", 0)) * 10,
                "deep_dive": 0,
                "closing": 0,
            },
            detailed_analysis=json.dumps(summary),
            generation_metadata={"source": "websocket_summary"},
            created_at=datetime.utcnow()
        )
        
        db.add(feedback)
        await db.flush()
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        session = self.connection_manager.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
            
        context = session.context
        return {
            "session_id": session_id,
            "status": session.status.value,
            "current_turn": session.current_turn,
            "interview_id": session.interview_id,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "current_question": context.get("current_question", {}),
            "conversation_history_length": len(context.get("conversation_history", []))
        }

interview_engine = None