import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class Intent(Enum):
    """Defined intents for the school chatbot"""
    GREETING_WITH_NAME = "greeting_with_name"
    GREETING_SIMPLE = "greeting_simple" 
    ENROLLMENT_INQUIRY = "enrollment_inquiry"
    SCHOOL_INFO = "school_info"
    STAFF_INQUIRY = "staff_inquiry"
    SCHEDULE_INQUIRY = "schedule_inquiry"
    CONTACT_INFO = "contact_info"
    NAME_INTRODUCTION = "name_introduction"
    CHILD_INTRODUCTION = "child_introduction"
    NAME_QUERY = "name_query"  # New: "what is my name" queries
    CLARIFICATION = "clarification"
    DENIAL = "denial"
    GOODBYE = "goodbye"
    UNKNOWN = "unknown"

@dataclass
class Entity:
    """Represents an extracted entity from user input"""
    type: str  # e.g., "person_name", "child_name", "age"
    value: str
    confidence: float
    start: int = 0
    end: int = 0

@dataclass
class NLUResult:
    """Result of NLU analysis"""
    intent: Intent
    confidence: float
    entities: List[Entity]

class NLUEngine:
    """
    Natural Language Understanding engine for the school chatbot.
    Uses AI-powered intent classification with rule-based fallback.
    """
    
    def __init__(self):
        # Optional: Initialize AI clients (OpenAI/Groq) for advanced classification
        self.openai_client = None
        self.groq_client = None
        
    async def analyze_intent(self, user_input: str, context: Dict = None) -> NLUResult:
        """
        Analyze user input to determine intent and extract entities
        """
        # Start with rule-based classification (fast and reliable)
        rule_result = self._rule_based_classification(user_input)
        
        # If rule-based classification is confident, use it
        if rule_result.confidence >= 0.7:
            logger.info(f"🎯 Rule-based classification: {rule_result.intent.value} (confidence: {rule_result.confidence:.2f})")
            return rule_result
        
        # For low-confidence cases, could fall back to AI classification
        # For now, return the rule-based result
        logger.info(f"🔍 Using rule-based result: {rule_result.intent.value} (confidence: {rule_result.confidence:.2f})")
        return rule_result
    
    def _rule_based_classification(self, user_input: str) -> NLUResult:
        """Fallback rule-based classification"""
        user_lower = user_input.lower().strip()
        
        # Priority 1: Denials and clarifications (check first to avoid false positives)
        if any(phrase in user_lower for phrase in ["not asking", "i am not", "i'm not", "hindi ako", "wala ako"]):
            return NLUResult(Intent.DENIAL, 0.9, [])
        
        if any(phrase in user_lower for phrase in ["i meant", "what i mean", "clarify", "correction"]):
            return NLUResult(Intent.CLARIFICATION, 0.8, [])
        
        # Priority 2: Greetings with names
        if any(greet in user_lower for greet in ["hi", "hello", "hey", "kamusta", "kumusta"]):
            if "my name is" in user_lower or "i am" in user_lower or "i'm" in user_lower:
                return NLUResult(Intent.GREETING_WITH_NAME, 0.9, [])
            else:
                return NLUResult(Intent.GREETING_SIMPLE, 0.8, [])
        
        # Priority 3: Time-based greetings
        if any(greet in user_lower for greet in ["good morning", "good afternoon", "good evening", "magandang umaga", "magandang hapon"]):
            return NLUResult(Intent.GREETING_SIMPLE, 0.9, [])
        
        # Priority 4: Name queries - asking about their own name
        name_query_patterns = [
            "what is my name", "whats my name", "my name is", "tell me my name",
            "do you remember my name", "can you remember my name", 
            "sino ang pangalan ko", "ano ang pangalan ko", "pangalan ko",
            "sino ako", "who am i"
        ]
        if any(pattern in user_lower for pattern in name_query_patterns):
            # But exclude name introductions ("my name is John")
            if not any(intro in user_lower for intro in ["my name is", "ako si"]):
                return NLUResult(Intent.NAME_QUERY, 0.9, [])
        
        # Priority 5: Name introductions (without greeting)
        name_intro_patterns = [
            "my name is", "i am", "i'm", "im ", "ako si", "ako ay"
        ]
        for pattern in name_intro_patterns:
            if pattern in user_lower and not any(greet in user_lower for greet in ["hi", "hello", "hey"]):
                return NLUResult(Intent.NAME_INTRODUCTION, 0.8, [])
        
        # Priority 5: Enrollment (check before child introduction to avoid conflicts)
        if any(word in user_lower for word in ["enroll", "enrollment", "admission", "register", "pag-enroll"]):
            return NLUResult(Intent.ENROLLMENT_INQUIRY, 0.8, [])
        
        # Priority 6: Child introductions - simplified and more inclusive
        child_indicators = ["my son", "my daughter", "my child", "anak ko", "ang anak ko", "i have a son", "i have a daughter", "i have a child"]
        if any(indicator in user_lower for indicator in child_indicators):
            return NLUResult(Intent.CHILD_INTRODUCTION, 0.8, [])
        
        # Priority 7: Schedule inquiries
        schedule_words = ["time", "schedule", "hours", "what time", "when", "open", "close", "start", "end", "oras"]
        if any(word in user_lower for word in schedule_words):
            return NLUResult(Intent.SCHEDULE_INQUIRY, 0.7, [])
        
        # Priority 8: Staff inquiries
        staff_words = ["teacher", "teachers", "staff", "principal", "head teacher", "guro", "maestro", "faculty"]
        if any(word in user_lower for word in staff_words):
            return NLUResult(Intent.STAFF_INQUIRY, 0.7, [])
        
        # Priority 9: School information
        school_words = ["curriculum", "program", "subjects", "classes", "facilities", "school hours"]
        if any(word in user_lower for word in school_words):
            return NLUResult(Intent.SCHOOL_INFO, 0.7, [])
        
        # Priority 10: Contact information
        contact_words = ["contact", "phone", "number", "address", "location", "email"]
        if any(word in user_lower for word in contact_words):
            return NLUResult(Intent.CONTACT_INFO, 0.7, [])
        
        # Priority 11: Goodbyes
        if any(word in user_lower for word in ["bye", "goodbye", "thanks", "thank you", "salamat", "tapos na"]):
            return NLUResult(Intent.GOODBYE, 0.7, [])
        
        # Default: unknown
        return NLUResult(Intent.UNKNOWN, 0.3, [])
    
    def _create_intent_prompt(self, user_input: str, context: Dict = None) -> str:
        """Create a prompt for AI intent classification"""
        intents_description = """
        Available intents:
        - greeting_with_name: User greets and introduces their name
        - greeting_simple: Simple greeting without name
        - name_introduction: User introduces their name without greeting
        - child_introduction: User introduces their child
        - enrollment_inquiry: Questions about school enrollment/admission
        - staff_inquiry: Questions about teachers or staff
        - school_info: General school information requests
        - schedule_inquiry: Questions about school hours or schedules
        - contact_info: Requests for contact information
        - denial: User denying or clarifying they weren't asking about something
        - clarification: User clarifying what they meant
        - goodbye: User saying goodbye or thanks
        - unknown: Cannot determine intent clearly
        """
        
        prompt = f"""
        Analyze this user message and classify the intent.
        
        User message: "{user_input}"
        
        {intents_description}
        
        Context: {context or "No previous context"}
        
        Return only a JSON object with:
        {{"intent": "intent_name", "confidence": 0.0-1.0, "entities": []}}
        """
        
        return prompt
    
    async def _ai_classify_intent(self, user_input: str, context: Dict = None) -> NLUResult:
        """Use AI (OpenAI/Groq) for intent classification"""
        
        prompt = self._create_intent_prompt(user_input, context)
        
        try:
            # Try OpenAI first, then Groq as fallback
            if self.openai_client:
                response = await self._call_openai(prompt)
            elif self.groq_client:
                response = await self._call_groq(prompt)
            else:
                # No AI client available, fall back to rules
                return self._rule_based_classification(user_input)
            
            # Parse AI response
            result_data = json.loads(response)
            intent = Intent(result_data["intent"])
            confidence = float(result_data["confidence"])
            entities = [Entity(**e) for e in result_data.get("entities", [])]
            
            return NLUResult(intent, confidence, entities)
            
        except Exception as e:
            logger.warning(f"AI classification failed: {e}")
            return self._rule_based_classification(user_input)
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API for intent classification"""
        # Implementation would go here
        raise NotImplementedError("OpenAI integration not yet implemented")
    
    async def _call_groq(self, prompt: str) -> str:
        """Call Groq API for intent classification"""
        # Implementation would go here
        raise NotImplementedError("Groq integration not yet implemented")