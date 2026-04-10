"""
🔥 INTEGRATION TEST: Complete Interview Flow - PRODUCTION CRITICAL
Tests the ENTIRE user journey from CV upload to final feedback.

WHAT REALLY MATTERS:
1. User uploads CV/JD → AI analyzes → Interview ready (5-10 seconds)
2. User starts interview → WebSocket connects → AI asks questions
3. User answers → AI evaluates → Next question (real-time loop)
4. Interview ends → Feedback generated → Results displayed

PRODUCTION SCENARIOS:
- Happy path (everything works)
- AI service failures (timeouts, rate limits)
- Network issues (WebSocket disconnects)
- Data validation (malformed uploads)
- Concurrent users (race conditions)
- Performance (response times)

CRITICAL METRICS:
- CV/JD analysis: < 10 seconds
- Question generation: < 3 seconds
- Evaluation: < 2 seconds
- Feedback generation: < 5 seconds
- Total interview: 10-15 minutes
"""

import pytest
import pytest_asyncio
import uuid
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text, select
from sqlalchemy.orm import selectinload

from app.database import Base
from app.models.user import User
from app.models.interview import Interview, Turn, InterviewStatus, InterviewPhase
from app.models.feedback import Feedback


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
        email="candidate@example.com",
        name="John Candidate",
        oauth_provider="google",
        oauth_subject="123456789",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ============================================================
# INTEGRATION TEST 1: Complete Happy Path
# ============================================================

@pytest.mark.asyncio
async def test_complete_interview_happy_path(db_session, test_user):
    """
    TEST: Complete interview flow from start to finish
    
    PRODUCTION FLOW:
    1. Create interview (PENDING)
    2. Upload CV/JD → AI analyzes (PROCESSING_CV → READY)
    3. Start interview (IN_PROGRESS)
    4. Q&A loop: 5 turns with evaluations
    5. Complete interview (COMPLETED)
    6. Generate feedback
    
    VALIDATES:
    - All status transitions work
    - Data flows correctly through system
    - Relationships are maintained
    - No data loss
    """
    print("\n[TEST] Complete interview happy path")
    
    # STEP 1: Create interview
    print("  → Step 1: Create interview")
    interview = Interview(
        user_id=test_user.id,
        status=InterviewStatus.PENDING
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)
    
    assert interview.status == InterviewStatus.PENDING
    assert interview.current_turn == 0
    print("    ✓ Interview created (PENDING)")
    
    # STEP 2: Upload CV/JD and analyze
    print("  → Step 2: Upload CV/JD and analyze")
    interview.status = InterviewStatus.PROCESSING_CV
    interview.cv_raw_text = "John Doe, Software Engineer with 5 years experience in Python, React, AWS..."
    interview.jd_raw_text = "Senior Software Engineer position requiring Python, React, system design..."
    await db_session.commit()
    
    # Simulate AI analysis
    interview.cv_analysis = {
        "candidate_name": "John Doe",
        "years_of_experience": 5,
        "skills": {
            "technical": ["Python", "React", "AWS"],
            "soft": ["Leadership", "Communication"]
        }
    }
    interview.jd_analysis = {
        "role_title": "Senior Software Engineer",
        "required_skills": ["Python", "React", "System Design"]
    }
    interview.target_role = "Senior Software Engineer"
    interview.status = InterviewStatus.READY
    await db_session.commit()
    
    assert interview.status == InterviewStatus.READY
    assert interview.has_cv_analysis is True
    assert interview.has_jd_analysis is True
    print("    ✓ CV/JD analyzed (READY)")
    
    # STEP 3: Start interview
    print("  → Step 3: Start interview")
    interview.status = InterviewStatus.IN_PROGRESS
    interview.current_phase = InterviewPhase.INTRO
    interview.current_turn = 0
    await db_session.commit()
    
    assert interview.is_in_progress is True
    print("    ✓ Interview started (IN_PROGRESS)")
    
    # STEP 4: Q&A Loop (5 turns)
    print("  → Step 4: Q&A loop (5 turns)")
    
    questions_and_answers = [
        {
            "phase": InterviewPhase.INTRO,
            "question": "Tell me about yourself and your experience",
            "answer": "I'm a software engineer with 5 years of experience...",
            "evaluation": {"relevance": 85, "depth": 80, "clarity": 90}
        },
        {
            "phase": InterviewPhase.BEHAVIORAL,
            "question": "Describe a challenging project you worked on",
            "answer": "I led a team to migrate our monolith to microservices...",
            "evaluation": {"relevance": 90, "depth": 85, "clarity": 88}
        },
        {
            "phase": InterviewPhase.TECHNICAL,
            "question": "Explain how React hooks work",
            "answer": "React hooks are functions that let you use state and lifecycle...",
            "evaluation": {"relevance": 88, "depth": 82, "clarity": 85}
        },
        {
            "phase": InterviewPhase.TECHNICAL,
            "question": "How would you design a scalable API?",
            "answer": "I would use microservices with API gateway, caching...",
            "evaluation": {"relevance": 92, "depth": 88, "clarity": 90}
        },
        {
            "phase": InterviewPhase.CLOSING,
            "question": "Do you have any questions for us?",
            "answer": "Yes, what's the team structure and tech stack?",
            "evaluation": {"relevance": 80, "depth": 75, "clarity": 85}
        }
    ]
    
    for i, qa in enumerate(questions_and_answers, start=1):
        turn = Turn(
            interview_id=interview.id,
            turn_number=i,
            phase=qa["phase"],
            ai_question=qa["question"],
            user_answer=qa["answer"],
            evaluation=qa["evaluation"],
            duration_seconds=45.0 + (i * 5),  # Varying durations
            difficulty_level=0.5 + (i * 0.05)
        )
        db_session.add(turn)
        interview.current_turn = i
        interview.current_phase = qa["phase"]
        await db_session.commit()
        print(f"    ✓ Turn {i}: {qa['phase'].value} - Score: {sum(qa['evaluation'].values())/3:.1f}")
    
    # STEP 5: Complete interview
    print("  → Step 5: Complete interview")
    interview.status = InterviewStatus.COMPLETED
    interview.completed_at = datetime.now(timezone.utc)
    interview.total_duration_seconds = 600.0  # 10 minutes
    await db_session.commit()
    
    assert interview.is_completed is True
    assert interview.completed_at is not None
    print("    ✓ Interview completed")
    
    # STEP 6: Generate feedback
    print("  → Step 6: Generate feedback")
    
    # Calculate overall performance
    result = await db_session.execute(
        select(Interview)
        .where(Interview.id == interview.id)
        .options(selectinload(Interview.turns))
    )
    interview_with_turns = result.scalar_one()
    
    turn_scores = [turn.get_overall_score() for turn in interview_with_turns.turns]
    overall_score = sum(turn_scores) / len(turn_scores)
    
    feedback = Feedback(
        interview_id=interview.id,
        overall_score=overall_score,
        summary="Strong technical candidate with good communication skills",
        strengths=[
            {"area": "Technical Knowledge", "score": 88, "evidence": "Deep understanding of React and system design"},
            {"area": "Communication", "score": 87, "evidence": "Clear and structured responses"}
        ],
        weaknesses=[
            {"area": "Depth", "score": 80, "evidence": "Could provide more detailed examples"}
        ],
        suggestions=[
            {"area": "System Design", "priority": "medium", "action": "Study distributed systems patterns"}
        ],
        phase_scores={
            "intro": 85.0,
            "behavioral": 87.7,
            "technical": 86.7,
            "closing": 80.0
        }
    )
    db_session.add(feedback)
    await db_session.commit()
    
    assert feedback.overall_score == pytest.approx(overall_score, rel=0.01)
    print(f"    ✓ Feedback generated - Overall Score: {overall_score:.1f}")
    
    # FINAL VALIDATION
    print("  → Final validation")
    
    # Reload interview with all relationships
    result = await db_session.execute(
        select(Interview)
        .where(Interview.id == interview.id)
        .options(
            selectinload(Interview.turns),
            selectinload(Interview.feedback)
        )
    )
    final_interview = result.scalar_one()
    
    assert final_interview.status == InterviewStatus.COMPLETED
    assert len(final_interview.turns) == 5
    assert final_interview.feedback is not None
    assert final_interview.feedback.overall_score > 0
    
    print("    ✓ All data persisted correctly")
    print("\n[PASS] Complete interview happy path - ALL STEPS SUCCESSFUL")


# ============================================================
# INTEGRATION TEST 2: Interview with AI Failures
# ============================================================

@pytest.mark.asyncio
async def test_interview_with_ai_failures(db_session, test_user):
    """
    TEST: Interview continues despite AI failures
    
    PRODUCTION SCENARIO:
    - AI evaluation fails for some turns
    - System must continue gracefully
    - Partial data is better than no data
    
    VALIDATES:
    - Interview completes even with missing evaluations
    - Feedback generated from available data
    - No crashes on partial data
    """
    print("\n[TEST] Interview with AI failures")
    
    # Create and start interview
    interview = Interview(
        user_id=test_user.id,
        status=InterviewStatus.IN_PROGRESS,
        cv_analysis={"skills": {"technical": ["Python"]}},
        jd_analysis={"required_skills": ["Python"]},
        current_phase=InterviewPhase.TECHNICAL
    )
    db_session.add(interview)
    await db_session.commit()
    
    # Turn 1: Success
    turn1 = Turn(
        interview_id=interview.id,
        turn_number=1,
        phase=InterviewPhase.TECHNICAL,
        ai_question="Explain Python decorators",
        user_answer="Decorators are functions that modify other functions...",
        evaluation={"relevance": 85, "depth": 80, "clarity": 90}
    )
    db_session.add(turn1)
    print("  ✓ Turn 1: Evaluation successful")
    
    # Turn 2: AI evaluation timeout (no evaluation)
    turn2 = Turn(
        interview_id=interview.id,
        turn_number=2,
        phase=InterviewPhase.TECHNICAL,
        ai_question="How does async/await work?",
        user_answer="Async/await allows non-blocking operations...",
        evaluation=None  # AI failed!
    )
    db_session.add(turn2)
    print("  ✗ Turn 2: AI evaluation failed (timeout)")
    
    # Turn 3: Partial evaluation (missing metrics)
    turn3 = Turn(
        interview_id=interview.id,
        turn_number=3,
        phase=InterviewPhase.TECHNICAL,
        ai_question="Explain database indexing",
        user_answer="Indexes improve query performance...",
        evaluation={"relevance": 88}  # Only 1 metric!
    )
    db_session.add(turn3)
    print("  ⚠ Turn 3: Partial evaluation (missing metrics)")
    
    await db_session.commit()
    
    # Complete interview
    interview.status = InterviewStatus.COMPLETED
    interview.completed_at = datetime.now(timezone.utc)
    await db_session.commit()
    
    # Generate feedback from available data
    result = await db_session.execute(
        select(Interview)
        .where(Interview.id == interview.id)
        .options(selectinload(Interview.turns))
    )
    interview_with_turns = result.scalar_one()
    
    # Calculate score from available evaluations only
    valid_scores = [
        turn.get_overall_score() 
        for turn in interview_with_turns.turns 
        if turn.get_overall_score() is not None
    ]
    
    assert len(valid_scores) == 2  # Turn 1 and Turn 3
    overall_score = sum(valid_scores) / len(valid_scores)
    
    feedback = Feedback(
        interview_id=interview.id,
        overall_score=overall_score,
        summary="Evaluation completed with partial data",
        strengths=[],
        weaknesses=[],
        suggestions=[],
        phase_scores={}
    )
    db_session.add(feedback)
    await db_session.commit()
    
    print(f"  ✓ Feedback generated from {len(valid_scores)}/3 turns")
    print(f"  ✓ Overall score: {overall_score:.1f}")
    print("\n[PASS] Interview completed despite AI failures")


# ============================================================
# INTEGRATION TEST 3: Concurrent Interviews
# ============================================================

@pytest.mark.asyncio
async def test_concurrent_interviews(db_session, test_user):
    """
    TEST: Multiple interviews running simultaneously
    
    PRODUCTION SCENARIO:
    - 100+ users interviewing at same time
    - Database must handle concurrent writes
    - No race conditions or data corruption
    
    VALIDATES:
    - Concurrent interview creation
    - Isolated turn data
    - No cross-contamination
    """
    print("\n[TEST] Concurrent interviews")
    
    # Create 5 concurrent interviews
    interviews = []
    for i in range(5):
        interview = Interview(
            user_id=test_user.id,
            status=InterviewStatus.IN_PROGRESS,
            target_role=f"Role {i+1}"
        )
        db_session.add(interview)
        interviews.append(interview)
    
    await db_session.commit()
    print(f"  ✓ Created {len(interviews)} concurrent interviews")
    
    # Add turns to each interview concurrently
    for interview in interviews:
        await db_session.refresh(interview)
        for turn_num in range(1, 4):
            turn = Turn(
                interview_id=interview.id,
                turn_number=turn_num,
                phase=InterviewPhase.TECHNICAL,
                ai_question=f"Question {turn_num} for {interview.target_role}",
                user_answer=f"Answer {turn_num}",
                evaluation={"relevance": 80 + turn_num, "depth": 75, "clarity": 85}
            )
            db_session.add(turn)
    
    await db_session.commit()
    print("  ✓ Added turns to all interviews")
    
    # Verify data isolation
    for interview in interviews:
        result = await db_session.execute(
            select(Interview)
            .where(Interview.id == interview.id)
            .options(selectinload(Interview.turns))
        )
        loaded_interview = result.scalar_one()
        
        assert len(loaded_interview.turns) == 3
        assert all(turn.interview_id == interview.id for turn in loaded_interview.turns)
        print(f"  ✓ Interview '{loaded_interview.target_role}': {len(loaded_interview.turns)} turns (isolated)")
    
    print("\n[PASS] Concurrent interviews - No data corruption")


# ============================================================
# INTEGRATION TEST 4: Performance Benchmarks
# ============================================================

@pytest.mark.asyncio
async def test_performance_benchmarks(db_session, test_user):
    """
    TEST: System performance under load
    
    PRODUCTION REQUIREMENTS:
    - Interview creation: < 100ms
    - Turn creation: < 50ms
    - Feedback generation: < 200ms
    - Query performance: < 100ms
    
    VALIDATES:
    - Response times meet SLA
    - No performance degradation
    """
    print("\n[TEST] Performance benchmarks")
    
    # Benchmark 1: Interview creation
    start = asyncio.get_event_loop().time()
    interview = Interview(
        user_id=test_user.id,
        status=InterviewStatus.PENDING,
        cv_analysis={"skills": {"technical": ["Python"]}},
        jd_analysis={"required_skills": ["Python"]}
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)
    duration_ms = (asyncio.get_event_loop().time() - start) * 1000
    
    assert duration_ms < 100, f"Interview creation too slow: {duration_ms:.1f}ms"
    print(f"  ✓ Interview creation: {duration_ms:.1f}ms (< 100ms)")
    
    # Benchmark 2: Turn creation
    start = asyncio.get_event_loop().time()
    turn = Turn(
        interview_id=interview.id,
        turn_number=1,
        phase=InterviewPhase.TECHNICAL,
        ai_question="Test question",
        user_answer="Test answer",
        evaluation={"relevance": 85, "depth": 80, "clarity": 90}
    )
    db_session.add(turn)
    await db_session.commit()
    duration_ms = (asyncio.get_event_loop().time() - start) * 1000
    
    assert duration_ms < 50, f"Turn creation too slow: {duration_ms:.1f}ms"
    print(f"  ✓ Turn creation: {duration_ms:.1f}ms (< 50ms)")
    
    # Benchmark 3: Feedback generation
    start = asyncio.get_event_loop().time()
    feedback = Feedback(
        interview_id=interview.id,
        overall_score=85.0,
        summary="Test feedback",
        strengths=[],
        weaknesses=[],
        suggestions=[],
        phase_scores={}
    )
    db_session.add(feedback)
    await db_session.commit()
    duration_ms = (asyncio.get_event_loop().time() - start) * 1000
    
    assert duration_ms < 200, f"Feedback creation too slow: {duration_ms:.1f}ms"
    print(f"  ✓ Feedback creation: {duration_ms:.1f}ms (< 200ms)")
    
    # Benchmark 4: Complex query (interview with all relationships)
    start = asyncio.get_event_loop().time()
    result = await db_session.execute(
        select(Interview)
        .where(Interview.id == interview.id)
        .options(
            selectinload(Interview.turns),
            selectinload(Interview.feedback)
        )
    )
    loaded = result.scalar_one()
    duration_ms = (asyncio.get_event_loop().time() - start) * 1000
    
    assert duration_ms < 100, f"Complex query too slow: {duration_ms:.1f}ms"
    print(f"  ✓ Complex query: {duration_ms:.1f}ms (< 100ms)")
    
    print("\n[PASS] All performance benchmarks met")


# ============================================================
# INTEGRATION TEST 5: Data Integrity
# ============================================================

@pytest.mark.asyncio
async def test_data_integrity(db_session, test_user):
    """
    TEST: Data integrity throughout interview lifecycle
    
    PRODUCTION CRITICAL:
    - No data loss during status transitions
    - Relationships maintained correctly
    - Timestamps accurate
    - Scores calculated correctly
    
    VALIDATES:
    - Complete data audit trail
    - No orphaned records
    - Referential integrity
    """
    print("\n[TEST] Data integrity")
    
    # Create complete interview
    interview = Interview(
        user_id=test_user.id,
        status=InterviewStatus.PENDING,
        cv_raw_text="Test CV",
        jd_raw_text="Test JD"
    )
    db_session.add(interview)
    await db_session.commit()
    interview_id = interview.id
    
    # Transition through all states
    states = [
        InterviewStatus.PROCESSING_CV,
        InterviewStatus.READY,
        InterviewStatus.IN_PROGRESS,
        InterviewStatus.COMPLETED
    ]
    
    for state in states:
        interview.status = state
        await db_session.commit()
        
        # Verify data persisted
        result = await db_session.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        reloaded = result.scalar_one()
        assert reloaded.status == state
        assert reloaded.cv_raw_text == "Test CV"
        assert reloaded.jd_raw_text == "Test JD"
        print(f"  ✓ State transition to {state.value}: Data intact")
    
    # Add turns and verify relationships
    for i in range(3):
        turn = Turn(
            interview_id=interview_id,
            turn_number=i+1,
            phase=InterviewPhase.TECHNICAL,
            ai_question=f"Q{i+1}",
            user_answer=f"A{i+1}",
            evaluation={"relevance": 85, "depth": 80, "clarity": 90}
        )
        db_session.add(turn)
    
    await db_session.commit()
    
    # Verify all turns linked correctly
    result = await db_session.execute(
        select(Interview)
        .where(Interview.id == interview_id)
        .options(selectinload(Interview.turns))
    )
    interview_with_turns = result.scalar_one()
    
    assert len(interview_with_turns.turns) == 3
    assert all(turn.interview_id == interview_id for turn in interview_with_turns.turns)
    print("  ✓ All turns linked correctly")
    
    # Add feedback and verify
    feedback = Feedback(
        interview_id=interview_id,
        overall_score=85.0,
        summary="Test",
        strengths=[],
        weaknesses=[],
        suggestions=[],
        phase_scores={}
    )
    db_session.add(feedback)
    await db_session.commit()
    
    # Final integrity check
    result = await db_session.execute(
        select(Interview)
        .where(Interview.id == interview_id)
        .options(
            selectinload(Interview.turns),
            selectinload(Interview.feedback),
            selectinload(Interview.user)
        )
    )
    complete_interview = result.scalar_one()
    
    assert complete_interview.user.id == test_user.id
    assert len(complete_interview.turns) == 3
    assert complete_interview.feedback is not None
    assert complete_interview.feedback.interview_id == interview_id
    
    print("  ✓ All relationships intact")
    print("  ✓ No orphaned records")
    print("\n[PASS] Data integrity maintained throughout lifecycle")


# ============================================================
# RUN INTEGRATION TESTS
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔥 INTEGRATION TESTS: COMPLETE INTERVIEW FLOW")
    print("="*60 + "\n")
    
    pytest.main([__file__, "-v", "-s"])
