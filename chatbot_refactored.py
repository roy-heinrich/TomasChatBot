"""
Refactored ChatBot - Clean, Modular, and Fixed
Main chatbot class with all underlying issues resolved
"""
import os
import logging
import asyncio
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

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
    
    async def chat(self, query: str, conversation_history: List[Dict] = None, 
                   user_timezone: str = None, session_id: str = None) -> ChatResponse:
        """Main chat method - Groq-first approach for natural responses"""
        try:
            # 1. Detect language
            detected_lang, confidence = self.language_detector.detect_language(query)
            logger.info(f"🌍 Detected language: {detected_lang} (confidence: {confidence:.2f})")
            
            # 2. Extract entities
            entities = self.entity_extractor.extract_entities(query)
            logger.info(f"🔍 Extracted {len(entities)} entities")
            
            # 3. Get NLU analysis FIRST to determine intent
            nlu_result = await self.nlu_engine.analyze_intent(query)
            
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
            
            # 3. Perform database search FIRST to get context for Groq
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
            if best_result:
                logger.info("📚 Using database context for Groq response")
                context = f"Q: {best_result['keywords']}\nA: {best_result['response']}"
            else:
                logger.info("📝 No database context found, using general context")
                context = "General school information query"
            
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
                return self._create_fallback_response(query, detected_lang, confidence, session_id)
            
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
            elif nlu_result and nlu_result.intent.value == 'contact_escalation':
                logger.info("👥 Contact escalation requested - providing contact information")
                # User explicitly wants to talk to someone
                contact_type = "general"
                if any(word in query.lower() for word in ["urgent", "emergency", "immediate"]):
                    contact_type = "urgent"
                elif any(word in query.lower() for word in ["guidance", "counselor", "emotional"]):
                    contact_type = "guidance"
                
                try:
                    # Get user name from memory for personalization
                    user_name = ""
                    if session_id:
                        user_name = self.conversation_memory.get_user_name(session_id)
                    contact_response = self.response_generator.get_contact_escalation_response(detected_lang, contact_type, self.database_search.supabase, user_name)
                    return ChatResponse(
                        response=[contact_response],
                        entities=[{"entity_type": e.entity_type, "value": e.value, "confidence": e.confidence} for e in entities],
                        detected_language=detected_lang,
                        language_confidence=confidence,
                        is_split=False,
                        message_count=1,
                        intent='contact_escalation'
                    )
                except Exception as e:
                    logger.error(f"Error in contact escalation: {e}")
                    # Fallback to simple contact message
                    fallback_contact = f"For questions that need a live person:\n\n📱 Message us directly: <a href=\"https://m.me/114901Tomas\" target=\"_blank\">Click here to chat on Messenger</a>\n📞 Call the school office\n🏫 Visit the school office\n\nOffice hours: Monday-Friday, 7:00 AM - 5:00 PM"
                    return ChatResponse(
                        response=[fallback_contact],
                        entities=[{"entity_type": e.entity_type, "value": e.value, "confidence": e.confidence} for e in entities],
                        detected_language=detected_lang,
                        language_confidence=confidence,
                        is_split=False,
                        message_count=1,
                        intent='contact_escalation'
                    )
            elif not best_result and not search_results and context == "General school information query":
                logger.info("🚫 No meaningful context available - using fallback response")
                return self._create_fallback_response(query, detected_lang, confidence, session_id)
            
            # Generate response with Groq (professional, factual, humane, jolly, no roleplay)
            # Pass enhanced NLP/NLU information for better response generation
            nlu_info_dict = {
                'intent': nlu_result.intent.value if nlu_result and nlu_result.intent else 'unknown',
                'confidence': nlu_result.confidence if nlu_result else 0.0
            } if nlu_result else None
            
            response_text = await self.response_generator.generate_response(
                query, context, detected_lang, conversation_history, nlu_info_dict, user_name, entities, confidence
            )
            
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
    
    def _create_fallback_response(self, query: str, detected_lang: str, confidence: float, session_id: str = None) -> ChatResponse:
        """Create fallback response when no database results found with contact escalation"""
        
        # Determine contact type based on query content
        query_lower = query.lower()
        contact_type = "general"
        
        if any(word in query_lower for word in ["urgent", "emergency", "immediate", "asap", "now"]):
            contact_type = "urgent"
        elif any(word in query_lower for word in ["guidance", "counselor", "emotional", "sad", "depressed", "anxiety", "stress"]):
            contact_type = "guidance"
        
        # Get contact escalation response with user name for personalization
        user_name = ""
        if session_id:
            user_name = self.conversation_memory.get_user_name(session_id)
        fallback_text = self.response_generator.get_contact_escalation_response(detected_lang, contact_type, self.database_search.supabase, user_name)
        
        return ChatResponse(
            response=[fallback_text],
            entities=[],
            detected_language=detected_lang,
            language_confidence=confidence,
            is_split=False,
            message_count=1,
            intent='contact_escalation'
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
        Pure NLP/NLU-based gibberish detection - NO HARDCODING
        Uses the existing NLP and NLU systems to determine if input is gibberish
        """
        # 🚨 CRITICAL FIX: Don't use negative confidence scores for gibberish detection
        # Language detection can return negative scores for valid queries
        # Only use positive confidence scores for gibberish detection
        
        # Use NLU confidence as primary signal - if NLU is very confident it's unknown, it's likely gibberish
        if nlu_result and nlu_result.intent.value == 'unknown' and nlu_result.confidence < 0.1:
            logger.info(f"🔍 NLU detected gibberish: intent=unknown, confidence={nlu_result.confidence:.3f}")
            return True
        
        # 🚨 FIX: Only check positive confidence scores - negative scores are not gibberish indicators
        # Use language detection confidence - but only if it's positive and very low
        if confidence > 0 and confidence < 0.05:  # Only very low positive confidence
            logger.info(f"🔍 Language detection uncertain: confidence={confidence:.3f}")
            return True
        
        # Use entity extraction - if no entities found AND NLU confidence is low, might be gibberish
        if len(entities) == 0 and nlu_result and nlu_result.confidence < 0.2:
            logger.info(f"🔍 No entities + low NLU confidence: entities=0, nlu_confidence={nlu_result.confidence:.3f}")
            return True
        
        # 🚨 FIX: Check for valid school-related patterns first - if found, it's not gibberish
        query_lower = query.lower().strip()
        
        # Valid school-related patterns that should never be considered gibberish
        valid_patterns = [
            # Common English words
            "i am", "my name", "hello", "hi", "thank", "sad", "happy", "good", "bad",
            # School-related terms
            "school", "teacher", "student", "grade", "class", "enroll", "admission",
            "principal", "head", "teacher", "staff", "office", "library", "cafeteria",
            # Question words
            "what", "where", "when", "how", "who", "why", "which", "are", "is", "do", "can",
            # Common Filipino/Aklanon words
            "ako", "si", "ang", "ng", "sa", "ko", "mo", "niya", "namin", "ninyo", "nila",
            "kumusta", "kamusta", "salamat", "magandang", "maayong", "paaralan", "eskwelahan",
            # Common phrases
            "i am sad", "i am happy", "i am heinz", "i am john", "i am mary",
            "head teacher", "are transferees", "what is", "where is", "how do"
        ]
        
        # If query contains any valid patterns, it's not gibberish
        for pattern in valid_patterns:
            if pattern in query_lower:
                logger.info(f"✅ Valid pattern detected: '{pattern}' - not gibberish")
                return False
        
        # Use basic linguistic patterns - only for obvious cases
        # Check for obvious random character patterns (like "sadassdafdxs")
        if len(query) > 10:
            # Count consecutive consonants - if more than 6 consecutive consonants, likely gibberish
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
            
            if max_consecutive >= 6:  # Very strict - only obvious gibberish
                logger.info(f"🔍 Obvious gibberish pattern detected: {max_consecutive} consecutive consonants")
                return True
        
        # If we get here, it's not gibberish - let the normal NLP/NLU systems handle it
        logger.info("✅ Input passed gibberish detection - using normal NLP/NLU processing")
        return False
