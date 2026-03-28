
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class InsightType(str, Enum):
    STRENGTH = "strength"
    WEAKNESS = "weakness"
    TECHNICAL_DEPTH = "technical_depth"
    COMMUNICATION_PATTERN = "communication_pattern"
    RED_FLAG = "red_flag"
    CONTRADICTION = "contradiction"
    CONFIDENCE_INDICATOR = "confidence_indicator"


@dataclass
class ConversationInsight:
    type: InsightType
    area: str
    evidence: str
    turn_number: int
    score: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "area": self.area,
            "evidence": self.evidence[:200],  # Truncate for efficiency
            "turn_number": self.turn_number,
            "score": self.score,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class PerformanceMetrics:
    average_score: float = 0.0
    score_trend: str = "stable"  # improving, declining, stable
    recent_scores: List[float] = field(default_factory=list)
    technical_depth_avg: float = 0.0
    communication_clarity_avg: float = 0.0
    response_length_avg: int = 0
    confidence_level: str = "medium"  # low, medium, high
    
    def update(self, evaluation: Dict[str, Any], response_text: str):
        overall_score = evaluation.get("overall_score", 0.0)
        
        # Update recent scores (keep last 5)
        self.recent_scores.append(overall_score)
        if len(self.recent_scores) > 5:
            self.recent_scores.pop(0)
        
        # Calculate average
        self.average_score = sum(self.recent_scores) / len(self.recent_scores)
        
        # Determine trend
        if len(self.recent_scores) >= 3:
            recent_avg = sum(self.recent_scores[-3:]) / 3
            older_avg = sum(self.recent_scores[:-3]) / max(1, len(self.recent_scores) - 3)
            
            if recent_avg > older_avg + 0.5:
                self.score_trend = "improving"
            elif recent_avg < older_avg - 0.5:
                self.score_trend = "declining"
            else:
                self.score_trend = "stable"
        
        # Update specific metrics
        criteria_scores = evaluation.get("criteria_scores", {})
        self.technical_depth_avg = criteria_scores.get("technical_knowledge", 
                                                       criteria_scores.get("depth", 5.0))
        self.communication_clarity_avg = criteria_scores.get("communication_skills",
                                                             criteria_scores.get("clarity", 5.0))
        
        # Response length
        self.response_length_avg = len(response_text.split())
        
        # Confidence indicators
        confidence_words = ["definitely", "certainly", "confident", "sure", "absolutely"]
        uncertainty_words = ["maybe", "perhaps", "not sure", "don't know", "uncertain", "think"]
        
        text_lower = response_text.lower()
        confidence_count = sum(1 for word in confidence_words if word in text_lower)
        uncertainty_count = sum(1 for word in uncertainty_words if word in text_lower)
        
        if confidence_count > uncertainty_count:
            self.confidence_level = "high"
        elif uncertainty_count > confidence_count + 1:
            self.confidence_level = "low"
        else:
            self.confidence_level = "medium"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "average_score": round(self.average_score, 2),
            "score_trend": self.score_trend,
            "recent_scores": [round(s, 2) for s in self.recent_scores],
            "technical_depth_avg": round(self.technical_depth_avg, 2),
            "communication_clarity_avg": round(self.communication_clarity_avg, 2),
            "response_length_avg": self.response_length_avg,
            "confidence_level": self.confidence_level
        }


class ConversationMemory:
    
    def __init__(self, cv_analysis: Dict[str, Any], jd_analysis: Dict[str, Any]):
        self.cv_analysis = cv_analysis
        self.jd_analysis = jd_analysis
        
        # Full conversation history
        self.full_history: List[Dict[str, Any]] = []
        
        # Extracted insights
        self.insights: List[ConversationInsight] = []
        
        # Performance tracking
        self.performance = PerformanceMetrics()
        
        # Topic coverage tracking
        self.covered_topics: set = set()
        self.required_topics = set(jd_analysis.get("interview_focus_areas", []))
        
        # Pattern detection
        self.detected_patterns: Dict[str, List[str]] = {
            "strengths": [],
            "weaknesses": [],
            "red_flags": [],
            "contradictions": []
        }
    
    def add_turn(self, turn_data: Dict[str, Any]) -> None:
        # Add to full history
        self.full_history.append(turn_data)
        
        # Update performance metrics
        evaluation = turn_data.get("evaluation", {})
        response = turn_data.get("response", "")
        self.performance.update(evaluation, response)
        
        # Extract insights
        self._extract_insights(turn_data)
        
        # Track topic coverage
        focus_area = turn_data.get("focus_area", "")
        if focus_area:
            self.covered_topics.add(focus_area.lower())
    
    def _extract_insights(self, turn_data: Dict[str, Any]) -> None:
        evaluation = turn_data.get("evaluation", {})
        response = turn_data.get("response", "")
        turn_number = turn_data.get("turn_number", 0)
        overall_score = evaluation.get("overall_score", 0.0)
        
        # Extract strengths (score > 7.5)
        if overall_score > 7.5:
            strengths = evaluation.get("strengths", [])
            for strength in strengths[:2]:  # Top 2 strengths
                insight = ConversationInsight(
                    type=InsightType.STRENGTH,
                    area=turn_data.get("focus_area", "general"),
                    evidence=strength,
                    turn_number=turn_number,
                    score=overall_score,
                    timestamp=datetime.utcnow(),
                    metadata={"question_type": turn_data.get("question_type", "")}
                )
                self.insights.append(insight)
                self.detected_patterns["strengths"].append(strength)
        
        # Extract weaknesses (score < 6.0)
        if overall_score < 6.0:
            weaknesses = evaluation.get("areas_for_improvement", [])
            for weakness in weaknesses[:2]:  # Top 2 weaknesses
                insight = ConversationInsight(
                    type=InsightType.WEAKNESS,
                    area=turn_data.get("focus_area", "general"),
                    evidence=weakness,
                    turn_number=turn_number,
                    score=overall_score,
                    timestamp=datetime.utcnow(),
                    metadata={"question_type": turn_data.get("question_type", "")}
                )
                self.insights.append(insight)
                self.detected_patterns["weaknesses"].append(weakness)
        
        # Detect red flags
        red_flag_phrases = [
            "never worked with", "don't have experience", "not familiar",
            "can't remember", "don't know", "no idea", "never done"
        ]
        response_lower = response.lower()
        for phrase in red_flag_phrases:
            if phrase in response_lower:
                insight = ConversationInsight(
                    type=InsightType.RED_FLAG,
                    area=turn_data.get("focus_area", "general"),
                    evidence=f"Candidate said: '{phrase}'",
                    turn_number=turn_number,
                    score=overall_score,
                    timestamp=datetime.utcnow(),
                    metadata={"phrase": phrase}
                )
                self.insights.append(insight)
                self.detected_patterns["red_flags"].append(phrase)
        
        # Detect CV contradictions
        contradiction = self._detect_cv_contradiction(turn_data)
        if contradiction:
            insight = ConversationInsight(
                type=InsightType.CONTRADICTION,
                area=turn_data.get("focus_area", "general"),
                evidence=contradiction,
                turn_number=turn_number,
                score=overall_score,
                timestamp=datetime.utcnow()
            )
            self.insights.append(insight)
            self.detected_patterns["contradictions"].append(contradiction)
        
        # Assess technical depth
        criteria_scores = evaluation.get("criteria_scores", {})
        tech_score = criteria_scores.get("technical_knowledge", 
                                        criteria_scores.get("depth", 5.0))
        
        if tech_score > 0:  # Only if technical question
            depth_level = "high" if tech_score > 7.5 else "medium" if tech_score > 5.0 else "low"
            insight = ConversationInsight(
                type=InsightType.TECHNICAL_DEPTH,
                area=turn_data.get("focus_area", "general"),
                evidence=f"Technical depth: {depth_level}",
                turn_number=turn_number,
                score=tech_score,
                timestamp=datetime.utcnow(),
                metadata={"depth_level": depth_level}
            )
            self.insights.append(insight)
    
    def _detect_cv_contradiction(self, turn_data: Dict[str, Any]) -> Optional[str]:
        response = turn_data.get("response", "").lower()
        
        # Check claimed skills vs CV skills
        cv_skills = set(
            skill.lower() 
            for skill in self.cv_analysis.get("skills", {}).get("technical", [])
        )
        
        # Common skill-related phrases
        claim_phrases = [
            "i have experience with", "i've worked with", "i know",
            "i'm familiar with", "i've used", "i can work with"
        ]
        
        for phrase in claim_phrases:
            if phrase in response:
                # Extract what comes after the phrase
                start_idx = response.find(phrase) + len(phrase)
                claimed_text = response[start_idx:start_idx + 100]
                
                # Check if claimed skill is in CV
                # This is a simple heuristic - could be enhanced with NLP
                for cv_skill in cv_skills:
                    if cv_skill in claimed_text:
                        return None  # Matches CV
                
                # If we get here, might be a new claim not in CV
                return f"Claimed experience not found in CV: {claimed_text[:50]}"
        
        return None
    
    def get_relevant_context(self, next_focus_area: str, max_turns: int = 5) -> Dict[str, Any]:
        # Get recent turns
        recent_turns = self.full_history[-max_turns:] if self.full_history else []
        
        # Get insights related to next focus area
        relevant_insights = [
            insight for insight in self.insights
            if next_focus_area.lower() in insight.area.lower()
        ][-3:]  # Last 3 relevant insights
        
        # Get uncovered required topics
        uncovered_topics = list(self.required_topics - self.covered_topics)
        
        return {
            "recent_turns": recent_turns,
            "relevant_insights": [i.to_dict() for i in relevant_insights],
            "performance_summary": self.performance.to_dict(),
            "detected_patterns": self.detected_patterns,
            "uncovered_topics": uncovered_topics[:5],  # Top 5 uncovered
            "topic_coverage_percentage": self._calculate_coverage_percentage()
        }
    
    def _calculate_coverage_percentage(self) -> float:
        if not self.required_topics:
            return 100.0
        
        covered_count = len(self.covered_topics & self.required_topics)
        return (covered_count / len(self.required_topics)) * 100
    
    def get_performance_summary(self) -> str:
        perf = self.performance
        
        summary_parts = [
            f"Average Score: {perf.average_score:.1f}/10",
            f"Trend: {perf.score_trend}",
            f"Technical Depth: {perf.technical_depth_avg:.1f}/10",
            f"Communication: {perf.communication_clarity_avg:.1f}/10",
            f"Confidence: {perf.confidence_level}"
        ]
        
        # Add pattern summary
        if self.detected_patterns["strengths"]:
            summary_parts.append(
                f"Key Strengths: {', '.join(self.detected_patterns['strengths'][:3])}"
            )
        
        if self.detected_patterns["weaknesses"]:
            summary_parts.append(
                f"Areas for Improvement: {', '.join(self.detected_patterns['weaknesses'][:3])}"
            )
        
        if self.detected_patterns["red_flags"]:
            summary_parts.append(
                f"⚠️ Red Flags: {len(self.detected_patterns['red_flags'])} detected"
            )
        
        return "\n".join(summary_parts)
    
    def should_probe_deeper(self, last_turn: Dict[str, Any]) -> Tuple[bool, str]:
        evaluation = last_turn.get("evaluation", {})
        response = last_turn.get("response", "")
        overall_score = evaluation.get("overall_score", 0.0)
        
        # Check for vague answer
        word_count = len(response.split())
        if word_count < 30:
            return True, "Response too brief - needs elaboration"
        
        # Check for low technical depth
        criteria_scores = evaluation.get("criteria_scores", {})
        tech_score = criteria_scores.get("technical_knowledge", 
                                        criteria_scores.get("depth", 10))
        if tech_score < 6.0 and tech_score > 0:
            return True, "Technical depth insufficient - probe for details"
        
        # Check for missing specifics
        specific_indicators = ["example", "specifically", "instance", "case", "project"]
        if not any(indicator in response.lower() for indicator in specific_indicators):
            if overall_score < 7.0:
                return True, "Lacks specific examples - request concrete instance"
        
        # Check for red flags
        if self.detected_patterns["red_flags"] and \
           self.detected_patterns["red_flags"][-1] in response.lower():
            return True, "Red flag detected - clarify experience level"
        
        # Check for contradictions
        if self.detected_patterns["contradictions"]:
            last_contradiction = self.detected_patterns["contradictions"][-1]
            if last_contradiction:
                return True, f"Potential contradiction - {last_contradiction}"
        
        return False, ""
    
    def get_next_focus_recommendation(self) -> Dict[str, Any]:
        # Prioritize uncovered required topics
        uncovered = list(self.required_topics - self.covered_topics)
        
        # Identify weak areas that need more probing
        weak_areas = [
            insight.area for insight in self.insights
            if insight.type == InsightType.WEAKNESS
        ]
        
        # Identify strong areas for validation
        strong_areas = [
            insight.area for insight in self.insights
            if insight.type == InsightType.STRENGTH
        ]
        
        return {
            "priority_topics": uncovered[:3],
            "weak_areas_to_probe": list(set(weak_areas))[:2],
            "strong_areas_to_validate": list(set(strong_areas))[:2],
            "recommendation": self._generate_focus_recommendation(
                uncovered, weak_areas, strong_areas
            )
        }
    
    def _generate_focus_recommendation(self, uncovered: List[str], weak_areas: List[str], strong_areas: List[str]) -> str:
        if uncovered:
            return f"Focus on uncovered required topics: {', '.join(uncovered[:2])}"
        elif weak_areas:
            return f"Probe deeper into weak areas: {', '.join(set(weak_areas)[:2])}"
        elif strong_areas:
            return f"Validate strengths with harder scenarios: {', '.join(set(strong_areas)[:2])}"
        else:
            return "Continue with balanced technical and behavioral questions"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "full_history": self.full_history,
            "insights": [i.to_dict() for i in self.insights],
            "performance": self.performance.to_dict(),
            "covered_topics": list(self.covered_topics),
            "detected_patterns": self.detected_patterns,
            "topic_coverage_percentage": self._calculate_coverage_percentage()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], cv_analysis: Dict[str, Any], jd_analysis: Dict[str, Any]) -> "ConversationMemory":
        memory = cls(cv_analysis, jd_analysis)
        memory.full_history = data.get("full_history", [])
        memory.covered_topics = set(data.get("covered_topics", []))
        memory.detected_patterns = data.get("detected_patterns", {
            "strengths": [],
            "weaknesses": [],
            "red_flags": [],
            "contradictions": []
        })
        
        # Restore performance metrics
        perf_data = data.get("performance", {})
        memory.performance.average_score = perf_data.get("average_score", 0.0)
        memory.performance.score_trend = perf_data.get("score_trend", "stable")
        memory.performance.recent_scores = perf_data.get("recent_scores", [])
        
        return memory
