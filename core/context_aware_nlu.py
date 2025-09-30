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
        self.specificity_patterns = {
            "high": [
                r"who is\s+", r"who is the", r"what is\s+", r"what is the",
                r"grade\s+\d+\s+teacher", r"grade\s+\d+\s+adviser", 
                r"principal", r"head teacher", r"guidance counselor",
                r"where is\s+", r"where is the", r"saan ang"
            ],
            "medium": [
                r"teacher", r"staff", r"where", r"when", r"how many",
                r"guro", r"faculty", r"adviser"
            ],
            "low": [
                r"help", r"information", r"what", r"tell me", r"explain",
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
        
        if specificity_score > 0.4 and match_quality["score"] > 0.5:
            return ContextAnalysis(
                should_use_context=True,
                confidence_level=ContextConfidence.HIGH,
                reasoning=f"High specificity ({specificity_score:.2f}) and good match ({match_quality['score']:.2f})",
                suggested_response_style="confident_with_details",
                fallback_suggestions=[]
            )
        elif specificity_score > 0.2 and match_quality["score"] > 0.3:
            return ContextAnalysis(
                should_use_context=True,
                confidence_level=ContextConfidence.MEDIUM,
                reasoning=f"Medium specificity ({specificity_score:.2f}) and moderate match ({match_quality['score']:.2f})",
                suggested_response_style="cautious_with_qualifiers",
                fallback_suggestions=["Ask for more specific information"]
            )
        else:
            return ContextAnalysis(
                should_use_context=False,
                confidence_level=ContextConfidence.LOW,
                reasoning=f"Low specificity or poor match",
                suggested_response_style="apologetic_with_alternatives",
                fallback_suggestions=["Ask about specific topics"]
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
        
        # Enhanced match quality calculation
        score = 0.0
        
        # 1. Direct keyword matching (high weight)
        if any(word in keywords for word in query_lower.split() if len(word) > 2):
            score += 0.4
        
        # 2. Semantic matching for common terms
        semantic_matches = {
            'teacher': ['adviser', 'guro', 'faculty', 'staff'],
            'grade': ['grade'],
            'who': ['name', 'person'],
            'where': ['location', 'place'],
            'what': ['information', 'details']
        }
        
        for query_word in query_lower.split():
            if query_word in semantic_matches:
                for semantic_term in semantic_matches[query_word]:
                    if semantic_term in keywords or semantic_term in response:
                        score += 0.2
                        break
        
        # 3. Grade number matching (very specific)
        import re
        grade_match = re.search(r'grade\s+(\d+)', query_lower)
        if grade_match:
            grade_num = grade_match.group(1)
            if grade_num in keywords or f'grade {grade_num}' in keywords:
                score += 0.3
        
        # 4. Response relevance (if response contains useful info)
        if response and len(response) > 5:  # Non-empty response
            score += 0.1
        
        return {
            "score": min(score, 1.0),
            "best_match": best_result,
            "relevance": "high" if score > 0.6 else "medium" if score > 0.3 else "low"
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