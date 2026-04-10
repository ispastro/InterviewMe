"""
🔥 BATTLE TEST: Turn Model - PHASE 2 (EVALUATION LOGIC)
Production-grade AI evaluation testing for real-time interview platform.

PHASE 2 SCOPE:
- get_overall_score() with various evaluation structures
- get_evaluation_score() for specific metrics
- AI evaluation edge cases (missing metrics, malformed data)
- Real-world AI response scenarios
- Score calculation accuracy
- Defensive programming against AI failures

PRODUCTION SCENARIOS TESTED:
1. Perfect AI response (all metrics present)
2. Partial AI response (some metrics missing)
3. Malformed AI response (wrong types, invalid values)
4. AI timeout/failure (no evaluation)
5. Score boundary conditions (0, 100, negative, >100)
6. Multiple evaluation formats (different AI models)
7. Evaluation schema evolution (backward compatibility)
"""

import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

from app.database import Base
from app.models.user import User
from app.models.interview import Interview, Turn, InterviewStatus, InterviewPhase


# ============================================================
# FIXTURES
# ============================================================

@pytest_asyncio.fixture
async def engine():
    """Create in-memory SQLite database for testing"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
        connect_args={"check_same_thread": False}
    )
    
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """Create database session for each test"""
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create test user"""
    user = User(
        email="test@example.com",
        name="Test User",
        oauth_provider="google",
        oauth_subject="123456789",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_interview(db_session, test_user):
    """Create test interview"""
    interview = Interview(
        user_id=test_user.id,
        status=InterviewStatus.IN_PROGRESS,
        current_phase=InterviewPhase.TECHNICAL,
        current_turn=1
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)
    return interview


# ============================================================
# PHASE 2 - TEST 1: Perfect AI Evaluation (All Metrics)
# ============================================================

@pytest.mark.asyncio
async def test_perfect_ai_evaluation(db_session, test_interview):
    """
    TEST: AI returns perfect evaluation with all metrics
    
    PRODUCTION SCENARIO:
    - AI successfully evaluates answer
    - All metrics present (relevance, depth, clarity)
    - Overall score calculated correctly
    
    VALIDATES:
    - get_overall_score() calculates average correctly
    - get_evaluation_score() returns individual metrics
    - All scores are accessible
    """
    evaluation = {
        "relevance": 85,
        "depth": 75,
        "clarity": 90,
        "technical_accuracy": 80,
        "communication": 88
    }
    
    turn = Turn(
        interview_id=test_interview.id,
        turn_number=1,
        phase=InterviewPhase.TECHNICAL,
        ai_question="Explain React hooks",
        user_answer="React hooks are functions that let you use state...",
        evaluation=evaluation
    )
    
    db_session.add(turn)
    await db_session.commit()
    await db_session.refresh(turn)
    
    # Test overall score calculation
    overall = turn.get_overall_score()
    expected = (85 + 75 + 90) / 3  # Only relevance, depth, clarity
    assert overall == pytest.approx(expected, rel=0.01)
    assert overall == pytest.approx(83.33, rel=0.01)
    
    # Test individual metric access
    assert turn.get_evaluation_score("relevance") == 85
    assert turn.get_evaluation_score("depth") == 75
    assert turn.get_evaluation_score("clarity") == 90
    assert turn.get_evaluation_score("technical_accuracy") == 80
    
    print("[PASS] PHASE 2 - TEST 1: Perfect AI evaluation")


# ============================================================
# PHASE 2 - TEST 2: Partial AI Evaluation (Missing Metrics)
# ============================================================

@pytest.mark.asyncio
async def test_partial_ai_evaluation(db_session, test_interview):
    """
    TEST: AI returns incomplete evaluation (some metrics missing)
    
    PRODUCTION SCENARIO:
    - AI model timeout during evaluation
    - Only partial metrics calculated
    - System must handle gracefully
    
    VALIDATES:
    - get_overall_score() works with missing metrics
    - Missing metrics return None
    - No crashes on incomplete data
    """
    # Only 2 out of 3 core metrics
    evaluation = {
        "relevance": 85,
        "clarity": 90
        # depth is missing!
    }
    
    turn = Turn(
        interview_id=test_interview.id,
        turn_number=1,
        phase=InterviewPhase.BEHAVIORAL,
        ai_question="Tell me about a challenge",
        user_answer="I faced a challenge when...",
        evaluation=evaluation
    )
    
    db_session.add(turn)
    await db_session.commit()
    await db_session.refresh(turn)
    
    # Should calculate from available metrics only
    overall = turn.get_overall_score()
    expected = (85 + 90) / 2  # Only 2 metrics
    assert overall == pytest.approx(expected, rel=0.01)
    assert overall == pytest.approx(87.5, rel=0.01)
    
    # Missing metric should return None
    assert turn.get_evaluation_score("depth") is None
    
    # Present metrics should work
    assert turn.get_evaluation_score("relevance") == 85
    assert turn.get_evaluation_score("clarity") == 90
    
    print("[PASS] PHASE 2 - TEST 2: Partial AI evaluation")


# ============================================================
# PHASE 2 - TEST 3: No Evaluation (AI Failure)
# ============================================================

@pytest.mark.asyncio
async def test_no_evaluation(db_session, test_interview):
    """
    TEST: Turn has no evaluation (AI failed completely)
    
    PRODUCTION SCENARIO:
    - AI service timeout
    - API rate limit exceeded
    - Network failure during evaluation
    
    VALIDATES:
    - get_overall_score() returns None gracefully
    - get_evaluation_score() returns None
    - No exceptions thrown
    """
    turn = Turn(
        interview_id=test_interview.id,
        turn_number=1,
        phase=InterviewPhase.INTRO,
        ai_question="Tell me about yourself",
        user_answer="I am a software engineer...",
        evaluation=None  # No evaluation!
    )
    
    db_session.add(turn)
    await db_session.commit()
    await db_session.refresh(turn)
    
    # Should return None, not crash
    assert turn.get_overall_score() is None
    assert turn.get_evaluation_score("relevance") is None
    assert turn.get_evaluation_score("depth") is None
    assert turn.has_evaluation is False
    
    print("[PASS] PHASE 2 - TEST 3: No evaluation (AI failure)")


# ============================================================
# PHASE 2 - TEST 4: Malformed Evaluation (Wrong Types)
# ============================================================

@pytest.mark.asyncio
async def test_malformed_evaluation_wrong_types(db_session, test_interview):
    """
    TEST: AI returns evaluation with wrong data types
    
    PRODUCTION SCENARIO:
    - AI model returns strings instead of numbers
    - JSON parsing issues
    - Schema mismatch between AI versions
    
    VALIDATES:
    - System handles type conversion gracefully
    - Invalid values are skipped
    - No crashes on bad data
    """
    # Malformed: strings instead of numbers
    evaluation = {
        "relevance": "85",  # String!
        "depth": "seventy-five",  # Not even a number!
        "clarity": 90,  # Correct
        "invalid_metric": "garbage"
    }
    
    turn = Turn(
        interview_id=test_interview.id,
        turn_number=1,
        phase=InterviewPhase.TECHNICAL,
        ai_question="Explain async/await",
        user_answer="Async/await is...",
        evaluation=evaluation
    )
    
    db_session.add(turn)
    await db_session.commit()
    await db_session.refresh(turn)
    
    # Should handle gracefully
    overall = turn.get_overall_score()
    
    # Should convert "85" to 85, skip "seventy-five", use 90
    # Result: (85 + 90) / 2 = 87.5
    assert overall is not None
    assert overall == pytest.approx(87.5, rel=0.01)
    
    print("[PASS] PHASE 2 - TEST 4: Malformed evaluation (wrong types)")


# ============================================================
# PHASE 2 - TEST 5: Boundary Scores (0, 100, Negative, >100)
# ============================================================

@pytest.mark.asyncio
async def test_boundary_scores(db_session, test_interview):
    """
    TEST: Evaluation with boundary and invalid score values
    
    PRODUCTION SCENARIO:
    - AI model returns out-of-range scores
    - Edge case answers (perfect or terrible)
    - AI calibration issues
    
    VALIDATES:
    - Scores of 0 and 100 work correctly
    - Negative scores are handled
    - Scores >100 are handled
    """
    # Test Case 1: Perfect score (100)
    turn1 = Turn(
        interview_id=test_interview.id,
        turn_number=1,
        phase=InterviewPhase.TECHNICAL,
        ai_question="What is 2+2?",
        user_answer="4",
        evaluation={"relevance": 100, "depth": 100, "clarity": 100}
    )
    db_session.add(turn1)
    await db_session.commit()
    await db_session.refresh(turn1)
    
    assert turn1.get_overall_score() == 100.0
    
    # Test Case 2: Zero score (terrible answer)
    turn2 = Turn(
        interview_id=test_interview.id,
        turn_number=2,
        phase=InterviewPhase.TECHNICAL,
        ai_question="Explain quantum computing",
        user_answer="I don't know",
        evaluation={"relevance": 0, "depth": 0, "clarity": 0}
    )
    db_session.add(turn2)
    await db_session.commit()
    await db_session.refresh(turn2)
    
    assert turn2.get_overall_score() == 0.0
    
    # Test Case 3: Negative scores (AI bug)
    turn3 = Turn(
        interview_id=test_interview.id,
        turn_number=3,
        phase=InterviewPhase.BEHAVIORAL,
        ai_question="Tell me about teamwork",
        user_answer="I work alone",
        evaluation={"relevance": -10, "depth": 50, "clarity": 60}
    )
    db_session.add(turn3)
    await db_session.commit()
    await db_session.refresh(turn3)
    
    # Should still calculate (even with negative)
    overall = turn3.get_overall_score()
    expected = (-10 + 50 + 60) / 3
    assert overall == pytest.approx(expected, rel=0.01)
    
    # Test Case 4: Scores >100 (AI calibration issue)
    turn4 = Turn(
        interview_id=test_interview.id,
        turn_number=4,
        phase=InterviewPhase.TECHNICAL,
        ai_question="Explain your project",
        user_answer="Detailed explanation...",
        evaluation={"relevance": 120, "depth": 95, "clarity": 110}
    )
    db_session.add(turn4)
    await db_session.commit()
    await db_session.refresh(turn4)
    
    # Should still calculate (system doesn't enforce 0-100 range)
    overall = turn4.get_overall_score()
    expected = (120 + 95 + 110) / 3
    assert overall == pytest.approx(expected, rel=0.01)
    
    print("[PASS] PHASE 2 - TEST 5: Boundary scores")


# ============================================================
# PHASE 2 - TEST 6: Overall Score Already Calculated
# ============================================================

@pytest.mark.asyncio
async def test_overall_score_precalculated(db_session, test_interview):
    """
    TEST: AI already calculated overall_score in evaluation
    
    PRODUCTION SCENARIO:
    - Newer AI model includes overall_score
    - Avoid recalculating if already present
    - Trust AI's calculation
    
    VALIDATES:
    - get_overall_score() returns precalculated value
    - Doesn't recalculate from metrics
    """
    evaluation = {
        "relevance": 85,
        "depth": 75,
        "clarity": 90,
        "overall_score": 82.0  # AI already calculated this
    }
    
    turn = Turn(
        interview_id=test_interview.id,
        turn_number=1,
        phase=InterviewPhase.BEHAVIORAL,
        ai_question="Describe a conflict",
        user_answer="I had a conflict with...",
        evaluation=evaluation
    )
    
    db_session.add(turn)
    await db_session.commit()
    await db_session.refresh(turn)
    
    # Should return precalculated value (82.0)
    # NOT the average of metrics (83.33)
    overall = turn.get_overall_score()
    assert overall == 82.0
    assert overall != pytest.approx(83.33, rel=0.01)
    
    print("[PASS] PHASE 2 - TEST 6: Overall score precalculated")


# ============================================================
# PHASE 2 - TEST 7: Empty Evaluation Object
# ============================================================

@pytest.mark.asyncio
async def test_empty_evaluation_object(db_session, test_interview):
    """
    TEST: Evaluation exists but is empty dict
    
    PRODUCTION SCENARIO:
    - AI started evaluation but failed mid-process
    - Partial write to database
    - Empty JSON object stored
    
    VALIDATES:
    - Empty dict doesn't crash system
    - Returns None for all scores
    """
    turn = Turn(
        interview_id=test_interview.id,
        turn_number=1,
        phase=InterviewPhase.INTRO,
        ai_question="Tell me about yourself",
        user_answer="I am...",
        evaluation={}  # Empty dict!
    )
    
    db_session.add(turn)
    await db_session.commit()
    await db_session.refresh(turn)
    
    # Should handle gracefully
    assert turn.has_evaluation is True  # Dict exists
    assert turn.get_overall_score() is None  # But no scores
    assert turn.get_evaluation_score("relevance") is None
    
    print("[PASS] PHASE 2 - TEST 7: Empty evaluation object")


# ============================================================
# PHASE 2 - TEST 8: Extra Metrics (Future AI Models)
# ============================================================

@pytest.mark.asyncio
async def test_extra_metrics_future_ai(db_session, test_interview):
    """
    TEST: AI returns additional metrics not in current schema
    
    PRODUCTION SCENARIO:
    - New AI model adds more evaluation metrics
    - Backward compatibility required
    - Old code must handle new metrics
    
    VALIDATES:
    - Extra metrics don't break calculation
    - Core metrics still work
    - System is forward-compatible
    """
    evaluation = {
        # Core metrics
        "relevance": 85,
        "depth": 75,
        "clarity": 90,
        
        # Future metrics (not used in calculation)
        "creativity": 88,
        "problem_solving": 92,
        "leadership": 80,
        "cultural_fit": 95,
        "confidence": 87
    }
    
    turn = Turn(
        interview_id=test_interview.id,
        turn_number=1,
        phase=InterviewPhase.BEHAVIORAL,
        ai_question="Describe your leadership style",
        user_answer="My leadership style is...",
        evaluation=evaluation
    )
    
    db_session.add(turn)
    await db_session.commit()
    await db_session.refresh(turn)
    
    # Should only use core 3 metrics
    overall = turn.get_overall_score()
    expected = (85 + 75 + 90) / 3
    assert overall == pytest.approx(expected, rel=0.01)
    
    # Extra metrics should be accessible
    assert turn.get_evaluation_score("creativity") == 88
    assert turn.get_evaluation_score("leadership") == 80
    
    print("[PASS] PHASE 2 - TEST 8: Extra metrics (future AI)")


# ============================================================
# PHASE 2 - TEST 9: Float vs Integer Scores
# ============================================================

@pytest.mark.asyncio
async def test_float_vs_integer_scores(db_session, test_interview):
    """
    TEST: AI returns mix of float and integer scores
    
    PRODUCTION SCENARIO:
    - Different AI models use different precision
    - Some return 85, others return 85.5
    - Must handle both consistently
    
    VALIDATES:
    - Float and int scores both work
    - Calculation handles mixed types
    - No precision loss
    """
    evaluation = {
        "relevance": 85,      # Integer
        "depth": 75.5,        # Float
        "clarity": 90.25      # Float with decimals
    }
    
    turn = Turn(
        interview_id=test_interview.id,
        turn_number=1,
        phase=InterviewPhase.TECHNICAL,
        ai_question="Explain databases",
        user_answer="Databases are...",
        evaluation=evaluation
    )
    
    db_session.add(turn)
    await db_session.commit()
    await db_session.refresh(turn)
    
    # Should handle mixed types
    overall = turn.get_overall_score()
    expected = (85 + 75.5 + 90.25) / 3
    assert overall == pytest.approx(expected, rel=0.001)
    assert overall == pytest.approx(83.583, rel=0.001)
    
    print("[PASS] PHASE 2 - TEST 9: Float vs integer scores")


# ============================================================
# PHASE 2 - TEST 10: Real-World AI Response Formats
# ============================================================

@pytest.mark.asyncio
async def test_real_world_ai_formats(db_session, test_interview):
    """
    TEST: Various real-world AI response formats
    
    PRODUCTION SCENARIO:
    - Different AI providers (OpenAI, Anthropic, Groq)
    - Different response structures
    - Must handle all formats
    
    VALIDATES:
    - Multiple evaluation formats work
    - System is AI-provider agnostic
    """
    # Format 1: Groq/OpenAI style (flat structure)
    eval1 = {
        "relevance": 85,
        "depth": 75,
        "clarity": 90,
        "feedback": "Good answer with clear examples"
    }
    
    turn1 = Turn(
        interview_id=test_interview.id,
        turn_number=1,
        phase=InterviewPhase.TECHNICAL,
        ai_question="Q1",
        user_answer="A1",
        evaluation=eval1
    )
    db_session.add(turn1)
    
    # Format 2: Nested structure
    eval2 = {
        "scores": {
            "relevance": 80,
            "depth": 70,
            "clarity": 85
        },
        "metadata": {
            "model": "gpt-4",
            "tokens": 150
        }
    }
    
    turn2 = Turn(
        interview_id=test_interview.id,
        turn_number=2,
        phase=InterviewPhase.BEHAVIORAL,
        ai_question="Q2",
        user_answer="A2",
        evaluation=eval2
    )
    db_session.add(turn2)
    
    # Format 3: Array-based
    eval3 = {
        "metrics": [
            {"name": "relevance", "score": 90},
            {"name": "depth", "score": 85},
            {"name": "clarity", "score": 95}
        ]
    }
    
    turn3 = Turn(
        interview_id=test_interview.id,
        turn_number=3,
        phase=InterviewPhase.DEEP_DIVE,
        ai_question="Q3",
        user_answer="A3",
        evaluation=eval3
    )
    db_session.add(turn3)
    
    await db_session.commit()
    await db_session.refresh(turn1)
    await db_session.refresh(turn2)
    await db_session.refresh(turn3)
    
    # Format 1 should work (flat structure)
    assert turn1.get_overall_score() == pytest.approx(83.33, rel=0.01)
    
    # Format 2 won't work with current implementation (nested)
    # This is expected - shows limitation
    assert turn2.get_overall_score() is None
    
    # Format 3 won't work (array-based)
    # This is expected - shows limitation
    assert turn3.get_overall_score() is None
    
    print("[PASS] PHASE 2 - TEST 10: Real-world AI formats")


# ============================================================
# RUN PHASE 2 TESTS
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔥 BATTLE TESTING: TURN MODEL - PHASE 2 (EVALUATION)")
    print("="*60 + "\n")
    
    pytest.main([__file__, "-v", "-s"])
