from typing import Dict, List, Any, Optional, AsyncIterator
import json
import logging
from ...config import settings
from app.modules.llm.gateway import llm_gateway
from app.modules.llm.prompt_compressor import get_compressor

# Setup logging
logger = logging.getLogger(__name__)

class InterviewConductor:
    
    def __init__(self, use_compression: bool = True, compression_level: float = 0.7):
        self.settings = settings
        self.use_compression = use_compression
        self.compressor = get_compressor(compression_level) if use_compression else None
        
    async def generate_opening_question(self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        
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
            # Use LLM Gateway with caching
            result = await llm_gateway.completion_json(
                prompt=prompt,
                temperature=0.7,
                max_tokens=500,
                use_cache=True,
                cache_ttl=1800  # Cache for 30 minutes
            )
            
            result["turn_number"] = 1
            return result
            
        except Exception as e:
            logger.error(f"Error generating opening question: {e}")
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
        current_turn: int,
        memory_context: Optional[Dict[str, Any]] = None,
        focus_recommendation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        
        cv_analysis = interview_data.get("cv_analysis", {})
        jd_analysis = interview_data.get("jd_analysis", {})
        
        # Use memory context if available (AGENTIC ENHANCEMENT)
        if memory_context:
            performance_summary = memory_context.get("performance_summary", {})
            detected_patterns = memory_context.get("detected_patterns", {})
            uncovered_topics = memory_context.get("uncovered_topics", [])
        else:
            performance_summary = {}
            detected_patterns = {}
            uncovered_topics = []
        
        # Get focus area
        focus_area = "general"
        if focus_recommendation and focus_recommendation.get("priority_topics"):
            focus_area = focus_recommendation["priority_topics"][0]
        
        # 🎯 USE PROMPT COMPRESSION (if enabled)
        if self.use_compression and self.compressor:
            logger.info(f"🗜️ Using prompt compression for turn {current_turn}")
            prompt = self.compressor.build_compressed_prompt(
                cv_analysis=cv_analysis,
                jd_analysis=jd_analysis,
                conversation_history=conversation_history,
                focus_area=focus_area,
                performance_summary=performance_summary,
                current_turn=current_turn,
                detected_patterns=detected_patterns,
                uncovered_topics=uncovered_topics
            )
        else:
            # Fallback to original verbose prompt
            logger.info(f"📝 Using original prompt (no compression) for turn {current_turn}")
            interview_strategy = interview_data.get("interview_strategy", {})
            recent_turns = conversation_history[-3:]
            
            # Format conversation history
            history_text = ""
            for turn in recent_turns:
                history_text += f"Q{turn.get('turn_number', 0)}: {turn.get('question', '')}\n"
                history_text += f"A{turn.get('turn_number', 0)}: {turn.get('response', '')}\n"
                eval_score = turn.get('evaluation', {}).get('overall_score', 0)
                history_text += f"Score: {eval_score}/10\n\n"
            
            # Build performance text
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
            # Use LLM Gateway (no caching for context-dependent questions)
            result = await llm_gateway.completion_json(
                prompt=prompt,
                temperature=0.8,
                max_tokens=600,
                use_cache=False
            )
            
            result["turn_number"] = current_turn
            return result
            
        except Exception as e:
            logger.error(f"Error generating follow-up question: {e}")
            
            # Context-aware fallback questions to prevent loops
            fallback_questions = [
                {
                    "question": "Can you tell me more about a challenging project you've worked on and how you approached it?",
                    "focus_area": "problem_solving"
                },
                {
                    "question": "How do you stay updated with the latest technologies and industry trends in your field?",
                    "focus_area": "continuous_learning"
                },
                {
                    "question": "Describe a situation where you had to work with a difficult team member. How did you handle it?",
                    "focus_area": "teamwork"
                },
                {
                    "question": "What's your approach to debugging a complex issue in production?",
                    "focus_area": "debugging"
                },
                {
                    "question": "Tell me about a time when you had to make a technical decision with incomplete information.",
                    "focus_area": "decision_making"
                }
            ]
            
            # Select fallback based on turn number to avoid repetition
            fallback_index = (current_turn - 1) % len(fallback_questions)
            selected_fallback = fallback_questions[fallback_index]
            
            return {
                "question": selected_fallback["question"],
                "question_type": "behavioral",
                "focus_area": selected_fallback["focus_area"],
                "expected_duration": 3,
                "evaluation_criteria": ["problem_solving", "communication", "technical_depth"],
                "turn_number": current_turn
            }
    
    async def generate_probe_question(self, turn_data: Dict[str, Any], probe_reason: str, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        
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
            # Use LLM Gateway
            result = await llm_gateway.completion_json(
                prompt=prompt,
                temperature=0.7,
                max_tokens=400,
                use_cache=False
            )
            
            result["turn_number"] = turn_data.get('turn_number', 0)
            result["is_probe"] = True
            return result
            
        except Exception as e:
            logger.error(f"Error generating probe question: {e}")
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
    
    async def evaluate_response(self, question_data: Dict[str, Any], user_response: str, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        
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
            # Use LLM Gateway
            result = await llm_gateway.completion_json(
                prompt=prompt,
                temperature=0.3,
                max_tokens=800,
                use_cache=False
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating response: {e}")
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
    
    async def should_end_interview(self, conversation_history: List[Dict[str, Any]], current_turn: int, target_duration: int = 10) -> Dict[str, Any]:
        
        # Simple heuristics for ending interview
        should_end = False
        reason = ""
        
        if current_turn >= 5:  # Changed from 8 to 5 for 10-minute interviews
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
    
    async def generate_interview_summary(self, interview_data: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        
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
            # Use LLM Gateway
            result = await llm_gateway.completion_json(
                prompt=prompt,
                temperature=0.2,
                max_tokens=1000,
                use_cache=False
            )
            
            result["interview_duration"] = len(conversation_history)
            result["total_turns"] = len(conversation_history)
            return result
            
        except Exception as e:
            logger.error(f"Error generating interview summary: {e}")
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
    
    def get_compression_metrics(self) -> Dict[str, Any]:
        """
        Get prompt compression metrics.
        
        Returns:
            Dictionary with compression statistics
        """
        if self.use_compression and self.compressor:
            return self.compressor.get_metrics()
        return {"enabled": False, "message": "Compression is disabled"}
    
    async def generate_follow_up_question_stream(
        self,
        interview_data: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        current_turn: int,
        memory_context: Optional[Dict[str, Any]] = None,
        focus_recommendation: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """
        Stream follow-up question generation in real-time.
        
        Yields text chunks as they arrive from the LLM.
        
        Args:
            interview_data: Interview context
            conversation_history: Previous Q&A turns
            current_turn: Current turn number
            memory_context: Agentic memory context
            focus_recommendation: Focus area recommendation
            
        Yields:
            JSON string chunks (partial or complete)
        """
        cv_analysis = interview_data.get("cv_analysis", {})
        jd_analysis = interview_data.get("jd_analysis", {})
        
        # Use memory context if available
        if memory_context:
            performance_summary = memory_context.get("performance_summary", {})
            detected_patterns = memory_context.get("detected_patterns", {})
            uncovered_topics = memory_context.get("uncovered_topics", [])
        else:
            performance_summary = {}
            detected_patterns = {}
            uncovered_topics = []
        
        # Get focus area
        focus_area = "general"
        if focus_recommendation and focus_recommendation.get("priority_topics"):
            focus_area = focus_recommendation["priority_topics"][0]
        
        # Build prompt (with compression if enabled)
        if self.use_compression and self.compressor:
            logger.info(f"🗜️ Using prompt compression for streaming turn {current_turn}")
            prompt = self.compressor.build_compressed_prompt(
                cv_analysis=cv_analysis,
                jd_analysis=jd_analysis,
                conversation_history=conversation_history,
                focus_area=focus_area,
                performance_summary=performance_summary,
                current_turn=current_turn,
                detected_patterns=detected_patterns,
                uncovered_topics=uncovered_topics
            )
        else:
            # Use original verbose prompt (same as non-streaming version)
            logger.info(f"📝 Using original prompt for streaming turn {current_turn}")
            interview_strategy = interview_data.get("interview_strategy", {})
            recent_turns = conversation_history[-3:]
            
            history_text = ""
            for turn in recent_turns:
                history_text += f"Q{turn.get('turn_number', 0)}: {turn.get('question', '')}\n"
                history_text += f"A{turn.get('turn_number', 0)}: {turn.get('response', '')}\n"
                eval_score = turn.get('evaluation', {}).get('overall_score', 0)
                history_text += f"Score: {eval_score}/10\n\n"
            
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
            # Stream from LLM Gateway
            async for chunk in llm_gateway.completion_stream(
                prompt=prompt,
                temperature=0.8,
                max_tokens=600,
                use_cache=False
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error streaming follow-up question: {e}")
            # Yield fallback question as single chunk
            fallback_questions = [
                {
                    "question": "Can you tell me more about a challenging project you've worked on and how you approached it?",
                    "focus_area": "problem_solving"
                },
                {
                    "question": "How do you stay updated with the latest technologies and industry trends in your field?",
                    "focus_area": "continuous_learning"
                },
                {
                    "question": "Describe a situation where you had to work with a difficult team member. How did you handle it?",
                    "focus_area": "teamwork"
                },
                {
                    "question": "What's your approach to debugging a complex issue in production?",
                    "focus_area": "debugging"
                },
                {
                    "question": "Tell me about a time when you had to make a technical decision with incomplete information.",
                    "focus_area": "decision_making"
                }
            ]
            
            fallback_index = (current_turn - 1) % len(fallback_questions)
            selected_fallback = fallback_questions[fallback_index]
            
            fallback_response = json.dumps({
                "question": selected_fallback["question"],
                "question_type": "behavioral",
                "focus_area": selected_fallback["focus_area"],
                "expected_duration": 3,
                "evaluation_criteria": ["problem_solving", "communication", "technical_depth"],
                "turn_number": current_turn
            })
            
            yield fallback_response

interview_conductor = InterviewConductor(use_compression=True, compression_level=0.7)
