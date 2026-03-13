"""
Quick AI Demo - Test Real Groq API Responses
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.modules.websocket.interview_conductor import InterviewConductor

async def test_real_ai():
    print("[AI] Testing Real AI Integration with Groq API")
    print("=" * 50)
    
    conductor = InterviewConductor()
    
    # Sample interview data
    interview_data = {
        "cv_analysis": {
            "candidate_name": "John Smith",
            "years_of_experience": 3,
            "skills": {
                "technical": ["Python", "FastAPI", "React", "PostgreSQL", "Docker"],
                "soft": ["Communication", "Problem-solving", "Leadership"]
            },
            "experience": [
                {
                    "role": "Software Developer",
                    "company": "Tech Corp",
                    "duration": "2 years",
                    "technologies_used": ["Python", "FastAPI", "React"]
                }
            ]
        },
        "jd_analysis": {
            "role_title": "Senior Backend Developer",
            "required_skills": ["Python", "FastAPI", "System Design", "AWS"],
            "experience_level": "3-5 years",
            "company": "InnovateTech"
        },
        "interview_strategy": {
            "focus_areas": ["technical_skills", "system_design", "problem_solving"],
            "difficulty": "medium"
        }
    }
    
    print("[STEP 1] Generating Opening Question...")
    opening = await conductor.generate_opening_question(interview_data)
    print(f"Question: {opening['question']}")
    print(f"Type: {opening['question_type']}")
    print(f"Focus: {opening['focus_area']}")
    print()
    
    print("[STEP 2] Simulating User Response...")
    user_response = "Hi! I'm John, a software developer with 3 years of experience in Python and web development. I'm excited about this senior backend role because it aligns perfectly with my skills in FastAPI and system design. I've built several scalable APIs at my current company and I'm passionate about clean, efficient code."
    
    print("[STEP 3] Evaluating Response...")
    evaluation = await conductor.evaluate_response(opening, user_response, interview_data)
    print(f"Overall Score: {evaluation['overall_score']}/10")
    print(f"Strengths: {', '.join(evaluation['strengths'])}")
    print(f"Feedback: {evaluation['feedback']}")
    print()
    
    print("[STEP 4] Generating Follow-up Question...")
    conversation_history = [
        {
            "turn_number": 1,
            "question": opening["question"],
            "response": user_response,
            "evaluation": evaluation
        }
    ]
    
    follow_up = await conductor.generate_follow_up_question(
        interview_data, conversation_history, 2
    )
    print(f"Next Question: {follow_up['question']}")
    print(f"Type: {follow_up['question_type']}")
    print(f"Focus: {follow_up['focus_area']}")
    print()
    
    print("[STEP 5] Generating Interview Summary...")
    summary = await conductor.generate_interview_summary(interview_data, conversation_history)
    print(f"Overall Rating: {summary['overall_rating']}")
    print(f"Overall Score: {summary['overall_score']}/10")
    print(f"Recommendation: {summary['recommendation']}")
    print(f"Key Strengths: {', '.join(summary['key_strengths'])}")
    print(f"Recommendation Reason: {summary['recommendation_reason']}")
    
    print("\n[SUCCESS] AI Integration Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_real_ai())