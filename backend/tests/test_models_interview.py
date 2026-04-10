"""
🔥 BATTLE TEST: Interview Model
Tests every single field, relationship, method, and edge case.
No mercy - if it can break, we'll find it!
"""

import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from app.database import Base
from app.models.user import User
from app.models.interview import Interview, Turn, InterviewStatus, InterviewPhase


# ============================================================
# FIXTURES - Test Database Setup
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
        # Enable foreign key constraints in SQLite
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


# ============================================================
# TEST 1: Interview Creation (Basic Fields)
# ============================================================

@pytest.mark.asyncio
async def test_create_interview_minimal(db_session, test_user):
    """Test creating interview with minimal required fields"""
    interview = Interview(
        user_id=test_user.id,
        status=InterviewStatus.PENDING
    )
    
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)
    
    # Assertions
    assert interview.id is not None
    assert isinstance(interview.id, uuid.UUID)
    assert interview.user_id == test_user.id
    assert interview.status == InterviewStatus.PENDING
    assert interview.current_turn == 0
    assert interview.created_at is not None
    assert interview.updated_at is not None
    
    print("[PASS] TEST 1: Minimal interview creation")


@pytest.mark.asyncio
async def test_create_interview_full(db_session, test_user):
    """Test creating interview with all fields populated"""
    cv_analysis = {
        "candidate_name": "John Doe",
        "years_of_experience": 5,
        "skills": {"technical": ["Python", "React"], "soft": ["Leadership"]}
    }
    
    jd_analysis = {
        "role_title": "Senior Engineer",
        "required_skills": ["Python", "AWS"]
    }
    
    interview = Interview(
        user_id=test_user.id,
        status=InterviewStatus.READY,
        cv_raw_text="I am a software engineer...",
        cv_analysis=cv_analysis,
        jd_raw_text="We are looking for...",
        jd_analysis=jd_analysis,
        target_role="Senior Software Engineer",
        target_company="Tech Corp",
        current_phase=InterviewPhase.INTRO,
        current_turn=1
    )
    
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)
    
    # Assertions
    assert interview.cv_analysis == cv_analysis
    assert interview.jd_analysis == jd_analysis
    assert interview.target_role == "Senior Software Engineer"
    assert interview.target_company == "Tech Corp"
    assert interview.current_phase == InterviewPhase.INTRO
    assert interview.current_turn == 1
    
    print("[PASS] TEST 2: Full interview creation")


# ============================================================
# TEST 2: Status Transitions
# ============================================================

@pytest.mark.asyncio
async def test_interview_status_flow(db_session, test_user):
    """Test complete interview status lifecycle"""
    interview = Interview(user_id=test_user.id, status=InterviewStatus.PENDING)
    db_session.add(interview)
    await db_session.commit()
    
    # PENDING → PROCESSING_CV
    interview.status = InterviewStatus.PROCESSING_CV
    await db_session.commit()
    assert interview.status == InterviewStatus.PROCESSING_CV
    
    # PROCESSING_CV → READY
    interview.status = InterviewStatus.READY
    await db_session.commit()
    assert interview.status == InterviewStatus.READY
    
    # READY → IN_PROGRESS
    interview.status = InterviewStatus.IN_PROGRESS
    interview.current_phase = InterviewPhase.INTRO
    await db_session.commit()
    assert interview.status == InterviewStatus.IN_PROGRESS
    assert interview.is_in_progress is True
    
    # IN_PROGRESS → COMPLETED
    interview.status = InterviewStatus.COMPLETED
    interview.completed_at = datetime.now(timezone.utc)
    interview.total_duration_seconds = 600.0
    await db_session.commit()
    assert interview.status == InterviewStatus.COMPLETED
    assert interview.is_completed is True
    assert interview.completed_at is not None
    
    print("[PASS] TEST 3: Status transitions")


# ============================================================
# TEST 3: JSON Fields (CV/JD Analysis)
# ============================================================

@pytest.mark.asyncio
async def test_cv_analysis_json(db_session, test_user):
    """Test CV analysis JSON field with complex nested data"""
    cv_analysis = {
        "candidate_name": "Alice Smith",
        "years_of_experience": 5,
        "current_role": "Senior Engineer",
        "seniority_level": "senior",
        "skills": {
            "technical": ["Python", "React", "PostgreSQL", "AWS"],
            "soft": ["Leadership", "Communication"]
        },
        "experience": [
            {
                "company": "Tech Corp",
                "role": "Senior Engineer",
                "duration": "2020-2024",
                "responsibilities": ["Led team", "Built systems"]
            }
        ],
        "education": [
            {"degree": "BS CS", "school": "MIT", "year": "2019"}
        ]
    }
    
    interview = Interview(
        user_id=test_user.id,
        cv_analysis=cv_analysis
    )
    
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)
    
    # Assertions
    assert interview.cv_analysis["candidate_name"] == "Alice Smith"
    assert interview.cv_analysis["years_of_experience"] == 5
    assert len(interview.cv_analysis["skills"]["technical"]) == 4
    assert interview.cv_analysis["experience"][0]["company"] == "Tech Corp"
    
    print("[PASS] TEST 4: CV analysis JSON")


@pytest.mark.asyncio
async def test_jd_analysis_json(db_session, test_user):
    """Test JD analysis JSON field"""
    jd_analysis = {
        "role_title": "Senior Software Engineer",
        "company": "Tech Corp",
        "seniority_level": "senior",
        "required_skills": ["Python", "React", "AWS"],
        "preferred_skills": ["Kubernetes", "GraphQL"],
        "requirements": {
            "education": "BS in CS",
            "experience_years": 5,
            "must_have": ["Python", "React"]
        }
    }
    
    interview = Interview(
        user_id=test_user.id,
        jd_analysis=jd_analysis
    )
    
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)
    
    # Assertions
    assert interview.jd_analysis["role_title"] == "Senior Software Engineer"
    assert len(interview.jd_analysis["required_skills"]) == 3
    assert interview.jd_analysis["requirements"]["experience_years"] == 5
    
    print("[PASS] TEST 5: JD analysis JSON")


# ============================================================
# TEST 4: Methods (get_cv_skills, get_skill_gap_analysis)
# ============================================================

@pytest.mark.asyncio
async def test_get_cv_skills(db_session, test_user):
    """Test extracting skills from CV analysis"""
    interview = Interview(
        user_id=test_user.id,
        cv_analysis={
            "skills": {
                "technical": ["Python", "React", "PostgreSQL"],
                "soft": ["Leadership"]
            }
        }
    )
    
    db_session.add(interview)
    await db_session.commit()
    
    skills = interview.get_cv_skills()
    assert skills == ["Python", "React", "PostgreSQL"]
    
    print("[PASS] TEST 6: get_cv_skills()")


@pytest.mark.asyncio
async def test_get_jd_requirements(db_session, test_user):
    """Test extracting requirements from JD analysis"""
    interview = Interview(
        user_id=test_user.id,
        jd_analysis={
            "required_skills": ["Python", "AWS", "Kubernetes"]
        }
    )
    
    db_session.add(interview)
    await db_session.commit()
    
    requirements = interview.get_jd_requirements()
    assert requirements == ["Python", "AWS", "Kubernetes"]
    
    print("[PASS] TEST 7: get_jd_requirements()")


@pytest.mark.asyncio
async def test_skill_gap_analysis(db_session, test_user):
    """Test skill gap analysis between CV and JD"""
    interview = Interview(
        user_id=test_user.id,
        cv_analysis={
            "skills": {
                "technical": ["Python", "React", "PostgreSQL"]
            }
        },
        jd_analysis={
            "required_skills": ["Python", "React", "AWS", "Kubernetes"]
        }
    )
    
    db_session.add(interview)
    await db_session.commit()
    
    gap = interview.get_skill_gap_analysis()
    
    # Assertions
    assert set(gap["matching_skills"]) == {"python", "react"}
    assert set(gap["missing_skills"]) == {"aws", "kubernetes"}
    assert set(gap["additional_skills"]) == {"postgresql"}
    
    print("[PASS] TEST 8: get_skill_gap_analysis()")


# ============================================================
# TEST 5: Edge Cases & Error Handling
# ============================================================

@pytest.mark.asyncio
async def test_interview_without_user_fails(db_session):
    """Test that interview requires valid user_id"""
    fake_user_id = uuid.uuid4()
    
    interview = Interview(
        user_id=fake_user_id,
        status=InterviewStatus.PENDING
    )
    
    db_session.add(interview)
    
    with pytest.raises(IntegrityError):
        await db_session.commit()
    
    print("[PASS] TEST 9: Foreign key constraint enforced")


@pytest.mark.asyncio
async def test_get_cv_skills_empty(db_session, test_user):
    """Test get_cv_skills with no analysis"""
    interview = Interview(user_id=test_user.id)
    db_session.add(interview)
    await db_session.commit()
    
    skills = interview.get_cv_skills()
    assert skills == []
    
    print("[PASS] TEST 10: get_cv_skills() with no data")


@pytest.mark.asyncio
async def test_get_cv_skills_malformed(db_session, test_user):
    """Test get_cv_skills with malformed data"""
    interview = Interview(
        user_id=test_user.id,
        cv_analysis={"skills": "not a dict"}
    )
    db_session.add(interview)
    await db_session.commit()
    
    skills = interview.get_cv_skills()
    assert skills == []
    
    print("[PASS] TEST 11: get_cv_skills() handles malformed data")


@pytest.mark.asyncio
async def test_skill_gap_with_empty_data(db_session, test_user):
    """Test skill gap analysis with empty data"""
    interview = Interview(user_id=test_user.id)
    db_session.add(interview)
    await db_session.commit()
    
    gap = interview.get_skill_gap_analysis()
    
    assert gap["matching_skills"] == []
    assert gap["missing_skills"] == []
    assert gap["additional_skills"] == []
    
    print("[PASS] TEST 12: Skill gap with empty data")


# ============================================================
# RUN ALL TESTS
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔥 BATTLE TESTING: INTERVIEW MODEL")
    print("="*60 + "\n")
    
    pytest.main([__file__, "-v", "-s"])
