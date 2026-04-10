"""
🔥 BATTLE TEST: Turn Model - PHASE 1 (FOUNDATION)
Tests basic Turn creation, fields, and relationships.

PHASE 1 SCOPE:
- Turn creation (minimal & full)
- Field validation (turn_number, phase, question, answer)
- Foreign key relationship to Interview
- Timestamps
- Basic properties (has_answer, has_evaluation)

NEXT PHASES:
- Phase 2: Evaluation logic (get_overall_score, metrics)
- Phase 3: Edge cases (malformed evaluation, missing data)
- Phase 4: AI evaluation scenarios (realistic test data)
"""

import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from app.database import Base
from app.models.user import User
from app.models.interview import Interview, Turn, InterviewStatus, InterviewPhase


# ============================================================
# FIXTURES - Reuse from Interview tests
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
    """Create test interview for Turn tests"""
    interview = Interview(
        user_id=test_user.id,
        status=InterviewStatus.IN_PROGRESS,
        current_phase=InterviewPhase.INTRO,
        current_turn=0
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)
    return interview


# ============================================================
# PHASE 1 - TEST 1: Turn Creation (Minimal)
# ============================================================

@pytest.mark.asyncio
async def test_create_turn_minimal(db_session, test_interview):
    """
    TEST: Create turn with minimal required fields
    
    VALIDATES:
    - Turn can be created with just interview_id, turn_number, phase, ai_question
    - UUID primary key is auto-generated
    - Timestamps are auto-set
    - Optional fields default to None
    """
    turn = Turn(
        interview_id=test_interview.id,
        turn_number=1,
        phase=InterviewPhase.INTRO,
        ai_question="Tell me about yourself"
    )
    
    db_session.add(turn)
    await db_session.commit()
    await db_session.refresh(turn)
    
    # Core assertions
    assert turn.id is not None
    assert isinstance(turn.id, uuid.UUID)
    assert turn.interview_id == test_interview.id
    assert turn.turn_number == 1
    assert turn.phase == InterviewPhase.INTRO
    assert turn.ai_question == "Tell me about yourself"
    
    # Optional fields should be None
    assert turn.user_answer is None
    assert turn.evaluation is None
    assert turn.duration_seconds is None
    assert turn.difficulty_level is None
    
    # Timestamps should be set
    assert turn.created_at is not None
    assert turn.updated_at is not None
    
    print("[PASS] PHASE 1 - TEST 1: Minimal turn creation")


# ============================================================
# PHASE 1 - TEST 2: Turn Creation (Full)
# ============================================================

@pytest.mark.asyncio
async def test_create_turn_full(db_session, test_interview):
    """
    TEST: Create turn with all fields populated
    
    VALIDATES:
    - All optional fields can be set
    - Evaluation JSON is stored correctly
    - Duration and difficulty are stored as floats
    """
    evaluation = {
        "relevance": 85,
        "depth": 75,
        "clarity": 90,
        "overall_score": 83.33
    }
    
    turn = Turn(
        interview_id=test_interview.id,
        turn_number=1,
        phase=InterviewPhase.BEHAVIORAL,
        ai_question="Describe a time you faced a challenge",
        user_answer="I once had to debug a production issue...",
        evaluation=evaluation,
        duration_seconds=45.5,
        difficulty_level=0.6
    )
    
    db_session.add(turn)
    await db_session.commit()
    await db_session.refresh(turn)
    
    # All fields should be set
    assert turn.user_answer == "I once had to debug a production issue..."
    assert turn.evaluation == evaluation
    assert turn.evaluation["relevance"] == 85
    assert turn.duration_seconds == 45.5
    assert turn.difficulty_level == 0.6
    
    print("[PASS] PHASE 1 - TEST 2: Full turn creation")


# ============================================================
# PHASE 1 - TEST 3: Turn Number Sequence
# ============================================================

@pytest.mark.asyncio
async def test_turn_number_sequence(db_session, test_interview):
    """
    TEST: Multiple turns with sequential numbers
    
    VALIDATES:
    - Multiple turns can be created for same interview
    - Turn numbers are independent (not auto-increment)
    - Turns are ordered by turn_number
    """
    # Create 3 turns
    turn1 = Turn(
        interview_id=test_interview.id,
        turn_number=1,
        phase=InterviewPhase.INTRO,
        ai_question="Question 1"
    )
    
    turn2 = Turn(
        interview_id=test_interview.id,
        turn_number=2,
        phase=InterviewPhase.BEHAVIORAL,
        ai_question="Question 2"
    )
    
    turn3 = Turn(
        interview_id=test_interview.id,
        turn_number=3,
        phase=InterviewPhase.TECHNICAL,
        ai_question="Question 3"
    )
    
    db_session.add_all([turn1, turn2, turn3])
    await db_session.commit()
    
    # Refresh interview and eagerly load turns
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    result = await db_session.execute(
        select(Interview)
        .where(Interview.id == test_interview.id)
        .options(selectinload(Interview.turns))
    )
    interview_with_turns = result.scalar_one()
    
    # Verify turns are loaded and ordered
    assert len(interview_with_turns.turns) == 3
    assert interview_with_turns.turns[0].turn_number == 1
    assert interview_with_turns.turns[1].turn_number == 2
    assert interview_with_turns.turns[2].turn_number == 3
    
    print("[PASS] PHASE 1 - TEST 3: Turn number sequence")


# ============================================================
# PHASE 1 - TEST 4: Unique Constraint (interview_id + turn_number)
# ============================================================

@pytest.mark.asyncio
async def test_duplicate_turn_number_fails(db_session, test_interview):
    """
    TEST: Cannot create two turns with same interview_id + turn_number
    
    VALIDATES:
    - Unique constraint on (interview_id, turn_number) is enforced
    - Database prevents duplicate turn numbers
    """
    turn1 = Turn(
        interview_id=test_interview.id,
        turn_number=1,
        phase=InterviewPhase.INTRO,
        ai_question="Question 1"
    )
    
    db_session.add(turn1)
    await db_session.commit()
    
    # Try to create another turn with same number
    turn2 = Turn(
        interview_id=test_interview.id,
        turn_number=1,  # Same number!
        phase=InterviewPhase.INTRO,
        ai_question="Question 2"
    )
    
    db_session.add(turn2)
    
    with pytest.raises(IntegrityError):
        await db_session.commit()
    
    print("[PASS] PHASE 1 - TEST 4: Duplicate turn number prevented")


# ============================================================
# PHASE 1 - TEST 5: Foreign Key Constraint
# ============================================================

@pytest.mark.asyncio
async def test_turn_requires_valid_interview(db_session):
    """
    TEST: Turn requires valid interview_id
    
    VALIDATES:
    - Foreign key constraint is enforced
    - Cannot create turn with non-existent interview
    """
    fake_interview_id = uuid.uuid4()
    
    turn = Turn(
        interview_id=fake_interview_id,
        turn_number=1,
        phase=InterviewPhase.INTRO,
        ai_question="Question"
    )
    
    db_session.add(turn)
    
    with pytest.raises(IntegrityError):
        await db_session.commit()
    
    print("[PASS] PHASE 1 - TEST 5: Foreign key constraint enforced")


# ============================================================
# PHASE 1 - TEST 6: Cascade Delete
# ============================================================

@pytest.mark.asyncio
async def test_delete_interview_deletes_turns(db_session, test_interview):
    """
    TEST: Deleting interview deletes all its turns
    
    VALIDATES:
    - CASCADE delete works correctly
    - No orphaned turns left in database
    """
    # Create 3 turns
    for i in range(1, 4):
        turn = Turn(
            interview_id=test_interview.id,
            turn_number=i,
            phase=InterviewPhase.INTRO,
            ai_question=f"Question {i}"
        )
        db_session.add(turn)
    
    await db_session.commit()
    
    # Verify turns exist
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    result = await db_session.execute(
        select(Interview)
        .where(Interview.id == test_interview.id)
        .options(selectinload(Interview.turns))
    )
    interview_with_turns = result.scalar_one()
    assert len(interview_with_turns.turns) == 3
    
    # Delete interview
    await db_session.delete(test_interview)
    await db_session.commit()
    
    # Verify turns are deleted (query directly)
    from sqlalchemy import select
    result = await db_session.execute(select(Turn))
    remaining_turns = result.scalars().all()
    
    assert len(remaining_turns) == 0
    
    print("[PASS] PHASE 1 - TEST 6: Cascade delete works")


# ============================================================
# PHASE 1 - TEST 7: Properties (has_answer, has_evaluation)
# ============================================================

@pytest.mark.asyncio
async def test_turn_properties(db_session, test_interview):
    """
    TEST: has_answer and has_evaluation properties
    
    VALIDATES:
    - has_answer returns False when user_answer is None or empty
    - has_answer returns True when user_answer has content
    - has_evaluation returns False when evaluation is None
    - has_evaluation returns True when evaluation exists
    """
    # Turn without answer
    turn1 = Turn(
        interview_id=test_interview.id,
        turn_number=1,
        phase=InterviewPhase.INTRO,
        ai_question="Question 1"
    )
    db_session.add(turn1)
    await db_session.commit()
    
    assert turn1.has_answer is False
    assert turn1.has_evaluation is False
    
    # Add answer
    turn1.user_answer = "My answer"
    await db_session.commit()
    
    assert turn1.has_answer is True
    assert turn1.has_evaluation is False
    
    # Add evaluation
    turn1.evaluation = {"relevance": 85}
    await db_session.commit()
    
    assert turn1.has_answer is True
    assert turn1.has_evaluation is True
    
    # Empty answer should return False
    turn2 = Turn(
        interview_id=test_interview.id,
        turn_number=2,
        phase=InterviewPhase.INTRO,
        ai_question="Question 2",
        user_answer="   "  # Only whitespace
    )
    db_session.add(turn2)
    await db_session.commit()
    
    assert turn2.has_answer is False
    
    print("[PASS] PHASE 1 - TEST 7: Properties work correctly")


# ============================================================
# PHASE 1 - TEST 8: Timestamps
# ============================================================

@pytest.mark.asyncio
async def test_turn_timestamps(db_session, test_interview):
    """
    TEST: created_at and updated_at timestamps
    
    VALIDATES:
    - created_at is set on creation
    - updated_at is set on creation
    - updated_at changes when turn is modified
    - created_at never changes
    """
    before = datetime.now(timezone.utc)
    
    turn = Turn(
        interview_id=test_interview.id,
        turn_number=1,
        phase=InterviewPhase.INTRO,
        ai_question="Question"
    )
    
    db_session.add(turn)
    await db_session.commit()
    await db_session.refresh(turn)
    
    after = datetime.now(timezone.utc)
    
    # Timestamps should be set
    assert turn.created_at is not None
    assert turn.updated_at is not None
    # SQLite stores naive datetimes, so compare without timezone
    assert before.replace(tzinfo=None) <= turn.created_at <= after.replace(tzinfo=None)
    assert before.replace(tzinfo=None) <= turn.updated_at <= after.replace(tzinfo=None)
    
    original_created_at = turn.created_at
    original_updated_at = turn.updated_at
    
    # Wait and update
    import asyncio
    await asyncio.sleep(0.1)
    
    turn.user_answer = "My answer"
    await db_session.commit()
    await db_session.refresh(turn)
    
    # created_at should NOT change
    assert turn.created_at == original_created_at
    
    # updated_at SHOULD change
    assert turn.updated_at > original_updated_at
    
    print("[PASS] PHASE 1 - TEST 8: Timestamps work correctly")


# ============================================================
# PHASE 1 - TEST 9: Phase Enum Validation
# ============================================================

@pytest.mark.asyncio
async def test_phase_enum_values(db_session, test_interview):
    """
    TEST: All InterviewPhase enum values work
    
    VALIDATES:
    - All phase values can be stored
    - Phase is stored as string in database
    - Phase can be compared with enum
    """
    phases = [
        InterviewPhase.INTRO,
        InterviewPhase.BEHAVIORAL,
        InterviewPhase.TECHNICAL,
        InterviewPhase.DEEP_DIVE,
        InterviewPhase.CLOSING
    ]
    
    for i, phase in enumerate(phases, start=1):
        turn = Turn(
            interview_id=test_interview.id,
            turn_number=i,
            phase=phase,
            ai_question=f"Question for {phase.value}"
        )
        db_session.add(turn)
    
    await db_session.commit()
    
    # Verify all phases stored correctly
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    result = await db_session.execute(
        select(Interview)
        .where(Interview.id == test_interview.id)
        .options(selectinload(Interview.turns))
    )
    interview_with_turns = result.scalar_one()
    assert len(interview_with_turns.turns) == 5
    
    for i, phase in enumerate(phases):
        # Phase is stored as string, compare values
        assert interview_with_turns.turns[i].phase == phase.value or interview_with_turns.turns[i].phase == phase
        if hasattr(interview_with_turns.turns[i].phase, 'value'):
            assert interview_with_turns.turns[i].phase.value == phase.value
        else:
            assert interview_with_turns.turns[i].phase == phase.value
    
    print("[PASS] PHASE 1 - TEST 9: All phase enum values work")


# ============================================================
# PHASE 1 - TEST 10: Long Text Fields
# ============================================================

@pytest.mark.asyncio
async def test_long_text_fields(db_session, test_interview):
    """
    TEST: ai_question and user_answer can store long text
    
    VALIDATES:
    - Text fields have no practical length limit
    - Long questions and answers are stored correctly
    """
    # Generate long text (2000 characters)
    long_question = "Can you explain " + ("your experience with " * 100) + "this technology?"
    long_answer = "I have worked on " + ("various projects including " * 100) + "many systems."
    
    turn = Turn(
        interview_id=test_interview.id,
        turn_number=1,
        phase=InterviewPhase.TECHNICAL,
        ai_question=long_question,
        user_answer=long_answer
    )
    
    db_session.add(turn)
    await db_session.commit()
    await db_session.refresh(turn)
    
    # Verify long text stored correctly
    assert len(turn.ai_question) > 1000
    assert len(turn.user_answer) > 1000
    assert turn.ai_question == long_question
    assert turn.user_answer == long_answer
    
    print("[PASS] PHASE 1 - TEST 10: Long text fields work")


# ============================================================
# RUN PHASE 1 TESTS
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔥 BATTLE TESTING: TURN MODEL - PHASE 1 (FOUNDATION)")
    print("="*60 + "\n")
    
    pytest.main([__file__, "-v", "-s"])
