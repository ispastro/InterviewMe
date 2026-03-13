"""
Phase 3 Test Suite: WebSocket Interview Engine
Tests all components of the real-time interview system
"""
import asyncio
import json
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Test imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings
from app.database import engine, Base
from app.models.user import User
from app.models.interview import Interview, Turn
from app.models.feedback import Feedback
from app.modules.auth.dependencies import create_test_token
from app.modules.websocket.connection_manager import ConnectionManager, SessionStatus, MessageType, InterviewSession
from app.modules.websocket.interview_conductor import InterviewConductor
from app.modules.websocket.interview_engine import InterviewEngine

class TestPhase3WebSocketEngine:
    """Test suite for Phase 3 WebSocket Interview Engine"""
    
    @classmethod
    async def setup_class(cls):
        """Set up test environment"""
        print("Setting up Phase 3 test environment...")
        
        # Get settings and engine
        cls.settings = settings
        cls.engine = engine
        
        # Create all tables
        async with cls.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("Phase 3 test environment ready")
    
    async def test_1_connection_manager(self):
        """Test WebSocket connection management"""
        print("\n1. Testing Connection Manager...")
        
        # Create connection manager
        manager = ConnectionManager()
        
        # Test session creation
        session_id = "test-session-123"
        interview_id = "test-interview-456"
        user_id = "test-user-789"
        
        # Create session manually (simulating WebSocket connection)
        session = InterviewSession(session_id, interview_id, user_id)
        manager.active_sessions[session_id] = session
        manager.user_sessions[user_id] = session_id
        
        # Test session retrieval
        retrieved_session = manager.get_session(session_id)
        assert retrieved_session is not None
        assert retrieved_session.session_id == session_id
        assert retrieved_session.interview_id == interview_id
        assert retrieved_session.user_id == user_id
        assert retrieved_session.status == SessionStatus.WAITING
        
        # Test user session lookup
        user_session = manager.get_user_session(user_id)
        assert user_session is not None
        assert user_session.session_id == session_id
        
        # Test status update
        manager.update_session_status(session_id, SessionStatus.ACTIVE)
        assert session.status == SessionStatus.ACTIVE
        
        # Test context update
        test_context = {"test_key": "test_value"}
        manager.update_session_context(session_id, test_context)
        assert session.context["test_key"] == "test_value"
        
        # Test session stats
        stats = manager.get_session_stats()
        assert stats["total_sessions"] == 1
        assert "active" in stats["status_breakdown"]
        
        print("   [OK] Connection Manager working correctly")
    
    async def test_2_interview_conductor(self):
        """Test AI Interview Conductor"""
        print("\n2. Testing Interview Conductor...")
        
        conductor = InterviewConductor()
        
        # Test data
        interview_data = {
            "cv_analysis": {
                "skills": ["Python", "FastAPI", "React"],
                "experience_years": 3,
                "education": "Computer Science"
            },
            "jd_analysis": {
                "required_skills": ["Python", "API Development"],
                "role_level": "Mid-level",
                "company": "Tech Corp"
            },
            "interview_strategy": {
                "focus_areas": ["technical_skills", "problem_solving"],
                "difficulty": "medium"
            }
        }
        
        # Test opening question generation
        opening_question = await conductor.generate_opening_question(interview_data)
        
        assert "question" in opening_question
        assert "question_type" in opening_question
        assert "focus_area" in opening_question
        assert "evaluation_criteria" in opening_question
        assert opening_question["turn_number"] == 1
        assert len(opening_question["question"]) > 10  # Should be a real question
        
        print(f"   [OK] Generated opening question: {opening_question['question'][:50]}...")
        
        # Test follow-up question generation
        conversation_history = [
            {
                "turn_number": 1,
                "question": opening_question["question"],
                "response": "I'm a software developer with 3 years of experience in Python and web development.",
                "evaluation": {"overall_score": 8.0}
            }
        ]
        
        follow_up = await conductor.generate_follow_up_question(
            interview_data, conversation_history, 2
        )
        
        assert "question" in follow_up
        assert follow_up["turn_number"] == 2
        assert len(follow_up["question"]) > 10
        
        print(f"   [OK] Generated follow-up question: {follow_up['question'][:50]}...")
        
        # Test response evaluation
        evaluation = await conductor.evaluate_response(
            opening_question,
            "I'm a passionate developer with experience in Python, FastAPI, and React. I love solving complex problems.",
            interview_data
        )
        
        assert "overall_score" in evaluation
        assert "criteria_scores" in evaluation
        assert "strengths" in evaluation
        assert "areas_for_improvement" in evaluation
        assert "feedback" in evaluation
        assert isinstance(evaluation["overall_score"], (int, float))
        assert 0 <= evaluation["overall_score"] <= 10
        
        print(f"   [OK] Generated evaluation with score: {evaluation['overall_score']}")
        
        # Test interview ending logic
        end_check = await conductor.should_end_interview(conversation_history, 2)
        assert "should_end" in end_check
        assert "reason" in end_check
        assert isinstance(end_check["should_end"], bool)
        
        # Test interview summary
        summary = await conductor.generate_interview_summary(interview_data, conversation_history)
        assert "overall_rating" in summary
        assert "overall_score" in summary
        assert "key_strengths" in summary
        assert "recommendation" in summary
        
        print("   [OK] Interview Conductor working correctly")
    
    async def test_3_database_models(self):
        """Test database models for interview turns and feedback"""
        print("\n3. Testing Database Models...")
        
        async with AsyncSession(self.engine) as db:
            # Create test user
            user = User.create_from_jwt(
                email=f"test-phase3-{datetime.utcnow().timestamp()}@example.com",
                name="Test User"
            )
            db.add(user)
            await db.flush()
            
            # Create test interview
            interview = Interview(
                user_id=user.id,
                target_role="Test Interview",
                status="ready",
                cv_analysis={"skills": ["Python"]},
                jd_analysis={"role": "Developer"},
                interview_config={"focus": "technical"}
            )
            db.add(interview)
            await db.flush()
            
            # Create test turn
            turn = Turn(
                interview_id=interview.id,
                turn_number=1,
                ai_question="What is your experience with Python?",
                phase="technical",
                user_answer="I have 3 years of Python experience.",
                evaluation={
                    "overall_score": 8.5,
                    "criteria_scores": {"technical_knowledge": 8.0},
                    "feedback": "Good response"
                }
            )
            db.add(turn)
            await db.flush()
            
            # Create test feedback
            feedback = Feedback(
                interview_id=interview.id,
                overall_score=85.0,
                strengths=[{"area": "communication", "score": 9.0}],
                weaknesses=[{"area": "technical_depth", "score": 7.0}],
                suggestions=[{"action": "Practice more algorithms", "priority": "medium"}],
                phase_scores={"technical": 8.5},
                summary="Good overall performance"
            )
            db.add(feedback)
            await db.commit()
            
            # Refresh objects to get IDs
            await db.refresh(interview)
            await db.refresh(turn)
            await db.refresh(feedback)
            
            # Verify data was saved
            stmt = select(Turn).where(Turn.interview_id == interview.id)
            result = await db.execute(stmt)
            saved_turn = result.scalar_one()
            
            assert saved_turn.turn_number == 1
            assert saved_turn.phase == "technical"
            assert saved_turn.evaluation["overall_score"] == 8.5
            
            stmt = select(Feedback).where(Feedback.interview_id == interview.id)
            result = await db.execute(stmt)
            saved_feedback = result.scalar_one()
            
            assert saved_feedback.overall_score == 85.0
            assert len(saved_feedback.strengths) == 1
            
        print("   [OK] Database models working correctly")
    
    async def test_4_interview_engine_integration(self):
        """Test Interview Engine integration"""
        print("\n4. Testing Interview Engine Integration...")
        
        # Create components
        connection_manager = ConnectionManager()
        interview_conductor = InterviewConductor()
        interview_engine = InterviewEngine(connection_manager, interview_conductor)
        
        async with AsyncSession(self.engine) as db:
            # Create test data with hardcoded IDs to avoid async issues
            user_id = "12345678-1234-1234-1234-123456789012"
            interview_id = "87654321-4321-4321-4321-210987654321"
            
            # Create session without database interaction
            session = InterviewSession("engine-session", interview_id, user_id)
            connection_manager.active_sessions["engine-session"] = session
            connection_manager.user_sessions[user_id] = "engine-session"
            
            # Test session status retrieval
            status = await interview_engine.get_session_status("engine-session")
            assert status["session_id"] == "engine-session"
            assert status["status"] == SessionStatus.WAITING.value
            assert status["interview_id"] == interview_id
            
            # Test pause/resume (should work even without active interview)
            # First set session to active
            connection_manager.update_session_status("engine-session", SessionStatus.ACTIVE)
            
            pause_result = await interview_engine.pause_interview("engine-session")
            assert pause_result["status"] == "paused"
            
            resume_result = await interview_engine.resume_interview("engine-session")
            assert resume_result["status"] == "resumed"
            
        print("   [OK] Interview Engine integration working correctly")
    
    async def test_5_message_types_and_flow(self):
        """Test message types and interview flow"""
        print("\n5. Testing Message Types and Flow...")
        
        # Test message type enum
        assert MessageType.CONNECT == "connect"
        assert MessageType.START_INTERVIEW == "start_interview"
        assert MessageType.USER_RESPONSE == "user_response"
        assert MessageType.AI_QUESTION == "ai_question"
        assert MessageType.AI_FEEDBACK == "ai_feedback"
        assert MessageType.SESSION_STATUS == "session_status"
        assert MessageType.ERROR == "error"
        assert MessageType.PING == "ping"
        assert MessageType.PONG == "pong"
        
        # Test session status enum
        assert SessionStatus.WAITING == "waiting"
        assert SessionStatus.ACTIVE == "active"
        assert SessionStatus.PAUSED == "paused"
        assert SessionStatus.COMPLETED == "completed"
        assert SessionStatus.DISCONNECTED == "disconnected"
        
        # Test interview session serialization
        session = InterviewSession("test-123", "interview-456", "user-789")
        session_dict = session.to_dict()
        
        assert session_dict["session_id"] == "test-123"
        assert session_dict["interview_id"] == "interview-456"
        assert session_dict["user_id"] == "user-789"
        assert session_dict["status"] == "waiting"
        assert session_dict["current_turn"] == 0
        assert "created_at" in session_dict
        assert "last_activity" in session_dict
        
        print("   [OK] Message types and flow working correctly")
    
    async def test_6_error_handling(self):
        """Test error handling in WebSocket components"""
        print("\n6. Testing Error Handling...")
        
        connection_manager = ConnectionManager()
        interview_conductor = InterviewConductor()
        interview_engine = InterviewEngine(connection_manager, interview_conductor)
        
        # Test invalid session access
        invalid_session = connection_manager.get_session("non-existent")
        assert invalid_session is None
        
        invalid_user_session = connection_manager.get_user_session("non-existent")
        assert invalid_user_session is None
        
        # Test interview engine with invalid session
        try:
            async with AsyncSession(self.engine) as db:
                await interview_engine.get_session_status("non-existent")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Session not found" in str(e)
        
        # Test AI conductor with minimal data (should not crash)
        minimal_data = {"cv_analysis": {}, "jd_analysis": {}, "interview_strategy": {}}
        
        # Should return fallback responses, not crash
        opening = await interview_conductor.generate_opening_question(minimal_data)
        assert "question" in opening
        assert len(opening["question"]) > 0
        
        evaluation = await interview_conductor.evaluate_response(
            {"question": "Test?", "question_type": "test", "evaluation_criteria": []},
            "Test response",
            minimal_data
        )
        assert "overall_score" in evaluation
        assert isinstance(evaluation["overall_score"], (int, float))
        
        print("   [OK] Error handling working correctly")

async def run_phase3_tests():
    """Run all Phase 3 tests"""
    print("=" * 60)
    print("PHASE 3 TEST SUITE: WebSocket Interview Engine")
    print("=" * 60)
    
    test_suite = TestPhase3WebSocketEngine()
    
    try:
        # Setup
        await test_suite.setup_class()
        
        # Run tests
        await test_suite.test_1_connection_manager()
        await test_suite.test_2_interview_conductor()
        await test_suite.test_3_database_models()
        await test_suite.test_4_interview_engine_integration()
        await test_suite.test_5_message_types_and_flow()
        await test_suite.test_6_error_handling()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] ALL PHASE 3 TESTS PASSED!")
        print("WebSocket Interview Engine is ready for production")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n[FAILED] PHASE 3 TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_phase3_tests())
    exit(0 if success else 1)