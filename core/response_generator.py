"""
Optimized Response Generation Module - Token-Efficient
Handles response generation with minimal system prompts
"""
import logging
import os
import re
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """
    Token-efficient response generator with minimal system prompts
    """
    
    def __init__(self, groq_key: str = None):
        # Initialize multi-provider AI system
        from core.ai_providers import MultiProviderAI
        self.multi_ai = MultiProviderAI()
        
        # Keep backward compatibility with Groq
        self.groq_key = groq_key
        self.groq_client = None
        
        if groq_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=groq_key)
                # logger.info("✅ Groq client initialized (legacy support)")  # Reduced for Railway
            except ImportError as e:
                logger.error(f"❌ Groq library not installed: {e}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Groq client: {e}")
        
        # Log available providers
        stats = self.multi_ai.get_provider_stats()
        # logger.info(f"🚀 Multi-provider AI initialized: {stats}")  # Reduced for Railway
        
        # Cache common responses
        self._fallback_cache = {
            "tl": "Paumanhin, may problema sa pagproseso. Subukan ulit mamaya.",
            "en": "Sorry, there was a problem. Please try again later."
        }
        
        self._messenger_button = '<a href="https://m.me/114901Tomas" target="_blank" style="display: inline-block; background-color: #0084ff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 10px 0;">📱 Messenger</a>'

    def get_system_prompt(self, lang: str, user_name: str = "", nlu_info: Dict = None, 
                         entities: List = None, confidence: float = 0.0) -> str:
        """Generate concise, focused system prompt"""
        time_context = self._get_time_context()
        name_context = f" User: {user_name}." if user_name else ""
        
        # Core instructions only - TOKEN EFFICIENT
        base_rules = """You are TOMAS, digital assistant for Tomas SM. Bautista Elementary School.

RULES:
1. Use ONLY database context - never invent data
2. No roleplay - you're an assistant
3. If no answer: offer admin contact
4. Stay school-focused
5. Medical emergency → 911
6. For lists: Use numbered format (1. Item 2. Item 3. Item)"""
        
        # Language-specific additions (keep minimal)
        lang_rules = self._get_lang_rules(lang)
        
        # Context hints (only if provided)
        context_hints = ""
        if nlu_info:
            context_hints = f"\nIntent: {nlu_info.get('intent')} ({nlu_info.get('confidence'):.2f})"
        if entities:
            context_hints += f"\nEntities: {', '.join(e.entity_type for e in entities[:3])}"
        
        return f"{time_context}{base_rules}{lang_rules}{context_hints}"
    
    def _get_lang_rules(self, lang: str) -> str:
        """Get minimal language-specific rules - TOKEN EFFICIENT"""
        if lang in ["tl", "akl"]:
            return "\nLANGUAGE: TAGALOG only. TONE: Warm, helpful school staff."
        else:
            return "\nLANGUAGE: ENGLISH only. TONE: Warm, helpful school staff."
    
    def _get_time_context(self) -> str:
        """Get time-aware context for responses - TOKEN EFFICIENT"""
        from datetime import datetime
        now = datetime.now()
        hour = now.hour
        
        if 5 <= hour < 12:
            return "Morning! "
        elif 12 <= hour < 17:
            return "Afternoon! "
        else:
            return "Evening! "
    
    def _build_concise_message(self, query: str, context: str, lang: str, nlu_info: Dict = None) -> str:
        """Build minimal, focused message"""
        
        # Handle special cases first
        if context == "User is introducing themselves with their name":
            return f"User introduced themselves: {query}\nRespond with friendly greeting using their name."
        
        if context == "User is expressing their emotional state":
            return f"User emotional: {query}\nAcknowledge briefly, redirect to school services."
        
        # Database context - the priority case
        if context and context not in ["General school information query", 
                                       "No specific information available in database for this query"]:
            lang_code = "TL" if lang in ["tl", "akl"] else "EN"
            
            if lang in ["tl", "akl"]:
                return f"""DATABASE: {context}

QUERY: {query}
LANG: {lang_code}

Use database info to answer directly. Be natural and helpful."""
            else:
                # Enhanced English context - conversational but token-efficient
                return f"""DATABASE: {context}

QUERY: {query}
LANG: {lang_code}

Use database info to answer directly. Be warm and conversational like a friendly school staff member. Add context about the person's role and offer additional help."""
        
        # No context available
        return f"QUERY: {query}\nNo database info. Ask what else they'd like to know, use NLU to suggest topics."
    
    async def generate_response(self, query: str, context: str, lang: str, 
                              conversation_history: List[Dict] = None, 
                              nlu_info: Dict = None, user_name: str = "", 
                              entities: List = None, confidence: float = 0.0, 
                              context_analysis: Dict = None) -> str:
        """Generate response using multi-provider AI system with intelligent fallback"""
        
        try:
            # Build the system prompt
            system_prompt = self.get_system_prompt(lang, user_name, nlu_info, entities, confidence)
            
            # Build concise user message
            user_message = self._build_concise_message(query, context, lang, nlu_info)
            
            # Optimized max_tokens - complete responses without waste
            max_tokens = 400 if lang in ["tl", "akl"] else 350
            
            # Use multi-provider AI system
            ai_response = await self.multi_ai.generate_response(
                prompt=user_message,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            if ai_response.success:
                # logger.info(f"✅ Response generated using {ai_response.provider} ({ai_response.model})")  # Reduced for Railway
                response = ai_response.content.strip()
                
                # Remove bold formatting and context annotations
                response = response.replace('**', '')
                response = response.replace('(context: academic)', '')
                response = response.replace('(context: staff)', '')
                response = response.replace('(context: general)', '')
                
                return response
            else:
                logger.warning(f"⚠️ Multi-provider AI failed: {ai_response.error}")
                return self._get_fallback_response(lang)
            
        except Exception as e:
            logger.error(f"❌ Response generation failed: {e}")
            return self._get_fallback_response(lang)
    
    def _get_fallback_response(self, lang: str) -> str:
        """Minimal fallback response"""
        if lang in ["tl", "akl"]:
            return "Paumanhin, hindi ko alam ang sagot sa tanong na ito. Makipag-ugnayan sa opisina ng paaralan para sa karagdagang impormasyon."
        else:
            return "I don't have that information. Please contact the school office for details."
    
    def split_long_response(self, response: str, max_length: int = 400) -> List[str]:
        """Enhanced response splitting that preserves numbering and formatting"""
        
        # Special case for messenger links
        if "m.me/" in response:
            max_length = 500
        
        if len(response) <= max_length:
            return [response]
        
        # Skip numbered list splitting for now - use regular text splitting
        # if re.search(r'\d+\.\s+', response):
        #     return self._split_numbered_list(response, max_length)
        
        # Use regex for faster splitting on sentences, but avoid splitting numbered lists
        # Split on sentence endings but not after numbers followed by periods
        # Enhanced splitting for long responses - bubble them properly
        if re.search(r'\d+\.\s+', response):
            # For numbered lists, ALWAYS split by complete numbered items
            sentences = self._split_numbered_list_smart(response, max_length)
        else:
            # Regular sentence splitting for non-numbered content
            sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', response)
        
        messages = []
        current = ""
        
        for sentence in sentences:
            if len(current) + len(sentence) + 1 <= max_length:
                current = f"{current} {sentence}".strip()
            else:
                if current:
                    messages.append(current)
                current = sentence if len(sentence) <= max_length else self._force_split(sentence, max_length)
        
        if current:
            messages.append(current)
        
        return messages
    
    def _split_numbered_list_smart(self, response: str, max_length: int) -> List[str]:
        """Simple splitting for numbered lists - each number gets its own bubble"""
        # Simple approach: split by numbered items
        parts = re.split(r'(?=\d+\.\s+)', response)
        
        messages = []
        for part in parts:
            if part.strip():
                messages.append(part.strip())
        
        return messages if messages else [response]
    
    def _split_numbered_list(self, response: str, max_length: int) -> List[str]:
        """Split numbered lists while preserving complete numbered items"""
        # Simple approach: split by double newlines or by numbered items
        # First, try to split by paragraphs (double newlines)
        paragraphs = response.split('\n\n')
        
        if len(paragraphs) > 1:
            # Split by paragraphs
            messages = []
            current = ""
            
            for paragraph in paragraphs:
                if not paragraph.strip():
                    continue
                    
                if current and len(current) + len(paragraph) + 2 > max_length:
                    messages.append(current.strip())
                    current = paragraph
                else:
                    if current:
                        current = f"{current}\n\n{paragraph}".strip()
                    else:
                        current = paragraph.strip()
            
            if current:
                messages.append(current)
            
            return messages
        
        # If no paragraph breaks, try to split by sentences but preserve numbering
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', response)
        
        messages = []
        current = ""
        
        for sentence in sentences:
            if len(current) + len(sentence) + 1 <= max_length:
                current = f"{current} {sentence}".strip()
            else:
                if current:
                    messages.append(current)
                current = sentence if len(sentence) <= max_length else self._force_split(sentence, max_length)
        
        if current:
            messages.append(current)
        
        return messages
    
    def _split_regular_text(self, response: str, max_length: int) -> List[str]:
        """Split regular text by sentences"""
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', response)
        
        messages = []
        current = ""
        
        for sentence in sentences:
            if len(current) + len(sentence) + 1 <= max_length:
                current = f"{current} {sentence}".strip()
            else:
                if current:
                    messages.append(current)
                current = sentence if len(sentence) <= max_length else self._force_split(sentence, max_length)
        
        if current:
            messages.append(current)
        
        return messages
    
    def _force_split(self, text: str, max_length: int) -> str:
        """Split oversized sentence at word boundary"""
        if len(text) <= max_length:
            return text
        
        split_point = text[:max_length].rfind(' ')
        return text[:split_point] + '.' if split_point > 0 else text[:max_length]