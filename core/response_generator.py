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
        base_rules = """You are TOMAS, a digital assistant for Tomas SM. Bautista Elementary School.

PERSONALITY:
- Be polite, professional, factual, and communicative
- Use clear, helpful language that parents and students can understand
- Be direct and helpful without roleplay
- Show genuine interest in assisting with school-related matters

CORE PRINCIPLES:
- Use ONLY the database information provided - never make up names, contact info, or details
- If you don't have the information, acknowledge politely and suggest contacting the school office
- For medical emergencies, direct to 911 immediately
- Be helpful and offer assistance, but don't ask questions you can't answer

RESPONSE STYLE:
- Be conversational but professional
- Give complete, helpful answers
- Use natural transitions and explanations
- Avoid repetitive phrases or templates
- Use NLU/NLP analysis to understand queries dynamically
- End responses with helpful offers like "Let me know if you need anything else!" or "Feel free to ask if you have more questions!"

TAGALOG RESPONSES:
- Use natural, grammatically correct Tagalog
- Be polite, professional, factual, and communicative
- Use proper grammar and natural sentence structure
- Avoid roleplay - be direct and helpful
- For unclear queries, acknowledge politely and redirect to school assistance
- End with helpful offers like "Kung may iba pang katanungan, huwag mag-atubiling magtanong!"

ENGLISH RESPONSES:
- Use clear, friendly English
- Be helpful and informative
- Avoid overly formal language
- End with helpful offers like "Let me know if you need anything else!" or "Feel free to ask if you have more questions!" """
        
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
        # Remove the bypass - we want AI processing
            
            lang_code = "TL" if lang in ["tl", "akl"] else "EN"
            
            if lang in ["tl", "akl"]:
                return f"""DATABASE INFORMATION:
{context}

USER QUESTION: {query}

CRITICAL INSTRUCTIONS:
- The database information above is COMPLETE and ACCURATE
- You MUST use this information to answer the user's question
- Rephrase the database information naturally in Tagalog
- NEVER say "I don't have" or "I don't know" when the database provides the information
- If the database says "You can ask their names here", tell the user they can ask for the names
- Be helpful and direct - the database has the information the user needs
- Use proper Tagalog grammar and be conversational

RESPONSE:"""
            else:
                return f"""DATABASE INFORMATION:
{context}

USER QUESTION: {query}

CRITICAL INSTRUCTIONS:
- The database information above is COMPLETE and ACCURATE
- You MUST use this information to answer the user's question
- Rephrase the database information naturally in English
- NEVER say "I don't have" or "I don't know" when the database provides the information
- If the database says "You can ask their names here", tell the user they can ask for the names
- Be helpful and direct - the database has the information the user needs
- Use proper English grammar and be conversational

RESPONSE:"""
        
        # No context available - use NLU/NLP approach
        if lang in ["tl", "akl"]:
            return f"""USER QUERY: {query}

ANALYSIS REQUIRED:
- Analyze the query using NLU/NLP to understand intent and clarity
- If query is unclear or gibberish, acknowledge politely and redirect to school assistance
- If query is clear but no database info available, provide helpful general response
- Be polite, professional, factual, and communicative
- Avoid roleplay - be direct and helpful
- Use natural Tagalog grammar and sentence structure
- Do NOT ask follow-up questions

Provide a natural, helpful response based on the analysis:"""
        else:
            return f"""USER QUERY: {query}

ANALYSIS REQUIRED:
- Analyze the query using NLU/NLP to understand intent and clarity
- If query is unclear or gibberish, acknowledge politely and redirect to school assistance
- If query is clear but no database info available, provide helpful general response
- Be polite, professional, factual, and communicative
- Avoid roleplay - be direct and helpful
- Use clear English grammar and sentence structure
- Do NOT ask follow-up questions

Provide a natural, helpful response based on the analysis:"""
    
    def _generate_greeting_response(self, query: str, lang: str, user_name: str, nlu_info: Dict) -> str:
        """Generate proper greeting response with introduction, matching the user's greeting style"""
        
        # Extract the greeting word/phrase from the user's query
        query_lower = query.lower()
        user_greeting = "Hi"  # Default for English
        user_greeting_tl = "Kumusta"  # Default for Tagalog
        
        # Check for specific time-of-day greetings and extract them
        time_greetings_map = {
            'good morning': ('Good morning', 'Magandang umaga'),
            'good afternoon': ('Good afternoon', 'Magandang hapon'),
            'good evening': ('Good evening', 'Magandang gabi'),
            'good noon': ('Good noon', 'Magandang tanghali'),
            'magandang umaga': ('Good morning', 'Magandang umaga'),
            'magandang hapon': ('Good afternoon', 'Magandang hapon'),
            'magandang gabi': ('Good evening', 'Magandang gabi'),
            'magandang tanghali': ('Good noon', 'Magandang tanghali'),
            'maayong aga': ('Good morning', 'Maayong aga'),
            'maayong hapon': ('Good afternoon', 'Maayong hapon'),
            'maayong gab-i': ('Good evening', 'Maayong gab-i'),
            'maayong gabii': ('Good evening', 'Maayong gabii'),
            'maayong buntag': ('Good morning', 'Maayong buntag'),
            'kumusta': ('Hey', 'Kumusta'),
            'kamusta': ('Hey', 'Kamusta'),
            'hiya': ('Hey', 'Hiya'),
            'hello': ('Hello', 'Hello'),
            'hi': ('Hi', 'Hi'),
        }
        
        # Find matching greeting in user's query
        for greeting_phrase, (en_greeting, tl_greeting) in time_greetings_map.items():
            if greeting_phrase in query_lower:
                user_greeting = en_greeting
                user_greeting_tl = tl_greeting
                break
        
        # Base introduction in both languages
        if lang in ["tl", "akl"]:
            # Tagalog/Aklanon greeting
            if user_name:
                greeting = f"{user_greeting_tl}, {user_name}! Ako si TOMAS, ang digital assistant ng Tomas SM. Bautista Elementary School."
            else:
                greeting = f"{user_greeting_tl}! Ako si TOMAS, ang digital assistant ng Tomas SM. Bautista Elementary School."
            
            introduction = "Tumutulong ako sa mga tanong tungkol sa paaralan, mga guro, aktibidad, at iba pang impormasyon. Paano kita matutulungan ngayon?"
            
        else:
            # English greeting
            if user_name:
                greeting = f"{user_greeting} {user_name}! I'm TOMAS, the digital assistant for Tomas SM. Bautista Elementary School."
            else:
                greeting = f"{user_greeting}! I'm TOMAS, the digital assistant for Tomas SM. Bautista Elementary School."
            
            introduction = "I help with questions about the school, teachers, activities, and other information. How can I assist you today?"
        
        # Customize based on greeting type (only for excited/formal/casual when no specific time-of-day greeting)
        intent = nlu_info.get('intent', 'greeting_simple')
        
        if intent == 'greeting_excited' and 'good' not in query_lower:
            if lang in ["tl", "akl"]:
                greeting = greeting.replace(user_greeting_tl, f"{user_greeting_tl}! Ang saya!")
            else:
                greeting = greeting.replace(user_greeting, f"{user_greeting}! Great to see you!")
        
        elif intent == 'greeting_formal' and 'good' not in query_lower:
            if lang in ["tl", "akl"]:
                greeting = greeting.replace(user_greeting_tl, "Magandang araw po")
            else:
                greeting = greeting.replace(user_greeting, "Good day")
        
        elif intent == 'greeting_casual' and 'good' not in query_lower:
            if lang in ["tl", "akl"]:
                greeting = greeting.replace(user_greeting_tl, f"{user_greeting_tl}!")
            else:
                greeting = greeting.replace(user_greeting, "Hey there!")
        
        elif intent == 'greeting_returning_user' and 'good' not in query_lower:
            if lang in ["tl", "akl"]:
                greeting = greeting.replace(user_greeting_tl, f"{user_greeting_tl}! Welcome back!")
            else:
                greeting = greeting.replace(user_greeting, f"{user_greeting}! Welcome back!")
        
        return f"{greeting} {introduction}"
    
    def _generate_appreciation_response(self, query: str, lang: str, user_name: str) -> str:
        """Generate appropriate response for gratitude/appreciation"""
        
        if lang in ["tl", "akl"]:
            # Tagalog/Aklanon response
            if user_name:
                return f"Walang anuman, {user_name}! Masayang makatulong. Kung may iba pang katanungan, huwag mag-atubiling magtanong!"
            else:
                return "Walang anuman! Masayang makatulong. Kung may iba pang katanungan, huwag mag-atubiling magtanong!"
        else:
            # English response
            if user_name:
                return f"You're welcome, {user_name}! Happy to help. Let me know if you need anything else!"
            else:
                return "You're welcome! Happy to help. Let me know if you need anything else!"
    
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
            
            # Special handling for gratitude/appreciation - simple acknowledgment
            if nlu_info and nlu_info.get('intent') in ['appreciation', 'APPRECIATION']:
                return self._generate_appreciation_response(query, lang, user_name)
            
            # Build the system prompt
            system_prompt = self.get_system_prompt(lang, user_name, nlu_info, entities, confidence)
            
            # Build concise user message
            user_message = self._build_concise_message(query, context, lang, nlu_info)
            
        # Remove the bypass - we want AI processing
            
            # Allow for complete responses without truncation
            max_tokens = 250 if lang in ["tl", "akl"] else 220
            
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
                
                # Apply smart chunking for long responses - RE-ENABLED for bubble separation
                response = self._apply_smart_chunking(response)
                
                # Process each response item
                if isinstance(response, list):
                    processed_responses = []
                    for item in response:
                        processed_item = self._clean_response(item)
                        # Fix capitalization for sentence beginnings
                        processed_item = self._fix_sentence_capitalization(processed_item)
                        processed_responses.append(processed_item)
                    return processed_responses
                else:
                    cleaned_response = self._clean_response(response)
                    # Fix capitalization for sentence beginnings
                    return self._fix_sentence_capitalization(cleaned_response)
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
    
    def _fix_sentence_capitalization(self, text: str) -> str:
        """Fix capitalization at the beginning of sentences"""
        if not text or len(text.strip()) == 0:
            return text
        
        # Capitalize the first letter of the text
        text = text.strip()
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        return text
    
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
    
    def _apply_smart_chunking(self, response) -> List[str]:
        """Apply smart sentence-aware chunking for long responses"""
        
        # If response is already a list, process each item
        if isinstance(response, list):
            chunked_responses = []
            for item in response:
                chunked_items = self._chunk_single_response(item)
                chunked_responses.extend(chunked_items)
            return chunked_responses
        
        # Process single response
        return self._chunk_single_response(response)
    
    def _chunk_single_response(self, response: str) -> List[str]:
        """Chunk a single response into multiple bubbles based on sentence boundaries"""
        
        # Configuration - larger bubbles for better readability
        MAX_CHARS_PER_BUBBLE = 300  # Larger bubbles for better readability
        MIN_CHARS_PER_BUBBLE = 120  # Larger minimum to avoid tiny fragments
        
        # If response is short enough, return as-is
        if len(response) <= MAX_CHARS_PER_BUBBLE:
            return [response]
        
        # Split by sentences first
        sentences = self._split_by_sentences(response)
        
        # If only one sentence or sentences are too long, try splitting by clauses
        if len(sentences) == 1 or (len(sentences) > 0 and max(len(s) for s in sentences) > MAX_CHARS_PER_BUBBLE):
            # Try clause-based splitting for better chunking
            clause_sentences = []
            for sentence in sentences:
                if len(sentence) > MAX_CHARS_PER_BUBBLE:
                    clause_sentences.extend(self._split_by_clauses(sentence))
                else:
                    clause_sentences.append(sentence)
            sentences = clause_sentences
        
        # NEW APPROACH: Each sentence becomes its own bubble (unless it's very short)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # If sentence is short enough to stand alone, add it as a bubble
            if len(sentence) >= MIN_CHARS_PER_BUBBLE:
                if current_chunk:
                    # Add any pending chunk first
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                # Add this sentence as its own bubble
                chunks.append(sentence)
            else:
                # Very short sentence - merge with previous or next
                if current_chunk and len(current_chunk + " " + sentence) <= MAX_CHARS_PER_BUBBLE:
                    current_chunk += " " + sentence
                elif not current_chunk:
                    current_chunk = sentence
                else:
                    # Current chunk is full, start new one
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [response]
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentence boundaries with abbreviation handling and punctuation preservation"""
        
        # Common abbreviations that shouldn't end sentences
        abbreviations = [
            'mr', 'mrs', 'ms', 'dr', 'prof', 'rev', 'sr', 'jr', 'esq',
            'st', 'ave', 'blvd', 'rd', 'ct', 'ln', 'pl', 'pkwy',
            'inc', 'corp', 'ltd', 'llc', 'co', 'etc', 'vs', 'v',
            'am', 'pm', 'ad', 'bc', 'ce', 'bce', 'no', 'nos',
            'vol', 'pp', 'ch', 'sec', 'fig', 'ref', 'ex', 'eg',
            'ie', 'viz', 'cf', 'et', 'al', 'ca', 'approx', 'est',
            'dept', 'govt', 'mgr', 'asst', 'dir', 'pres', 'vice',
            'gen', 'adm', 'col', 'maj', 'capt', 'lt', 'sgt', 'cpl',
            'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug',
            'sep', 'oct', 'nov', 'dec', 'mon', 'tue', 'wed', 'thu',
            'fri', 'sat', 'sun', 'sm'
        ]
        
        # First, try to restore missing punctuation
        text = self._restore_punctuation(text)
        
        # Use finditer to extract sentences WITH their punctuation
        sentences = []
        current_pos = 0
        
        # Pattern to find sentence endings (periods, exclamation marks, question marks)
        sentence_endings = re.compile(r'[.!?]+')
        
        for match in sentence_endings.finditer(text):
            end_pos = match.end()
            
            # Check if this punctuation is part of an abbreviation
            is_abbreviation = False
            
            # Look backwards to see if this period is part of an abbreviation
            start_check = max(0, end_pos - 20)  # Check up to 20 characters back
            context = text[start_check:end_pos].lower()
            
            # Check for abbreviations
            for abbr in abbreviations:
                if context.endswith(abbr + '.'):
                    # Additional check: make sure it's not followed by a space and capital letter
                    # (which would indicate a real sentence boundary)
                    if end_pos < len(text) and text[end_pos:end_pos+2] == ' ' and end_pos+1 < len(text) and text[end_pos+1].isupper():
                        # This is likely a real sentence boundary, not an abbreviation
                        is_abbreviation = False
                    else:
                        is_abbreviation = True
                    break
            
            # If it's not an abbreviation, extract the sentence
            if not is_abbreviation:
                sentence = text[current_pos:end_pos].strip()
                if sentence and len(sentence) > 10:  # Ignore very short fragments
                    sentences.append(sentence)
                current_pos = end_pos
        
        # Add the last sentence if there's remaining text
        if current_pos < len(text):
            remaining = text[current_pos:].strip()
            if remaining and len(remaining) > 10:
                sentences.append(remaining)
        
        return sentences if sentences else [text]
    
    def _restore_punctuation(self, text: str) -> str:
        """Restore missing punctuation in text - simplified approach"""
        
        # Only add periods at the end if missing
        if not any(text.endswith(p) for p in ['.', '!', '?']):
            text += '.'
        
        return text
    
    def _split_by_clauses(self, text: str) -> List[str]:
        """Split text by clause boundaries when sentences are too long"""
        
        # Clause splitting patterns
        clause_patterns = [
            r',\s+(?=[A-Z])',  # Comma followed by capital letter
            r';\s+',           # Semicolon
            r':\s+',           # Colon
            r'\s+and\s+',      # "and" conjunction
            r'\s+but\s+',      # "but" conjunction
            r'\s+or\s+',       # "or" conjunction
            r'\s+so\s+',       # "so" conjunction
            r'\s+however\s+',  # "however" conjunction
            r'\s+therefore\s+', # "therefore" conjunction
            r'\s+also\s+',     # "also" conjunction
            r'\s+additionally\s+', # "additionally" conjunction
            r'\s+furthermore\s+', # "furthermore" conjunction
            r'\s+moreover\s+', # "moreover" conjunction
            r'\s+in\s+addition\s+', # "in addition" conjunction
            r'\s+on\s+the\s+other\s+hand\s+', # "on the other hand" conjunction
        ]
        
        # Try each pattern
        for pattern in clause_patterns:
            clauses = re.split(pattern, text, flags=re.IGNORECASE)
            if len(clauses) > 1:
                # Clean up clauses
                cleaned_clauses = []
                for clause in clauses:
                    clause = clause.strip()
                    if clause and len(clause) > 20:  # Ignore very short fragments
                        cleaned_clauses.append(clause)
                
                if len(cleaned_clauses) > 1:
                    return cleaned_clauses
        
        # If no clause splitting worked, return the original text
        return [text]
    
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