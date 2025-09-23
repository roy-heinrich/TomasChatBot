"""
Response Generation Module - Fixed
Handles response generation with proper language support
"""
import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """Fixed response generator with proper language handling"""
    
    def __init__(self, groq_key: str):
        self.groq_key = groq_key
        self.groq_client = None
        
        if not groq_key:
            logger.warning("Groq API key not provided")
            return
            
        try:
            from groq import Groq
            self.groq_client = Groq(api_key=groq_key)
            logger.info("✅ Groq client initialized successfully")
        except ImportError as e:
            logger.error(f"❌ Groq library not installed: {e}")
            logger.warning("Install with: pip install groq")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Groq client: {e}")
            logger.warning("Check your GROQ_API_KEY environment variable")
    
    def get_system_prompt(self, lang: str, user_name: str = "", nlu_info: Dict = None) -> str:
        """Generate language-specific system prompt with explicit tone instructions"""
        time_context = self._get_time_context()
        name_context = f" Ang kausap mo ay si {user_name}." if user_name and lang == "tl" else f" The person you're talking to is named {user_name}." if user_name else ""
        
        nlu_context = ""
        if nlu_info:
            nlu_context = f" NLU Intent: {nlu_info.get('intent', 'unknown')} (confidence: {nlu_info.get('confidence', 0.0):.2f})."
        
        if lang == "tl" or lang == "akl":
            return f"Ikaw si TOMAS, ang propesyonal na digital assistant ng Tomas SM. Bautista Elementary School. {time_context}{name_context}{nlu_context} MAHALAGA: SUMAGOT LAMANG SA TAGALOG/FILIPINO. TONE: Maging propesyonal, factual, at humane na may kaunting kasiyahan. HUWAG mag-roleplay o magdagdag ng emosyon. Magbigay ng tumpak at factual na impormasyon sa isang mapagkakatiwalaan at propesyonal na paraan. Maging mabait at kaunting masaya ngunit panatilihin ang propesyonalismo. KAPANSIN-PANSIN: Ang context na ibinigay ay naglalaman ng EKSAKTONG SAGOT mula sa aming school database. Ang inyong trabaho ay ipakita ang impormasyong ito nang malinaw at propesyonal habang pinapanatili ang lahat ng katotohanan. HUWAG baguhin ang mga katotohanan, numero, o pangunahing impormasyon. HUWAG magdagdag ng personal na opinyon, emosyon, o roleplay."
        else:
            return f"You are TOMAS, the professional digital assistant for Tomas SM. Bautista Elementary School. {time_context}{name_context}{nlu_context} IMPORTANT: RESPOND ONLY IN ENGLISH. TONE: Be professional, factual, and humane with a touch of cheerfulness. NO roleplay or added emotions. Provide accurate, factual information in a helpful and professional manner. Be friendly and slightly cheerful but maintain professionalism. CRITICAL: The context provided contains the EXACT ANSWER from our school database. Your job is to present this information clearly and professionally while keeping all facts unchanged. DO NOT change facts, numbers, or core information. DO NOT add personal opinions, emotions, or roleplay."
    
    def _get_time_context(self) -> str:
        """Get time-aware context for responses"""
        from datetime import datetime
        now = datetime.now()
        hour = now.hour
        
        if 5 <= hour < 12:
            return "Good morning! "
        elif 12 <= hour < 17:
            return "Good afternoon! "
        else:
            return "Good evening! "
    
    async def generate_response(self, query: str, context: str, lang: str, 
                              conversation_history: List[Dict] = None, 
                              nlu_info: Dict = None) -> str:
        """Generate response using Groq with proper language handling"""
        if not self.groq_client:
            return self._get_fallback_response(lang)
        
        try:
            system_prompt = self.get_system_prompt(lang, "", nlu_info)
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if provided
            if conversation_history:
                recent_history = conversation_history[-8:]  # Limit to last 8 messages
                for msg in recent_history:
                    messages.append({
                        "role": "user" if msg.get("role") == "user" else "assistant",
                        "content": msg.get("content", "")
                    })
            
            # Add current query with context
            user_message = f"Context: {context}\nQuestion: {query}" if context else query
            messages.append({"role": "user", "content": user_message})
            
            # Call Groq API with timeout
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                max_tokens=600,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.warning(f"Groq response generation failed: {e}")
            return self._get_fallback_response(lang)
    
    def _get_fallback_response(self, lang: str) -> str:
        """Get fallback response in appropriate language"""
        if lang == "tl" or lang == "akl":
            return "Paumanhin, may problema sa pagproseso ng inyong tanong. Subukan ninyo ulit mamaya."
        else:
            return "Sorry, there was a problem processing your question. Please try again later."
    
    def split_long_response(self, response: str, max_length: int = 250) -> List[str]:
        """Split long responses into multiple messages"""
        if len(response) <= max_length:
            return [response]
        
        # Split by sentences first
        sentences = response.split('. ')
        messages = []
        current_message = ""
        
        for sentence in sentences:
            if len(current_message + sentence) <= max_length:
                current_message += sentence + ". "
            else:
                if current_message:
                    messages.append(current_message.strip())
                current_message = sentence + ". "
        
        if current_message:
            messages.append(current_message.strip())
        
        return messages
