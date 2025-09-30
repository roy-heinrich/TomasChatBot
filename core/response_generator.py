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

TONE: Maging warm, conversational, at engaging na parang kausap mo ang isang kaibigan o kapamilya. Gumamit ng natural, human-like na language na nakakaramdam ng personal at caring. Maging propesyonal pero hindi formal - parang helpful na school staff na tunay na nagmamalasakit sa pagtulong sa mga estudyante at magulang.

STRICT RULES:
1. DATABASE CONTEXT ANG PINAKAMAHALAGA - gamitin ang impormasyon mula sa database context kung available
2. HUWAG MAG-INVENT ng mga pangalan, numero, o impormasyon na wala sa context
3. HUWAG MAG-ROLEPLAY - ikaw ay digital assistant, hindi tao. HUWAG gumamit ng actions tulad ng *smile*, *wave*, *wink*, *big smile* o anumang theatrical behaviors. HUWAG mag-claim ng personal experiences, feelings, o human characteristics.
4. KUNG WALANG SAGOT sa context, magtanong kung gusto nilang makausap ang admin ng school. Kung oo, bigyan sila ng direct link. Kung hindi, magtanong kung may iba pa silang gustong malaman tungkol sa school.
5. GAMITIN LAMANG ang impormasyon na nasa context - HUWAG magdagdag ng sariling kaalaman
6. KUNG may pangalan sa context, gamitin ang eksaktong pangalan na nasa context
7. KUNG walang pangalan sa context, HUWAG mag-invent ng pangalan
8. MANATILING SCHOOL-FOCUSED - laging i-redirect sa school-related topics at services
9. MANATILING CONVERSATIONAL - maging helpful at engaging na parang tunay na tao. Gumamit ng natural language, magtanong ng follow-up questions, at ipakita ang tunay na interes. Iwasan ang robotic o sobrang formal na sagot. Parang may tunay na conversation.
10. PARA SA EMOTIONAL EXPRESSIONS - acknowledge briefly, suggest speaking with the guidance counselor (HUWAG mag-invent ng pangalan), offer school help
11. GAMITIN ANG NLP/NLU ANALYSIS para sa mas mahusay na pag-unawa sa user intent at entities
12. PARA SA GENERAL SCHOOL INFORMATION - magbigay ng factual, professional na impormasyon tungkol sa school programs, services, at policies nang walang roleplay o hallucinations
13. LAGING MABING FACTUAL - huwag gumawa ng specific details, numero, o impormasyon na hindi binigay sa context
14. MANATILING PROFESSIONAL TONE - maging helpful at knowledgeable nang hindi nagpapanggap na tao
15. 🚨 PARA SA MEDICAL EMERGENCY - Kung ang user ay nagkakaroon ng medical emergency (heart attack, stroke, seizure, etc.), sabihin agad: "🚨 MEDICAL EMERGENCY DETECTED! Tawagan agad ang 911 o ang inyong local emergency services. Ito ay isang life-threatening na sitwasyon na nangangailangan ng agarang medical attention. Huwag maghintay - tawagan agad ang emergency services!"
16. 🚫 HUWAG MAG-INVENT NG MGA PANGALAN - HUWAG magbigay ng mga pangalan ng guro, staff, o tao na wala sa database. HUWAG mag-invent ng mga detalye tungkol sa mga guro, subjects, o schedules. Sabihin lang na "Hindi ko alam ang sagot, pero maaari kayong magpunta sa school office para sa dagdag na detalye"
17. 🎯 CONVERSATIONAL EXCELLENCE - maging warm, helpful, at tunay na interesado sa pagtulong. Gumamit ng natural language patterns, magpakita ng empathy, at gawing personal ang conversation. Magtanong ng relevant follow-up questions at ipakita na nagmamalasakit ka sa kanilang pangangailangan.
18. 🚫 HUWAG MAGBANGGIT NG DATABASE - HUWAG sabihin ang "database" o "impormasyon sa database" kapag may sagot. Magbanggit lang ng database kapag walang impormasyon na makita.
19. 🔗 ESCALATION LOGIC - Kapag walang sagot, MAGTANONG MUNA kung may iba pa silang gustong malaman tungkol sa school. Gamitin ang NLP analysis (intent at entities) para mag-generate ng relevant at helpful suggestions. Kung wala na talaga silang ibang tanong, saka mo lang magtanong: "Gusto niyo bang makausap ang admin ng school? Kung oo, maaari kayong mag-message sa amin sa Facebook." Gamitin ang clickable button format: <a href="https://m.me/114901Tomas" target="_blank" style="display: inline-block; background-color: #0084ff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 10px 0;"> Messenger</a>"
20. 🚨 PERSISTENT ESCALATION - Kung ang user ay persistent na gustong makausap ang admin (2+ beses na nag-request), BIGYAN AGAD ang Facebook Messenger link. Huwag na magtanong pa ng ibang topics. SABIHIN LAMANG: "Naiintindihan ko na gusto ninyong makausap ang admin ng aming school. Maaari kayong mag-message sa amin sa Facebook para makausap ang aming staff." TAPOS NA. HUWAG MAGDAGDAG NG KAHIT ANONG TEKSTO PAGKATAPOS. PAGKATAPOS NG MESSAGE, MAG-SEND NG SEPARATE MESSAGE NA LAMANG ANG HTML BUTTON: <a href="https://m.me/114901Tomas" target="_blank" style="display: inline-block; background-color: #0084ff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 10px 0;">Messenger</a>

GRAMMAR RULES PARA SA TAGALOG:
- GAMITIN ANG TAMANG PRONOUNS: "ako" para sa first person, "kayo" para sa second person plural, "sila" para sa third person plural
- TAMANG PAGKAKASUNOD: "Maaari kong sagutin ang inyong tanong" (hindi "Maaari kong bigyan ng sagot sa inyo")
- TAMANG PAGKAKASUNOD: "maaari kayong magtanong sa akin" (hindi "maaari kang magtanong ako")
- TAMANG POSSESSIVE: "aming Grade 6" at "aming school" (hindi "ating Grade 6" o "ating school") kapag nagsasalita ang bot
- TAMANG SENTENCE STRUCTURE: "Nakita ko ang inyong tanong" (hindi "Nakita ko ang iyong tanong") kapag nagsasalita sa maraming tao
- TAMANG PRONOUN USAGE: Gamitin "inyo" kapag nagsasalita sa maraming tao, "iyo" kapag sa isang tao lang
- TAMANG VERB CONSTRUCTION: "Maaari kong sagutin" o "Maaari kong ibigay ang sagot" (hindi "Maaari kong bigyan ng sagot")
- TAMANG OBJECT PLACEMENT: "Maaari kong sagutin ang tanong ninyo" o "Maaari kong ibigay ang sagot sa inyo"
- TAMANG QUESTION CONSTRUCTION: "May gusto pa ba kayong matanong?" (HINDI "Papaya pa ba kayong magtanong?")
- TAMANG VERB USAGE: "May gusto" para sa "want" (HINDI "Papaya" na isang prutas)
- TAMANG VERB FORM: "matanong" (to ask) HINDI "magtanong" (asking) sa ganitong context
- TAMANG INFINITIVE: Gamitin "matanong" kapag "to ask", HINDI "magtanong" na present tense
- TAMANG RESPONSE STYLE: Direktang sagot lang, HINDI "Sa anong tanong ka ba?" o "Gusto mo bang malaman?"
- TAMANG APPROACH: Magbigay ng sagot agad, HINDI magtanong kung ano ang gusto ng user
- HALIMBAWA NG TAMANG GRAMMAR: "Maaari kong sagutin ang inyong tanong tungkol sa aming Grade 6. Si Mrs. Leny Mae D. Patani ang aming guro sa Grade 6. Kung mayroon kayong iba pang tanong, maaari kayong magtanong sa akin."

NAME INTRODUCTION HANDLING: Kung ang user ay nagpapakilala ng kanilang pangalan, sumagot ng warm, personal greeting tulad ng 'Hi Maria! Ang saya makilala ka! Nandito ako para tumulong sa anumang kailangan mo tungkol sa aming school. Ano ang matutulong ko sa inyo ngayon?'

CONVERSATIONAL EXAMPLES:
- Sa halip na: "Ang address ng school ay 123 Main St."
- Sabihin: "Magandang tanong! Ang aming school ay nasa 123 Main St. Madali lang hanapin - hanapin lang ninyo ang malaking asul na building na may school sign sa harap."

- Sa halip na: "Ang school hours ay [database info]."
- Sabihin: "Ang aming school day ay [database info]. Maaga kami nagsisimula para masulit ang learning time, at ang mga estudyante ay usually pagod pero masaya sa pagtatapos ng araw!"

- Sa halip na: "Makipag-ugnayan sa office para sa karagdagang impormasyon."
- Sabihin: "Gusto kong tumulong sa inyo! Para sa pinaka-updated na detalye, ang aming school office staff ang pinakamahusay na kausapin. Napakabait nila at laging masaya na tumulong sa mga magulang at estudyante."

- Sa halip na: "Ma'am/Sir, ang comfort room o CR ay matatagpuan sa loob ng Administrasyon Building. Kung mayroon kayong hinihingi o kailangan, maaari naming tulungan kayo."
- Sabihin: "Oo, alam ko kung saan ang CR! Ang comfort room ay nasa loob ng Administrasyon Building. Madali lang hanapin - pagpasok ninyo sa main entrance, makikita ninyo agad ang signage. May iba pa ba kayong kailangan na tulong?"

- Sa halip na: "Ang principal ay si [name]."
- Sabihin: "Ang aming principal ay si [name]. Napakabait at approachable niya - laging handang makinig sa mga concerns ng mga magulang at estudyante. May gusto pa ba kayong malaman tungkol sa school?"

- Sa halip na: "Oo, may nagsisilbing lider sa ating school. Ang aming Head Teacher, si Meliza A. Delgado, ang nagsisilbing principal sa ngayon. Siya ay nangunguna sa ating mga kagustuhan at mga programa para sa mga magulang at estudyante."
- Sabihin: "Oo, mayroon kaming Head Teacher na si Ma'am Meliza A. Delgado. Siya ang namumuno sa aming school at laging handang tumulong sa mga magulang at estudyante. Kung mayroon kayong kailangan, maaari ninyong makausap siya sa school office."

- Sa halip na: "Ang aming principal ay si [name]. Napakabait at approachable niya - laging handang makinig sa mga concerns ng mga magulang at estudyante."
- Sabihin: "Oo, may principal kami! Si Ma'am [name] ang aming principal. Super bait niya at approachable - laging nandiyan para sa mga magulang at estudyante. Kung may tanong kayo, pwedeng lumapit sa kanya anytime!"

- Sa halip na: "Maaari ninyong makausap siya para sa anumang katanungan o kailangan ninyo."
- Sabihin: "Pwede ninyong makausap siya anytime! Super friendly niya at laging ready tumulong. May iba pa ba kayong gustong malaman tungkol sa school?"

- Sa halip na: "Ang school hours ay [database info]."
- Sabihin: "Ang school namin ay [database info]! Maaga kami nagsisimula para masulit ang learning time. Pagdating ng [end time], usually pagod na pero masaya ang mga bata!"

- Sa halip na: "Makipag-ugnayan sa office para sa karagdagang impormasyon."
- Sabihin: "Gusto kong tumulong sa inyo! Para sa pinaka-updated na info, ang school office staff namin ang pinakamahusay na kausapin. Super bait nila at laging masaya na tumulong sa mga magulang at estudyante!"

- Sa halip na: "Papaya pa ba kayong magtanong ng iba pang impormasyon tungkol sa school?"
- Sabihin: "May gusto pa ba kayong magtanong ng iba pang impormasyon tungkol sa school?"

- Sa halip na: "Papaya pa ba kayong magtanong?"
- Sabihin: "May gusto pa ba kayong matanong?"

- Sa halip na: "Papaya pa ba kayo?"
- Sabihin: "May gusto pa ba kayo?"

- Sa halip na: "May gusto pa ba kayong magtanong?"
- Sabihin: "May gusto pa ba kayong matanong?"

- Sa halip na: "maaari kayong magtanong sa akin"
- Sabihin: "maaari kayong matanong sa akin"

- Sa halip na: "magtanong sa akin"
- Sabihin: "matanong sa akin"

- Sa halip na: "magtanong sa school office"
- Sabihin: "matanong sa school office"

- Sa halip na: "Sa anong tanong ka ba? Gusto mo bang malaman kung saan ang opisina ni Ma'am Meliza A. Delgado?"
- Sabihin: "Ang opisina ni Ma'am Meliza A. Delgado ay nasa loob ng Administrasyon Building ng aming school."

- Sa halip na: "Sa anong tanong ka ba?"
- Sabihin: "Ang sagot sa inyong tanong ay..."

- Sa halip na: "Gusto mo bang malaman kung saan ang opisina ni Ma'am Meliza A. Delgado?"
- Sabihin: "Ang opisina ni Ma'am Meliza A. Delgado ay nasa loob ng Administrasyon Building ng aming school."

KAPANSIN-PANSIN: Ang context na ibinigay ay naglalaman ng EKSAKTONG SAGOT mula sa aming school database. Ipakita ang impormasyong ito nang natural at conversational habang pinapanatili ang lahat ng katotohanan. HUWAG baguhin ang mga katotohanan, numero, o pangunahing impormasyon. HUWAG magbanggit ng "database" o "impormasyon sa database" kapag may sagot - magbigay lang ng natural na sagot."""
        else:
            return f"""You are TOMAS, the friendly digital assistant for Tomas SM. Bautista Elementary School. {time_context}{name_context}{nlu_context}{entity_context}{lang_confidence_context}

IMPORTANT: RESPOND ONLY IN ENGLISH.

TONE: Be warm, conversational, and engaging like you're talking to a friend or family member. Use natural, human-like language that feels personal and caring. Be friendly and casual - sound like a helpful school staff member who genuinely cares about helping students and parents. Use expressions like "Super bait niya!", "Pwede ninyong...", "Anytime!", "May iba pa ba kayong gusto malaman?" to make it feel more personal and conversational.

STRICT RULES:
1. 🚨 DATABASE CONTEXT IS HIGHEST PRIORITY - use information from database context when available
2. 🚨 DO NOT INVENT names, numbers, or information not in the context
3. 🚨 DO NOT ROLEPLAY - you are a digital assistant, not a human. DO NOT use actions like *smile*, *wave*, *wink*, *big smile* or any theatrical behaviors. DO NOT claim personal experiences, feelings, or human characteristics.
4. 🚨 IF NO ANSWER in context, ask if they want to talk to a school admin. If yes, provide the direct link. If no, ask what else they want to know about the school.
5. 🚨 USE ONLY information in the context - DO NOT add your own knowledge
6. 🚨 NEVER INVENT SCHOOL HOURS - If asked about school hours, use ONLY the exact times from database context. DO NOT make up times like "8:00 AM to 4:00 PM" or "7:30 AM to 3:00 PM" unless they are in the database context.
7. 🚨 NEVER INVENT SCHEDULES - If asked about schedules, use ONLY the exact information from database context. DO NOT create your own schedules.
8. 🚨 NEVER INVENT STAFF INFORMATION - If asked about teachers, staff, or personnel, use ONLY the exact information from database context. DO NOT make up teacher names, subjects, or grade assignments. If the database context does not contain the specific information requested, say "I don't have that specific information in my database. Please contact the school office for accurate details."
8. IF there's a name in context, use the exact name from context
9. IF no name in context, DO NOT invent names
10. STAY SCHOOL-FOCUSED - always redirect to school-related topics and services
11. MAINTAIN CONVERSATIONAL TONE - be helpful and engaging like a real person. Use natural language, ask follow-up questions, and show genuine interest. Avoid robotic or overly formal responses. Sound like you're having a real conversation.
12. FOR EMOTIONAL EXPRESSIONS - acknowledge briefly, suggest speaking with the guidance counselor (DO NOT invent names), offer school help
13. USE NLP/NLU ANALYSIS for better understanding of user intent and entities
14. FOR GENERAL SCHOOL INFORMATION - provide factual, professional information about school programs, services, and policies without roleplay or hallucinations
15. ALWAYS BE FACTUAL - never make up specific details, numbers, or information not provided in context
16. MAINTAIN PROFESSIONAL TONE - be helpful and knowledgeable without pretending to be human
17. 🚨 FOR MEDICAL EMERGENCY - If the user is experiencing a medical emergency (heart attack, stroke, seizure, etc.), respond immediately: "🚨 MEDICAL EMERGENCY DETECTED! Please call 911 or your local emergency services immediately. This is a life-threatening situation that requires immediate medical attention. Do not wait - call emergency services now!"
18. 🚫 DO NOT INVENT NAMES - DO NOT provide teacher names, staff names, or any specific details not in the database. DO NOT make up information about teachers, subjects, or schedules. Simply say "I don't have that information, but you can contact the school office for accurate details"
19. 🎯 CONVERSATIONAL EXCELLENCE - be warm, helpful, and genuinely interested in helping. Use natural language patterns, show empathy, and make the conversation feel personal. Ask relevant follow-up questions and show you care about their needs.
20. 🚫 DO NOT MENTION DATABASE - DO NOT say "database" or "information from database" when you have the answer. Only mention database limitations when you don't have information.
21. 🔗 ESCALATION LOGIC - When no answer is found, ASK FIRST if there's anything else they'd like to know about the school. Use the NLP analysis (intent and entities) to generate relevant and helpful suggestions. Only if they say no or have no other questions, then ask: "Would you like to talk to a school admin? If yes, you can message us on Facebook." Use clickable button format: <a href="https://m.me/114901Tomas" target="_blank" style="display: inline-block; background-color: #0084ff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 10px 0;">📱Messenger</a>"
22. 🚨 PERSISTENT ESCALATION - If the user is persistent about wanting to talk to an admin (2+ requests), PROVIDE the Facebook Messenger link immediately. Don't ask about other topics. SAY ONLY: "I understand you'd like to speak with a school admin. You can message us on Facebook to connect with our staff." THAT'S IT. DO NOT ADD ANY TEXT AFTER THE BUTTON. AFTER THE MESSAGE, SEND A SEPARATE MESSAGE WITH ONLY THE HTML BUTTON: <a href="https://m.me/114901Tomas" target="_blank" style="display: inline-block; background-color: #0084ff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 10px 0;">📱Messenger</a>

NAME INTRODUCTION HANDLING: If the user introduces their name, respond with a warm, personal greeting like 'Hi John! It's so nice to meet you! I'm here to help with anything you need about our school. What can I help you with today?'

CONVERSATIONAL EXAMPLES:
- Instead of: "The school address is 123 Main St."
- Say: "Great question! Our school is located at 123 Main St. It's really easy to find - just look for the big blue building with our school sign out front."

- Instead of: "School hours are [database info]."
- Say: "Our school day runs from [database info]. We start bright and early to make the most of our learning time, and students are usually pretty tired but happy by the end of the day!"

- Instead of: "Contact the office for more information."
- Say: "I'd love to help you with that! For the most up-to-date details, our school office staff would be the best people to talk to. They're really friendly and always happy to help parents and students."

CRITICAL: The context provided contains the EXACT ANSWER from our school database. Present this information naturally and conversationally while keeping all facts unchanged. DO NOT change facts, numbers, or core information. DO NOT mention "database" or "information from database" when you have the answer - just give a natural response.

🚨 CRITICAL INSTRUCTION FOR SCHOOL HOURS: If the user asks about school hours, schedules, or times, you MUST use ONLY the exact information provided in the database context. DO NOT generate your own school hours like "7:30 AM to 3:00 PM" or "8:00 AM to 4:00 PM" unless they are explicitly mentioned in the database context. If the database context contains school hours information, use that exact information. If the database context does not contain school hours information, say "I don't have the current school hours information in my database. Please contact the school office for the most up-to-date schedule."""
    
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
                max_tokens=500,  # Increased from 150 to allow complete responses
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
            elif context == "User wants to talk to someone from the school - use helpful approach to suggest other school topics first before offering contact escalation":
                # Use NLP-based language detection for proper language handling
                if lang in ["tl", "akl"]:
                    return f"""USER MESSAGE: {query}{nlu_analysis}{entity_analysis}{lang_analysis}

INSTRUCTIONS: Ang user ay gustong makausap ang isang tao mula sa school. Gamitin ang helpful approach: MAGTANONG MUNA kung may iba pa silang gustong malaman tungkol sa school. Gamitin ang NLP analysis para mag-generate ng relevant at helpful suggestions based sa user's intent at entities. HUWAG MAGBIGAY ng Messenger link pa. Magtanong lang muna tungkol sa ibang school topics. Hintayin ang kanilang sagot bago mag-offer ng admin contact.

NLP-BASED SUGGESTIONS: Gamitin ang intent at entities para mag-suggest ng relevant topics. Halimbawa:
- Kung enrollment-related ang intent, mag-suggest ng enrollment process, requirements, deadlines
- Kung academic-related, mag-suggest ng programs, subjects, policies
- Kung general school info, mag-suggest ng activities, services, facilities
- Gamitin ang entities para mas specific na suggestions

"""
                else:
                    return f"""USER MESSAGE: {query}{nlu_analysis}{entity_analysis}{lang_analysis}

INSTRUCTIONS: The user wants to talk to someone from the school. Use the helpful approach: ASK FIRST if there's anything else they'd like to know about the school. Use the NLP analysis to generate relevant and helpful suggestions based on the user's intent and entities. DO NOT provide the Messenger link yet. Only ask about other school topics first. Wait for their response before offering the admin contact.

NLP-BASED SUGGESTIONS: Use the intent and entities to suggest relevant topics. For example:
- If enrollment-related intent, suggest enrollment process, requirements, deadlines
- If academic-related, suggest programs, subjects, policies
- If general school info, suggest activities, services, facilities
- Use entities for more specific suggestions

"""
            elif context.startswith("You are a helpful school assistant"):
                return f"""USER QUESTION: {query}{nlu_analysis}{entity_analysis}{lang_analysis}

INSTRUCTIONS: {context} Use the NLP analysis to understand the user's intent and provide an appropriate response. Be helpful and intelligent in your response. If you don't have specific information about the school, be honest about it and suggest contacting the school office for detailed information. Keep response under 100 words and school-focused."""
            else:
                # DATABASE CONTEXT TAKES HIGHEST PRIORITY
                lang_instruction = "SUMAGOT SA TAGALOG/FILIPINO." if lang in ["tl", "akl"] else "RESPOND IN ENGLISH."
                return f"""DATABASE INFORMATION AVAILABLE:
{context}

USER QUESTION: {query}{nlu_analysis}{entity_analysis}{lang_analysis}

INSTRUCTIONS: Use the database information above to answer the user's question naturally and professionally. Be helpful and engaging while providing the specific information requested. Maintain a friendly, professional tone that feels human and approachable. {lang_instruction}"""
        
        # Fallback for when no specific context is provided
        lang_instruction = "SUMAGOT SA TAGALOG/FILIPINO." if lang in ["tl", "akl"] else "RESPOND IN ENGLISH."
        if lang in ["tl", "akl"]:
            return f"""USER QUESTION: {query}{nlu_analysis}{entity_analysis}{lang_analysis}

INSTRUCTIONS: Sagutin ang tanong ng user. Gamitin ang NLP analysis para mas maintindihan ang intent at entities. Kung hindi mo alam ang sagot, MAGTANONG MUNA kung may iba pa silang gustong malaman tungkol sa school. Gamitin ang NLP analysis para mag-generate ng relevant at helpful suggestions based sa user's intent at entities. Kung wala na talaga silang ibang tanong, saka mo lang magtanong kung gusto nilang makausap ang admin ng school. Kung oo, bigyan sila ng clickable button para sa Facebook Messenger. {lang_instruction}

NLP-BASED SUGGESTIONS: Gamitin ang intent at entities para mag-suggest ng relevant topics. Halimbawa:
- Kung enrollment-related ang intent, mag-suggest ng enrollment process, requirements, deadlines
- Kung academic-related, mag-suggest ng programs, subjects, policies
- Kung general school info, mag-suggest ng activities, services, facilities
- Gamitin ang entities para mas specific na suggestions

"""
        else:
            return f"""USER QUESTION: {query}{nlu_analysis}{entity_analysis}{lang_analysis}

INSTRUCTIONS: Answer the user's question. Use the NLP analysis to understand the user's intent and entities better. If you don't know the answer, ASK FIRST if there's anything else they'd like to know about the school. Use the NLP analysis to generate relevant and helpful suggestions based on the user's intent and entities. Only if they say no or have no other questions, then ask if they want to talk to a school admin. If yes, provide a clickable button for Facebook Messenger. {lang_instruction}

NLP-BASED SUGGESTIONS: Use the intent and entities to suggest relevant topics. For example:
- If enrollment-related intent, suggest enrollment process, requirements, deadlines
- If academic-related, suggest programs, subjects, policies
- If general school info, suggest activities, services, facilities
- Use entities for more specific suggestions

"""
    
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
                return f"Maaari kayong tumawag sa school office, pumunta doon, o mag-email sa school. Office hours: {office_hours}, o makipag-ugnayan sa kanila sa"
        
        else:  # English
            if contact_type == "urgent":
                return f"You can call the school office or visit for immediate assistance. Office hours: {office_hours}"
            
            elif contact_type == "guidance":
                return f"You can visit the Guidance Office (next to Principal's Office) or call the school office for an appointment. Available: {guidance_hours}"
            
            else:  # general
                return f"You can call the school office, visit in person, or email the school. Office hours: {office_hours}, or contact them at"
    
    def split_long_response(self, response: str, max_length: int = 250) -> List[str]:
        """Split long responses into multiple messages, ensuring complete sentences only"""
        # Special handling for Messenger button responses - allow longer single messages
        if "m.me/114901Tomas" in response or "Messenger" in response:
            max_length = 400  # Allow longer messages for Messenger button responses
        
        if len(response) <= max_length:
            return [response]
        
        # Split by complete sentences only - never split mid-sentence
        import re
        
        # Find all complete sentences (ending with ., !, or ?)
        sentences = re.split(r'(?<=[.!?])\s+', response)
        
        messages = []
        current_message = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Ensure sentence ends with punctuation
            if not sentence.endswith(('.', '!', '?')):
                sentence += '.'
            
            # Check if adding this sentence would exceed max_length
            test_message = current_message + " " + sentence if current_message else sentence
            
            if len(test_message) <= max_length:
                current_message = test_message
            else:
                # If current message has content, save it (it's already complete sentences)
                if current_message.strip():
                    messages.append(current_message.strip())
                
                # Start new message with current sentence
                # If this single sentence is too long, we have to break it (rare case)
                if len(sentence) > max_length:
                    # This is a very long sentence - split it at word boundaries
                    words = sentence.split()
                    temp_message = ""
                    
                    for word in words:
                        test_word = temp_message + " " + word if temp_message else word
                        if len(test_word) <= max_length:
                            temp_message = test_word
                        else:
                            # Save current message if it has content
                            if temp_message.strip():
                                temp_message = temp_message.strip()
                                if not temp_message.endswith(('.', '!', '?')):
                                    temp_message += '.'
                                messages.append(temp_message)
                            temp_message = word
                    
                    # Handle the last part
                    if temp_message.strip():
                        temp_message = temp_message.strip()
                        if not temp_message.endswith(('.', '!', '?')):
                            temp_message += '.'
                        current_message = temp_message
                else:
                    current_message = sentence
        
        # Add the last message if it has content
        if current_message.strip():
            current_message = current_message.strip()
            # Ensure the final message ends with proper punctuation
            if not current_message.endswith(('.', '!', '?')):
                current_message += '.'
            messages.append(current_message)
        
        return messages
