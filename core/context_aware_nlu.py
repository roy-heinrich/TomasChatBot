"""
Context-Aware NLU Engine
Enhanced Natural Language Understanding that dynamically determines when to use database context
"""

import logging
import re
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ContextConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"
    NONE = "none"

@dataclass
class ContextAnalysis:
    should_use_context: bool
    confidence_level: ContextConfidence
    reasoning: str
    suggested_response_style: str
    fallback_suggestions: List[str]

class ContextAwareNLU:
    def __init__(self):
        # Much simpler and more general patterns
        self.specificity_patterns = {
            "high": [
                # Question words that indicate specific queries
                r"who is\s+", r"who is the", r"who is the school head", r"what is\s+", r"what is the", r"what are\s+", r"what are the",
                r"where is\s+", r"where is the", r"where are\s+", r"where are the",
                r"when is\s+", r"when is the", r"when are\s+", r"when are the",
                r"how many\s+", r"how much\s+", r"how does\s+", r"how do\s+",
                r"sino ang", r"ano ang", r"saan ang", r"kailan ang",
                # Grade-specific queries
                r"grade\s+\d+", r"grade\s+\w+",
                # Specific roles/positions
                r"teacher", r"adviser", r"principal", r"head teacher", r"school head", r"guidance counselor",
                r"guro", r"faculty", r"staff",
                # Activities and events
                r"activities", r"events", r"programs", r"drill", r"celebration",
                r"aktibidad", r"programa", r"pagdiriwang"
            ],
            "medium": [
                # General school terms
                r"school", r"student", r"class", r"schedule", r"uniform",
                r"paaralan", r"estudyante", r"klase", r"iskuwela"
            ],
            "low": [
                # Vague terms
                r"help", r"information", r"tell me", r"explain",
                r"tulong", r"impormasyon", r"ano", r"paano"
            ]
        }
        
    def analyze_context_usage(self, query: str, database_results: List[Dict], 
                            intent: str, entities: List[Dict]) -> ContextAnalysis:
        if not database_results:
            return ContextAnalysis(
                should_use_context=False,
                confidence_level=ContextConfidence.NONE,
                reasoning="No database results found",
                suggested_response_style="apologetic_with_alternatives",
                fallback_suggestions=["Ask about specific staff", "Inquire about locations"]
            )
        
        specificity_score = self._calculate_specificity_score(query)
        match_quality = self._analyze_match_quality(query, database_results)
        
        # Much more liberal logic - if we have ANY decent database results, use them!
        # 🎯 FIX: Special handling for grade-related questions
        query_lower = query.lower()
        is_grade_question = 'grade' in query_lower
        has_grade_info = any('grade' in str(result.get('keywords', '')).lower() or 'grade' in str(result.get('response', '')).lower() for result in database_results)
        
        if is_grade_question and has_grade_info:
            # For grade questions, always use database context if we have grade information
            return ContextAnalysis(
                should_use_context=True,
                confidence_level=ContextConfidence.HIGH,
                reasoning="Grade question with grade information in database",
                suggested_response_style="confident_with_details",
                fallback_suggestions=[]
            )
        
        # Context analysis completed
        
        # 🎯 ULTRA-PERMISSIVE APPROACH: If we have ANY database results, use them
        # Let the AI determine what's relevant and what's not
        # Using database context for response generation
        return ContextAnalysis(
            should_use_context=True,
            confidence_level=ContextConfidence.HIGH,
            reasoning=f"Found {len(database_results)} database results - let AI determine relevance",
            suggested_response_style="confident_with_details",
            fallback_suggestions=[]
        )
    
    def _calculate_specificity_score(self, query: str) -> float:
        query_lower = query.lower()
        score = 0.0
        
        for pattern in self.specificity_patterns["high"]:
            if re.search(pattern, query_lower):
                score += 0.4
        
        for pattern in self.specificity_patterns["medium"]:
            if re.search(pattern, query_lower):
                score += 0.2
        
        for pattern in self.specificity_patterns["low"]:
            if re.search(pattern, query_lower):
                score += 0.1
        
        return min(score, 1.0)
    
    def _analyze_match_quality(self, query: str, database_results: List[Dict]) -> Dict[str, Any]:
        if not database_results:
            return {"score": 0.0}
        
        best_result = database_results[0]
        keywords = best_result.get('keywords', '').lower()
        response = best_result.get('response', '').lower()
        query_lower = query.lower()
        
        # 🎯 SIMPLIFIED AND INTELLIGENT MATCH QUALITY
        score = 0.0
        
        # 1. Basic keyword matching
        query_words = [word for word in query_lower.split() if len(word) > 2]
        if any(word in keywords for word in query_words):
            score += 0.3
            # Keyword match found
        
        # 2. Response content relevance - if response has useful content, it's relevant
        if response and len(response) > 10:  # Non-empty, substantial response
            score += 0.4
            # Substantial response found
        
        # 3. Semantic understanding - broader matching
        # If query is about school topics and we have school-related results, use them
        school_terms = ['school', 'teacher', 'student', 'grade', 'class', 'head', 'principal', 'adviser', 'faculty', 'staff']
        if any(term in query_lower for term in school_terms):
            if any(term in keywords or term in response for term in school_terms):
                score += 0.3
                # School-related semantic match found
        
        # 4. Question word matching - if it's a question and we have answers, use them
        question_words = ['who', 'what', 'where', 'when', 'how', 'why', 'sino', 'ano', 'saan', 'kailan', 'paano', 'bakit']
        if any(word in query_lower for word in question_words):
            if response and len(response) > 5:  # We have an answer
                score += 0.2
                logger.info(f"🔍 Question-answer match found")
        
        return {
            "score": min(score, 1.0),
            "best_match": best_result,
            "relevance": "high" if score > 0.5 else "medium" if score > 0.2 else "low"
        }
    
    def _calculate_text_overlap(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0