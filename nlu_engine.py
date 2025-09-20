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
    FACILITIES_INQUIRY = "facilities_inquiry"  # New: cafeteria, library, gym, etc.
    FINANCIAL_INQUIRY = "financial_inquiry"  # New: tuition, fees, payments
    GENERAL_INFO = "general_info"  # New: school overview, mission, vision
    CONFIRMATION = "confirmation"  # New: yes/no responses
    LOCATION_INQUIRY = "location_inquiry"  # New: directions, address, campus map
    HELP_REQUEST = "help_request"  # New: general help, assistance
    APPRECIATION = "appreciation"  # New: thank you, thanks
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
        """Enhanced rule-based classification with better multilingual support"""
        user_lower = user_input.lower().strip()
        
        # PHASE 1: Exact phrase matching (highest priority)
        # This catches complex multilingual phrases before word-by-word analysis
        exact_phrases = {
            # Tagalog location phrases
            "saan ang lokasyon ng paaralan": (Intent.LOCATION_INQUIRY, 0.9),
            "saan ang paaralan": (Intent.LOCATION_INQUIRY, 0.9),
            "ano ang contact number ninyo": (Intent.CONTACT_INFO, 0.9),
            "sabihin mo sa akin ang tungkol sa school programs": (Intent.SCHOOL_INFO, 0.9),
            "sabihin sa akin tungkol sa": (Intent.GENERAL_INFO, 0.8),
            
            # Aklanon location phrases  
            "diin ang lokasyon sang paaralan": (Intent.LOCATION_INQUIRY, 0.9),
            "diin ang paaralan": (Intent.LOCATION_INQUIRY, 0.9),
            "diin nga lokasyon": (Intent.LOCATION_INQUIRY, 0.9),
            "ano nga contact number": (Intent.CONTACT_INFO, 0.9),
        }
        
        for phrase, (intent, confidence) in exact_phrases.items():
            if phrase in user_lower:
                logger.info(f"🎯 Exact phrase match: '{phrase}' → {intent.value}")
                return NLUResult(intent, confidence, [])
        
        # PHASE 2: Pattern-based matching with context awareness
        
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
        
        # Priority 9: School information - expanded patterns but lower priority than general_info
        school_words = [
            "curriculum", "program", "subjects", "classes", "school hours",
            "looking for", "we need information", "help me understand",
            "available programs", "what programs", "what classes", "school offers",
            # School name and identification queries
            "school called", "school name", "name of school", "what is your school",
            "whats your school", "what's your school", "school's name", "name of your school",
            "what is the school", "what school", "which school"
        ]
        if any(word in user_lower for word in school_words):
            return NLUResult(Intent.SCHOOL_INFO, 0.8, [])
        
        # Priority 10.5: Financial inquiries (moved up before facilities for "scholarship available")
        financial_patterns = [
            "tuition", "fee", "fees", "payment", "cost", "price", "bayad", 
            "magkano", "how much", "pricing", "scholarship", "financial aid",
            "installment", "bayarin", "singil", "scholarship available"
        ]
        if any(pattern in user_lower for pattern in financial_patterns):
            return NLUResult(Intent.FINANCIAL_INQUIRY, 0.8, [])
        
        # Priority 10: Facilities inquiries
        facilities_patterns = [
            "cafeteria", "canteen", "library", "gym", "gymnasium", "playground", 
            "computer lab", "science lab", "clinic", "office", "classroom",
            "facilities", "amenities", "available", "have you got",
            "saan ang", "nasaan ang", "may"
        ]
        if any(pattern in user_lower for pattern in facilities_patterns):
            return NLUResult(Intent.FACILITIES_INQUIRY, 0.7, [])
        
        # Priority 11: General Info inquiries - Enhanced for multilingual
        general_info_patterns = [
            "about the school", "school overview", "mission", "vision", 
            "history", "background", "tell me about", "describe",
            "ano ang", "tungkol sa", "paano ang", "school description",
            # Enhanced Tagalog patterns
            "sabihin mo sa akin", "sabihin sa akin", "tungkol sa school",
            "kwento mo", "ikwento mo", "about sa school", "tungkol sa paaralan",
            "ano about", "ano tungkol", "tell me tungkol sa",
            # Enhanced Aklanon patterns  
            "storya mo", "istorya mo", "tungkol sa eskwelahan",
            "ano parte sa", "sabihin parte sa", "kwento nga"
        ]
        if any(pattern in user_lower for pattern in general_info_patterns):
            return NLUResult(Intent.GENERAL_INFO, 0.8, [])
        
        # Priority 13: Location inquiries - Enhanced for multilingual
        location_patterns = [
            "where", "direction", "directions", "address", "location", "map",
            "how to get", "how do i get", "saan", "paano pumunta", "nasaan",
            "address ninyo", "located", "find you", "school located",
            # Enhanced Tagalog patterns
            "saan ang lokasyon", "saan ang paaralan", "lokasyon ng", "address ng",
            "nasaan ang school", "saan makikita", "paano makarating",
            # Enhanced Aklanon patterns  
            "diin ang lokasyon", "diin ang paaralan", "diin nga", "asa ang",
            "lokasyon sang", "diin makita", "paano maka-abot"
        ]
        if any(pattern in user_lower for pattern in location_patterns):
            return NLUResult(Intent.LOCATION_INQUIRY, 0.8, [])
        
        # Priority 14: Help requests
        help_patterns = [
            "help", "assist", "assistance", "support", "tulong", "guide",
            "help me", "can you help", "i need help", "tulungan mo ako",
            "guide me", "what should i do", "ano gagawin ko"
        ]
        if any(pattern in user_lower for pattern in help_patterns):
            return NLUResult(Intent.HELP_REQUEST, 0.7, [])
        
        # Priority 15: Appreciation/Thanks
        appreciation_patterns = [
            "thank you", "thanks", "salamat", "thank u", "thx", "maraming salamat",
            "appreciate", "grateful", "nice", "good", "great", "excellent"
        ]
        if any(pattern in user_lower for pattern in appreciation_patterns):
            return NLUResult(Intent.APPRECIATION, 0.7, [])
        
        # Priority 16: Confirmation responses - Enhanced for multilingual but more specific
        confirmation_patterns = [
            "yes", "yeah", "yep", "yup", "correct", "right", "exactly", "oo", 
            "tama", "yes please", "that's right", "ganun nga", "ok", "okay",
            # Enhanced Tagalog patterns - but avoid "diin" which means "where" in Aklanon
            "sakto", "tumpak", "oo nga", "ganon nga", "korek", "sige",
            # Enhanced Aklanon patterns - be careful not to include location words
            "huo", "sakto man", "tama man", "oo man"
        ]
        # Special handling: avoid classifying location words or questions as confirmation
        if any(pattern in user_lower for pattern in confirmation_patterns):
            # But NOT if it contains question indicators
            question_indicators = ["what", "whats", "what's", "called", "name", "school", "where", "diin", "lokasyon", "paaralan", "eskwelahan", "sang"]
            if not any(exc in user_lower for exc in question_indicators):
                return NLUResult(Intent.CONFIRMATION, 0.7, [])
        
        # Priority 17: Contact information - Enhanced for multilingual
        contact_patterns = [
            "contact", "phone", "number", "address", "email", "telephone",
            "contact number", "phone number", "contact info", "contact information",
            # Enhanced Tagalog patterns
            "numero", "contact number ninyo", "phone number ninyo", "numero ninyo",
            "ano ang contact", "ano ang numero", "contact info ninyo",
            # Enhanced Aklanon patterns
            "numero ninyo", "contact nga numero", "phone nga numero",
            "ano nga contact", "ano nga numero"
        ]
        if any(pattern in user_lower for pattern in contact_patterns):
            return NLUResult(Intent.CONTACT_INFO, 0.8, [])
        
        # Priority 18: Goodbyes
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
        - name_query: User asks about their own name ("what is my name", "sino ang pangalan ko")
        - child_introduction: User introduces their child
        - enrollment_inquiry: Questions about school enrollment/admission
        - staff_inquiry: Questions about teachers or staff
        - school_info: General school information requests
        - schedule_inquiry: Questions about school hours or schedules
        - facilities_inquiry: Questions about school facilities (cafeteria, library, gym, etc.)
        - financial_inquiry: Questions about tuition, fees, payments, costs
        - general_info: Questions about school overview, mission, vision, history
        - location_inquiry: Questions about school address, directions, location
        - help_request: General requests for help or assistance
        - appreciation: Thank you messages, gratitude expressions
        - confirmation: Yes/no responses, agreement ("yes", "oo", "correct")
        - contact_info: Requests for contact information
        - denial: User denying or clarifying they weren't asking about something
        - clarification: User clarifying what they meant
        - goodbye: User saying goodbye or thanks
        - unknown: Cannot determine intent clearly
        """
        
        prompt = f"""
        Analyze this user message and classify the intent. Also extract any important entities.
        
        User message: "{user_input}"
        
        {intents_description}
        
        Context: {context or "No previous context"}
        
        Extract entities such as:
        - person_name: The user's own name (when they introduce themselves)
        - child_name: Names of children/students mentioned
        - relationship: Family relationships (son, daughter, child)
        - age: Ages mentioned
        - grade: School grades mentioned
        - location: Places or locations mentioned
        - staff_name: Names of teachers or staff mentioned
        
        Return only a JSON object with:
        {{"intent": "intent_name", "confidence": 0.0-1.0, "entities": [
            {{"type": "entity_type", "value": "extracted_value", "confidence": 0.0-1.0}}
        ]}}
        
        Examples:
        "Hi my name is John" -> {{"intent": "name_introduction", "confidence": 0.9, "entities": [{{"type": "person_name", "value": "John", "confidence": 0.9}}]}}
        "I got a daughter named Sarah" -> {{"intent": "child_introduction", "confidence": 0.9, "entities": [{{"type": "child_name", "value": "Sarah", "confidence": 0.9}}, {{"type": "relationship", "value": "daughter", "confidence": 0.9}}]}}
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
        import httpx
        import os
        
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise Exception("GROQ_API_KEY not found")
            
        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "You are an expert at analyzing user messages for intent and entity extraction. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 200
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.groq.com/openai/v1/chat/completions", 
                                       headers=headers, json=data, timeout=10.0)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()