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
        
        logger.info("✅ ChatBot initialized with clean, modular architecture")
    
    def _extract_user_name(self, conversation_history: List[Dict]) -> str:
        """Extract user name from conversation history"""
        for msg in reversed(conversation_history):
            if msg.get("role") == "user":
                content = msg.get("content", "").lower()
                # Look for name introduction patterns
                if "i am" in content or "ako si" in content or "ang pangalan ko" in content:
                    # Extract name after introduction
                    parts = content.split()
                    for i, part in enumerate(parts):
                        if part in ["am", "si", "ko"] and i + 1 < len(parts):
                            return parts[i + 1].title()
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
            
            # 3. Perform database search FIRST to get context for Groq
            search_results = await self.database_search.search_prompts(query, limit=10)
            
            # 4. Select best result for context
            best_result = None
            if search_results:
                best_result = self.database_search.select_best_result(search_results, query)
            
            # 5. Generate response using Groq with database context
            if best_result:
                logger.info("📚 Using database context for Groq response")
                context = f"Q: {best_result['keywords']}\nA: {best_result['response']}"
            else:
                logger.info("📝 No database context found, using general context")
                context = "General school information query"
            
            # Get NLU info for better context
            nlu_result = await self.nlu_engine.analyze_intent(query)
            nlu_info = {
                'intent': nlu_result.intent.value if nlu_result else 'unknown',
                'confidence': nlu_result.confidence if nlu_result else 0.0,
                'entities': [(e.entity_type, e.value) for e in entities]
            }
            
            # Generate response with Groq (professional, factual, humane, jolly, no roleplay)
            response_text = await self.response_generator.generate_response(
                query, context, detected_lang, conversation_history, nlu_info
            )
            
            # 6. Split long responses if needed
            split_messages = self.response_generator.split_long_response(response_text)
            
            return ChatResponse(
                response=split_messages,
                entities=[{"entity_type": e.entity_type, "value": e.value, "confidence": e.confidence} for e in entities],
                detected_language=detected_lang,
                language_confidence=confidence,
                is_split=len(split_messages) > 1,
                message_count=len(split_messages)
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
            message_count=len(split_messages)
        )
    
    def _create_fallback_response(self, query: str, detected_lang: str, confidence: float) -> ChatResponse:
        """Create fallback response when no database results found"""
        if detected_lang == "tl" or detected_lang == "akl":
            fallback_text = "Paumanhin, hindi ko mahanap ang impormasyon na hinahanap ninyo. Maaari po kayong magpunta sa school office para sa dagdag na detalye."
        else:
            fallback_text = "I'm sorry, I couldn't find the information you're looking for. Please visit the school office for more details."
        
        return ChatResponse(
            response=[fallback_text],
            entities=[],
            detected_language=detected_lang,
            language_confidence=confidence,
            is_split=False,
            message_count=1
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
            message_count=1
        )
