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
2. If no database info: provide helpful response and offer to help with other school topics
3. Medical emergency → 911
4. For lists: Use numbered format (1. Item 2. Item 3. Item) - but NOT for years like 1960
5. Complete numbered lists - never cut off mid-sentence
6. NO HALLUCINATIONS: Only use information provided in database context
7. TONE: Be polite, professional, factual, and communicative - vary your responses naturally, use different sentence structures and openings, and offer additional help when appropriate
8. NO EXCESSIVE INTRODUCTIONS: Don't introduce yourself in every response
9. FORMAT NUMBERS PROPERLY: Write years like "1960" not "1 9 6 0" - keep numbers together
10. NO LINE BREAKS IN NUMBERS: Never put line breaks between digits in years or numbers"""
        
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
            return "\nLANGUAGE: TAGALOG ONLY. Use natural, grammatically correct Tagalog. Be conversational but professional."
        else:
            return "\nLANGUAGE: ENGLISH ONLY. Use ONLY English words. NO Tagalog words in response."
    
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
        """Build minimal, focused message with multi-question support"""
        
        # Handle multi-question context
        if nlu_info and nlu_info.get('is_multi_question'):
            question_number = nlu_info.get('question_number', 1)
            total_questions = nlu_info.get('total_questions', 1)
            
            if context and context not in ["General school information query", 
                                           "No specific information available in database for this query"]:
                lang_code = "TL" if lang in ["tl", "akl"] else "EN"
                
                if lang in ["tl", "akl"]:
                    return f"""DATABASE: {context}

QUERY: {query}
LANG: {lang_code}
MULTI-QUESTION: Question {question_number} of {total_questions}

CRITICAL: Use ONLY database info above. This is part of a multi-question session. Provide a natural, paragraph-style response that directly answers the question. Be polite, professional, factual, and communicative. Use proper Tagalog grammar. Don't introduce yourself. Format numbers properly: "1960" not "1 9 6 0". Write as a complete paragraph, not bullet points."""
                else:
                    return f"""DATABASE: {context}

QUERY: {query}
LANG: {lang_code}
MULTI-QUESTION: Question {question_number} of {total_questions}

Use ONLY English. Provide a natural, paragraph-style response that directly answers the question. This is part of a multi-question session. Be polite, professional, factual, and communicative. Don't introduce yourself. Format numbers properly: "1960" not "1 9 6 0". Write as a complete paragraph, not bullet points."""
            else:
                if lang in ["tl", "akl"]:
                    return f"QUERY: {query}\nMULTI-QUESTION: Question {question_number} of {total_questions}\nNo database info available. Provide helpful response in Tagalog. Answer concisely since this is part of multiple questions."
                else:
                    return f"QUERY: {query}\nMULTI-QUESTION: Question {question_number} of {total_questions}\nNo database info available. Provide helpful response in English. Answer concisely since this is part of multiple questions."
        
        # Handle special cases first
        if context == "User is introducing themselves with their name":
            return f"User introduced themselves: {query}\nRespond with friendly greeting using their name."
        
        if context == "User is expressing their emotional state":
            return f"User emotional: {query}\nAcknowledge briefly, redirect to school services."
        
        # Handle name requests - be direct and helpful
        if "pangalan" in query.lower() or "name" in query.lower():
            if lang in ["tl", "akl"]:
                return f"QUERY: {query}\nUser asking for their name. Respond in Tagalog that you don't have their name but can help with school info."
            else:
                return f"QUERY: {query}\nUser asking for their name. Respond in English that you don't have their name but can help with school info."
        
        # Database context - the priority case
        if context and context not in ["General school information query", 
                                       "No specific information available in database for this query"]:
            lang_code = "TL" if lang in ["tl", "akl"] else "EN"
            
            if lang in ["tl", "akl"]:
                return f"""DATABASE: {context}

QUERY: {query}
LANG: {lang_code}

CRITICAL: Use ONLY database info above. Do NOT invent staff names, positions, contacts, or stats. Answer exactly what database says. Use proper Tagalog grammar. Vary response format. Offer help (e.g. "Kung may iba pang katanungan..."). Don't introduce yourself. Format numbers properly: "1960" not "1 9 6 0"."""
            else:
                return f"""DATABASE: {context}

QUERY: {query}
LANG: {lang_code}

Use ONLY English. Answer directly. Be polite, professional, factual, communicative. Vary response format. Offer help (e.g. "Feel free to ask..."). Don't introduce yourself. Format numbers properly: "1960" not "1 9 6 0"."""
        
        # No context available
        if lang in ["tl", "akl"]:
            return f"QUERY: {query}\nNo database info available. Provide helpful response in Tagalog. Offer to help with other school topics."
        else:
            return f"QUERY: {query}\nNo database info available. Provide helpful response in {lang_code}. Offer to help with other school topics."
    
    async def generate_response(self, query: str, context: str, lang: str, 
                              conversation_history: List[Dict] = None, 
                              nlu_info: Dict = None, user_name: str = "", 
                              entities: List = None, confidence: float = 0.0, 
                              context_analysis: Dict = None, is_multi_question: bool = False, 
                              questions: List[str] = None) -> str:
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
                
                # Remove all context annotations (comprehensive)
                import re
                # Remove context annotations in various formats
                response = re.sub(r'\(context:\s*[^)]+\)', '', response, flags=re.IGNORECASE)
                response = re.sub(r'\[context:\s*[^\]]+\]', '', response, flags=re.IGNORECASE)
                response = re.sub(r'\{context:\s*[^}]+\}', '', response, flags=re.IGNORECASE)
                
                # Fix broken numbers BEFORE any other processing - ULTRA AGGRESSIVE
                # Fix numbers with spaces (like "1 9 6 0" should be "1960")
                response = re.sub(r'\b(\d)\s+(\d)\s+(\d)\s+(\d)\b', r'\1\2\3\4', response)
                response = re.sub(r'\b(\d)\s+(\d)\s+(\d)\b', r'\1\2\3', response)
                response = re.sub(r'\b(\d)\s+(\d)\b', r'\1\2', response)
                
                # Fix numbers split across lines (like "1\n9\n6\n0" should be "1960")
                response = re.sub(r'(\d)\s*\n\s*(\d)\s*\n\s*(\d)\s*\n\s*(\d)', r'\1\2\3\4', response)
                response = re.sub(r'(\d)\s*\n\s*(\d)\s*\n\s*(\d)', r'\1\2\3', response)
                response = re.sub(r'(\d)\s*\n\s*(\d)', r'\1\2', response)
                
                # Fix numbers with any whitespace (tabs, spaces, newlines)
                response = re.sub(r'(\d)\s+(\d)\s+(\d)\s+(\d)', r'\1\2\3\4', response)
                response = re.sub(r'(\d)\s+(\d)\s+(\d)', r'\1\2\3', response)
                response = re.sub(r'(\d)\s+(\d)', r'\1\2', response)
                
                # Clean up any extra spaces or punctuation left behind
                response = re.sub(r'\s+', ' ', response)  # Multiple spaces to single space
                response = response.strip()
                
                # 🚨 CRITICAL FIX: Add messenger link for contact escalation
                messenger_result = self.add_messenger_link_if_needed(response, query, context, lang)
                
                # Handle messenger link result (could be string or list)
                if isinstance(messenger_result, list):
                    # Messenger link was added as separate bubbles
                    return messenger_result
                else:
                    # No messenger link, split long responses into multiple bubbles
                    split_responses = self.split_long_response(messenger_result)
                    return split_responses
            else:
                # Removed verbose AI provider logging
                return self._get_fallback_response(lang)
            
        except Exception as e:
            logger.error(f"❌ Response generation failed: {e}")
            return self._get_fallback_response(lang)
    
    def _get_fallback_response(self, lang: str) -> str:
        """Minimal fallback response"""
        if lang in ["tl", "akl"]:
            return "Paumanhin, hindi ko alam ang sagot sa tanong na ito. Makipag-ugnayan sa opisina ng paaralan para sa karagdagang impormasyon."
        else:
            return "I'm sorry, I don't have that specific information. Please contact the school office for details."
    
    def add_messenger_link_if_needed(self, response: str, query: str, context: str, lang: str) -> str:
        """Add messenger link ONLY for persistent escalation requests - returns list for separate bubbles"""
        context_lower = context.lower() if context else ""
        
        # 🚨 DEBUG: Log the context to see what's being passed
        # logger.info(f"🔍 MESSENGER LINK DEBUG: context='{context_lower[:100]}...'")
        
        # ONLY add messenger link if context specifically indicates persistent escalation
        # This ensures we're helpful first, then provide contact as last resort
        persistent_escalation_context = any(phrase in context_lower for phrase in [
            'contact link immediately', 'persistent about wanting to talk to a live person/admin',
            'user has been persistent about wanting to talk to a live person/admin',  # Add the actual context phrase
            'user wants to talk to someone from the school'  # Add this pattern too
        ])
        
        # logger.info(f"🔍 MESSENGER LINK DEBUG: persistent_escalation_context={persistent_escalation_context}")
        
        # Only add messenger link for persistent escalation, not for first-time requests
        if persistent_escalation_context:
            # logger.info("🔍 MESSENGER LINK DEBUG: Adding messenger link!")
            # Return as separate bubbles: main response + messenger link with intro text
            messenger_intro = "If none, here's the messenger link:"
            return [response, f"{messenger_intro}\n\n{self._messenger_button}"]
        
        # logger.info("🔍 MESSENGER LINK DEBUG: Not adding messenger link")
        return response
    
    def split_long_response(self, response: str, max_length: int = 400) -> List[str]:
        """Enhanced response splitting that preserves numbering and formatting"""
        
        # Special case for messenger links
        if "m.me/" in response:
            max_length = 500
        
        # Enhanced numbered list detection - look for multiple numbered items
        numbered_list_pattern = r'\d+\.\s+[A-Za-z]'
        numbered_matches = re.findall(numbered_list_pattern, response)
        
        if len(numbered_matches) >= 2 and not re.search(r'\b\d{4}\b', response):
            # This is a numbered list - split each item into its own bubble
            return self._split_numbered_list_smart(response, max_length)
        
        if len(response) <= max_length:
            return [response]
        
        # Skip numbered list splitting for now - use regular text splitting
        # if re.search(r'\d+\.\s+', response):
        #     return self._split_numbered_list(response, max_length)
        
        # Use regex for faster splitting on sentences, but avoid splitting numbered lists
        # Split on sentence endings but not after numbers followed by periods
        # Enhanced splitting for long responses - bubble them properly
        # Only split numbered lists if they are actual lists (like "1. Item 2. Item")
        # Must have multiple numbered items to be considered a list
        # BUT NEVER split if it's just a year like "1960" or "1 9 6 0"
        if re.search(r'\d+\.\s+[A-Za-z].*\d+\.\s+[A-Za-z]', response) and not re.search(r'\b\d{4}\b', response):
            # For numbered lists, ALWAYS split by complete numbered items
            return self._split_numbered_list_smart(response, max_length)
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
        """Enhanced splitting - each numbered item gets its own bubble"""
        messages = []
        
        # Find all numbered items with their content
        numbered_pattern = r'(\d+\.\s+[^0-9]+?)(?=\d+\.\s+|$)'
        numbered_items = re.findall(numbered_pattern, response, re.DOTALL)
        
        if numbered_items:
            # Extract intro text before the first numbered item
            first_number_match = re.search(r'(\d+\.\s+)', response)
            if first_number_match:
                intro_text = response[:first_number_match.start()].strip()
                if intro_text and len(intro_text) > 10:
                    messages.append(intro_text)
            
            # Add each numbered item as a separate bubble
            for item in numbered_items:
                item = item.strip()
                if item:
                    messages.append(item)
            
            return messages if messages else [response]
        else:
            # Fallback: try to split by numbered items manually
            parts = re.split(r'(?=\d+\.\s+)', response)
            
            for part in parts:
                part = part.strip()
                if part:
                    # If this part starts with a number, it's a numbered item
                    if re.match(r'\d+\.\s+', part):
                        messages.append(part)
                    elif not re.search(r'\d+\.\s+', part) and len(part) > 10:
                        # This is intro text
                        messages.append(part)
            
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