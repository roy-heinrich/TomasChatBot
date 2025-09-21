import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Import the new multilingual NLP engine with robust fallbacks
MULTILINGUAL_NLP_AVAILABLE = False
multilingual_nlp = None
SemanticIntent = None
MultilingualEntity = None
try:
    # First try package-relative import (preferred in package context)
    from .multilingual_nlp import multilingual_nlp, SemanticIntent, MultilingualEntity
    MULTILINGUAL_NLP_AVAILABLE = True
except Exception:
    try:
        # Fall back to absolute import for scripts run directly
        from multilingual_nlp import multilingual_nlp, SemanticIntent, MultilingualEntity
        MULTILINGUAL_NLP_AVAILABLE = True
    except Exception as e:
        MULTILINGUAL_NLP_AVAILABLE = False
        logger.warning(f"Multilingual NLP engine not available: {e}")

class Intent(Enum):
    """Defined intents for the school chatbot"""
    # Enhanced greeting intents for better personalization
    GREETING_WITH_NAME = "greeting_with_name"
    GREETING_SIMPLE = "greeting_simple"
    GREETING_RETURNING_USER = "greeting_returning_user"  # New: returning user greeting
    GREETING_EXCITED = "greeting_excited"  # New: enthusiastic greeting
    GREETING_FORMAL = "greeting_formal"  # New: formal/polite greeting
    GREETING_CASUAL = "greeting_casual"  # New: casual greeting
    
    # Existing intents
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
    
    # Conversation Flow Intents - for better multi-turn conversations
    ENROLLMENT_DOCUMENTS = "enrollment_documents"  # Specific document requirements
    ENROLLMENT_DEADLINE = "enrollment_deadline"    # Deadline and timeline questions
    ENROLLMENT_PROCESS = "enrollment_process"      # Step-by-step process
    SCHOOL_OVERVIEW = "school_overview"            # General school information request
    GRADE_LEVELS = "grade_levels"                  # What grades/levels offered
    SCHOOL_PROGRAMS = "school_programs"            # Academic programs and curricula
    FOLLOW_UP_QUESTION = "follow_up_question"      # Follow-up to previous answer
    TOPIC_CONTINUATION = "topic_continuation"      # Continuing same topic
    CLARIFICATION_REQUEST = "clarification_request" # Asking for more details
    COMPARISON_REQUEST = "comparison_request"       # Comparing options/programs
    
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
        Analyze user input to determine intent and extract entities using advanced NLP
        """
        
        # First, try semantic classification with the new multilingual NLP engine
        if MULTILINGUAL_NLP_AVAILABLE:
            try:
                # Detect language semantically
                lang_result = await multilingual_nlp.detect_language_semantic(user_input)
                logger.info(f"🔍 Semantic language detection: {lang_result.language} (confidence: {lang_result.confidence:.2f})")
                
                # Classify intent semantically
                semantic_intent = await multilingual_nlp.classify_intent_semantic(user_input, lang_result.language)
                
                # If semantic classification is confident, use it
                if semantic_intent.confidence >= 0.5:
                    # Extract entities using multilingual NER
                    entities = await multilingual_nlp.extract_entities_multilingual(user_input, lang_result.language)
                    
                    # Convert to our format
                    nlu_entities = []
                    for entity in entities:
                        nlu_entities.append(Entity(
                            type=entity.label.lower(),
                            value=entity.normalized_form or entity.text,
                            confidence=entity.confidence,
                            start=entity.start,
                            end=entity.end
                        ))
                    
                    # Convert semantic intent to Intent enum
                    try:
                        intent_enum = Intent(semantic_intent.intent)
                    except ValueError:
                        intent_enum = Intent.UNKNOWN
                    
                    logger.info(f"🎯 Semantic classification: {intent_enum.value} (confidence: {semantic_intent.confidence:.2f}, similarity: {semantic_intent.similarity_score:.2f})")
                    logger.info(f"📝 Matched example: '{semantic_intent.matched_example}'")

                    # If semantic classifier detected a greeting-with-name or name_introduction
                    # but the multilingual NER returned no entities, try a lightweight
                    # regex extraction as a safe fallback so we can persist person_name.
                    try:
                        if intent_enum in (Intent.GREETING_WITH_NAME, Intent.NAME_INTRODUCTION) and len(nlu_entities) == 0:
                            import re
                            name_match = re.search(r"(?:my name is|i am|i'm|im|ako si|ako ay|call me|this is)\s+([A-Za-z'\-]{2,})", user_input, flags=re.IGNORECASE)
                            if name_match:
                                name_val = name_match.group(1).strip().title()
                                nlu_entities.append(Entity(type="person_name", value=name_val, confidence=0.9))
                                logger.info(f"🔎 Extracted name via regex (semantic fallback): {name_val}")
                    except Exception:
                        # Non-critical: if regex fails for any reason, continue without entities
                        pass

                    return NLUResult(intent_enum, semantic_intent.confidence, nlu_entities)
                    
            except Exception as e:
                logger.warning(f"⚠️ Semantic classification failed: {e}, falling back to rule-based")
        
        # Fallback to rule-based classification with enhanced confidence
        rule_result = self._rule_based_classification(user_input)
        
        # Boost confidence if we have semantic backup data
        if MULTILINGUAL_NLP_AVAILABLE and rule_result.confidence < 0.7:
            try:
                # Get semantic confirmation
                semantic_intent = await multilingual_nlp.classify_intent_semantic(user_input)
                if semantic_intent.intent == rule_result.intent.value and semantic_intent.confidence > 0.3:
                    # Boost confidence when both methods agree
                    boosted_confidence = min(rule_result.confidence + 0.2, 0.9)
                    logger.info(f"🔗 Semantic confirmation boosted confidence: {rule_result.confidence:.2f} → {boosted_confidence:.2f}")
                    return NLUResult(rule_result.intent, boosted_confidence, rule_result.entities)
            except Exception:
                pass
        
        logger.info(f"🔍 Using rule-based result: {rule_result.intent.value} (confidence: {rule_result.confidence:.2f})")
        return rule_result
    
    def _rule_based_classification(self, user_input: str) -> NLUResult:
        """Enhanced rule-based classification with better multilingual support and confidence scoring"""
        user_lower = user_input.lower().strip()
        
        # PHASE 1: Exact phrase matching (highest priority)
        # This catches complex multilingual phrases before word-by-word analysis
        exact_phrases = {
            # English location phrases
            "where is the school": (Intent.LOCATION_INQUIRY, 0.95),
            "where is your school": (Intent.LOCATION_INQUIRY, 0.95),
            "where is the school located": (Intent.LOCATION_INQUIRY, 0.95),
            "what is the school location": (Intent.LOCATION_INQUIRY, 0.9),
            "school location": (Intent.LOCATION_INQUIRY, 0.85),
            "where can i find the school": (Intent.LOCATION_INQUIRY, 0.9),
            "school address": (Intent.LOCATION_INQUIRY, 0.9),
            
            # Enhanced multilingual greetings
            "kumusta": (Intent.GREETING_SIMPLE, 0.9),
            "salamat": (Intent.APPRECIATION, 0.85),
            "hola": (Intent.GREETING_SIMPLE, 0.8),
            "konnichiwa": (Intent.GREETING_SIMPLE, 0.8),
            
            # Tagalog location phrases
            "saan ang lokasyon ng paaralan": (Intent.LOCATION_INQUIRY, 0.95),
            "saan ang paaralan": (Intent.LOCATION_INQUIRY, 0.9),
            "ano ang contact number ninyo": (Intent.CONTACT_INFO, 0.95),
            "sabihin mo sa akin ang tungkol sa school programs": (Intent.SCHOOL_INFO, 0.9),
            "sabihin sa akin tungkol sa": (Intent.GENERAL_INFO, 0.8),
            
            # Aklanon location phrases  
            "diin ang lokasyon sang paaralan": (Intent.LOCATION_INQUIRY, 0.95),
            "diin ang paaralan": (Intent.LOCATION_INQUIRY, 0.9),
            "diin nga lokasyon": (Intent.LOCATION_INQUIRY, 0.9),
            "ano nga contact number": (Intent.CONTACT_INFO, 0.9),
        }
        
        for phrase, (intent, confidence) in exact_phrases.items():
            if phrase in user_lower:
                logger.info(f"🎯 Exact phrase match: '{phrase}' → {intent.value}")
                return NLUResult(intent, confidence, [])
        
        # PHASE 2: Enhanced pattern-based matching with weighted confidence scoring
        confidence_score = 0.0
        detected_intent = Intent.UNKNOWN
        evidence_factors = []
        
        # Priority: Name introductions - higher priority than greetings
        # This catches "hi i am john" as a name_introduction rather than a plain greeting
        name_intro_patterns = [
            "my name is", "i am", "i'm", "im ", "ako si", "ako ay", "called"
        ]
        for pattern in name_intro_patterns:
            if pattern in user_lower:
                # Check if there's an actual name after the pattern (not just the pattern alone)
                pattern_pos = user_lower.find(pattern)
                text_after = user_lower[pattern_pos + len(pattern):].strip()
                if len(text_after) > 0 and not text_after.startswith("asking") and not text_after.startswith("not"):
                    # Try to extract the name with a regex so we can return it as an entity
                    import re
                    name_match = re.search(r"(?:my name is|i am|i'm|im|ako si|ako ay|call me|this is)\s+([A-Za-z'-]{2,})", user_lower)
                    entities = []
                    if name_match:
                        name_val = name_match.group(1).strip().title()
                        entities.append(Entity(type="person_name", value=name_val, confidence=0.9))
                        logger.info(f"🔎 Extracted name via regex: {name_val}")
                    return NLUResult(Intent.NAME_INTRODUCTION, 0.95, entities)

        # Enhanced greeting detection with confidence scoring
        greeting_indicators = self._analyze_greeting_patterns(user_lower)
        if greeting_indicators['intent'] != Intent.UNKNOWN:
            return NLUResult(greeting_indicators['intent'], greeting_indicators['confidence'], [])
        
        # Enhanced enrollment detection
        enrollment_score = self._calculate_enrollment_confidence(user_lower)
        if enrollment_score > 0.6:
            return NLUResult(Intent.ENROLLMENT_INQUIRY, enrollment_score, [])
        
        # Enhanced location detection
        location_score = self._calculate_location_confidence(user_lower)
        if location_score > 0.6:
            return NLUResult(Intent.LOCATION_INQUIRY, location_score, [])
        
        # Enhanced staff inquiry detection
        staff_score = self._calculate_staff_confidence(user_lower)
        if staff_score > 0.6:
            return NLUResult(Intent.STAFF_INQUIRY, staff_score, [])
        
        # Continue with priority-based classification for other intents
        # DO NOT return early - let it fall through to Priority rules
        
        # Priority 1: Denials and clarifications (check first to avoid false positives)
        if any(phrase in user_lower for phrase in ["not asking", "i am not", "i'm not", "hindi ako", "wala ako"]):
            return NLUResult(Intent.DENIAL, 0.9, [])
        
        if any(phrase in user_lower for phrase in ["i meant", "what i mean", "clarify", "correction"]):
            return NLUResult(Intent.CLARIFICATION, 0.8, [])
        
        # Priority 2: Enhanced greeting classification with mood/style detection
        greeting_keywords = ["hi", "hello", "hey", "kamusta", "kumusta", "maayong", "good morning", "good afternoon", "good evening", "magandang umaga", "magandang hapon", "maayong aga", "maayong hapon", "maayong gab-i", "morning", "afternoon", "evening", "greetings", "hiya", "wassup", "howdy", "sup", "yo"]
        # Priority 3: Name introductions - higher priority than greetings
        # This catches "hi i am john" as name_introduction rather than greeting_with_name
        name_intro_patterns = [
            "my name is", "i am", "i'm", "im ", "ako si", "ako ay", "called"
        ]
        for pattern in name_intro_patterns:
            if pattern in user_lower:
                # Check if there's an actual name after the pattern (not just the pattern alone)
                pattern_pos = user_lower.find(pattern)
                text_after = user_lower[pattern_pos + len(pattern):].strip()
                if len(text_after) > 0 and not text_after.startswith("asking") and not text_after.startswith("not"):
                    # Try to extract the name with a regex so we can return it as an entity
                    import re
                    name_match = re.search(r"(?:my name is|i am|i'm|im|ako si|ako ay|call me|this is)\s+([A-Za-z'-]{2,})", user_lower)
                    entities = []
                    if name_match:
                        name_val = name_match.group(1).strip().title()
                        entities.append(Entity(type="person_name", value=name_val, confidence=0.9))
                        logger.info(f"🔎 Extracted name via regex: {name_val}")
                    return NLUResult(Intent.NAME_INTRODUCTION, 0.95, entities)

        if any(greet in user_lower for greet in greeting_keywords):
            # Now only classify as greeting_with_name if it's a pure greeting without introduction intent
            # This should catch cases like "hello, my name is john" where greeting comes first
            if any(pattern in user_lower for pattern in ["my name is", "i am", "i'm", "im ", "ako si"]):
                # But if it's clearly a name introduction, it was already caught above
                # This is for cases where greeting is the primary intent
                return NLUResult(Intent.GREETING_WITH_NAME, 0.85, [])
            
            # Detect greeting style/mood for dynamic personalization
            elif any(word in user_lower for word in ["awesome", "great", "fantastic", "wonderful", "amazing", "excited", "!!!", "super", "really good"]):
                return NLUResult(Intent.GREETING_EXCITED, 0.9, [])
            elif any(word in user_lower for word in ["sir", "ma'am", "please", "good day", "greetings", "salutations", "formal"]):
                return NLUResult(Intent.GREETING_FORMAL, 0.9, [])
            elif any(word in user_lower for word in ["sup", "yo", "hiya", "wassup", "howdy", "hey there", "casual"]):
                return NLUResult(Intent.GREETING_CASUAL, 0.9, [])
            elif any(word in user_lower for word in ["back", "again", "return", "here again", "returning"]):
                return NLUResult(Intent.GREETING_RETURNING_USER, 0.9, [])
            else:
                return NLUResult(Intent.GREETING_SIMPLE, 0.8, [])
        
        # Priority 4: Name queries - asking about their own name
        name_query_patterns = [
            "what is my name", "whats my name", "tell me my name",
            "do you remember my name", "can you remember my name", 
            "sino ang pangalan ko", "ano ang pangalan ko", "pangalan ko",
            "sino ako", "who am i"
        ]
        if any(pattern in user_lower for pattern in name_query_patterns):
            # But exclude name introductions ("my name is John") which were already handled above
            if not any(intro in user_lower for intro in ["my name is", "ako si", "i am", "i'm"]):
                return NLUResult(Intent.NAME_QUERY, 0.9, [])
        
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
        staff_words = ["teacher", "teachers", "staff", "principal", "head teacher", "school head", "head", "director", "administrator", "guro", "maestro", "faculty", "guidance", "counselor"]
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
        
        # CONVERSATION FLOW INTENTS - for better multi-turn conversations
        
        # Priority 18: Enrollment-specific conversation flow
        enrollment_doc_patterns = [
            "what documents", "what papers", "documents needed", "requirements", "papers needed",
            "what do i need", "documents required", "anong documents", "anong papers",
            "ano mga requirements", "kailangan nga papers", "documents nga kailangan"
        ]
        if any(pattern in user_lower for pattern in enrollment_doc_patterns):
            return NLUResult(Intent.ENROLLMENT_DOCUMENTS, 0.85, [])
            
        enrollment_deadline_patterns = [
            "when is the deadline", "deadline", "last day", "cut off", "when to enroll",
            "deadline ng enrollment", "kailan deadline", "hanggang kailan", "last day ng",
            "cut off nga enrollment", "hasta san", "deadline sang enrollment"
        ]
        if any(pattern in user_lower for pattern in enrollment_deadline_patterns):
            return NLUResult(Intent.ENROLLMENT_DEADLINE, 0.85, [])
            
        enrollment_process_patterns = [
            "how to enroll", "enrollment process", "steps to enroll", "paano mag-enroll",
            "process ng enrollment", "hakbang sa enrollment", "paano enrollment",
            "steps nga enrollment", "paano mag-register", "process sang enrollment"
        ]
        if any(pattern in user_lower for pattern in enrollment_process_patterns):
            return NLUResult(Intent.ENROLLMENT_PROCESS, 0.85, [])
        
        # Priority 19: School information-specific conversation flow
        school_overview_patterns = [
            "tell me about your school", "about the school", "school overview", "describe your school",
            "what kind of school", "type of school", "sabihin mo tungkol sa school",
            "kwento mo ang school", "ano bang school", "klaseng school", "uri ng school"
        ]
        if any(pattern in user_lower for pattern in school_overview_patterns):
            return NLUResult(Intent.SCHOOL_OVERVIEW, 0.85, [])
            
        grade_levels_patterns = [
            "what grades", "grade levels", "what levels", "grades offered", "anong grade",
            "grade levels ninyo", "anong baitang", "mga baitang", "levels nga naa",
            "grade nga available", "anong year", "year levels"
        ]
        if any(pattern in user_lower for pattern in grade_levels_patterns):
            return NLUResult(Intent.GRADE_LEVELS, 0.85, [])
            
        school_programs_patterns = [
            "programs offered", "academic programs", "what programs", "curriculum",
            "subjects offered", "mga programa", "programa ninyo", "anong programa",
            "subjects nga naa", "curriculum ninyo", "mga subjects"
        ]
        if any(pattern in user_lower for pattern in school_programs_patterns):
            return NLUResult(Intent.SCHOOL_PROGRAMS, 0.85, [])
        
        # Priority 20: General conversation flow intents
        follow_up_patterns = [
            "and what about", "what else", "anything else", "also", "plus",
            "how about", "what about", "ano pa", "ano rin", "at ano pa",
            "amo pa", "ano pa nga", "diin pa", "unsa pa"
        ]
        if any(pattern in user_lower for pattern in follow_up_patterns):
            return NLUResult(Intent.FOLLOW_UP_QUESTION, 0.75, [])
            
        clarification_request_patterns = [
            "can you explain", "more details", "tell me more", "elaborate",
            "i need more info", "explain mo", "detalye pa", "explain nga",
            "mas detalye", "daghan pa nga info", "clarify mo"
        ]
        if any(pattern in user_lower for pattern in clarification_request_patterns):
            return NLUResult(Intent.CLARIFICATION_REQUEST, 0.8, [])
            
        topic_continuation_patterns = [
            "about that", "regarding that", "speaking of", "tungkol dyan",
            "about sa", "regarding nga", "speaking nga", "tungkol sa una"
        ]
        if any(pattern in user_lower for pattern in topic_continuation_patterns):
            return NLUResult(Intent.TOPIC_CONTINUATION, 0.75, [])
            
        comparison_patterns = [
            "compare", "difference", "better", "vs", "versus", "compared to",
            "mas maganda", "pagkakaiba", "difference sa", "compare nga"
        ]
        if any(pattern in user_lower for pattern in comparison_patterns):
            return NLUResult(Intent.COMPARISON_REQUEST, 0.8, [])
        
        # Priority 21: Goodbyes
        if any(word in user_lower for word in ["bye", "goodbye", "thanks", "thank you", "salamat", "tapos na"]):
            return NLUResult(Intent.GOODBYE, 0.7, [])
        
        # Default: unknown
        return NLUResult(Intent.UNKNOWN, 0.3, [])
    
    def _build_intent_classification_prompt(self, user_input: str, context: Dict = None) -> str:
        """Create a prompt for AI intent classification"""
        intents_description = """
        Available intents:
        - greeting_with_name: User greets and introduces their name
        - greeting_simple: Simple greeting without name
        - name_introduction: User introduces their name without greeting
        - name_query: User asks about their own name ("what is my name", "sino ang pangalan ko")
        - child_introduction: User introduces their child
        - enrollment_inquiry: General questions about school enrollment/admission
        - enrollment_documents: Specific questions about enrollment documents/requirements
        - enrollment_deadline: Questions about enrollment deadlines and timelines
        - enrollment_process: Questions about how to enroll step-by-step
        - staff_inquiry: Questions about teachers or staff
        - school_info: General school information requests
        - school_overview: Specific requests for school description/overview
        - grade_levels: Questions about what grades/levels are offered
        - school_programs: Questions about academic programs and curriculum
        - schedule_inquiry: Questions about school hours or schedules
        - facilities_inquiry: Questions about school facilities (cafeteria, library, gym, etc.)
        - financial_inquiry: Questions about tuition, fees, payments, costs
        - general_info: Questions about school overview, mission, vision, history
        - location_inquiry: Questions about school address, directions, location
        - help_request: General requests for help or assistance
        - appreciation: Thank you messages, gratitude expressions
        - confirmation: Yes/no responses, agreement ("yes", "oo", "correct")
        - contact_info: Requests for contact information
        - follow_up_question: Follow-up questions ("what else", "and what about")
        - clarification_request: Requests for more details or explanations
        - topic_continuation: Continuing previous conversation topic
        - comparison_request: Asking to compare options or programs
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
    
    def _analyze_greeting_patterns(self, user_lower: str) -> dict:
        """Enhanced greeting analysis with confidence scoring"""
        confidence = 0.0
        intent = Intent.UNKNOWN
        
        # Enhanced greeting classification with mood/style detection
        greeting_keywords = ["hi", "hello", "hey", "kamusta", "kumusta", "maayong", "good morning", 
                           "good afternoon", "good evening", "magandang umaga", "magandang hapon", 
                           "maayong aga", "maayong hapon", "maayong gab-i", "morning", "afternoon", 
                           "evening", "greetings", "hiya", "wassup", "howdy", "sup", "yo"]
        
        if any(greet in user_lower for greet in greeting_keywords):
            confidence = 0.8  # Base confidence for greeting detection
            
            # Check for name introduction first
            if any(pattern in user_lower for pattern in ["my name is", "i am", "i'm", "im ", "ako si"]):
                intent = Intent.GREETING_WITH_NAME
                confidence = 0.95
            
            # Detect greeting style/mood for dynamic personalization
            elif any(word in user_lower for word in ["awesome", "great", "fantastic", "wonderful", "amazing", "excited", "!!!", "super", "really good"]):
                intent = Intent.GREETING_EXCITED
                confidence = 0.9
            elif any(word in user_lower for word in ["sir", "ma'am", "please", "good day", "greetings", "salutations", "formal"]):
                intent = Intent.GREETING_FORMAL
                confidence = 0.9
            elif any(word in user_lower for word in ["sup", "yo", "hiya", "wassup", "howdy", "hey there", "casual"]):
                intent = Intent.GREETING_CASUAL
                confidence = 0.9
            elif any(word in user_lower for word in ["back", "again", "return", "here again", "returning"]):
                intent = Intent.GREETING_RETURNING_USER
                confidence = 0.9
            else:
                intent = Intent.GREETING_SIMPLE
                confidence = 0.8
        
        return {"intent": intent, "confidence": confidence}
    
    def _calculate_enrollment_confidence(self, user_lower: str) -> float:
        """Calculate confidence score for enrollment intent"""
        confidence = 0.0
        
        # Primary enrollment keywords (high weight)
        primary_keywords = ["enroll", "enrollment", "register", "registration", "admission", "apply", "application"]
        for keyword in primary_keywords:
            if keyword in user_lower:
                confidence += 0.4
        
        # Secondary enrollment keywords (medium weight)
        secondary_keywords = ["join", "enter", "start school", "new student", "mag-enroll", "pag-enroll", "rehistro"]
        for keyword in secondary_keywords:
            if keyword in user_lower:
                confidence += 0.3
        
        # Context boosters (small weight)
        context_boosters = ["child", "son", "daughter", "kid", "anak", "bata"]
        for booster in context_boosters:
            if booster in user_lower:
                confidence += 0.1
        
        # Question indicators (small weight)
        question_indicators = ["how", "what", "when", "where", "paano", "ano", "kailan", "saan"]
        for indicator in question_indicators:
            if indicator in user_lower:
                confidence += 0.1
        
        return min(confidence, 0.95)  # Cap at 95%
    
    def _calculate_location_confidence(self, user_lower: str) -> float:
        """Calculate confidence score for location intent"""
        confidence = 0.0
        
        # Primary location keywords
        primary_keywords = ["where", "location", "address", "saan", "nasaan", "diin"]
        for keyword in primary_keywords:
            if keyword in user_lower:
                confidence += 0.4
        
        # School context
        school_keywords = ["school", "paaralan", "eskwelahan"]
        for keyword in school_keywords:
            if keyword in user_lower:
                confidence += 0.3
        
        # Direction/navigation keywords  
        nav_keywords = ["directions", "how to get", "find", "paano pumunta", "located"]
        for keyword in nav_keywords:
            if keyword in user_lower:
                confidence += 0.2
        
        return min(confidence, 0.95)
    
    def _calculate_staff_confidence(self, user_lower: str) -> float:
        """Calculate confidence score for staff inquiry intent"""
        confidence = 0.0
        
        # Staff roles and titles - expanded for better detection
        staff_keywords = [
            "teacher", "principal", "staff", "guro", "maestro", "head teacher", 
            "school head", "head", "director", "administrator", "guidance", 
            "counselor", "faculty", "nurse", "secretary"
        ]
        for keyword in staff_keywords:
            if keyword in user_lower:
                confidence += 0.4
        
        # Question words about people
        people_questions = ["who", "sino", "sin-o", "who is", "sino ang", "sin-o ang"]
        for question in people_questions:
            if question in user_lower:
                confidence += 0.3
        
        # Administrative inquiry patterns
        admin_patterns = ["head is", "head of", "in charge", "administrator", "director"]
        for pattern in admin_patterns:
            if pattern in user_lower:
                confidence += 0.3
        
        # Known staff names (partial matching)
        known_names = ["meliza", "delgado", "nelda", "annalyn", "lezil", "michelle", "thedy", "jessica", "leny"]
        for name in known_names:
            if name in user_lower:
                confidence += 0.4
        
        return min(confidence, 0.95)
    
    def _legacy_classification_fallback(self, user_lower: str) -> NLUResult:
        """Fallback to original classification logic for unhandled cases"""
        
        # Priority 1: Denials and clarifications (check first to avoid false positives)
        if any(phrase in user_lower for phrase in ["not asking", "i am not", "i'm not", "hindi ako", "wala ako"]):
            return NLUResult(Intent.DENIAL, 0.9, [])
        
        if any(phrase in user_lower for phrase in ["i meant", "what i mean", "clarify", "correction"]):
            return NLUResult(Intent.CLARIFICATION, 0.8, [])
        
        # Add other fallback classifications here...
        # For now, return unknown with low confidence
        return NLUResult(Intent.UNKNOWN, 0.1, [])
    
    async def _ai_intent_classification(self, user_input: str, context: Dict = None) -> NLUResult:
        """Use AI (OpenAI/Groq) for intent classification"""
        
        prompt = self._build_intent_classification_prompt(user_input, context)
        
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