"""
AI Interview Conductor for InterviewMe Platform
Generates dynamic questions and provides real-time feedback using Groq API
"""
from typing import Dict, List, Any, Optional
import json
from groq import AsyncGroq
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import logging
from ...config import settings

# Setup logging for retry attempts
logger = logging.getLogger(__name__)

class InterviewConductor:
    """AI-powered interview conductor for real-time interviews"""
    
    def __init__(self):
        self.settings = settings
        self.client = AsyncGroq(api_key=self.settings.GROQ_API_KEY)
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
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
            
            try:
                result = json.loads(response.choices[0].message.content.strip())
            except json.JSONDecodeError:
                # Try to extract JSON from markdown if needed
                content = response.choices[0].message.content.strip()
                if "```" in content:
                    if "```json" in content:
                        json_start = content.find("```json") + 7
                    else:
                        json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    if json_end > json_start:
                        content = content[json_start:json_end].strip()
                        result = json.loads(content)
                    else:
                        raise
                else:
                    raise
            
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
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def generate_follow_up_question(
        self, 
        interview_data: Dict[str, Any], 
        conversation_history: List[Dict[str, Any]], 
        current_turn: int,
        memory_context: Optional[Dict[str, Any]] = None,
        focus_recommendation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate follow-up question based on conversation history"""
        
        cv_analysis = interview_data.get("cv_analysis", {})
        jd_analysis = interview_data.get("jd_analysis", {})
        interview_strategy = interview_data.get("interview_strategy", {})
        
        # Use memory context if available (AGENTIC ENHANCEMENT)
        if memory_context:
            recent_turns = memory_context.get("recent_turns", conversation_history[-3:])
            performance_summary = memory_context.get("performance_summary", {})
            detected_patterns = memory_context.get("detected_patterns", {})
            uncovered_topics = memory_context.get("uncovered_topics", [])
        else:
            recent_turns = conversation_history[-3:]
            performance_summary = {}
            detected_patterns = {}
            uncovered_topics = []
        
        # Format conversation history with richer context
        history_text = ""
        for turn in recent_turns:
            history_text += f"Q{turn.get('turn_number', 0)}: {turn.get('question', '')}\n"
            history_text += f"A{turn.get('turn_number', 0)}: {turn.get('response', '')}\n"
            eval_score = turn.get('evaluation', {}).get('overall_score', 0)
            history_text += f"Score: {eval_score}/10\n\n"
        
        # Build agentic prompt with memory insights
        performance_text = ""
        if performance_summary:
            performance_text = f"""

CANDIDATE PERFORMANCE SO FAR:
- Average Score: {performance_summary.get('average_score', 0)}/10
- Trend: {performance_summary.get('score_trend', 'stable')}
- Technical Depth: {performance_summary.get('technical_depth_avg', 0)}/10
- Communication: {performance_summary.get('communication_clarity_avg', 0)}/10
- Confidence Level: {performance_summary.get('confidence_level', 'medium')}
"""
        
        patterns_text = ""
        if detected_patterns:
            if detected_patterns.get('strengths'):
                patterns_text += f"\n✓ IDENTIFIED STRENGTHS: {', '.join(detected_patterns['strengths'][:3])}"
            if detected_patterns.get('weaknesses'):
                patterns_text += f"\n⚠ AREAS NEEDING IMPROVEMENT: {', '.join(detected_patterns['weaknesses'][:3])}"
            if detected_patterns.get('red_flags'):
                patterns_text += f"\n🚩 RED FLAGS: {len(detected_patterns['red_flags'])} detected"
        
        focus_text = ""
        if focus_recommendation:
            focus_text = f"""

RECOMMENDED FOCUS:
{focus_recommendation.get('recommendation', '')}
- Priority Topics: {', '.join(focus_recommendation.get('priority_topics', [])[:3])}
- Weak Areas to Probe: {', '.join(focus_recommendation.get('weak_areas_to_probe', [])[:2])}
"""
        
        uncovered_text = ""
        if uncovered_topics:
            uncovered_text = f"\n\nUNCOVERED REQUIRED TOPICS: {', '.join(uncovered_topics[:5])}"
        
        prompt = f"""
You are an expert AI interviewer with deep memory and context awareness. You conduct natural, conversational interviews that adapt to the candidate's performance.

CANDIDATE PROFILE:
{json.dumps(cv_analysis, indent=2)}

JOB REQUIREMENTS:
{json.dumps(jd_analysis, indent=2)}

INTERVIEW STRATEGY:
{json.dumps(interview_strategy, indent=2)}
{performance_text}
{patterns_text}
{focus_text}
{uncovered_text}

RECENT CONVERSATION:
{history_text}

CURRENT TURN: {current_turn}

🎯 YOUR MISSION:
Generate the next question that feels like a REAL human interviewer who:
1. **Remembers everything** - Reference specific things they said earlier
2. **Adapts difficulty** - If they're doing well, challenge them harder. If struggling, ease up.
3. **Probes intelligently** - Follow up on weak areas, validate strengths
4. **Connects to the job** - Tie questions to actual job requirements from the JD
5. **Sounds natural** - Use conversational transitions like "That's interesting...", "Building on that...", "I noticed you mentioned..."
6. **Covers gaps** - Focus on uncovered required topics

⚡ AGENTIC BEHAVIOR:
- If they showed weakness in an area, probe deeper with a specific scenario
- If they're performing well, increase difficulty with edge cases or system design
- If they mentioned something from their CV, ask them to elaborate with specifics
- If they're struggling, provide a hint or rephrase to build confidence

Return ONLY a JSON object:
{{
    "question": "[Natural transition] + [The actual question]",
    "question_type": "technical|behavioral|situational|deep_dive|closing",
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
            
            try:
                result = json.loads(response.choices[0].message.content.strip())
            except json.JSONDecodeError:
                # Try to extract JSON from markdown if needed
                content = response.choices[0].message.content.strip()
                if "```" in content:
                    if "```json" in content:
                        json_start = content.find("```json") + 7
                    else:
                        json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    if json_end > json_start:
                        content = content[json_start:json_end].strip()
                        result = json.loads(content)
                    else:
                        raise
                else:
                    raise
            
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
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def generate_probe_question(
        self,
        turn_data: Dict[str, Any],
        probe_reason: str,
        interview_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a probing follow-up question based on the last response"""
        
        question = turn_data.get('question', '')
        response = turn_data.get('response', '')
        evaluation = turn_data.get('evaluation', {})
        focus_area = turn_data.get('focus_area', '')
        
        prompt = f"""
You are an expert interviewer who just received an answer that needs clarification or deeper exploration.

ORIGINAL QUESTION:
{question}

CANDIDATE'S RESPONSE:
{response}

EVALUATION:
- Score: {evaluation.get('overall_score', 0)}/10
- Feedback: {evaluation.get('feedback', '')}

REASON FOR PROBING:
{probe_reason}

FOCUS AREA: {focus_area}

🔍 YOUR TASK:
Generate a natural, conversational follow-up question that:
1. **Acknowledges their answer** - Start with "Interesting...", "I see...", "That makes sense, but..."
2. **Probes deeper** - Ask for specifics, examples, or clarification
3. **Feels natural** - Not interrogative, but genuinely curious
4. **Targets the gap** - Address the specific reason we're probing

EXAMPLES:
- If vague: "That's a good start. Can you walk me through a specific example of when you did this?"
- If lacks technical depth: "Interesting approach. How exactly did you implement the caching layer? What data structures did you use?"
- If contradicts CV: "I noticed your CV mentions experience with Kubernetes, but you mentioned you haven't worked with container orchestration. Can you clarify?"
- If red flag: "You mentioned you're not familiar with that. How would you approach learning it if this role required it?"

Return ONLY a JSON object:
{{
    "question": "[Acknowledgment] + [Probing question]",
    "question_type": "probe",
    "focus_area": "{focus_area}",
    "expected_duration": 2,
    "evaluation_criteria": ["specificity", "technical_depth", "clarity"]
}}
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=400
            )
            
            try:
                result = json.loads(response.choices[0].message.content.strip())
            except json.JSONDecodeError:
                content = response.choices[0].message.content.strip()
                if "```" in content:
                    if "```json" in content:
                        json_start = content.find("```json") + 7
                    else:
                        json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    if json_end > json_start:
                        content = content[json_start:json_end].strip()
                        result = json.loads(content)
                    else:
                        raise
                else:
                    raise
            
            result["turn_number"] = turn_data.get('turn_number', 0)
            result["is_probe"] = True
            return result
            
        except Exception as e:
            print(f"Error generating probe question: {e}")
            # Fallback probe question
            return {
                "question": "Can you elaborate on that with a specific example from your experience?",
                "question_type": "probe",
                "focus_area": focus_area,
                "expected_duration": 2,
                "evaluation_criteria": ["specificity", "clarity"],
                "turn_number": turn_data.get('turn_number', 0),
                "is_probe": True
            }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
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

JOB REQUIREMENTS & NUANCES:
{json.dumps(jd_analysis, indent=2)}

INTERVIEW STRATEGY:
{json.dumps(interview_data.get('interview_strategy', {}), indent=2)}

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
            
            try:
                result = json.loads(response.choices[0].message.content.strip())
            except json.JSONDecodeError:
                # Try to extract JSON from markdown if needed
                content = response.choices[0].message.content.strip()
                if "```" in content:
                    if "```json" in content:
                        json_start = content.find("```json") + 7
                    else:
                        json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    if json_end > json_start:
                        content = content[json_start:json_end].strip()
                        result = json.loads(content)
                    else:
                        raise
                else:
                    raise
            
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
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
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
            
            try:
                result = json.loads(response.choices[0].message.content.strip())
            except json.JSONDecodeError:
                # Try to extract JSON from markdown if needed
                content = response.choices[0].message.content.strip()
                if "```" in content:
                    if "```json" in content:
                        json_start = content.find("```json") + 7
                    else:
                        json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    if json_end > json_start:
                        content = content[json_start:json_end].strip()
                        result = json.loads(content)
                    else:
                        raise
                else:
                    raise
            
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