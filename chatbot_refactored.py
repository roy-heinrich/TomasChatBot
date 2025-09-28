"""
Refactored ChatBot - Clean, Modular, and Fixed
Main chatbot class with all underlying issues resolved
"""
import os
import logging
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our clean modules
from core.database_search import DatabaseSearchEngine
from core.language_detector import LanguageDetector
from core.response_generator import ResponseGenerator
from core.keyword_matcher import KeywordMatcher
from core.conversation_memory import ConversationMemory

# Import existing modules
from nlu_engine import NLUEngine, Intent, NLUResult
from entity_extractor import AdvancedEntityExtractor, ExtractedEntity

logger = logging.getLogger(__name__)

@dataclass
class ChatResponse:
    """Clean response structure"""
    response: List[str]  # Can be single message or split messages
    entities: List[Dict[str, Any]]
    detected_language: str
    language_confidence: float
    is_split: bool
    message_count: int
    intent: Optional[str] = None  # Add intent field

class ChatBot:
    """Clean, refactored chatbot with fixed underlying issues"""
    
    def __init__(self, groq_key: str):
        # Initialize core components
        self.language_detector = LanguageDetector()
        self.response_generator = ResponseGenerator(groq_key)
        self.keyword_matcher = KeywordMatcher()
        
        # Initialize database search
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        self.database_search = DatabaseSearchEngine(supabase_url, supabase_key)
        
        # Initialize NLP components
        self.nlu_engine = NLUEngine()
        self.entity_extractor = AdvancedEntityExtractor()
        
        # Initialize conversation memory
        self.conversation_memory = ConversationMemory()
        
        # Initialize context-aware translation
        from core.context_translator import ContextTranslator
        self.context_translator = ContextTranslator()
        
        logger.info("✅ ChatBot initialized with clean, modular architecture")
    
    def _extract_user_name(self, conversation_history: List[Dict]) -> str:
        """Extract user name from conversation history using NLP entity extraction"""
        for msg in reversed(conversation_history):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                # Use the entity extractor to find PERSON entities
                entities = self.entity_extractor.extract_entities(content)
                
                # Look for PERSON entities that could be names
                for entity in entities:
                    if entity.entity_type == "PERSON" and entity.confidence > 0.7:
                        # Clean up the name (remove punctuation, capitalize properly)
                        name = ''.join(c for c in entity.value if c.isalnum() or c.isspace()).strip()
                        if name and len(name) > 1 and len(name) < 50:  # Reasonable name length
                            return name.title()
                
                # Use the NLU engine's NLP-based name extraction for better accuracy
                extracted_name = self.nlu_engine._extract_name_using_nlp(content, "name_introduction")
                if extracted_name:
                    return extracted_name
        return ""
    
    def _extract_child_name(self, conversation_history: List[Dict]) -> str:
        """Extract child name from conversation history"""
        for msg in reversed(conversation_history):
            if msg.get("role") == "user":
                content = msg.get("content", "").lower()
                # Look for child name patterns
                if "my child" in content or "anak ko" in content or "child's name" in content:
                    # Extract child name
                    parts = content.split()
                    for i, part in enumerate(parts):
                        if part in ["child", "anak"] and i + 1 < len(parts):
                            return parts[i + 1].title()
        return ""
    
    def _detect_context_language(self, conversation_history: List[Dict]) -> Tuple[str, float]:
        """Detect language based on conversation context"""
        try:
            if not conversation_history:
                return "en", 0.5
            
            # Analyze recent messages for language patterns
            recent_messages = conversation_history[-3:]  # Last 3 messages
            language_scores = {"en": 0.0, "tl": 0.0, "akl": 0.0}
            
            for msg in recent_messages:
                if msg.get("role") == "user":
                    content = msg.get("content", "")
                    if content:
                        # Use enhanced language detection
                        lang, conf = self.language_detector.detect_language(content)
                        if lang in language_scores:
                            language_scores[lang] += conf
            
            # Get the language with highest score
            if any(score > 0 for score in language_scores.values()):
                best_lang = max(language_scores.items(), key=lambda x: x[1])
                return best_lang[0], min(best_lang[1], 0.9)
            else:
                return "en", 0.5
                
        except Exception as e:
            logger.error(f"Context language detection failed: {e}")
            return "en", 0.5
    
    async def chat(self, query: str, conversation_history: List[Dict] = None, 
                   user_timezone: str = None, session_id: str = None) -> ChatResponse:
        """Main chat method - Groq-first approach for natural responses"""
        try:
            # 1. Enhanced language detection with mixed-language support
            try:
                from multilingual_nlp import multilingual_nlp
                if multilingual_nlp:
                    lang_result = await multilingual_nlp.detect_language_semantic(query)
                    detected_lang = lang_result.language
                    confidence = lang_result.confidence
                    logger.info(f"🌍 Multilingual NLP detected: {detected_lang} (confidence: {confidence:.2f})")
                else:
                    raise ImportError("Multilingual NLP not available")
            except Exception as e:
                logger.warning(f"⚠️ Multilingual NLP language detection failed: {e}")
                # Enhanced fallback language detection
                detected_lang, confidence = self.language_detector.detect_language(query)
                logger.info(f"🌍 Enhanced language detection: {detected_lang} (confidence: {confidence:.2f})")
            
            # Check for mixed-language input
            if confidence < 0.7:
                logger.info("🔍 Low confidence language detection - may be mixed language")
                # Use context-aware translation for mixed languages
                if conversation_history:
                    context_lang, context_confidence = self._detect_context_language(conversation_history)
                    if context_confidence > confidence:
                        detected_lang = context_lang
                        confidence = context_confidence
                        logger.info(f"🌍 Context-based language detection: {detected_lang} (confidence: {confidence:.2f})")
            
            # 2. Get NLU analysis for intent
            nlu_result = await self.nlu_engine.analyze_intent(query)
            
            # 3. Enhanced entity extraction with relationships
            entities = self.entity_extractor.extract_entities(query, nlu_result.intent.value if nlu_result else None)
            logger.info(f"🔍 Enhanced entity extraction: {len(entities)} entities with relationships")
            
            # Log entity relationships
            for entity in entities:
                if hasattr(entity, 'relationships') and entity.relationships:
                    for rel in entity.relationships:
                        logger.info(f"🔗 Relationship: {entity.value} -> {rel['entity'].value} ({rel['relationship']['type']})")
            
            # 4. Enhanced memory system - extract user info and update memory
            user_name = ""
            child_name = ""
            if conversation_history:
                # Only extract names if NLU detects name introduction intent
                if nlu_result and nlu_result.intent.value in ['name_introduction', 'greeting_with_name']:
                    user_name = self._extract_user_name(conversation_history)
                    child_name = self._extract_child_name(conversation_history)
                    if user_name:
                        logger.info(f"🔍 Extracted names: user='{user_name}', child='{child_name}'")
                else:
                    logger.info(f"🔍 Skipping name extraction - intent is '{nlu_result.intent.value if nlu_result else 'unknown'}'")
            
            # Update conversation memory
            if session_id:
                user_memory = self.conversation_memory.update_user_memory(
                    session_id, user_name, query, conversation_history
                )
                logger.info(f"🧠 Updated memory for user: {user_memory.name}, topics: {list(user_memory.topics.keys())}")
            
            # 🚨 CRITICAL: Check for special intents FIRST before database search
            # These intents should skip database search entirely
            if nlu_result and nlu_result.intent.value == 'contact_escalation':
                logger.info("👥 Contact escalation requested - skipping database search, using helpful approach")
                # Skip database search entirely for contact escalation
                # Use the new helpful approach: ask about other school topics first
                search_results = []
                best_result = None
            else:
                # 3. Perform database search to get context for Groq
                search_results = self.database_search.search_prompts(query, limit=10)
                logger.info(f"🔍 Found {len(search_results)} search results")
                
                # 4. Select best result for context
                best_result = None
                if search_results:
                    best_result = self.database_search.select_best_result(search_results, query)
                    logger.info(f"🏆 Selected: {best_result['keywords'] if best_result else 'None'}")
                else:
                    logger.info("❌ No search results found")
            
            # 5. Generate response using Groq with enhanced context
            if nlu_result and nlu_result.intent.value == 'contact_escalation':
                # For contact escalation, use the helpful approach context
                logger.info("🤖 Using helpful approach for contact escalation")
                context = "User wants to talk to someone from the school - use helpful approach to suggest other school topics first before offering contact escalation"
            elif best_result:
                logger.info("📚 Using database context for Groq response")
                # Provide database information as context but let Groq expand naturally
                context = f"Database Information: {best_result['response']}"
            else:
                # Use Groq for intelligent responses when no database context, but with strict safeguards
                logger.info("🤖 No database context found - using Groq for intelligent response with safeguards")
                context = "CRITICAL: NO DATABASE INFORMATION AVAILABLE. You MUST respond that you don't have the specific information requested. Ask if they want to talk to a school admin - if yes, provide the Facebook link: https://web.facebook.com/114901Tomas. If no, ask what else they want to know about the school. DO NOT make up, invent, or hallucinate any information about teachers, staff names, schedules, or school policies. DO NOT provide specific teacher names, subjects, or any details not in your database. Be honest about your limitations."
            
            # Add personalized memory context
            if session_id:
                memory_context = self.conversation_memory.get_conversation_context(session_id, user_name)
                if memory_context:
                    context += f"\n\nPersonal Context: {memory_context}"
                    logger.info(f"🧠 Added memory context: {memory_context}")
                
                # Check if this is a greeting/returning user
                if any(word in query.lower() for word in ["hi", "hello", "hey", "kumusta", "kamusta"]):
                    personalized_greeting = self.conversation_memory.get_personalized_greeting(session_id, user_name)
                    if personalized_greeting:
                        context += f"\n\nPersonalized Greeting: {personalized_greeting}"
                        logger.info(f"👋 Added personalized greeting: {personalized_greeting}")
            
            # Get NLU info for better context (already analyzed above)
            nlu_info = {
                'intent': nlu_result.intent.value if nlu_result else 'unknown',
                'confidence': nlu_result.confidence if nlu_result else 0.0,
                'entities': [(e.entity_type, e.value) for e in entities]
            }
            
            # 🚨 CRITICAL FIX: Only catch obvious gibberish - let NLP/NLU handle everything else
            is_gibberish = self._detect_gibberish_input(query, nlu_result, entities, detected_lang, confidence)
            
            if is_gibberish:
                logger.info("🚫 Obvious gibberish detected - using fallback response")
                return await self._create_fallback_response(query, detected_lang, confidence, session_id)
            
            # 🚨 FIX: Handle name introductions and greeting with name even without database context
            if nlu_result and nlu_result.intent.value in ['name_introduction', 'greeting_with_name']:
                logger.info(f"👋 {nlu_result.intent.value} detected - handling with Groq even without database context")
                # For name introductions, we don't need database context
                context = "User is introducing themselves with their name"
            elif nlu_result and nlu_result.intent.value == 'emotional_expression':
                logger.info(f"😊 {nlu_result.intent.value} detected - handling emotional expression")
                # For emotional expressions, provide empathetic response
                context = "User is expressing their emotional state"
            elif nlu_result and nlu_result.intent.value == 'appreciation':
                logger.info(f"🙏 {nlu_result.intent.value} detected - handling appreciation/thanks")
                # For appreciation/thanks, provide friendly acknowledgment
                context = "User is expressing appreciation or thanks"
            elif nlu_result and nlu_result.intent.value == 'greeting_simple':
                logger.info(f"👋 {nlu_result.intent.value} detected - handling simple greeting")
                # For simple greetings, provide friendly response
                context = "User is giving a simple greeting"
            elif nlu_result and nlu_result.intent.value == 'medical_emergency':
                logger.info(f"🚨 {nlu_result.intent.value} detected - handling medical emergency")
                # For medical emergencies, provide immediate emergency response
                context = "MEDICAL EMERGENCY DETECTED - User is experiencing a medical emergency requiring immediate attention"
            elif nlu_result and nlu_result.intent.value == 'contact_escalation':
                logger.info(f"👥 {nlu_result.intent.value} detected - using helpful approach first")
                # For contact escalation, use helpful approach: ask about other school topics first
                context = "User wants to talk to someone from the school - use helpful approach to suggest other school topics first before offering contact escalation"
            # Remove the old fallback logic - let Groq handle all cases intelligently
            
            # Generate response with Groq (professional, factual, humane, jolly, no roleplay)
            # Pass enhanced NLP/NLU information for better response generation
            nlu_info_dict = {
                'intent': nlu_result.intent.value if nlu_result and nlu_result.intent else 'unknown',
                'confidence': nlu_result.confidence if nlu_result else 0.0
            } if nlu_result else None
            
            response_text = await self.response_generator.generate_response(
                query, context, detected_lang, conversation_history, nlu_info_dict, user_name, entities, confidence
            )
            
            # Apply context-aware translation if needed
            if detected_lang != "en" and confidence < 0.8:
                logger.info("🌐 Applying context-aware translation")
                translated_response, translation_confidence = self.context_translator.translate_with_context(
                    response_text, detected_lang, conversation_history, session_id
                )
                if translation_confidence > 0.7:
                    response_text = translated_response
                    logger.info(f"🌐 Context-aware translation applied (confidence: {translation_confidence:.2f})")
            
            # 6. Split long responses if needed
            split_messages = self.response_generator.split_long_response(response_text)
            
            return ChatResponse(
                response=split_messages,
                entities=[{"entity_type": e.entity_type, "value": e.value, "confidence": e.confidence} for e in entities],
                detected_language=detected_lang,
                language_confidence=confidence,
                is_split=len(split_messages) > 1,
                message_count=len(split_messages),
                intent=nlu_result.intent.value if nlu_result and nlu_result.intent else 'unknown'
            )
            
        except Exception as e:
            logger.error(f"❌ Chat error: {e}")
            # Only use keyword matching as fallback for errors
            try:
                keyword_response = self.keyword_matcher.find_match(query, detected_lang if 'detected_lang' in locals() else "en")
                if keyword_response:
                    logger.info("🔄 Using keyword fallback due to error")
                    return self._create_response(keyword_response, entities if 'entities' in locals() else [], detected_lang if 'detected_lang' in locals() else "en", confidence if 'confidence' in locals() else 0.5)
            except:
                pass
            
            return self._create_error_response(detected_lang if 'detected_lang' in locals() else "en")
    
    def _create_response(self, response_text: str, entities: List[ExtractedEntity], 
                        detected_lang: str, confidence: float) -> ChatResponse:
        """Create a ChatResponse object"""
        split_messages = self.response_generator.split_long_response(response_text)
        
        return ChatResponse(
            response=split_messages,
            entities=[{"entity_type": e.entity_type, "value": e.value, "confidence": e.confidence} for e in entities],
            detected_language=detected_lang,
            language_confidence=confidence,
            is_split=len(split_messages) > 1,
            message_count=len(split_messages),
            intent='keyword_match'
        )
    
    async def _create_no_information_response(self, query: str, detected_lang: str, confidence: float, nlu_result, entities: List, session_id: str = None) -> ChatResponse:
        """Create structured response when no database information is found"""
        
        # Analyze the query using NLP/NLU to understand what the user is asking about
        query_lower = query.lower().strip()
        
        # Determine the topic/subject of the query using NLP analysis
        topic_keywords = {
            'enrollment': ['enrollment', 'enroll', 'admission', 'register', 'registration', 'apply', 'application'],
            'schedule': ['schedule', 'time', 'when', 'hours', 'class', 'period', 'timetable'],
            'location': ['where', 'location', 'address', 'place', 'find', 'directions'],
            'contact': ['contact', 'phone', 'number', 'email', 'reach', 'call'],
            'academic': ['grade', 'subject', 'course', 'curriculum', 'study', 'learning'],
            'services': ['service', 'help', 'support', 'assistance', 'guidance', 'counselor'],
            'general': ['information', 'about', 'tell', 'know', 'question']
        }
        
        # Use NLU intent to better understand the query
        detected_topic = 'general'
        if nlu_result and nlu_result.intent:
            intent = nlu_result.intent.value
            if intent in ['question', 'information_request']:
                # Analyze the query content to determine topic
                for topic, keywords in topic_keywords.items():
                    if any(keyword in query_lower for keyword in keywords):
                        detected_topic = topic
                        break
        
        # Generate appropriate response based on detected language and topic
        if detected_lang in ['tl', 'akl']:  # Tagalog/Aklanon
            if detected_topic == 'enrollment':
                response_text = "Paumanhin, wala akong impormasyon tungkol sa enrollment. Mas mabuti kung makipag-ugnayan kayo sa school office para sa mas tiyak na kasagutan."
            elif detected_topic == 'schedule':
                response_text = "Paumanhin, wala akong impormasyon tungkol sa schedule na ito. Mas mabuti kung makipag-ugnayan kayo sa school office para sa mas tiyak na kasagutan."
            elif detected_topic == 'location':
                response_text = "Paumanhin, wala akong impormasyon tungkol sa lokasyon na ito. Mas mabuti kung makipag-ugnayan kayo sa school office para sa mas tiyak na kasagutan."
            elif detected_topic == 'contact':
                response_text = "Paumanhin, wala akong impormasyon tungkol sa contact na ito. Mas mabuti kung makipag-ugnayan kayo sa school office para sa mas tiyak na kasagutan."
            elif detected_topic == 'academic':
                response_text = "Paumanhin, wala akong impormasyon tungkol sa academic na ito. Mas mabuti kung makipag-ugnayan kayo sa school office para sa mas tiyak na kasagutan."
            elif detected_topic == 'services':
                response_text = "Paumanhin, wala akong impormasyon tungkol sa serbisyo na ito. Mas mabuti kung makipag-ugnayan kayo sa school office para sa mas tiyak na kasagutan."
            else:
                response_text = "Paumanhin, wala akong impormasyon tungkol sa inyong tanong. Mas mabuti kung makipag-ugnayan kayo sa school office para sa mas tiyak na kasagutan."
        else:  # English
            if detected_topic == 'enrollment':
                response_text = "I couldn't find any information about enrollment. It would be best if you can contact the school office to better cater your question."
            elif detected_topic == 'schedule':
                response_text = "I couldn't find any information about this schedule. It would be best if you can contact the school office to better cater your question."
            elif detected_topic == 'location':
                response_text = "I couldn't find any information about this location. It would be best if you can contact the school office to better cater your question."
            elif detected_topic == 'contact':
                response_text = "I couldn't find any information about this contact. It would be best if you can contact the school office to better cater your question."
            elif detected_topic == 'academic':
                response_text = "I couldn't find any information about this academic matter. It would be best if you can contact the school office to better cater your question."
            elif detected_topic == 'services':
                response_text = "I couldn't find any information about this service. It would be best if you can contact the school office to better cater your question."
            else:
                response_text = "I couldn't find any information about your question. It would be best if you can contact the school office to better cater your question."
        
        # Split long responses if needed
        split_messages = self.response_generator.split_long_response(response_text)
        
        return ChatResponse(
            response=split_messages,
            entities=[{"entity_type": e.entity_type, "value": e.value, "confidence": e.confidence} for e in entities],
            detected_language=detected_lang,
            language_confidence=confidence,
            is_split=len(split_messages) > 1,
            message_count=len(split_messages),
            intent='no_information_found'
        )

    async def _create_fallback_response(self, query: str, detected_lang: str, confidence: float, session_id: str = None) -> ChatResponse:
        """Create fallback response using Groq - no hardcoded responses"""
        
        # Use Groq to handle the query gracefully instead of hardcoded responses
        context = "User has sent a message that may be unclear or unusual. Respond helpfully and ask for clarification if needed."
        
        # Get user name for personalization
        user_name = ""
        if session_id:
            user_name = self.conversation_memory.get_user_name(session_id)
        
        try:
            # Use Groq to generate a helpful response
            response_text = await self.response_generator.generate_response(
                query, context, detected_lang, [], None, user_name, [], confidence
            )
            
            # Split long responses if needed
            split_messages = self.response_generator.split_long_response(response_text)
            
            return ChatResponse(
                response=split_messages,
                entities=[],
                detected_language=detected_lang,
                language_confidence=confidence,
                is_split=len(split_messages) > 1,
                message_count=len(split_messages),
                intent='fallback'
            )
        except Exception as e:
            logger.error(f"❌ Error in fallback response generation: {e}")
            # Only use this as absolute last resort
            if detected_lang == "tl" or detected_lang == "akl":
                fallback_text = "Paumanhin, hindi ko maintindihan ang inyong tanong. Maaari ba ninyong ulitin ito sa ibang paraan?"
            else:
                fallback_text = "I'm sorry, I didn't quite understand that. Could you please rephrase your question?"
            
            return ChatResponse(
                response=[fallback_text],
                entities=[],
            detected_language=detected_lang,
            language_confidence=confidence,
            is_split=False,
            message_count=1,
                intent='fallback'
        )
    
    def _create_error_response(self, detected_lang: str) -> ChatResponse:
        """Create error response"""
        if detected_lang == "tl" or detected_lang == "akl":
            error_text = "Paumanhin, may problema sa pagproseso ng inyong tanong. Subukan ninyo ulit mamaya."
        else:
            error_text = "Sorry, there was a problem processing your question. Please try again later."
        
        return ChatResponse(
            response=[error_text],
            entities=[],
            detected_language=detected_lang,
            language_confidence=0.5,
            is_split=False,
            message_count=1,
            intent='error'
        )
    
    def _detect_gibberish_input(self, query: str, nlu_result, entities: List, detected_lang: str, confidence: float) -> bool:
        """
        Very lenient gibberish detection - trust NLU/NLP systems to handle most cases
        Only catch extremely obvious gibberish patterns
        """
        # 🚨 CRITICAL: Trust the NLU system - if it has any confidence, let it handle the input
        if nlu_result and nlu_result.confidence > 0.05:  # Very low threshold - trust NLU
            logger.info(f"✅ NLU has confidence {nlu_result.confidence:.3f} - not gibberish")
            return False
        
        # Only catch extremely obvious patterns
        query_lower = query.lower().strip()
        
        # Check for extremely obvious gibberish patterns
        if len(query) > 15:  # Only check very long strings
            # Count consecutive consonants - only flag if more than 8 consecutive consonants
            consecutive_consonants = 0
            max_consecutive = 0
            vowels = set('aeiou')
            
            for char in query_lower:
                if char.isalpha():
                    if char not in vowels:
                        consecutive_consonants += 1
                        max_consecutive = max(max_consecutive, consecutive_consonants)
                    else:
                        consecutive_consonants = 0
            
            if max_consecutive >= 8:  # Very strict - only obvious gibberish
                logger.info(f"🔍 Obvious gibberish pattern detected: {max_consecutive} consecutive consonants")
                return True
        
        # Check for patterns that are clearly not human language
        obvious_gibberish_patterns = [
            "qwertyuiop", "asdfghjkl", "zxcvbnm",  # Keyboard patterns
            "aaaaaaaa", "bbbbbbbb", "cccccccc",    # Repeated single characters
            "123456789", "abcdefgh",               # Sequential patterns
        ]
        
        for pattern in obvious_gibberish_patterns:
            if pattern in query_lower:
                logger.info(f"🔍 Obvious gibberish pattern detected: '{pattern}'")
                return True
        
        # If we get here, it's not gibberish - let Groq handle it with NLP/NLU
        logger.info("✅ Input passed gibberish detection - using Groq with NLP/NLU processing")
        return False
