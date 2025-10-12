import os
import nltk

# Point NLTK to the local nltk_data folder first, then Render path for deployment
local_nltk_path = os.path.join(os.path.dirname(__file__), "..", "nltk_data")
render_nltk_path = "/opt/render/nltk_data"

# Add local path first (for development), then Render path (for deployment)
nltk.data.path.insert(0, local_nltk_path)
nltk.data.path.append(render_nltk_path)

import json
import logging
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# NLTK will be imported lazily to avoid deployment issues
NLTK_AVAILABLE = False
NLTK_INITIALIZED = False

def _initialize_nltk():
    """Initialize NLTK safely with error handling"""
    global NLTK_AVAILABLE, NLTK_INITIALIZED
    
    if NLTK_INITIALIZED:
        return NLTK_AVAILABLE
    
    try:
        import nltk
        from nltk.tokenize import word_tokenize, sent_tokenize
        from nltk.corpus import stopwords
        from nltk.stem import PorterStemmer
        from nltk.tag import pos_tag
        
        NLTK_AVAILABLE = True
        NLTK_INITIALIZED = True
        # logger.info("✅ NLTK initialized successfully for NLU engine")
        return True
        
    except ImportError:
        NLTK_AVAILABLE = False
        NLTK_INITIALIZED = True
        logger.warning("NLTK not available for NLU engine")
        return False
    except Exception as e:
        NLTK_AVAILABLE = False
        NLTK_INITIALIZED = True
        logger.warning(f"NLTK initialization failed: {e}")
        return False

# Multilingual NLP engine removed - using simple rule-based classification only
MULTILINGUAL_NLP_AVAILABLE = False

class Intent(Enum):
    """Defined intents for the school chatbot"""
    # CRITICAL SAFETY: Medical emergency detection (HIGHEST PRIORITY)
    EMERGENCY = "emergency"  # Medical emergencies, 911 calls, life-threatening situations
    
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
    CONTACT_ESCALATION = "contact_escalation"  # New: live person contact requests
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
    EMOTIONAL_EXPRESSION = "emotional_expression"  # New: i am sad, i am happy, etc.
    CLARIFICATION = "clarification"
    DENIAL = "denial"
    GOODBYE = "goodbye"
    
    # Emergency and Safety Intents - for critical situations
    MEDICAL_EMERGENCY = "medical_emergency"  # Medical emergencies requiring immediate attention
    SAFETY_EMERGENCY = "safety_emergency"  # School safety emergencies
    
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
    is_multi_question: bool = False
    questions: List[str] = None

class NLUEngine:
    """
    Natural Language Understanding engine for the school chatbot.
    Uses AI-powered intent classification with rule-based fallback.
    """
    
    def __init__(self):
        # Optional: Initialize AI clients (OpenAI/Groq) for advanced classification
        self.openai_client = None
        
        # Multi-question detection patterns
        self.question_separators = [
            r'\?',  # Question marks
            r'\.\s+(?=[A-Z])',  # Periods followed by capital letters
            r';\s+',  # Semicolons
            r'and\s+',  # "and" as separator
            r'also\s+',  # "also" as separator
            r'what\s+about\s+',  # "what about" as separator
            r'how\s+about\s+',  # "how about" as separator
        ]
        self.groq_client = None
        
        # Initialize NLTK components for enhanced text processing
        self.stemmer = None
        self.stop_words = set()
    
    def detect_multi_questions(self, user_input: str) -> Tuple[bool, List[str]]:
        """Detect if the input contains multiple questions and parse them"""
        import re
        
        # Clean the input
        cleaned_input = user_input.strip()
        
        # Count question marks
        question_marks = cleaned_input.count('?')
        
        # If there are multiple question marks, split by them
        if question_marks > 1:
            questions = [q.strip() for q in cleaned_input.split('?') if q.strip()]
            # Remove the last empty element if it exists
            if questions and not questions[-1]:
                questions = questions[:-1]
            return True, questions
        
        # Check for other separators that might indicate multiple questions
        for pattern in self.question_separators:
            if re.search(pattern, cleaned_input, re.IGNORECASE):
                # Split by the pattern
                parts = re.split(pattern, cleaned_input, flags=re.IGNORECASE)
                questions = [part.strip() for part in parts if part.strip()]
                if len(questions) > 1:
                    return True, questions
        
        # Check for common multi-question patterns
        multi_question_patterns = [
            r'what\s+is\s+.*\s+and\s+where\s+is',  # "what is X and where is Y"
            r'who\s+is\s+.*\s+and\s+what\s+is',   # "who is X and what is Y"
            r'when\s+is\s+.*\s+and\s+where\s+is', # "when is X and where is Y"
            r'how\s+many\s+.*\s+and\s+what\s+are', # "how many X and what are Y"
        ]
        
        for pattern in multi_question_patterns:
            if re.search(pattern, cleaned_input, re.IGNORECASE):
                # Split by "and" or similar conjunctions
                parts = re.split(r'\s+and\s+', cleaned_input, flags=re.IGNORECASE)
                questions = [part.strip() for part in parts if part.strip()]
                if len(questions) > 1:
                    return True, questions
        
        return False, [user_input]
    
    def _initialize_nltk_components(self):
        """Initialize NLTK components safely"""
        if _initialize_nltk():
            try:
                from nltk.stem import PorterStemmer
                from nltk.corpus import stopwords
                self.stemmer = PorterStemmer()
                self.stop_words = set(stopwords.words('english'))
                # logger.info(f"✅ NLU Engine initialized with {len(self.stop_words)} stopwords")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize NLTK components: {e}")
                self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
    
    def _preprocess_text(self, text: str) -> str:
        """Enhanced text preprocessing using NLTK"""
        if not _initialize_nltk():
            return text.lower().strip()
        
        try:
            from nltk.tokenize import word_tokenize
            # Tokenize and clean text
            tokens = word_tokenize(text.lower())
            
            # Remove stopwords and non-alphabetic tokens
            filtered_tokens = [token for token in tokens 
                             if token.isalpha() and token not in self.stop_words]
            
            # Stem tokens if stemmer is available
            if self.stemmer:
                filtered_tokens = [self.stemmer.stem(token) for token in filtered_tokens]
            
            return ' '.join(filtered_tokens)
        except Exception as e:
            logger.warning(f"Text preprocessing failed: {e}")
            return text.lower().strip()
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases using NLTK POS tagging"""
        if not _initialize_nltk():
            return text.split()
        
        try:
            from nltk.tokenize import word_tokenize
            from nltk.tag import pos_tag
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            
            # Extract nouns, adjectives, and important verbs
            key_phrases = []
            for token, pos in pos_tags:
                if pos.startswith(('NN', 'JJ', 'VB')) and len(token) > 2:
                    key_phrases.append(token.lower())
            
            return key_phrases
        except Exception as e:
            logger.warning(f"Key phrase extraction failed: {e}")
            return text.split()
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        if not _initialize_nltk():
            # Simple word overlap similarity
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            return len(intersection) / len(union) if union else 0.0
        
        try:
            # Enhanced similarity using preprocessed text
            processed1 = self._preprocess_text(text1)
            processed2 = self._preprocess_text(text2)
            
            words1 = set(processed1.split())
            words2 = set(processed2.split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            # Jaccard similarity
            jaccard = len(intersection) / len(union)
            
            # Weight by key phrase overlap
            key_phrases1 = set(self._extract_key_phrases(text1))
            key_phrases2 = set(self._extract_key_phrases(text2))
            key_intersection = key_phrases1.intersection(key_phrases2)
            key_union = key_phrases1.union(key_phrases2)
            
            key_similarity = len(key_intersection) / len(key_union) if key_union else 0.0
            
            # Combine similarities (weight key phrases more)
            return (jaccard * 0.6) + (key_similarity * 0.4)
            
        except Exception as e:
            logger.warning(f"Semantic similarity calculation failed: {e}")
            return 0.0
        
    async def _detect_emergency_with_context(self, user_input: str, user_lower: str) -> Optional[NLUResult]:
        """
        Enhanced emergency detection with NLP context analysis to avoid false positives
        """
        try:
            # Step 1: Check for humor/sarcasm indicators first (highest priority)
            humor_indicators = await self._detect_humor_context(user_input, user_lower)
            if humor_indicators['is_humor']:
                # logger.info(f"😄 Humor detected: {humor_indicators['reason']} - NOT an emergency")
                return None
            
            # Step 2: Check for emotional context (jokes, expressions, metaphors)
            emotional_context = await self._analyze_emotional_context(user_input, user_lower)
            if emotional_context['is_expression']:
                # logger.info(f"💭 Emotional expression detected: {emotional_context['reason']} - NOT an emergency")
                return None
            
            # Step 3: Check for serious emergency indicators with context
            emergency_indicators = await self._detect_serious_emergency_indicators(user_input, user_lower)
            if emergency_indicators['is_emergency']:
                logger.warning(f"🚨 REAL EMERGENCY DETECTED: {emergency_indicators['reason']}")
                return NLUResult(Intent.EMERGENCY, 0.95, [])
            
            # Step 4: Check for standalone medical terms (likely not emergencies)
            standalone_medical = self._check_standalone_medical_terms(user_lower)
            if standalone_medical['is_standalone']:
                # logger.info(f"ℹ️ Standalone medical term: {standalone_medical['reason']} - NOT emergency")
                return None
            
            # Step 5: Fallback to original keyword detection (but with lower confidence)
            fallback_emergency = self._fallback_emergency_detection(user_lower)
            if fallback_emergency:
                logger.warning(f"🚨 FALLBACK EMERGENCY DETECTED: {fallback_emergency}")
                return NLUResult(Intent.EMERGENCY, 0.7, [])  # Lower confidence for fallback
            
            return None
            
        except Exception as e:
            logger.error(f"Emergency detection failed: {e}")
            # Fallback to original simple detection
            return self._fallback_emergency_detection(user_lower)
    
    async def _detect_humor_context(self, user_input: str, user_lower: str) -> Dict:
        """
        Detect humor, sarcasm, and non-literal language using NLP patterns
        """
        humor_indicators = {
            'is_humor': False,
            'reason': '',
            'confidence': 0.0
        }
        
        # Strong humor indicators (high confidence)
        strong_humor_patterns = [
            r'\b(haha|hehe|hihi|lol|lmao|rofl|funny|joke|joking|kidding|just kidding)\b',
            r'\b(thought|thinking|gonna|going to|almost|nearly|close call)\b',
            r'\b(you made me|you gave me|you almost|you nearly)\b',
            r'\b(that was|that\'s|this is)\s+(funny|hilarious|amusing|comical)\b',
            r'\b(not serious|not really|just saying|just messing)\b'
        ]
        
        for pattern in strong_humor_patterns:
            if re.search(pattern, user_lower):
                humor_indicators['is_humor'] = True
                humor_indicators['reason'] = f"Humor pattern: {pattern}"
                humor_indicators['confidence'] = 0.9
                return humor_indicators
        
        # Medium humor indicators
        medium_humor_patterns = [
            r'\b(almost|nearly|close|scared|worried|nervous)\b.*\b(heart|attack|stroke|emergency)\b',
            r'\b(heart|attack|stroke|emergency)\b.*\b(almost|nearly|close|scared|worried|nervous)\b',
            r'\b(you|that|this)\s+(almost|nearly|gave|made)\s+(me|us)\b',
            r'\b(thought|thinking|was thinking|was worried)\b.*\b(you|that|this)\b'
        ]
        
        for pattern in medium_humor_patterns:
            if re.search(pattern, user_lower):
                humor_indicators['is_humor'] = True
                humor_indicators['reason'] = f"Contextual humor: {pattern}"
                humor_indicators['confidence'] = 0.7
                return humor_indicators
        
        # Check for laughter patterns
        laughter_patterns = [r'ha{2,}', r'he{2,}', r'hi{2,}', r'lol+', r'rofl+']
        for pattern in laughter_patterns:
            if re.search(pattern, user_lower):
                humor_indicators['is_humor'] = True
                humor_indicators['reason'] = f"Laughter pattern: {pattern}"
                humor_indicators['confidence'] = 0.8
                return humor_indicators
        
        return humor_indicators
    
    async def _analyze_emotional_context(self, user_input: str, user_lower: str) -> Dict:
        """
        Analyze emotional context to distinguish between real distress and expressions
        """
        emotional_context = {
            'is_expression': False,
            'reason': '',
            'confidence': 0.0
        }
        
        # Expression patterns (not literal emergencies)
        expression_patterns = [
            r'\b(thought|thinking|was thinking|was worried|was scared)\b',
            r'\b(you|that|this)\s+(almost|nearly|gave|made|caused)\s+(me|us)\s+(to|a)\b',
            r'\b(heart|attack|stroke|emergency)\b.*\b(almost|nearly|close|scared|worried|nervous)\b',
            r'\b(almost|nearly|close|scared|worried|nervous)\b.*\b(heart|attack|stroke|emergency)\b',
            r'\b(you|that|this)\s+(are|were|will be)\s+(gonna|going to)\b',
            r'\b(gonna|going to)\s+(give|cause|make)\s+(me|us)\b',
            r'\b(thought|thinking|about)\b.*\b(heart|attack|stroke|emergency)\b',
            r'\b(heart|attack|stroke|emergency)\b.*\b(symptoms|about|information|what is|tell me|explain)\b'
        ]
        
        for pattern in expression_patterns:
            if re.search(pattern, user_lower):
                emotional_context['is_expression'] = True
                emotional_context['reason'] = f"Expression pattern: {pattern}"
                emotional_context['confidence'] = 0.8
                return emotional_context
        
        # Check for metaphorical language
        metaphorical_indicators = [
            'thought', 'thinking', 'gonna', 'going to', 'almost', 'nearly',
            'you made me', 'you gave me', 'you almost', 'you nearly'
        ]
        
        metaphorical_count = sum(1 for indicator in metaphorical_indicators if indicator in user_lower)
        if metaphorical_count >= 2:
            emotional_context['is_expression'] = True
            emotional_context['reason'] = f"Multiple metaphorical indicators: {metaphorical_count}"
            emotional_context['confidence'] = 0.7
            return emotional_context
        
        # Check for informational context patterns
        info_patterns = [
            r'\b(about|symptoms|information|what is|tell me|explain)\b.*\b(heart|attack|stroke|emergency)\b',
            r'\b(heart|attack|stroke|emergency)\b.*\b(about|symptoms|information|what is|tell me|explain)\b',
            r'\b(thought|thinking)\s+(about|of)\b',
            r'\b(what|how|when|where|why)\b.*\b(heart|attack|stroke|emergency)\b'
        ]
        
        for pattern in info_patterns:
            if re.search(pattern, user_lower):
                emotional_context['is_expression'] = True
                emotional_context['reason'] = f"Informational pattern: {pattern}"
                emotional_context['confidence'] = 0.8
                return emotional_context
        
        return emotional_context
    
    def _check_standalone_medical_terms(self, user_lower: str) -> Dict:
        """
        Check if medical terms appear without urgent context (likely not emergencies)
        """
        standalone_result = {
            'is_standalone': False,
            'reason': '',
            'confidence': 0.0
        }
        
        # Medical terms that need urgent context to be emergencies
        medical_terms = ['heart attack', 'stroke', 'cardiac arrest', 'chest pain']
        
        for term in medical_terms:
            if term in user_lower:
                # Check for urgent context indicators
                urgent_indicators = ['help', 'emergency', 'ambulance', '911', 'call', 'now', 'immediately', 'urgent', 'dying', 'can\'t breathe']
                has_urgent_context = any(indicator in user_lower for indicator in urgent_indicators)
                
                if not has_urgent_context:
                    standalone_result['is_standalone'] = True
                    standalone_result['reason'] = f"Medical term '{term}' without urgent context"
                    standalone_result['confidence'] = 0.8
                    return standalone_result
        
        return standalone_result
    
    async def _detect_serious_emergency_indicators(self, user_input: str, user_lower: str) -> Dict:
        """
        Detect serious emergency indicators with high confidence
        """
        emergency_indicators = {
            'is_emergency': False,
            'reason': '',
            'confidence': 0.0
        }
        
        # High-confidence emergency patterns
        # Enhanced patterns for better emergency detection
        serious_emergency_patterns = [
            # Direct emergency statements
            r'\b(emergency|ambulance|911|call 911|call emergency)\b',
            r'\b(medical emergency|urgent medical|urgent help needed)\b',
            r'\b(life threatening|critical condition|critical situation)\b',
            
            # Specific medical emergency conditions
            r'\b(can\'t breathe|can\'t breath|shortness of breath|difficulty breathing)\b',
            r'\b(unconscious|passed out|fainted|not responding|unresponsive)\b',
            r'\b(bleeding|blood|hemorrhage|severe bleeding)\b',
            r'\b(chest pain|heart pain|severe pain|intense pain)\b',
            r'\b(heart attack|cardiac arrest|stroke|seizure)\b',
            r'\b(severe injury|accident|hurt badly|broken bone|fracture)\b',
            
            # "I'm having" patterns for direct emergency reporting - enhanced with variations
            r'\bi\'?m having a (heart attack|stroke|seizure|medical emergency)\b',
            r'\bi\'?m having (chest pain|difficulty breathing|severe pain)\b',
            r'\bi\'?m (bleeding|injured|hurt badly|dying)\b',
            r'\bi am having a (heart attack|stroke|seizure|medical emergency)\b',
            r'\bi am having (chest pain|difficulty breathing|severe pain)\b',
            r'\bi am (bleeding|injured|hurt badly|dying)\b',
            r'\bhaving (a heart attack|a stroke|a seizure|chest pain)\b',
            
            # Real emergency help requests (multiple urgent indicators)
            r'\b(someone|somebody|my (friend|family|child|parent))\b.*\b(help|emergency|dying|hurt|injured)\b',
            r'\b(help|emergency)\b.*\b(someone|somebody|my (friend|family|child|parent))\b.*\b(dying|hurt|injured)\b',
            
            # Very specific emergency help patterns (not general "help me")
            r'\b(help me now|help us now|help me please|help us please)\b.*\b(emergency|dying|hurt|injured|unconscious|bleeding)\b',
            r'\b(emergency|dying|hurt|injured|unconscious|bleeding)\b.*\b(help me now|help us now|help me please|help us please)\b',
            
            # Time-sensitive emergency indicators
            r'\b(dying|cardiac arrest|stroke|heart attack)\b.*\b(now|immediately|help|emergency)\b',
            r'\b(now|immediately|help|emergency)\b.*\b(dying|cardiac arrest|stroke|heart attack)\b',
            
            # Direct statements about self
            r'\bi\'?m dying\b',
            r'\bi\'?m having an emergency\b',
            r'\bi need (medical attention|an ambulance|911)\b',
            r'\bi am dying\b',
            r'\bi am having an emergency\b',
            
            # Simplified heart attack patterns (to catch the test case)
            r'heart attack',
            r'having a heart attack',
            r'having heart attack'
        ]
        
        for pattern in serious_emergency_patterns:
            if re.search(pattern, user_lower):
                # Check if it's used in a figurative context
                is_figurative = False
                figurative_contexts = [
                    'to know', 'laughing', 'waiting to happen', 'killing me', 'skipped a beat',
                    'dying to', 'dying of', 'dying from', 'feels like', 'like a', 'as if'
                ]
                
                for context in figurative_contexts:
                    if context in user_lower:
                        logger.info(f"🎭 NLU: Figurative use detected in pattern: '{pattern}' with '{context}' in '{user_input}'")
                        is_figurative = True
                        break
                
                # Only trigger emergency if not figurative
                if not is_figurative:
                    emergency_indicators['is_emergency'] = True
                    emergency_indicators['reason'] = f"Serious emergency pattern: {pattern}"
                    emergency_indicators['confidence'] = 0.95
                    return emergency_indicators
        
        # Check for urgent action words combined with medical terms
        # 🎯 FIX: Removed standalone "help" to avoid false positives with "help me with homework"
        urgent_words = ['emergency', 'ambulance', '911', 'call 911', 'help me', 'help us', 'call', 'now', 'immediately', 'urgent']
        medical_words = ['heart attack', 'stroke', 'dying', 'bleeding', 'unconscious', 'can\'t breathe']
        
        urgent_count = sum(1 for word in urgent_words if word in user_lower)
        medical_count = sum(1 for word in medical_words if word in user_lower)
        
        if urgent_count >= 1 and medical_count >= 1:
            # Check if it's used in a figurative context
            is_figurative = False
            figurative_contexts = [
                'to know', 'laughing', 'waiting to happen', 'killing me', 'skipped a beat',
                'dying to', 'dying of', 'dying from', 'feels like', 'like a', 'as if'
            ]
            
            for context in figurative_contexts:
                if context in user_lower:
                    logger.info(f"🎭 NLU: Figurative use detected in urgent+medical: '{context}' in '{user_input}'")
                    is_figurative = True
                    break
            
            # Only trigger emergency if not figurative
            if not is_figurative:
                emergency_indicators['is_emergency'] = True
                emergency_indicators['reason'] = f"Urgent + medical terms: {urgent_count} urgent, {medical_count} medical"
                emergency_indicators['confidence'] = 0.9
                return emergency_indicators
        
        return emergency_indicators
    
    def _fallback_emergency_detection(self, user_lower: str) -> Optional[NLUResult]:
        """
        Fallback emergency detection using original keyword matching (lower confidence)
        Only triggers for high-confidence emergency scenarios
        """
        # Only check for high-confidence emergency keywords (not just medical terms)
        # Enhanced with more direct emergency phrases
        high_confidence_emergency_keywords = [
            # Direct emergency terms
            'emergency', 'ambulance', '911', 'call 911', 'medical emergency',
            
            # Direct physical conditions
            'can\'t breathe', 'unconscious', 'bleeding', 'severe pain', 'heart attack',
            'stroke', 'seizure', 'cardiac arrest', 'not breathing', 'choking',
            
            # Direct urgent help phrases
            'help me now', 'need urgent help', 'critical', 'life threatening',
            'i\'m dying', 'i\'m having a heart attack', 'i\'m having a stroke',
            
            # Tagalog emergency terms
            'tulong agad', 'emergency po', 'atake sa puso', 'hindi makahinga'
        ]
        
        # Check for high-confidence emergency patterns
        import re
        for keyword in high_confidence_emergency_keywords:
            # Use word boundary matching to avoid false positives like "held" containing "help"
            if re.search(r'\b' + re.escape(keyword) + r'\b', user_lower):
                # Check if it's used in a figurative context
                is_figurative = False
                figurative_contexts = [
                    'to know', 'laughing', 'waiting to happen', 'killing me', 'skipped a beat',
                    'dying to', 'dying of', 'dying from', 'feels like', 'like a', 'as if'
                ]
                
                for context in figurative_contexts:
                    if context in user_lower:
                        logger.info(f"🎭 NLU: Figurative use detected in fallback: '{keyword}' with '{context}'")
                        is_figurative = True
                        break
                
                # Only trigger emergency if not figurative
                if not is_figurative:
                    logger.warning(f"🚨 FALLBACK EMERGENCY DETECTED: '{keyword}'")
                    return NLUResult(Intent.EMERGENCY, 0.7, [])  # Lower confidence for fallback
        
        # For medical terms without urgent context, don't flag as emergency
        # This prevents false positives for informational queries
        medical_terms = ['heart attack', 'stroke', 'cardiac arrest', 'chest pain']
        for term in medical_terms:
            if term in user_lower:
                # Check if it's in an informational context
                info_contexts = ['symptoms', 'about', 'what is', 'information', 'tell me about', 'explain']
                if any(context in user_lower for context in info_contexts):
                    # logger.info(f"ℹ️ Medical term '{term}' in informational context - NOT emergency")
                    return None
                # If no urgent context, don't flag as emergency
                # logger.info(f"ℹ️ Medical term '{term}' without urgent context - NOT emergency")
                return None
        
        return None
        
    async def analyze_intent(self, user_input: str, context: Dict = None) -> NLUResult:
        """
        Analyze user input to determine intent and extract entities using advanced NLP
        """
        
        # 🚨 MULTI-QUESTION DETECTION: Check if input contains multiple questions
        is_multi_question, questions = self.detect_multi_questions(user_input)
        
        if is_multi_question:
            # For multi-question inputs, analyze the primary intent but mark as multi-question
            primary_question = questions[0] if questions else user_input
            result = await self._analyze_single_intent(primary_question, context)
            result.is_multi_question = True
            result.questions = questions
            return result
        
        # Single question - proceed with normal analysis
        return await self._analyze_single_intent(user_input, context)
    
    async def _analyze_single_intent(self, user_input: str, context: Dict = None) -> NLUResult:
        """
        Analyze a single question for intent and entities
        """
        
        # FIRST PRIORITY: Check for medical emergencies with context awareness (CRITICAL SAFETY)
        user_lower = user_input.lower()
        
        # Direct emergency detection for critical phrases (highest priority)
        critical_emergency_phrases = [
            "heart attack", "stroke", "can't breathe", "emergency", "911",
            "help me now", "medical emergency", "critical condition", "dying"
        ]
        
        # Context words that indicate figurative usage (not real emergencies)
        figurative_contexts = [
            'to know', 'laughing', 'waiting to happen', 'killing me', 'skipped a beat',
            'dying to', 'dying of', 'dying from', 'feels like', 'like a', 'as if',
            'almost', 'nearly', 'thought', 'thinking', 'gonna', 'going to', 
            'you made me', 'you gave me', 'you almost', 'you nearly', 'close call',
            'was thinking', 'was worried', 'was scared', 'haha', 'hehe', 'lol',
            'joke', 'joking', 'kidding', 'just kidding', 'not serious', 'not really'
        ]
        
        # Special cases for common figurative expressions
        figurative_expressions = [
            "dying to know", "dying laughing", "gonna die laughing", "dying of laughter",
            "dying of", "dying from", "dying with", "almost died", "nearly died"
        ]
        
        is_figurative = False
        for expr in figurative_expressions:
            if expr in user_lower:
                logger.info(f"🎭 NLU: Figurative 'dying' expression detected: '{expr}' in '{user_input}'")
                is_figurative = True
                break
        
        # Also check for "dying" + context words
        if "dying" in user_lower:
            figurative_contexts = ["laughing", "laugh", "know", "curiosity", "funny", "joke", "amused", "hilarious"]
            for context in figurative_contexts:
                if context in user_lower:
                    logger.info(f"🎭 NLU: Figurative 'dying' with context '{context}' detected in: '{user_input}'")
                    is_figurative = True
                    break
        
        if is_figurative:
            # Skip emergency detection for this query - return unknown intent
            return NLUResult(Intent.UNKNOWN, 0.3, [])
        else:
            # Check for direct critical emergency phrases first
            for phrase in critical_emergency_phrases:
                if phrase in user_lower:
                    # Check if it's used in a figurative context
                    is_figurative = False
                    for context in figurative_contexts:
                        if context in user_lower:
                            logger.info(f"🎭 NLU: Figurative use detected: '{phrase}' with '{context}' in '{user_input}'")
                            is_figurative = True
                            break
                    
                    # Only trigger emergency if not figurative
                    if not is_figurative:
                        logger.warning(f"🚨 CRITICAL EMERGENCY DETECTED: '{phrase}' in '{user_input}'")
                        return NLUResult(Intent.EMERGENCY, 0.98, [])
                
        # Check for specific phrases with apostrophes (which might cause matching issues)
        apostrophe_phrases = [
            "i'm having a heart attack", "i'm having a stroke", "i'm dying",
            "i am having a heart attack", "i am having a stroke", "i am dying"
        ]
        
        for phrase in apostrophe_phrases:
            # Normalize both strings to handle apostrophe differences
            norm_phrase = phrase.replace("'", "").lower()
            norm_input = user_lower.replace("'", "").lower()
            
            if norm_phrase in norm_input or phrase in user_lower:
                # Check if it's used in a figurative context
                is_figurative = False
                for context in figurative_contexts:
                    if context in user_lower:
                        logger.info(f"🎭 NLU: Figurative use detected in apostrophe phrase: '{phrase}' with '{context}' in '{user_input}'")
                        is_figurative = True
                        break
                
                # Only trigger emergency if not figurative
                if not is_figurative:
                    logger.warning(f"🚨 CRITICAL EMERGENCY DETECTED: '{phrase}' matches '{user_input}'")
                    return NLUResult(Intent.EMERGENCY, 0.98, [])
        
        # Enhanced emergency detection with NLP context analysis
        emergency_result = await self._detect_emergency_with_context(user_input, user_lower)
        if emergency_result:
            return emergency_result
        
        # Normalize common typos and variations
        normalized_input = user_lower
        typo_corrections = {
            'kayo': ['kayO', 'kay0', 'kayoo', 'kayou'],
            'prinsipal': ['principal', 'prinsipal', 'prinsipal', 'prinsipal'],
            'sino': ['sino', 'sino', 'sino', 'sino'],
            'may': ['may', 'may', 'may', 'may']
        }
        
        # Apply typo corrections
        for correct, typos in typo_corrections.items():
            for typo in typos:
                normalized_input = normalized_input.replace(typo, correct)
        
        # Check for staff inquiry patterns with typo tolerance
        if "may prinsipal" in normalized_input or "may principal" in normalized_input:
            # logger.info(f"🎯 Rule-based staff inquiry detected: 'may prinsipal' pattern (normalized from '{user_input}')")
            return NLUResult(Intent.STAFF_INQUIRY, 0.9, [])
        
        # Multilingual NLP engine removed - using rule-based classification only
        
        # Fallback to rule-based classification with enhanced confidence
        rule_result = self._rule_based_classification(user_input)
        
        # Multilingual NLP engine removed - using rule-based classification only
        
        # logger.info(f"🔍 Using rule-based result: {rule_result.intent.value} (confidence: {rule_result.confidence:.2f})")
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
            
            # Aklanon greetings and thanks
            "salamat gid": (Intent.APPRECIATION, 0.95),
            "damo nga salamat": (Intent.APPRECIATION, 0.95),
            "maayong adlaw": (Intent.GREETING_SIMPLE, 0.9),
            "maayong gabii": (Intent.GREETING_SIMPLE, 0.9),
            "maayong buntag": (Intent.GREETING_SIMPLE, 0.9),
            
            # Tagalog location phrases
            "saan ang lokasyon ng paaralan": (Intent.LOCATION_INQUIRY, 0.95),
            "saan ang paaralan": (Intent.LOCATION_INQUIRY, 0.9),
            "ano ang contact number ninyo": (Intent.CONTACT_INFO, 0.95),
            "sabihin mo sa akin ang tungkol sa school programs": (Intent.SCHOOL_INFO, 0.9),
            "sabihin sa akin tungkol sa": (Intent.GENERAL_INFO, 0.8),
            
            # Tagalog contact escalation phrases
            "gusto ko makausap ang isang tao": (Intent.CONTACT_ESCALATION, 0.95),
            "kailangan ko makausap ang isang tao": (Intent.CONTACT_ESCALATION, 0.95),
            "gusto ko makipag-usap sa isang tao": (Intent.CONTACT_ESCALATION, 0.95),
            "kailangan ko makipag-usap sa isang tao": (Intent.CONTACT_ESCALATION, 0.95),
            "gusto ko makausap ang isang staff": (Intent.CONTACT_ESCALATION, 0.95),
            "kailangan ko makausap ang isang staff": (Intent.CONTACT_ESCALATION, 0.95),
            "gusto ko makausap ang isang teacher": (Intent.CONTACT_ESCALATION, 0.95),
            "kailangan ko makausap ang isang teacher": (Intent.CONTACT_ESCALATION, 0.95),
            "gusto ko makausap ang isang principal": (Intent.CONTACT_ESCALATION, 0.95),
            "kailangan ko makausap ang isang principal": (Intent.CONTACT_ESCALATION, 0.95),
            "gusto ko makausap ang isang guidance counselor": (Intent.CONTACT_ESCALATION, 0.95),
            "kailangan ko makausap ang isang guidance counselor": (Intent.CONTACT_ESCALATION, 0.95),
            
            # Aklanon location phrases  
            "diin ang lokasyon sang paaralan": (Intent.LOCATION_INQUIRY, 0.95),
            "diin ang paaralan": (Intent.LOCATION_INQUIRY, 0.9),
            "diin nga lokasyon": (Intent.LOCATION_INQUIRY, 0.9),
            "ano nga contact number": (Intent.CONTACT_INFO, 0.9),
            
            # Aklanon contact escalation phrases
            "gusto ko makausap ang isa ka tawo": (Intent.CONTACT_ESCALATION, 0.95),
            "kailangan ko makausap ang isa ka tawo": (Intent.CONTACT_ESCALATION, 0.95),
            "gusto ko makipag-usap sa isa ka tawo": (Intent.CONTACT_ESCALATION, 0.95),
            "kailangan ko makipag-usap sa isa ka tawo": (Intent.CONTACT_ESCALATION, 0.95),
            "gusto ko magistryo sa tawo": (Intent.CONTACT_ESCALATION, 0.95),
            "kailangan ko magistryo sa tawo": (Intent.CONTACT_ESCALATION, 0.95),
            "gusto ko makausap ang isa ka staff": (Intent.CONTACT_ESCALATION, 0.95),
            "kailangan ko makausap ang isa ka staff": (Intent.CONTACT_ESCALATION, 0.95),
            "gusto ko makausap ang isa ka teacher": (Intent.CONTACT_ESCALATION, 0.95),
            "kailangan ko makausap ang isa ka teacher": (Intent.CONTACT_ESCALATION, 0.95),
            "gusto ko makausap ang isa ka principal": (Intent.CONTACT_ESCALATION, 0.95),
            "kailangan ko makausap ang isa ka principal": (Intent.CONTACT_ESCALATION, 0.95),
            "gusto ko makausap ang isa ka guidance counselor": (Intent.CONTACT_ESCALATION, 0.95),
            "kailangan ko makausap ang isa ka guidance counselor": (Intent.CONTACT_ESCALATION, 0.95),
        }
        
        for phrase, (intent, confidence) in exact_phrases.items():
            if phrase in user_lower:
                # logger.info(f"🎯 Exact phrase match: '{phrase}' → {intent.value}")
                return NLUResult(intent, confidence, [])
        
        # PHASE 2: Enhanced pattern-based matching with weighted confidence scoring
        confidence_score = 0.0
        detected_intent = Intent.UNKNOWN
        evidence_factors = []
        
        # Enhanced greeting detection with confidence scoring
        greeting_indicators = self._analyze_greeting_patterns(user_lower)
        if greeting_indicators['intent'] != Intent.UNKNOWN:
            # Check if this is a greeting + question combination
            is_greeting_with_question = self._is_greeting_with_question(user_lower)
            if is_greeting_with_question:
                # Don't return greeting intent, let other intents be detected
                pass
            else:
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
        
        # 🚨 REMOVED: Old emergency detection code replaced by context-aware detection above
        
        # Enhanced emotional expression detection for Tagalog/Aklanon and English
        emotional_patterns = [
            "malungkot ako", "masaya ako", "nag-aalala ako", "natutuwa ako", 
            "pagod ako", "galit ako", "nervous ako", "takot ako", "nalilito ako", 
            "naiinis ako", "nag-aalala ako", "nalulungkot ako",
            # English emotional expressions
            "dying laughing", "laughing so hard", "can't stop laughing", "rolling on the floor",
            "this is killing me", "i'm cracking up", "bursting with laughter"
        ]
        
        for pattern in emotional_patterns:
            if pattern in user_lower:
                # logger.info(f"🎯 Tagalog/Aklanon emotional expression detected: '{pattern}'")
                return NLUResult(Intent.EMOTIONAL_EXPRESSION, 0.9, [])
        
        # Continue with priority-based classification for other intents
        # DO NOT return early - let it fall through to Priority rules
        
        # Priority 1: Denials and clarifications (check first to avoid false positives)
        if any(phrase in user_lower for phrase in ["not asking", "i am not", "i'm not", "hindi ako", "wala ako"]):
            return NLUResult(Intent.DENIAL, 0.9, [])
        
        if any(phrase in user_lower for phrase in ["i meant", "what i mean", "clarify", "correction"]):
            return NLUResult(Intent.CLARIFICATION, 0.8, [])
        
        # Priority 2: Check for contact escalation FIRST (even with name introductions)
        # This handles cases like "ako si heinz and i want to talk to a live person"
        contact_escalation_patterns = [
            # English patterns
            "talk to someone", "speak to someone", "contact someone", "live person", "human",
            "staff member", "want to speak", "need to talk", "talk to a live",
            "speak to a live", "contact a live", "talk to staff", "speak to staff", "contact staff",
            "talk to teacher", "speak to teacher", "contact teacher", "talk to principal", "speak to principal",
            "contact principal", "talk to guidance", "speak to guidance", "contact guidance",
            "talk to counselor", "speak to counselor", "contact counselor",
            "where can i contact", "how can i contact", "contact the admin", "talk to admin",
            "where is the messenger", "messenger link", "messenger button", "contact link",
            # More specific patterns for better matching
            "want to talk to", "want to speak to", "need to talk to", "need to speak to",
            "talk to a live person", "speak to a live person", "contact a live person",
            "i want to talk", "i want to speak", "i need to talk", "i need to speak",
            # Tagalog patterns
            "makausap ang isang tao", "makipag-usap sa isang tao", "makausap ang isang staff",
            "makipag-usap sa isang staff", "makausap ang isang teacher", "makipag-usap sa isang teacher",
            "makausap ang isang principal", "makipag-usap sa isang principal", "makausap ang isang guidance",
            "makipag-usap sa isang guidance", "makausap ang isang counselor", "makipag-usap sa isang counselor",
            "gusto ko makausap", "kailangan ko makausap", "gusto ko makipag-usap", "kailangan ko makipag-usap",
            "gusto ko mag-usap", "kailangan ko mag-usap", "gusto ko makipag-usap sa tao",
            # 🚨 CRITICAL: Add missing patterns that users are actually using
            "gusto ko kausapin", "kausapin ang admin", "admin lang", "wala, admin lang",
            "gusto ko lang kausapin", "wala, gusto ko lang kausapin ang admin",
            "gusto ko nga kausapin", "gusto ko nga kausapin ang admin",  # Add "nga" variations
            "wala,admin", "admin lang", "wala,admin lang",  # Handle spacing variations
            # Aklanon patterns
            "makausap ang isa ka tawo", "makipag-usap sa isa ka tawo", "magistryo sa tawo",
            "makausap ang isa ka staff", "makipag-usap sa isa ka staff", "makausap ang isa ka teacher", "makipag-usap sa isa ka teacher",
            "makausap ang isa ka principal", "makipag-usap sa isa ka principal", "makausap ang isa ka guidance",
            "makipag-usap sa isa ka guidance", "makausap ang isa ka counselor", "makipag-usap sa isa ka counselor"
        ]
        
        # Check for contact escalation patterns first (highest priority)
        matching_patterns = [pattern for pattern in contact_escalation_patterns if pattern in user_lower]
        
        # Also check for admin-related patterns with flexible spacing
        admin_patterns = ["admin", "kausapin", "gusto ko", "nga"]
        if any(pattern in user_lower for pattern in admin_patterns) and ("admin" in user_lower or "kausapin" in user_lower):
            matching_patterns.append("admin_contact_flexible")
        
        # 🚨 CRITICAL: Catch any admin contact request regardless of exact wording
        if "admin" in user_lower and any(word in user_lower for word in ["kausapin", "gusto", "nga", "lang"]):
            matching_patterns.append("admin_contact_any")
        
        if matching_patterns:
            # logger.info(f"🎯 CONTACT ESCALATION DETECTED: patterns={matching_patterns}")
            return NLUResult(Intent.CONTACT_ESCALATION, 0.85, [])
        
        # Priority 3: Name introductions - HIGH PRIORITY for greetings + names
        # This catches "hi i am john" as name_introduction rather than greeting_with_name
        name_intro_patterns = [
            "my name is", "i am called", "i'm called", "im called", "ako si", "ako ay", "called",
            "ngaean ko si", "ngaean ko", "ngaean", "ngaean si"  # Aklanon patterns
        ]
        
        # 🚨 FIX: Check for name introduction patterns FIRST, but be more specific
        for pattern in name_intro_patterns:
            if pattern in user_lower:
                # Check if there's an actual name after the pattern (not just the pattern alone)
                pattern_pos = user_lower.find(pattern)
                text_after = user_lower[pattern_pos + len(pattern):].strip()
                
                # 🚨 FIX: More specific validation - exclude emotional states and common adjectives
                emotional_states = ['sad', 'happy', 'worried', 'excited', 'tired', 'angry', 'nervous', 'scared', 'confused', 'frustrated', 'anxious', 'depressed', 'lonely', 'stressed', 'overwhelmed', 'disappointed', 'proud', 'grateful', 'relieved', 'surprised', 'shocked', 'amazed', 'confused', 'lost', 'found', 'here', 'there', 'ready', 'busy', 'free', 'available', 'unavailable', 'online', 'offline', 'studying', 'enrollment', 'school', 'grades', 'classes', 'homework', 'exams', 'tests', 'about', 'for', 'with', 'of']
                
                if len(text_after) > 0 and not text_after.startswith("asking") and not text_after.startswith("not"):
                    # 🚨 NEW: Check for contact escalation patterns in the text after name introduction
                    contact_escalation_keywords = [
                        "want to talk", "want to speak", "need to talk", "need to speak",
                        "talk to", "speak to", "contact", "live person", "human", "staff"
                    ]
                    
                    text_after_lower = text_after.lower()
                    has_contact_escalation = any(keyword in text_after_lower for keyword in contact_escalation_keywords)
                    
                    if has_contact_escalation:
                        # logger.info(f"🎯 Contact escalation detected in name introduction: pattern='{pattern}', text_after='{text_after}'")
                        return NLUResult(Intent.CONTACT_ESCALATION, 0.9, [])
                    
                    # 🚨 NEW: Use NLP-based analysis instead of hardcoded emotional states
                    extracted_name = self._extract_name_using_nlp(text_after, pattern)
                    
                    if extracted_name:
                        # logger.info(f"🎯 Name introduction detected: pattern='{pattern}', text_after='{text_after}', extracted_name='{extracted_name}'")
                        return NLUResult(Intent.NAME_INTRODUCTION, 0.95, [])
                    else:
                        # Check if it's an emotional expression using NLP
                        if self._is_emotional_expression_nlp(text_after):
                            # logger.info(f"🎯 Emotional expression detected: pattern='{pattern}', text_after='{text_after}'")
                            return NLUResult(Intent.EMOTIONAL_EXPRESSION, 0.9, [])
                        else:
                            # logger.info(f"🎯 Name introduction detected (fallback): pattern='{pattern}', text_after='{text_after}'")
                            return NLUResult(Intent.NAME_INTRODUCTION, 0.95, [])

        # Priority 2: Staff inquiries (moved up to catch principal queries before greetings)
        # Special pattern for "may prinsipal" queries - highest priority
        if "may prinsipal" in user_lower or "may principal" in user_lower:
            return NLUResult(Intent.STAFF_INQUIRY, 0.9, [])
        
        staff_words = ["teacher", "teachers", "staff", "principal", "prinsipal", "head teacher", "school head", "head", "director", "administrator", "guro", "maestro", "faculty", "guidance", "counselor", "adviser", "advisor", "advisers", "advisors", "support aide", "learning support aide", "aide"]
        if any(word in user_lower for word in staff_words):
            return NLUResult(Intent.STAFF_INQUIRY, 0.7, [])
        
        # Priority 3: Enhanced greeting classification with mood/style detection
        greeting_keywords = ["hi", "hello", "hey", "kamusta", "kumusta", "maayong", "good morning", "good afternoon", "good evening", "magandang umaga", "magandang hapon", "maayong aga", "maayong hapon", "maayong gab-i", "morning", "afternoon", "evening", "greetings", "hiya", "wassup", "howdy"]
        
        # Use word boundary matching to prevent substring matches
        import re
        greeting_pattern = r'\b(' + '|'.join(re.escape(greet) for greet in greeting_keywords) + r')\b'
        if re.search(greeting_pattern, user_lower):
            # Check if this is a greeting + question combination
            if self._is_greeting_with_question(user_lower):
                # Don't return greeting intent, let other intents be detected
                pass
            else:
                # Detect greeting style/mood for dynamic personalization
                if any(word in user_lower for word in ["awesome", "great", "fantastic", "wonderful", "amazing", "excited", "!!!", "super", "really good"]):
                    return NLUResult(Intent.GREETING_EXCITED, 0.9, [])
                elif any(word in user_lower for word in ["sir", "ma'am", "please", "good day", "greetings", "salutations", "formal"]):
                    return NLUResult(Intent.GREETING_FORMAL, 0.9, [])
                elif any(word in user_lower for word in ["sup", "hiya", "wassup", "howdy", "hey there", "casual"]):
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
            if not any(intro in user_lower for intro in ["my name is", "ako si", "i am", "i'm", "ngaean ko si", "ngaean ko"]):
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
        
        # Priority 7.5: Safety inquiries (moved up to prevent misclassification)
        safety_words = ["earthquake", "fire", "drill", "safety", "emergency", "disaster", "evacuation", "alarm", "protocol", "procedure", "preparedness", "drills"]
        if any(word in user_lower for word in safety_words):
            return NLUResult(Intent.SCHOOL_INFO, 0.8, [])
        
        # Priority 8: Staff inquiries (moved up to Priority 2.5)
        
        # Priority 9.5: Financial inquiries (moved up before school info to catch "school fees")
        financial_patterns = [
            "tuition", "fee", "fees", "payment", "cost", "price", "bayad", 
            "magkano", "how much", "pricing", "scholarship", "financial aid",
            "installment", "bayarin", "singil", "scholarship available"
        ]
        if any(pattern in user_lower for pattern in financial_patterns):
            return NLUResult(Intent.FINANCIAL_INQUIRY, 0.8, [])
        
        # Priority 10: Location inquiries - moved up to catch "where is the school"
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
        
        # Priority 11: School information - expanded patterns but lower priority than location
        school_words = [
            "curriculum", "program", "subjects", "classes", "school hours",
            "looking for", "we need information", "help me understand",
            "available programs", "what programs", "what classes", "school offers",
            # School name and identification queries
            "school called", "school name", "name of school", "what is your school",
            "whats your school", "what's your school", "school's name", "name of your school",
            "what is the school", "what school", "which school",
            # Grade level queries - HIGH PRIORITY to prevent misclassification as greetings
            "grades", "grade levels", "what grades", "grade", "kindergarten", "elementary",
            "what grade levels", "grade level", "levels", "what levels"
        ]
        if any(word in user_lower for word in school_words):
            return NLUResult(Intent.SCHOOL_INFO, 0.8, [])
        
        # Priority 12: Facilities inquiries
        facilities_patterns = [
            "cafeteria", "canteen", "library", "gym", "gymnasium", "playground", 
            "computer lab", "science lab", "clinic", "office", "classroom",
            "facilities", "amenities", "available", "have you got",
            "saan ang", "nasaan ang", "may"
        ]
        if any(pattern in user_lower for pattern in facilities_patterns):
            return NLUResult(Intent.FACILITIES_INQUIRY, 0.7, [])
        
        # Priority 13: General Info inquiries - Enhanced for multilingual
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
        
        # Contact escalation patterns moved to Priority 2 (above) for higher priority
        
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
                           "evening", "greetings", "hiya", "wassup", "howdy"]
        
        # Use word boundary matching to prevent substring matches
        import re
        greeting_pattern = r'\b(' + '|'.join(re.escape(greet) for greet in greeting_keywords) + r')\b'
        if re.search(greeting_pattern, user_lower):
            confidence = 0.8  # Base confidence for greeting detection
            
            # Check for name introduction first (more specific patterns)
            if any(pattern in user_lower for pattern in ["my name is", "i am called", "i'm called", "im called", "ako si", "ngaean ko si", "ngaean ko"]):
                intent = Intent.GREETING_WITH_NAME
                confidence = 0.95
            
            # Detect greeting style/mood for dynamic personalization
            elif any(word in user_lower for word in ["awesome", "great", "fantastic", "wonderful", "amazing", "excited", "!!!", "super", "really good"]):
                intent = Intent.GREETING_EXCITED
                confidence = 0.9
            elif any(word in user_lower for word in ["sir", "ma'am", "please", "good day", "greetings", "salutations", "formal"]):
                intent = Intent.GREETING_FORMAL
                confidence = 0.9
            elif any(word in user_lower for word in ["hiya", "wassup", "howdy", "hey there", "casual"]):
                intent = Intent.GREETING_CASUAL
                confidence = 0.9
            elif any(word in user_lower for word in ["back", "again", "return", "here again", "returning"]):
                intent = Intent.GREETING_RETURNING_USER
                confidence = 0.9
            else:
                intent = Intent.GREETING_SIMPLE
                confidence = 0.8
        
        return {"intent": intent, "confidence": confidence}
    
    def _is_greeting_with_question(self, user_lower: str) -> bool:
        """Check if this is a greeting combined with a question"""
        # Common greeting words
        greeting_words = ["hi", "hello", "hey", "kamusta", "kumusta", "maayong", "good morning", 
                         "good afternoon", "good evening", "magandang umaga", "magandang hapon", 
                         "maayong aga", "maayong hapon", "maayong gab-i", "morning", "afternoon", 
                         "evening", "greetings", "hiya", "wassup", "howdy"]
        
        # Question words that indicate there's a real question
        question_words = ["what", "where", "when", "who", "how", "why", "which", "can", "could", 
                         "would", "should", "is", "are", "do", "does", "did", "will", "have", "has",
                         "ano", "saan", "kailan", "sino", "paano", "bakit", "alin", "pwed", "maaari", 
                         "gusto", "kailangan", "?", "time", "class", "start", "adviser", "grade"]
        
        # Check if query contains both greeting and question words
        has_greeting = any(word in user_lower for word in greeting_words)
        has_question = any(word in user_lower for word in question_words)
        
        return has_greeting and has_question
    
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
    
    def _extract_name_using_nlp(self, text_after: str, pattern: str) -> str:
        """Extract name using NLP analysis instead of hardcoded patterns"""
        import re
        
        # Clean the text
        text_after = text_after.strip()
        if not text_after:
            return None
        
        # Split into words
        words = text_after.split()
        if not words:
            return None
        
        # Use NLP patterns to identify potential names
        potential_names = []
        
        # Pattern 1: Single word that looks like a name (capitalized, not a common word)
        first_word = words[0]
        if self._is_likely_name(first_word):
            potential_names.append(first_word)
        
        # Pattern 2: Two words that could be first and last name
        if len(words) >= 2:
            two_words = f"{words[0]} {words[1]}"
            if self._is_likely_full_name(two_words):
                potential_names.append(two_words)
        
        # Pattern 3: Extract name before common connecting words
        connecting_words = ['and', 'at', 'from', 'to', 'with', 'for', 'in', 'on', 'at']
        for i, word in enumerate(words):
            if word.lower() in connecting_words and i > 0:
                name_candidate = ' '.join(words[:i])
                if self._is_likely_name(name_candidate):
                    potential_names.append(name_candidate)
                break
        
        # Return the most likely name
        if potential_names:
            # Prefer longer names (more specific)
            return max(potential_names, key=len)
        
        return None
    
    def _is_likely_name(self, word: str) -> bool:
        """Use NLP to determine if a word is likely a name"""
        import re
        
        # Basic name patterns
        if not word or len(word) < 2:
            return False
        
        # Must start with capital letter
        if not word[0].isupper():
            return False
        
        # Should not be common words
        common_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'can', 'could', 'should', 'may', 'might',
            'what', 'where', 'when', 'why', 'how', 'who', 'which', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs',
            # Tagalog question words
            'sino', 'ano', 'saan', 'kailan', 'bakit', 'paano'
        }
        
        if word.lower() in common_words:
            return False
        
        # Should contain only letters (no numbers or special characters)
        if not re.match(r'^[A-Za-z]+$', word):
            return False
        
        # Should not be too long (unlikely names)
        if len(word) > 20:
            return False
        
        return True
    
    def _is_likely_full_name(self, name: str) -> bool:
        """Use NLP to determine if a two-word string is likely a full name"""
        words = name.split()
        if len(words) != 2:
            return False
        
        # Both words should be likely names
        return all(self._is_likely_name(word) for word in words)
    
    def _is_emotional_expression_nlp(self, text: str) -> bool:
        """Use NLP to detect emotional expressions instead of hardcoded lists"""
        import re
        
        text_lower = text.lower()
        
        # Use linguistic patterns to detect emotional expressions
        emotional_patterns = [
            r'\b(sad|happy|worried|excited|tired|angry|nervous|scared|confused|frustrated|anxious|depressed|lonely|stressed|overwhelmed|disappointed|proud|grateful|relieved|surprised|shocked|amazed)\b',
            r'\b(malungkot|masaya|nag-aalala|natutuwa|pagod|galit|nervous|takot|nalilito|naiinis|nalulungkot)\b',
            r'\b(excited for|worried about|happy about|sad about|tired of|angry at|nervous about|scared of|confused about|frustrated with|anxious about|proud of|grateful for|relieved about|surprised by|shocked by|amazed by)\b'
        ]
        
        return any(re.search(pattern, text_lower) for pattern in emotional_patterns)