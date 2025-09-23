"""
Enhanced Accuracy System for Chatbot
====================================

This module provides advanced accuracy improvements:
- Enhanced database search with semantic matching
- Improved keyword extraction and matching
- Better response generation for specific queries
- Query intent classification for better accuracy
"""

import logging
import re
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

@dataclass
class QueryIntent:
    """Enhanced query intent classification"""
    primary_intent: str
    secondary_intents: List[str]
    confidence: float
    entities: List[Dict]
    query_type: str  # factual, procedural, personal, general
    requires_specific_info: bool
    expected_response_length: str  # short, medium, long

@dataclass
class SearchResult:
    """Enhanced search result with relevance scoring"""
    content: str
    relevance_score: float
    match_type: str  # exact, semantic, fuzzy, fallback
    source: str
    confidence: float
    keywords_matched: List[str]

class EnhancedAccuracySystem:
    """
    Enhanced accuracy system with advanced search and response generation
    """
    
    def __init__(self):
        # Query intent patterns for better classification
        self.intent_patterns = {
            "school_name": {
                "patterns": [
                    r"what is the school name",
                    r"what's the school name", 
                    r"name of the school",
                    r"school called",
                    r"what school is this"
                ],
                "response_type": "factual",
                "expected_keywords": ["tomas", "bautista", "elementary", "school"]
            },
            "location": {
                "patterns": [
                    r"where is.*school",
                    r"school location",
                    r"address of.*school",
                    r"how to get to.*school"
                ],
                "response_type": "factual",
                "expected_keywords": ["fatima", "new washington", "aklan", "location"]
            },
            "safety_procedures": {
                "patterns": [
                    r"earthquake.*drill",
                    r"fire.*drill", 
                    r"emergency.*drill",
                    r"safety.*drill",
                    r"earthquake.*procedure",
                    r"fire.*procedure",
                    r"emergency.*procedure",
                    r"safety.*procedure",
                    r"what to do.*earthquake",
                    r"what to do.*fire",
                    r"emergency.*plan",
                    r"disaster.*preparedness"
                ],
                "response_type": "safety",
                "expected_keywords": ["earthquake", "fire", "drill", "emergency", "safety", "procedure"]
            },
            "enrollment": {
                "patterns": [
                    r"how to enroll",
                    r"enrollment process",
                    r"enroll.*child",
                    r"registration"
                ],
                "response_type": "procedural",
                "expected_keywords": ["enrollment", "documents", "requirements", "process"]
            },
            "fees": {
                "patterns": [
                    r"how much.*fee",
                    r"school fee",
                    r"tuition",
                    r"cost.*school",
                    r"price.*enroll"
                ],
                "response_type": "factual",
                "expected_keywords": ["fee", "tuition", "cost", "payment"]
            },
            "schedule": {
                "patterns": [
                    r"what time.*school",
                    r"school hours",
                    r"when.*school.*start",
                    r"schedule"
                ],
                "response_type": "factual",
                "expected_keywords": ["time", "hours", "schedule", "start"]
            },
            "staff": {
                "patterns": [
                    r"who is.*principal",
                    r"head teacher",
                    r"school staff",
                    r"guidance counselor"
                ],
                "response_type": "factual",
                "expected_keywords": ["principal", "teacher", "staff", "guidance"]
            }
        }
        
        # Enhanced keyword synonyms and variations
        self.keyword_synonyms = {
            "school_name": ["tomas", "bautista", "elementary", "school", "institution"],
            "location": ["fatima", "new washington", "aklan", "address", "location", "where"],
            "enrollment": ["enroll", "register", "admission", "application", "sign up"],
            "fees": ["fee", "tuition", "cost", "payment", "price", "charge"],
            "schedule": ["time", "hours", "schedule", "start", "end", "when"],
            "staff": ["principal", "teacher", "staff", "head", "director", "guidance"]
        }
        
        # Specific response templates for common queries
        self.specific_responses = {
            "school_name": "Our school is Tomas SM. Bautista Elementary School, located in Fatima, New Washington, Aklan.",
            "location": "Tomas SM. Bautista Elementary School is located in Fatima, New Washington, Aklan. You can find us at the heart of the community.",
            "enrollment": "To enroll your child, you'll need to bring the following documents: birth certificate, report card, and 2x2 ID photos. Visit our school office for the complete enrollment process.",
            "fees": "For information about school fees and tuition, please contact our school office at the school office or visit us in person for detailed fee structure.",
            "schedule": "School hours are from 7:00 AM to 5:00 PM, Monday to Friday. Classes start at 7:30 AM and end at 4:30 PM.",
            "staff": None  # Force database search instead of hardcoded response
        }
        
        # Intents that should trigger database search instead of specific responses
        self.database_search_intents = {
            "safety_procedures"
        }
    
    async def analyze_query_intent(self, query: str) -> QueryIntent:
        """
        Enhanced query intent analysis with better classification
        """
        query_lower = query.lower().strip()
        
        # Check for specific intent patterns
        for intent_name, intent_data in self.intent_patterns.items():
            for pattern in intent_data["patterns"]:
                if re.search(pattern, query_lower):
                    # Extract entities
                    entities = self._extract_entities(query)
                    
                    # Determine query type and requirements
                    query_type = intent_data["response_type"]
                    requires_specific = intent_data["response_type"] in ["factual", "procedural"]
                    
                    # Estimate response length
                    response_length = "short" if intent_name in ["school_name", "location"] else "medium"
                    
                    return QueryIntent(
                        primary_intent=intent_name,
                        secondary_intents=[],
                        confidence=0.9,
                        entities=entities,
                        query_type=query_type,
                        requires_specific_info=requires_specific,
                        expected_response_length=response_length
                    )
        
        # Fallback: general analysis
        entities = self._extract_entities(query)
        return QueryIntent(
            primary_intent="general",
            secondary_intents=[],
            confidence=0.5,
            entities=entities,
            query_type="general",
            requires_specific_info=False,
            expected_response_length="medium"
        )
    
    def _extract_entities(self, query: str) -> List[Dict]:
        """Extract entities from query"""
        entities = []
        query_lower = query.lower()
        
        # Name extraction
        name_patterns = [
            r"i am (\w+)",
            r"my name is (\w+)",
            r"i'm (\w+)",
            r"call me (\w+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, query_lower)
            if match:
                entities.append({
                    "type": "person_name",
                    "value": match.group(1).title(),
                    "confidence": 0.9
                })
        
        # School-related entities
        if "school" in query_lower:
            entities.append({
                "type": "institution",
                "value": "school",
                "confidence": 0.8
            })
        
        return entities
    
    async def enhanced_database_search(self, query: str, intent: QueryIntent) -> List[SearchResult]:
        """
        Enhanced database search with intent-aware matching
        """
        results = []
        
        # If we have a specific response for this intent, use it (unless it's a database search intent)
        if intent.primary_intent in self.specific_responses and intent.primary_intent not in self.database_search_intents:
            results.append(SearchResult(
                content=self.specific_responses[intent.primary_intent],
                relevance_score=1.0,
                match_type="exact",
                source="specific_response",
                confidence=0.95,
                keywords_matched=[intent.primary_intent]
            ))
            return results
        
        # Enhanced keyword extraction
        enhanced_keywords = self._extract_enhanced_keywords(query, intent)
        
        # Search with enhanced keywords
        for keyword in enhanced_keywords:
            # This would integrate with the existing database search
            # For now, we'll return the enhanced keywords for integration
            results.append(SearchResult(
                content=f"Enhanced search for: {keyword}",
                relevance_score=0.8,
                match_type="semantic",
                source="enhanced_search",
                confidence=0.7,
                keywords_matched=[keyword]
            ))
        
        return results
    
    def _extract_enhanced_keywords(self, query: str, intent: QueryIntent) -> List[str]:
        """Extract enhanced keywords with synonyms and variations"""
        query_lower = query.lower()
        keywords = []
        
        # Extract base keywords
        words = re.findall(r'\b\w+\b', query_lower)
        
        # Add synonyms for each word
        for word in words:
            if len(word) > 2:  # Skip short words
                keywords.append(word)
                
                # Add synonyms
                for category, synonyms in self.keyword_synonyms.items():
                    if word in synonyms:
                        keywords.extend(synonyms)
        
        # Add intent-specific keywords
        if intent.primary_intent in self.keyword_synonyms:
            keywords.extend(self.keyword_synonyms[intent.primary_intent])
        
        # Remove duplicates and return
        return list(set(keywords))
    
    def generate_enhanced_response(self, query: str, intent: QueryIntent, search_results: List[SearchResult]) -> str:
        """
        Generate enhanced response based on intent and search results
        """
        # Use specific response if available
        if intent.primary_intent in self.specific_responses:
            base_response = self.specific_responses[intent.primary_intent]
            
            # Add personalization if name was extracted
            if intent.entities:
                for entity in intent.entities:
                    if entity["type"] == "person_name":
                        name = entity["value"]
                        base_response = f"Hello {name}! {base_response}"
                        break
            
            return base_response
        
        # Use best search result
        if search_results:
            best_result = max(search_results, key=lambda x: x.relevance_score)
            return best_result.content
        
        # Fallback response
        return self._generate_fallback_response(intent)
    
    def _generate_fallback_response(self, intent: QueryIntent) -> str:
        """Generate appropriate fallback response based on intent"""
        if intent.primary_intent == "school_name":
            return "Our school is Tomas SM. Bautista Elementary School."
        elif intent.primary_intent == "location":
            return "We are located in Fatima, New Washington, Aklan."
        elif intent.primary_intent == "enrollment":
            return "For enrollment information, please contact our school office at the school office."
        elif intent.primary_intent == "fees":
            return "For fee information, please contact our school office for detailed pricing."
        elif intent.primary_intent == "schedule":
            return "School hours are from 7:00 AM to 5:00 PM, Monday to Friday."
        elif intent.primary_intent == "staff":
            return "For staff information, please contact our school office."
        else:
            return "I'm here to help with information about our school. Please let me know what specific information you need."
    
    def calculate_accuracy_score(self, query: str, response: str, expected_intent: str) -> float:
        """
        Calculate accuracy score for a query-response pair
        """
        score = 0.0
        
        # Check if response contains expected keywords
        if expected_intent in self.specific_responses:
            expected_keywords = self.keyword_synonyms.get(expected_intent, [])
            response_lower = response.lower()
            
            for keyword in expected_keywords:
                if keyword in response_lower:
                    score += 0.2
            
            # Check for specific response content
            if expected_intent == "school_name" and "tomas" in response_lower and "bautista" in response_lower:
                score += 0.4
            elif expected_intent == "location" and "fatima" in response_lower and "aklan" in response_lower:
                score += 0.4
            elif expected_intent == "enrollment" and any(word in response_lower for word in ["documents", "enroll", "process"]):
                score += 0.4
        
        # Check response length appropriateness
        if len(response) > 20:  # Substantial response
            score += 0.2
        
        # Check for complete sentences
        if response.count('.') >= 1:
            score += 0.2
        
        return min(score, 1.0)

# Global instance
enhanced_accuracy_system = EnhancedAccuracySystem()
