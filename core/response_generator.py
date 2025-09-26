"""
Response Generation Module - Multi-Provider AI System
Handles response generation with multiple AI providers and intelligent fallback
"""
import logging
import os
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """Multi-provider response generator with intelligent fallback"""
    
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
                logger.info("✅ Groq client initialized (legacy support)")
            except ImportError as e:
                logger.error(f"❌ Groq library not installed: {e}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Groq client: {e}")
        
        # Log available providers
        stats = self.multi_ai.get_provider_stats()
        logger.info(f"🚀 Multi-provider AI initialized: {stats}")
    
    def get_system_prompt(self, lang: str, user_name: str = "", nlu_info: Dict = None, 
                         entities: List = None, confidence: float = 0.0) -> str:
        """Generate language-specific system prompt with explicit tone instructions"""
        time_context = self._get_time_context()
        name_context = f" Ang kausap mo ay si {user_name}." if user_name and lang == "tl" else f" The person you're talking to is named {user_name}." if user_name else ""
        
        # Enhanced NLP/NLU context
        nlu_context = ""
        if nlu_info:
            intent = nlu_info.get('intent', 'unknown')
            nlu_confidence = nlu_info.get('confidence', 0.0)
            nlu_context = f" NLU Analysis: Intent={intent} (confidence: {nlu_confidence:.2f})."
        
        # Add entity information
        entity_context = ""
        if entities:
            entity_list = [f"{e.entity_type}: {e.value}" for e in entities if hasattr(e, 'entity_type')]
            if entity_list:
                entity_context = f" Extracted Entities: {', '.join(entity_list)}."
        
        # Add language confidence
        lang_confidence_context = f" Language Detection Confidence: {confidence:.2f}." if confidence > 0 else ""
        
        if lang == "tl" or lang == "akl":
            return f"""Ikaw si TOMAS, ang friendly na digital assistant ng Tomas SM. Bautista Elementary School. {time_context}{name_context}{nlu_context}{entity_context}{lang_confidence_context}

MAHALAGA: SUMAGOT LAMANG SA TAGALOG/FILIPINO. KUNG Aklanon ang user, sumagot sa Tagalog dahil mas maintindihan nila ito.

TONE: Maging friendly, conversational, at natural na parang kausap mo ang isang kaibigan. Gumamit ng casual na tono pero propesyonal pa rin.

STRICT RULES:
1. DATABASE CONTEXT ANG PINAKAMAHALAGA - gamitin ang impormasyon mula sa database context kung available
2. HUWAG MAG-INVENT ng mga pangalan, numero, o impormasyon na wala sa context
3. HUWAG MAG-ROLEPLAY - ikaw ay digital assistant, hindi tao. HUWAG gumamit ng actions tulad ng *smile*, *wave*, *wink*, *big smile* o anumang theatrical behaviors. HUWAG mag-claim ng personal experiences, feelings, o human characteristics.
4. KUNG WALANG SAGOT sa context, sabihin na "Hindi ko alam ang sagot, pero maaari kayong magpunta sa school office para sa dagdag na detalye"
5. GAMITIN LAMANG ang impormasyon na nasa context - HUWAG magdagdag ng sariling kaalaman
6. KUNG may pangalan sa context, gamitin ang eksaktong pangalan na nasa context
7. KUNG walang pangalan sa context, HUWAG mag-invent ng pangalan
8. MANATILING SCHOOL-FOCUSED - laging i-redirect sa school-related topics at services
9. PANATILIHING MAIKLI ang mga sagot - under 100 words maliban kung nagbibigay ng detailed school information
10. PARA SA EMOTIONAL EXPRESSIONS - acknowledge briefly, suggest speaking with the guidance counselor (HUWAG mag-invent ng pangalan), offer school help
11. GAMITIN ANG NLP/NLU ANALYSIS para sa mas mahusay na pag-unawa sa user intent at entities
12. PARA SA GENERAL SCHOOL INFORMATION - magbigay ng factual, professional na impormasyon tungkol sa school programs, services, at policies nang walang roleplay o hallucinations
13. LAGING MABING FACTUAL - huwag gumawa ng specific details, numero, o impormasyon na hindi binigay sa context
14. MANATILING PROFESSIONAL TONE - maging helpful at knowledgeable nang hindi nagpapanggap na tao

NAME INTRODUCTION HANDLING: Kung ang user ay nagpapakilala ng kanilang pangalan, sumagot ng friendly greeting tulad ng 'Hi Maria! Nice to meet you. What can I help you with today?'

KAPANSIN-PANSIN: Ang context na ibinigay ay naglalaman ng EKSAKTONG SAGOT mula sa aming school database. Ipakita ang impormasyong ito nang natural at conversational habang pinapanatili ang lahat ng katotohanan. HUWAG baguhin ang mga katotohanan, numero, o pangunahing impormasyon."""
        else:
            return f"""You are TOMAS, the friendly digital assistant for Tomas SM. Bautista Elementary School. {time_context}{name_context}{nlu_context}{entity_context}{lang_confidence_context}

IMPORTANT: RESPOND ONLY IN ENGLISH.

TONE: Be friendly, conversational, and natural like you're talking to a friend. Use a casual but professional tone.

STRICT RULES:
1. DATABASE CONTEXT IS HIGHEST PRIORITY - use information from database context when available
2. DO NOT INVENT names, numbers, or information not in the context
3. DO NOT ROLEPLAY - you are a digital assistant, not a human. DO NOT use actions like *smile*, *wave*, *wink*, *big smile* or any theatrical behaviors. DO NOT claim personal experiences, feelings, or human characteristics.
4. IF NO ANSWER in context, say "I don't know the answer, but you can visit the school office for more details"
5. USE ONLY information in the context - DO NOT add your own knowledge
6. IF there's a name in context, use the exact name from context
7. IF no name in context, DO NOT invent names
8. STAY SCHOOL-FOCUSED - always redirect to school-related topics and services
9. KEEP RESPONSES CONCISE - under 100 words unless providing detailed school information
10. FOR EMOTIONAL EXPRESSIONS - acknowledge briefly, suggest speaking with the guidance counselor (DO NOT invent names), offer school help
11. USE NLP/NLU ANALYSIS for better understanding of user intent and entities
12. FOR GENERAL SCHOOL INFORMATION - provide factual, professional information about school programs, services, and policies without roleplay or hallucinations
13. ALWAYS BE FACTUAL - never make up specific details, numbers, or information not provided in context
14. MAINTAIN PROFESSIONAL TONE - be helpful and knowledgeable without pretending to be human

NAME INTRODUCTION HANDLING: If the user introduces their name, respond with a friendly greeting like 'Hi John! Nice to meet you. What can I help you with today?'

CRITICAL: The context provided contains the EXACT ANSWER from our school database. Present this information naturally and conversationally while keeping all facts unchanged. DO NOT change facts, numbers, or core information."""
    
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
                              nlu_info: Dict = None, user_name: str = "", 
                              entities: List = None, confidence: float = 0.0) -> str:
        """Generate response using multi-provider AI system with intelligent fallback"""
        
        try:
            # Build the system prompt
            system_prompt = self.get_system_prompt(lang, user_name, nlu_info, entities, confidence)
            
            # Build the user message with context
            user_message = self._build_user_message(query, context, lang, nlu_info, entities, confidence)
            
            # Use multi-provider AI system
            ai_response = await self.multi_ai.generate_response(
                prompt=user_message,
                system_prompt=system_prompt,
                max_tokens=150,
                temperature=0.7
            )
            
            if ai_response.success:
                logger.info(f"✅ Response generated using {ai_response.provider} ({ai_response.model})")
                return ai_response.content.strip()
            else:
                logger.warning(f"⚠️ Multi-provider AI failed: {ai_response.error}")
                return self._get_fallback_response(lang)
            
        except Exception as e:
            logger.error(f"❌ Response generation failed: {e}")
            return self._get_fallback_response(lang)
    
    def _build_user_message(self, query: str, context: str, lang: str, 
                           nlu_info: Dict = None, entities: List = None, 
                           confidence: float = 0.0) -> str:
        """Build the user message with enhanced context"""
        
        # Enhanced user message with comprehensive NLP/NLU context
        nlu_analysis = ""
        if nlu_info:
            intent = nlu_info.get('intent', 'unknown')
            nlu_confidence = nlu_info.get('confidence', 0.0)
            nlu_analysis = f"\nNLP/NLU ANALYSIS: Intent={intent} (confidence: {nlu_confidence:.2f})"
        
        entity_analysis = ""
        if entities:
            entity_list = [f"{e.entity_type}: {e.value}" for e in entities if hasattr(e, 'entity_type')]
            if entity_list:
                entity_analysis = f"\nEXTRACTED ENTITIES: {', '.join(entity_list)}"
        
        lang_analysis = f"\nLANGUAGE: {lang} (confidence: {confidence:.2f})" if confidence > 0 else f"\nLANGUAGE: {lang}"
        
        # Add current query with enhanced context - DATABASE CONTEXT TAKES PRIORITY
        if context and context != "General school information query":
            if context == "User is introducing themselves with their name":
                return f"""USER MESSAGE: {query}{nlu_analysis}{entity_analysis}{lang_analysis}

INSTRUCTIONS: The user is introducing themselves with their name. Respond with a friendly greeting using their name, like "Hi [Name]! Nice to meet you. What can I help you with today?" Be warm and welcoming. Use the NLP analysis to understand their intent better."""
            elif context == "User is expressing their emotional state":
                return f"""USER MESSAGE: {query}{nlu_analysis}{entity_analysis}{lang_analysis}

INSTRUCTIONS: The user is expressing their emotional state. Respond briefly and professionally in 1-2 sentences. Acknowledge their feeling but immediately redirect to school services. If they seem to need support, suggest speaking with the guidance counselor (DO NOT invent names - just say "guidance counselor"). Always offer to help with school-related questions. Keep response under 80 words and school-focused. Use the NLP analysis to understand their emotional state better."""
            elif context == "User is expressing appreciation or thanks":
                return f"""USER MESSAGE: {query}{nlu_analysis}{entity_analysis}{lang_analysis}

INSTRUCTIONS: The user is expressing appreciation or thanks. Respond warmly and acknowledge their thanks. Be friendly and offer to help with any school-related questions they might have. Keep response under 60 words and school-focused. Use the NLP analysis to understand their appreciation better."""
            elif context == "User is giving a simple greeting":
                return f"""USER MESSAGE: {query}{nlu_analysis}{entity_analysis}{lang_analysis}

INSTRUCTIONS: The user is giving a simple greeting. Respond with a friendly greeting back and offer to help with school-related questions. Be warm and welcoming. Keep response under 50 words and school-focused. Use the NLP analysis to understand their greeting better."""
            elif context == "User has sent a message that may be unclear or unusual. Respond helpfully and ask for clarification if needed.":
                return f"""USER MESSAGE: The user has sent an unclear or unusual message.{nlu_analysis}{entity_analysis}{lang_analysis}

INSTRUCTIONS: The user's message is unclear or unusual. Respond helpfully and ask for clarification. Be polite and offer to help with school-related questions. Do NOT repeat or reference the unclear message. Simply ask them to rephrase their question or let you know how you can help. Keep response under 60 words and school-focused."""
            elif context.startswith("You are a helpful school assistant"):
                return f"""USER QUESTION: {query}{nlu_analysis}{entity_analysis}{lang_analysis}

INSTRUCTIONS: {context} Use the NLP analysis to understand the user's intent and provide an appropriate response. Be helpful and intelligent in your response. If you don't have specific information about the school, be honest about it and suggest contacting the school office for detailed information. Keep response under 100 words and school-focused."""
            else:
                # DATABASE CONTEXT TAKES HIGHEST PRIORITY
                lang_instruction = "SUMAGOT SA TAGALOG/FILIPINO." if lang in ["tl", "akl"] else "RESPOND IN ENGLISH."
                return f"""DATABASE INFORMATION AVAILABLE:
{context}

USER QUESTION: {query}{nlu_analysis}{entity_analysis}{lang_analysis}

INSTRUCTIONS: Use the database information above to answer the user's question naturally and conversationally. Expand on the information in a helpful way while keeping all facts accurate. Be informative and engaging, not just a simple Q&A. Use the NLP analysis to understand the user's intent and provide a comprehensive response. {lang_instruction}"""
        else:
            lang_instruction = "SUMAGOT SA TAGALOG/FILIPINO." if lang in ["tl", "akl"] else "RESPOND IN ENGLISH."
            return f"""USER QUESTION: {query}{nlu_analysis}{entity_analysis}{lang_analysis}

INSTRUCTIONS: Answer the user's question. Use the NLP analysis to understand the user's intent and entities better. If you don't know the answer, say you don't know and suggest visiting the school office. {lang_instruction}"""
    
    def _get_fallback_response(self, lang: str) -> str:
        """Get fallback response in appropriate language"""
        if lang == "tl" or lang == "akl":
            return "Paumanhin, may problema sa pagproseso ng inyong tanong. Subukan ninyo ulit mamaya."
        else:
            return "Sorry, there was a problem processing your question. Please try again later."
    
    def get_contact_escalation_response(self, lang: str, contact_type: str = "general", supabase_client=None, user_name: str = None) -> str:
        """Get personalized contact escalation response using NLP-based language detection and formatting"""
        
        # Contact information - configurable through environment variables
        import os
        messenger_url = os.environ.get("SCHOOL_MESSENGER_URL", "https://m.me/114901Tomas")
        
        # Get office hours from Supabase database
        office_hours = "Office hours not available"  # Default fallback
        guidance_hours = "Guidance hours not available"  # Default fallback
        
        if supabase_client:
            try:
                # Try to get office hours from database - exact match for "Office Hours"
                result = supabase_client.table("chatbot_prompts").select("response").ilike("keywords", "%Office Hours%").execute()
                if result.data and len(result.data) > 0:
                    office_hours = result.data[0].get("response", office_hours)
                    logger.info(f"📅 Retrieved office hours from database: {office_hours}")
                
                # Try to get guidance hours from database
                result = supabase_client.table("chatbot_prompts").select("response").ilike("keywords", "%guidance hours%").execute()
                if result.data and len(result.data) > 0:
                    guidance_hours = result.data[0].get("response", guidance_hours)
                    logger.info(f"📅 Retrieved guidance hours from database: {guidance_hours}")
            except Exception as e:
                logger.warning(f"Could not fetch office hours from database: {e}")
                # Use default values
        
        # 🚨 NEW: Use NLP to determine the appropriate language and create personalized response
        response_data = self._generate_personalized_contact_response(lang, contact_type, user_name, office_hours, guidance_hours, messenger_url)
        
        return response_data
    
    def _generate_personalized_contact_response(self, lang: str, contact_type: str, user_name: str, office_hours: str, guidance_hours: str, messenger_url: str) -> str:
        """Generate personalized contact response using NLP analysis"""
        
        # Determine if we should use Tagalog/Aklanon or English based on NLP analysis
        use_tagalog = self._should_use_tagalog_response(lang)
        
        # Create personalized greeting
        greeting = self._create_personalized_greeting(user_name, use_tagalog)
        
        # Generate contact information with proper formatting
        contact_info = self._format_contact_information(contact_type, use_tagalog, office_hours, guidance_hours)
        
        # Create the complete response
        response = f"""{greeting}

{contact_info}

<a href="{messenger_url}" target="_blank" style="display: inline-block; background-color: #0084ff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 10px 0;">📱 Chat with us on Messenger</a>"""
        
        return response
    
    def _should_use_tagalog_response(self, lang: str) -> bool:
        """Use NLP to determine if response should be in Tagalog/Aklanon"""
        # If language detection indicates Tagalog or Aklanon, use Tagalog response
        return lang in ["tl", "akl"]
    
    def _create_personalized_greeting(self, user_name: str, use_tagalog: bool) -> str:
        """Create personalized greeting using NLP"""
        if user_name:
            if use_tagalog:
                return f"Kumusta {user_name}! Para sa mga tanong na kailangan ng live person:"
            else:
                return f"Hi {user_name}! For questions that need a live person:"
        else:
            if use_tagalog:
                return "Para sa mga tanong na kailangan ng live person:"
            else:
                return "For questions that need a live person:"
    
    def _format_contact_information(self, contact_type: str, use_tagalog: bool, office_hours: str, guidance_hours: str) -> str:
        """Format contact information as natural sentences"""
        
        if use_tagalog:
            if contact_type == "urgent":
                return f"Maaari kayong tumawag sa school office o pumunta doon para sa immediate assistance. Office hours: {office_hours}"
            
            elif contact_type == "guidance":
                return f"Maaari kayong pumunta sa Guidance Office (katabi ng Principal's Office) o tumawag sa school office para sa appointment. Available: {guidance_hours}"
            
            else:  # general
                return f"Maaari kayong tumawag sa school office, pumunta doon, o mag-email sa school. Office hours: {office_hours}"
        
        else:  # English
            if contact_type == "urgent":
                return f"You can call the school office or visit for immediate assistance. Office hours: {office_hours}"
            
            elif contact_type == "guidance":
                return f"You can visit the Guidance Office (next to Principal's Office) or call the school office for an appointment. Available: {guidance_hours}"
            
            else:  # general
                return f"You can call the school office, visit in person, or email the school. Office hours: {office_hours}"
    
    def split_long_response(self, response: str, max_length: int = 200) -> List[str]:
        """Split long responses into multiple messages for better chat bubble display"""
        if len(response) <= max_length:
            return [response]
        
        # Split by sentences first, then by words if needed
        sentences = response.split('. ')
        messages = []
        current_message = ""
        
        for sentence in sentences:
            # Add period back if it was removed by split
            if not sentence.endswith('.') and not sentence.endswith('!') and not sentence.endswith('?'):
                sentence += '.'
            
            # Check if adding this sentence would exceed max_length
            test_message = current_message + sentence + " " if current_message else sentence + " "
            
            if len(test_message.strip()) <= max_length:
                current_message = test_message
            else:
                # If current message has content, save it
                if current_message.strip():
                    messages.append(current_message.strip())
                
                # If the sentence itself is too long, split it by words
                if len(sentence) > max_length:
                    words = sentence.split()
                    temp_message = ""
                    for word in words:
                        if len(temp_message + word + " ") <= max_length:
                            temp_message += word + " "
                        else:
                            if temp_message.strip():
                                messages.append(temp_message.strip())
                            temp_message = word + " "
                    current_message = temp_message
                else:
                    current_message = sentence + " "
        
        # Add the last message if it has content
        if current_message.strip():
            messages.append(current_message.strip())
        
        return messages
