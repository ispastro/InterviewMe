"""
AI Interview Conductor for InterviewMe Platform
Generates dynamic questions and provides real-time feedback using Groq API
"""
from typing import Dict, List, Any, Optional
import json
from groq import AsyncGroq
from ...config import settings

class InterviewConductor:
    """AI-powered interview conductor for real-time interviews"""
    
    def __init__(self):
        self.settings = settings
        self.client = AsyncGroq(api_key=self.settings.GROQ_API_KEY)
        
    async def generate_opening_question(self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the opening question for an interview"""
        
        cv_analysis = interview_data.get("cv_analysis", {})
        jd_analysis = interview_data.get("jd_analysis", {})
        interview_strategy = interview_data.get("interview_strategy", {})
        
        prompt = f"""
You are an expert interviewer conducting a job interview. Generate the opening question for this interview.

CANDIDATE PROFILE:
{json.dumps(cv_analysis, indent=2)}

JOB REQUIREMENTS:
{json.dumps(jd_analysis, indent=2)}

INTERVIEW STRATEGY:
{json.dumps(interview_strategy, indent=2)}

Generate an opening question that:
1. Is welcoming and professional
2. Allows the candidate to introduce themselves
3. Sets the tone for the interview
4. Is relevant to the role

Return ONLY a JSON object with this structure:
{{
    "question": "The opening question text",
    "question_type": "opening",
    "focus_area": "introduction",
    "expected_duration": 2,
    "evaluation_criteria": ["communication_skills", "confidence", "relevance"]
}}
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            result["turn_number"] = 1
            return result
            
        except Exception as e:
            print(f"Error generating opening question: {e}")
            # Fallback opening question
            return {
                "question": "Thank you for joining us today. Could you please start by telling me about yourself and what interests you about this position?",
                "question_type": "opening",
                "focus_area": "introduction",
                "expected_duration": 2,
                "evaluation_criteria": ["communication_skills", "confidence", "relevance"],
                "turn_number": 1
            }
    
    async def generate_follow_up_question(
        self, 
        interview_data: Dict[str, Any], 
        conversation_history: List[Dict[str, Any]], 
        current_turn: int
    ) -> Dict[str, Any]:
        """Generate follow-up question based on conversation history"""
        
        cv_analysis = interview_data.get("cv_analysis", {})
        jd_analysis = interview_data.get("jd_analysis", {})
        interview_strategy = interview_data.get("interview_strategy", {})
        
        # Format conversation history
        history_text = ""
        for turn in conversation_history[-3:]:  # Last 3 turns for context
            history_text += f"Q{turn.get('turn_number', 0)}: {turn.get('question', '')}\n"
            history_text += f"A{turn.get('turn_number', 0)}: {turn.get('response', '')}\n\n"
        
        prompt = f"""
You are an expert interviewer conducting a job interview. Generate the next question based on the conversation so far.

CANDIDATE PROFILE:
{json.dumps(cv_analysis, indent=2)}

JOB REQUIREMENTS:
{json.dumps(jd_analysis, indent=2)}

INTERVIEW STRATEGY:
{json.dumps(interview_strategy, indent=2)}

CONVERSATION HISTORY:
{history_text}

CURRENT TURN: {current_turn}

Generate the next question that:
1. Builds on the previous responses
2. Explores relevant skills/experience
3. Follows the interview strategy
4. Is appropriate for turn {current_turn}
5. Maintains natural conversation flow

Return ONLY a JSON object with this structure:
{{
    "question": "The follow-up question text",
    "question_type": "technical|behavioral|situational|closing",
    "focus_area": "specific skill or competency being assessed",
    "expected_duration": 3,
    "evaluation_criteria": ["criterion1", "criterion2", "criterion3"]
}}
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=600
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            result["turn_number"] = current_turn
            return result
            
        except Exception as e:
            print(f"Error generating follow-up question: {e}")
            # Fallback question
            return {
                "question": "Can you tell me more about a challenging project you've worked on and how you approached it?",
                "question_type": "behavioral",
                "focus_area": "problem_solving",
                "expected_duration": 3,
                "evaluation_criteria": ["problem_solving", "communication", "technical_depth"],
                "turn_number": current_turn
            }
    
    async def evaluate_response(
        self, 
        question_data: Dict[str, Any], 
        user_response: str, 
        interview_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate user response and provide feedback"""
        
        cv_analysis = interview_data.get("cv_analysis", {})
        jd_analysis = interview_data.get("jd_analysis", {})
        
        prompt = f"""
You are an expert interviewer evaluating a candidate's response. Provide constructive feedback.

QUESTION ASKED:
{question_data.get('question', '')}

QUESTION TYPE: {question_data.get('question_type', '')}
FOCUS AREA: {question_data.get('focus_area', '')}
EVALUATION CRITERIA: {question_data.get('evaluation_criteria', [])}

CANDIDATE'S RESPONSE:
{user_response}

CANDIDATE PROFILE:
{json.dumps(cv_analysis, indent=2)}

JOB REQUIREMENTS:
{json.dumps(jd_analysis, indent=2)}

Evaluate the response and provide feedback. Return ONLY a JSON object:
{{
    "overall_score": 7.5,
    "criteria_scores": {{
        "communication_skills": 8.0,
        "technical_knowledge": 7.0,
        "relevance": 8.0
    }},
    "strengths": ["Clear communication", "Good examples"],
    "areas_for_improvement": ["Could provide more technical details"],
    "feedback": "Good response with clear examples. Consider adding more technical depth.",
    "follow_up_suggestions": ["Ask about specific technologies used"]
}}
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            return result
            
        except Exception as e:
            print(f"Error evaluating response: {e}")
            # Fallback evaluation
            return {
                "overall_score": 7.0,
                "criteria_scores": {
                    "communication_skills": 7.0,
                    "relevance": 7.0
                },
                "strengths": ["Provided a response"],
                "areas_for_improvement": ["Could provide more detail"],
                "feedback": "Thank you for your response. Consider providing more specific examples.",
                "follow_up_suggestions": []
            }
    
    async def should_end_interview(
        self, 
        conversation_history: List[Dict[str, Any]], 
        current_turn: int,
        target_duration: int = 30
    ) -> Dict[str, Any]:
        """Determine if interview should end based on conversation flow"""
        
        # Simple heuristics for ending interview
        should_end = False
        reason = ""
        
        if current_turn >= 8:  # Maximum turns reached
            should_end = True
            reason = "Maximum number of questions reached"
        elif len(conversation_history) > 0:
            # Check if last few responses were very short
            recent_responses = conversation_history[-2:]
            avg_length = sum(len(turn.get('response', '')) for turn in recent_responses) / len(recent_responses)
            if avg_length < 50:  # Very short responses
                should_end = True
                reason = "Responses becoming too brief"
        
        return {
            "should_end": should_end,
            "reason": reason,
            "suggested_closing": "Thank you for your time today. Do you have any questions about the role or our company?"
        }
    
    async def generate_interview_summary(
        self, 
        interview_data: Dict[str, Any], 
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate final interview summary and recommendations"""
        
        # Format conversation for analysis
        conversation_text = ""
        total_score = 0
        score_count = 0
        
        for turn in conversation_history:
            conversation_text += f"Q: {turn.get('question', '')}\n"
            conversation_text += f"A: {turn.get('response', '')}\n"
            if turn.get('evaluation'):
                conversation_text += f"Score: {turn.get('evaluation', {}).get('overall_score', 0)}\n"
                total_score += turn.get('evaluation', {}).get('overall_score', 0)
                score_count += 1
            conversation_text += "\n"
        
        avg_score = total_score / score_count if score_count > 0 else 0
        
        prompt = f"""
You are an expert interviewer providing a final interview summary and recommendation.

INTERVIEW CONVERSATION:
{conversation_text}

AVERAGE SCORE: {avg_score:.1f}/10

Provide a comprehensive interview summary. Return ONLY a JSON object:
{{
    "overall_rating": "excellent|good|average|below_average|poor",
    "overall_score": 7.5,
    "key_strengths": ["strength1", "strength2"],
    "key_concerns": ["concern1", "concern2"],
    "technical_assessment": "Assessment of technical skills",
    "communication_assessment": "Assessment of communication skills",
    "cultural_fit": "Assessment of cultural fit",
    "recommendation": "hire|maybe|no_hire",
    "recommendation_reason": "Detailed reason for recommendation",
    "next_steps": ["Suggested next steps"]
}}
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1000
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            result["interview_duration"] = len(conversation_history)
            result["total_turns"] = len(conversation_history)
            return result
            
        except Exception as e:
            print(f"Error generating interview summary: {e}")
            # Fallback summary
            return {
                "overall_rating": "average",
                "overall_score": avg_score,
                "key_strengths": ["Participated in interview"],
                "key_concerns": ["Limited assessment due to technical issues"],
                "technical_assessment": "Unable to fully assess",
                "communication_assessment": "Basic communication observed",
                "cultural_fit": "Requires further evaluation",
                "recommendation": "maybe",
                "recommendation_reason": "Interview completed but requires additional assessment",
                "next_steps": ["Schedule follow-up interview"],
                "interview_duration": len(conversation_history),
                "total_turns": len(conversation_history)
            }

# Global interview conductor instance
interview_conductor = InterviewConductor()