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
        
        
        self._messenger_button = '<a href="https://m.me/114901Tomas" target="_blank" style="display: inline-block; background-color: #0084ff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 10px 0;">💬Messenger</a>'

    def get_system_prompt(self, lang: str, user_name: str = "", nlu_info: Dict = None, 
                         entities: List = None, confidence: float = 0.0) -> str:
        """Generate concise, focused system prompt"""
        time_context = self._get_time_context()
        name_context = f" User: {user_name}." if user_name else ""
        
        # Natural, conversational instructions
        base_rules = """You are TOMAS, a friendly and helpful digital assistant for Tomas SM. Bautista Elementary School.

PERSONALITY:
- Talk like a helpful school staff member giving directions
- Be warm, natural, and conversational
- Use simple, clear language that parents and students can understand
- Show genuine interest in helping

CORE PRINCIPLES:
- Use ONLY the database information provided - never make up names, contact info, or details
- If you don't have the information, say so naturally and suggest contacting the school office
- For medical emergencies, direct to 911 immediately
- NEVER ask follow-up questions - just provide the information and stop

RESPONSE STYLE:
- Be conversational, not robotic
- Give complete, helpful answers
- Use natural transitions and explanations
- Avoid repetitive phrases or templates

TAGALOG RESPONSES:
- Use natural, grammatically correct Tagalog
- Be warm and approachable
- Use proper grammar: "Maaari mong kausapin" not "Hindi may batas"

ENGLISH RESPONSES:
- Use clear, friendly English
- Be helpful and informative
- Avoid overly formal language"""
        
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
        """Get natural language-specific rules"""
        if lang in ["tl", "akl"]:
            return "\nLANGUAGE: Respond in natural Tagalog. Be warm and conversational, like a helpful school staff member. Use proper grammar and be approachable."
        else:
            return "\nLANGUAGE: Respond in natural English. Be friendly and helpful, like a school staff member giving directions to parents or students."
    
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
                    return f"""DB: {context}

Q: {query}
MULTI-Q: {question_number}/{total_questions}

CRITICAL: Answer EXACTLY what user asks. If user asks "support aide", answer about "support aide" ONLY. Never change "support" to "sports". Use DB info only. Natural tone. Correct grammar. Be brief."""
                else:
                    return f"""DB: {context}

Q: {query}
MULTI-Q: {question_number}/{total_questions}

CRITICAL: Answer EXACTLY what user asks. If user asks "support aide", answer about "support aide" ONLY. Never change "support" to "sports". Use DB info only. Natural tone. Be brief."""
            else:
                if lang in ["tl", "akl"]:
                    return f"Q: {query}\nMULTI-Q: {question_number}/{total_questions}\nNo DB info. Brief Tagalog response."
                else:
                    return f"Q: {query}\nMULTI-Q: {question_number}/{total_questions}\nNo DB info. Brief English response."
        
        # Handle special cases first
        if context == "User is introducing themselves with their name":
            return f"Name intro: {query}\nGreet using name."
        
        if context == "User is expressing their emotional state":
            return f"Emotional: {query}\nBrief acknowledge. Redirect to school."
        
        # Handle name requests - be direct and helpful
        if "pangalan" in query.lower() or "name" in query.lower():
            if lang in ["tl", "akl"]:
                return f"Q: {query}\nName request. Tagalog: No name but can help with school info."
            else:
                return f"Q: {query}\nName request. English: No name but can help with school info."
        
        # Handle admin/contact requests - hardcoded response to prevent hallucinations
        if any(word in query.lower() for word in ["admin", "administrator", "contact", "messenger", "link"]):
            if lang in ["tl", "akl"]:
                return "HARDCODED_ADMIN_TAGALOG"
            else:
                return "HARDCODED_ADMIN_ENGLISH"
        
        # Database context - the priority case
        if context and context not in ["General school information query", 
                                       "No specific information available in database for this query"]:
            lang_code = "TL" if lang in ["tl", "akl"] else "EN"
            
            if lang in ["tl", "akl"]:
                return f"""DATABASE INFORMATION:
{context}

USER QUESTION: {query}

INSTRUCTIONS:
- Use ONLY the database information above
- Answer in Tagalog
- Be conversational and helpful, like a school staff member
- Provide a natural, complete response that helps the user
- Do NOT invent any names or information not in the database
- If the database says "Meliza A. Delgado", use that exact name
- Give a helpful, informative response that feels like talking to a real person

Please provide a natural, conversational response:"""
            else:
                return f"""DATABASE INFORMATION:
{context}

USER QUESTION: {query}

INSTRUCTIONS:
- Use ONLY the database information above
- Answer in English
- Be conversational and helpful, like a school staff member
- Provide a natural, complete response that helps the user
- Do NOT invent any names or information not in the database
- If the database says "Meliza A. Delgado", use that exact name
- Give a helpful, informative response that feels like talking to a real person

Please provide a natural, conversational response:"""
        
        # No context available
        if lang in ["tl", "akl"]:
            return f"Q: {query}\nNo DB info. Helpful Tagalog response. Do NOT ask follow-up questions."
        else:
            return f"Q: {query}\nNo DB info. Helpful English response. Do NOT ask follow-up questions."
    
    def _generate_greeting_response(self, query: str, lang: str, user_name: str, nlu_info: Dict) -> str:
        """Generate proper greeting response with introduction"""
        
        # Base introduction in both languages
        if lang in ["tl", "akl"]:
            # Tagalog/Aklanon greeting
            if user_name:
                greeting = f"Kumusta, {user_name}! Ako si TOMAS, ang digital assistant ng Tomas SM. Bautista Elementary School."
            else:
                greeting = "Kumusta! Ako si TOMAS, ang digital assistant ng Tomas SM. Bautista Elementary School."
            
            introduction = "Tumutulong ako sa mga tanong tungkol sa paaralan, mga guro, aktibidad, at iba pang impormasyon. Paano kita matutulungan ngayon?"
            
        else:
            # English greeting
            if user_name:
                greeting = f"Hi {user_name}! I'm TOMAS, the digital assistant for Tomas SM. Bautista Elementary School."
            else:
                greeting = "Hi! I'm TOMAS, the digital assistant for Tomas SM. Bautista Elementary School."
            
            introduction = "I help with questions about the school, teachers, activities, and other information. How can I assist you today?"
        
        # Customize based on greeting type
        intent = nlu_info.get('intent', 'greeting_simple')
        
        if intent == 'greeting_excited':
            if lang in ["tl", "akl"]:
                greeting = greeting.replace("Kumusta", "Kumusta! Ang saya!")
            else:
                greeting = greeting.replace("Hi", "Hi! Great to see you!")
        
        elif intent == 'greeting_formal':
            if lang in ["tl", "akl"]:
                greeting = greeting.replace("Kumusta", "Magandang araw po")
            else:
                greeting = greeting.replace("Hi", "Good day")
        
        elif intent == 'greeting_casual':
            if lang in ["tl", "akl"]:
                greeting = greeting.replace("Kumusta", "Kumusta!")
            else:
                greeting = greeting.replace("Hi", "Hey there!")
        
        elif intent == 'greeting_returning_user':
            if lang in ["tl", "akl"]:
                greeting = greeting.replace("Kumusta", "Kumusta! Welcome back!")
            else:
                greeting = greeting.replace("Hi", "Hi! Welcome back!")
        
        return f"{greeting} {introduction}"
    
    async def generate_response(self, query: str, context: str, lang: str, 
                              conversation_history: List[Dict] = None, 
                              nlu_info: Dict = None, user_name: str = "", 
                              entities: List = None, confidence: float = 0.0, 
                              context_analysis: Dict = None, is_multi_question: bool = False, 
                              questions: List[str] = None) -> str:
        """Generate response using multi-provider AI system with intelligent fallback"""
        
        try:
            # Special handling for greetings - provide proper introduction
            if nlu_info and nlu_info.get('intent') in ['greeting_simple', 'greeting_with_name', 'greeting_casual', 'greeting_formal', 'greeting_excited', 'greeting_returning_user']:
                return self._generate_greeting_response(query, lang, user_name, nlu_info)
            
            # Build the system prompt
            system_prompt = self.get_system_prompt(lang, user_name, nlu_info, entities, confidence)
            
            # Build concise user message
            user_message = self._build_concise_message(query, context, lang, nlu_info)
            
            
            # Keep responses concise to save tokens
            max_tokens = 160 if lang in ["tl", "akl"] else 140
            
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
                
                # Check if response contains list items and split them into separate bubbles
                response = self._split_list_items(response)
                
                # Process each response item
                if isinstance(response, list):
                    processed_responses = []
                    for item in response:
                        processed_item = self._clean_response(item)
                        processed_responses.append(processed_item)
                    return processed_responses
                else:
                    return self._clean_response(response)
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
        
        # Add messenger link for admin/contact requests or persistent escalation
        query_lower = query.lower() if query else ""
        
        # Check for persistent escalation context (hardcoded admin responses)
        persistent_escalation_context = any(phrase in context_lower for phrase in [
            'hardcoded_admin_tagalog', 'hardcoded_admin_english'
        ])
        
        should_add_link = persistent_escalation_context
        
        # logger.info(f"🔍 MESSENGER LINK DEBUG: persistent_escalation_context={persistent_escalation_context}")
        
        # Add messenger link for admin/contact requests or persistent escalation
        if should_add_link:
            # logger.info("🔍 MESSENGER LINK DEBUG: Adding messenger link!")
            # Return as separate bubbles: main response + messenger button only
            return [response, self._messenger_button]
        
        # logger.info("🔍 MESSENGER LINK DEBUG: Not adding messenger link")
        return response
    
    def remove_unwanted_links(self, response: str) -> str:
        """Remove all links except the official messenger link"""
        if not response:
            return response
        
        # Remove WhatsApp links
        response = re.sub(r'<a[^>]*href="[^"]*whatsapp[^"]*"[^>]*>.*?</a>', '', response, flags=re.IGNORECASE)
        response = re.sub(r'<a[^>]*href="[^"]*wa\.me[^"]*"[^>]*>.*?</a>', '', response, flags=re.IGNORECASE)
        
        # Remove Facebook links (except official messenger)
        response = re.sub(r'<a[^>]*href="[^"]*facebook[^"]*"[^>]*>.*?</a>', '', response, flags=re.IGNORECASE)
        response = re.sub(r'<a[^>]*href="[^"]*fb\.com[^"]*"[^>]*>.*?</a>', '', response, flags=re.IGNORECASE)
        
        # Remove unofficial messenger links (keep only https://m.me/114901Tomas)
        response = re.sub(r'<a[^>]*href="[^"]*m\.me/[^"]*"[^>]*>.*?</a>', '', response, flags=re.IGNORECASE)
        response = re.sub(r'\[([^\]]+)\]\([^)]*m\.me/[^)]*\)', r'\1', response, flags=re.IGNORECASE)
        
        # Remove generic website links
        response = re.sub(r'<a[^>]*href="[^"]*example\.com[^"]*"[^>]*>.*?</a>', '', response, flags=re.IGNORECASE)
        response = re.sub(r'<a[^>]*href="[^"]*http[^"]*"[^>]*>.*?</a>', '', response, flags=re.IGNORECASE)
        
        # Remove phone number links
        response = re.sub(r'<a[^>]*href="[^"]*tel:[^"]*"[^>]*>.*?</a>', '', response, flags=re.IGNORECASE)
        
        # Remove button tags with unwanted links
        response = re.sub(r'<button[^>]*onclick="[^"]*window\.open[^"]*"[^>]*>.*?</button>', '', response, flags=re.IGNORECASE)
        
        # Remove markdown-style links
        response = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', response)
        
        # Remove messenger buttons from non-persistent escalation responses
        response = re.sub(r'\[Messenger Button:.*?\]', '', response, flags=re.IGNORECASE)
        response = re.sub(r'<button[^>]*href="[^"]*facebook[^"]*"[^>]*>.*?</button>', '', response, flags=re.IGNORECASE)
        response = re.sub(r'<button[^>]*href="[^"]*m\.me/[^"]*"[^>]*>.*?</button>', '', response, flags=re.IGNORECASE)
        
        # Remove messenger intro text
        response = re.sub(r'tungo sa sumusunod na link[:\s]*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'sa pamamagitan ng sumusunod na link[:\s]*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'here\'s the messenger link[:\s]*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'narito ang messenger link[:\s]*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'messenger link[:\s]*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'sumusunod na link[:\s]*', '', response, flags=re.IGNORECASE)
        
        
        # Clean up extra whitespace
        response = re.sub(r'\s+', ' ', response)
        response = response.strip()
        
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
    
    def _split_list_items(self, response: str) -> List[str]:
        """Split bullet-pointed lists into separate bubbles"""
        
        # Check if response contains bullet points
        if '•' not in response:
            return [response]
        
        # Split by lines
        lines = response.strip().split('\n')
        messages = []
        current = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('•'):
                # This is a list item - send as separate bubble
                if current:
                    messages.append(current)
                    current = ""
                messages.append(line)
            else:
                # This is intro/regular text
                if current:
                    current += " " + line
                else:
                    current = line
        
        if current:
            messages.append(current)
        
        return messages if len(messages) > 1 else [response]
    
    def _clean_response(self, response: str) -> str:
        """Clean and format a single response"""
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
        
        # Remove unwanted links (except messenger)
        response = self.remove_unwanted_links(response)
        
        # Clean up extra whitespace
        response = re.sub(r'\s+', ' ', response).strip()
        
        return response