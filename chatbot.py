import os
import re
import logging
import httpx
import langid
import random
from typing import List, Dict, Optional
from supabase import create_client, Client
# Remove unused import: from utils import fetch_summarized_text  
from fallback import FallbackHandler
from nlu_engine import NLUEngine, Intent, NLUResult
from dynamic_greetings import DynamicGreetingGenerator, GreetingContext
from entity_extractor import AdvancedEntityExtractor, ExtractedEntity
from conversation_memory import ConversationMemory, UserProfile, ConversationContext
from response_generator import ResponseGenerationEngine, ResponseContext, ResponseTone
from sentiment_analyzer import sentiment_analyzer, SentimentResult
import time
from datetime import datetime
from rapidfuzz import fuzz, process
import json
from deep_translator import GoogleTranslator
import openai
import asyncio
import urllib.parse
from dotenv import load_dotenv

# Optional Groq import - make it conditional
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger("chatbot")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
# Note: Supabase client will be created in the ChatBot class to ensure env vars are loaded

# Load Aklanon dictionary for query translation
# 🙏 Special thanks to Mr./Mrs. Cyberustics for providing the comprehensive 
# Aklanon-English dictionary JSON file that enables multilingual support!
# This valuable resource makes it possible for our chatbot to understand
# and translate Aklanon language queries effectively.
dict_path = os.path.join(os.path.dirname(__file__), "aklanon_dictionary.json")
aklanon_dict = {}
try:
    with open(dict_path, "r", encoding="utf-8") as f:
        aklanon_data = json.load(f)
        # Convert the nested dict structure to aklanon->english mapping
        for english_word, translations in aklanon_data.items():
            if isinstance(translations, dict) and "akl" in translations:
                aklanon_word = translations["akl"].lower()
                aklanon_dict[aklanon_word] = english_word
        logger.info(f"📚 Loaded {len(aklanon_dict)} Aklanon dictionary entries")
        # Debug: Show some sample entries
        sample_keys = list(aklanon_dict.keys())[:5]
        logger.info(f"📚 Sample entries: {[(k, aklanon_dict[k]) for k in sample_keys]}")
        # Debug: Check specific words we expect
        if "tawo" in aklanon_dict:
            logger.info(f"📚 Found 'tawo' → '{aklanon_dict['tawo']}'")
        if "minatuod" in aklanon_dict:
            logger.info(f"📚 Found 'minatuod' → '{aklanon_dict['minatuod']}'")
except Exception as e:
    logger.warning(f"Could not load Aklanon dictionary: {e}")
    aklanon_dict = {}

class ChatBot:
    def __init__(self, groq_key: str, enable_keyword_fallback: bool = True, aggressive_token_saving: bool = False):
        self.fallback_handler = FallbackHandler()
        self.groq_key = groq_key  
        self._cached_summary = None
        self._last_fetched = 0
        self.cache_ttl = 300  # e.g., 5 minutes
        self.groq_api = "https://api.groq.com/openai/v1/chat/completions"
        self.bucket = "summarized-text"
        self.file = "summarized_text.md"
        
        # Initialize NLU Engine for intent understanding
        self.nlu_engine = NLUEngine()
        
        # Initialize Advanced Entity Extractor
        self.entity_extractor = AdvancedEntityExtractor()
        
        # Initialize Conversation Memory System
        self.conversation_memory = ConversationMemory(max_history_length=50)
        logger.info("💭 Conversation memory system initialized")
        
        # Initialize Response Generation Intelligence
        self.response_generator = ResponseGenerationEngine()
        logger.info("🎯 Response Generation Intelligence initialized")
        
        # Initialize Dynamic Greeting Generator with optional groq client
        groq_client = None
        if GROQ_AVAILABLE and groq_key:
            try:
                groq_client = Groq(api_key=groq_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}")
        
        self.dynamic_greetings = DynamicGreetingGenerator(groq_client=groq_client)
        
        # Initialize Supabase client for full-text search
        from supabase import create_client, Client
        import os
        self.supabase: Client = create_client(
            os.environ.get("SUPABASE_URL"), 
            os.environ.get("SUPABASE_KEY")
        )
        
        # Token management settings
        self.enable_keyword_fallback = enable_keyword_fallback
        self.aggressive_token_saving = aggressive_token_saving

        # ✅ Centralized greetings + followups with time-aware variants
        self.messages = {
            "greeting": {
                "en": {
                    "morning": [
                        "Good morning! ☀️ I'm TOMAS, the chatbot representative of Tomas SM. Bautista Elementary School! What can I help you with today?",
                        "Good morning! 😊 I'm TOMAS, the chatbot representative of Tomas SM. Bautista Elementary School! How can I assist you?",
                        "Good morning! I'm TOMAS, the chatbot representative of Tomas SM. Bautista Elementary School! What would you like to know about our school?",
                        "Good morning! 🏫 I'm TOMAS, your chatbot assistant at Tomas SM. Bautista Elementary School! How may I help you?"
                    ],
                    "afternoon": [
                        "Good afternoon! ☀️ I'm TOMAS, the chatbot representative of Tomas SM. Bautista Elementary School! What can I help you with today?",
                        "Good afternoon! 😊 I'm TOMAS, the chatbot representative of Tomas SM. Bautista Elementary School! How can I assist you?",
                        "Good afternoon! I'm TOMAS, the chatbot representative of Tomas SM. Bautista Elementary School! What would you like to know about our school?",
                        "Good afternoon! 🏫 I'm TOMAS, your chatbot assistant at Tomas SM. Bautista Elementary School! How may I help you?"
                    ],
                    "evening": [
                        "Good evening! 🌙 I'm TOMAS, the chatbot representative of Tomas SM. Bautista Elementary School! What can I help you with today?",
                        "Good evening! 😊 I'm TOMAS, the chatbot representative of Tomas SM. Bautista Elementary School! How can I assist you?",
                        "Good evening! I'm TOMAS, the chatbot representative of Tomas SM. Bautista Elementary School! What would you like to know about our school?",
                        "Good evening! 🏫 I'm TOMAS, your chatbot assistant at Tomas SM. Bautista Elementary School! How may I help you?"
                    ],
                    "default": [
                        "Hello there! 👋 I'm TOMAS, the chatbot representative of Tomas SM. Bautista Elementary School! What can I help you with today?",
                        "Hi! 😊 I'm TOMAS, the chatbot representative of Tomas SM. Bautista Elementary School! How can I assist you?",
                        "Hello! I'm TOMAS, the chatbot representative of Tomas SM. Bautista Elementary School! What would you like to know about our school?",
                        "Hello! 🏫 I'm TOMAS, your chatbot assistant at Tomas SM. Bautista Elementary School! How may I help you?"
                    ]
                },
                "tl": {
                    "morning": [
                        "Magandang umaga! ☀️ Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Paano ko kayo matutulungan ngayon?",
                        "Magandang umaga! 😊 Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Ano ang maitutulong ko?",
                        "Magandang umaga po! Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Paano ko kayo matutulungan?",
                        "Magandang umaga po! 🏫 Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Paano ko kayo matutulong?"
                    ],
                    "afternoon": [
                        "Magandang hapon! ☀️ Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Paano ko kayo matutulungan ngayon?",
                        "Magandang hapon! 😊 Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Ano ang maitutulong ko?",
                        "Magandang hapon po! Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Paano ko kayo matutulungan?",
                        "Magandang hapon po! 🏫 Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Paano ko kayo matutulong?"
                    ],
                    "evening": [
                        "Magandang gabi! 🌙 Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Paano ko kayo matutulungan ngayon?",
                        "Magandang gabi! 😊 Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Ano ang maitutulong ko?",
                        "Magandang gabi po! Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Paano ko kayo matutulungan?",
                        "Magandang gabi po! 🏫 Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Paano ko kayo matutulong?"
                    ],
                    "default": [
                        "Magandang araw! 👋 Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Paano ko kayo matutulungan ngayon?",
                        "Kamusta! 😊 Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Ano ang maitutulong ko?",
                        "Kumusta po! Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Paano ko kayo matutulungan?",
                        "Hello po! 🏫 Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Paano ko kayo matutulong?"
                    ]
                }
            },
            "follow_up": {
                "en": [
                    "Anything else I can help you with? 😊",
                    "Got more questions? I'm all ears! 👂",
                    "Is there anything else you'd like to know?",
                    "What else can I help you discover about our school? 🏫"
                ],
                "tl": [
                    "May iba pa bang matutulungan ko sa inyo? 😊",
                    "May ibang tanong pa kaya? Nakikinig ako! 👂",
                    "Mayroon pa bang ibang gusto ninyong malaman?",
                    "Ano pa ang pwede kong ipakita sa inyo tungkol sa aming paaralan? 🏫"
                ]
            }
    }
    def reset_conversation(self, lang="en", user_timezone: str = None):
        """Reset chat history with a proper system prompt + greeting."""
        self.messages = [
            {
                "role": "system",
                "content": (
                    "You are TOMAS, a friendly and enthusiastic assistant for "
                    "Tomas SM. Bautista Elementary School! 🏫 You're like a warm, helpful "
                    "school staff member who genuinely loves helping people. Use emojis, "
                    "be conversational, and answer in the user's language (English, Tagalog, or Aklanon). "
                    "Make every interaction feel personal and welcoming! 😊"
                ),
            },
            {
                "role": "assistant",
                "content": self.get_greeting(lang, user_timezone),  # 👈 use your greeting helper
            },
        ]

    def get_time_period(self, user_timezone: str = None) -> str:
        """Determine the time of day based on current hour in user's timezone"""
        try:
            if user_timezone:
                # Use user's timezone if provided
                import pytz
                user_tz = pytz.timezone(user_timezone)
                current_hour = datetime.now(user_tz).hour
            else:
                # Fallback to Philippines timezone (server default for local users)
                import pytz
                ph_timezone = pytz.timezone('Asia/Manila')
                current_hour = datetime.now(ph_timezone).hour
        except Exception as e:
            # If timezone conversion fails, use server time as fallback
            logger.warning(f"Timezone conversion failed: {e}, using server time")
            current_hour = datetime.now().hour
        
        if 1 <= current_hour < 12:  # 1am-11:59am = morning
            return "morning"
        elif 12 <= current_hour < 19:  # 12pm-6:59pm = afternoon  
            return "afternoon"
        elif 19 <= current_hour <= 23 or current_hour == 0:  # 7pm-12:59am = evening
            return "evening"
        else:
            return "default"

    def get_time_aware_system_prompt(self, lang: str = "en", user_name: str = "", user_timezone: str = None):
        """Generate a time-aware system prompt for Groq API"""
        try:
            import pytz
            from datetime import datetime
            
            # Get current time in user's timezone or default to Philippines
            if user_timezone:
                user_tz = pytz.timezone(user_timezone)
            else:
                user_tz = pytz.timezone('Asia/Manila')  # Default to Philippines timezone
            
            current_time = datetime.now(user_tz)
            current_hour = current_time.hour
        except Exception as e:
            # Fallback to UTC time if timezone conversion fails
            current_hour = datetime.now().hour
        
        # Determine time context for the AI
        if 1 <= current_hour < 12:  # 1am-11:59am = morning
            time_context = "It's morning time (school starts at 8 AM)."
        elif 12 <= current_hour < 19:  # 12pm-6:59pm = afternoon
            time_context = "It's afternoon time (school day in progress or just ended)."
        elif 19 <= current_hour <= 23 or current_hour == 0:  # 7pm-12:59am = evening
            time_context = "It's evening time (school day has ended)."
        else:
            time_context = "It's late evening/night time (school is closed)."
        
        # Handle Aklanon by treating it as Tagalog
        if lang == "akl":
            lang = "tl"
        
        # Create language-specific system prompts
        if lang == "tl":
            # Add name context for Tagalog as well
            name_context = f" Ang kausap mo ay si {user_name}." if user_name else ""
            return f"Ikaw si TOMAS, ang digital assistant ng Tomas SM. Bautista Elementary School. {time_context}{name_context} Magbigay ng tumpak at kapaki-pakinabang na impormasyon tungkol sa paaralan. Huwag mag-imbento ng mga detalye na hindi mo alam. Kung hindi mo alam ang sagot, sabihin na makakausap nila ang school office para sa kumpletong impormasyon. Gamitin ang context na ibinigay para sa mga sagot sa TAGALOG. Tandaan ang mga pangalan mula sa conversation history kapag tinanong."
        else:  # Default to English
            # Add name context if available
            name_context = f" The person you're talking to is named {user_name}." if user_name else ""
            return f"You are TOMAS, the digital assistant for Tomas SM. Bautista Elementary School. {time_context}{name_context} Provide accurate and helpful information about the school based only on the context provided. Do not make up details, times, or procedures that you don't know. If you don't have specific information, direct them to contact the school office. Remember names from conversation history when asked. Keep responses professional and factual."

    async def get_greeting_async(self, lang: str = "en", user_timezone: str = None, intent: Intent = None, user_context: Dict = None) -> str:
        """Enhanced async greeting generation with dynamic AI-powered personalization"""
        
        # Create greeting context for dynamic generation
        if intent and intent in [Intent.GREETING_EXCITED, Intent.GREETING_FORMAL, Intent.GREETING_CASUAL, Intent.GREETING_RETURNING_USER]:
            context = GreetingContext(
                language=lang,
                time_period=self.get_time_period(user_timezone),
                user_name=user_context.get("name") if user_context else "",
                conversation_history=user_context.get("conversation_history", []) if user_context else [],
                user_mood=user_context.get("mood") if user_context else "",
                returning_user=(intent == Intent.GREETING_RETURNING_USER),
                school_context=intent.value.replace("greeting_", "")  # excited, formal, casual, returning_user
            )
            
            try:
                # Try to generate dynamic greeting (async)
                dynamic_greeting = await self.dynamic_greetings.generate_greeting(context)
                if dynamic_greeting and len(dynamic_greeting) > 10:  # Basic validation
                    logger.info(f"🎨 Using dynamic greeting for {intent.value}")
                    return dynamic_greeting
            except Exception as e:
                logger.warning(f"Dynamic greeting failed: {e}, falling back to static")
        
        # Fallback to existing static greeting system
        return self.get_greeting(lang, user_timezone)

    def get_greeting(self, lang: str = "en", user_timezone: str = None, intent: Intent = None, user_context: Dict = None) -> str:
        """Enhanced greeting generation with dynamic AI-powered personalization"""
        
        # For backwards compatibility, if intent is provided, try to run async version
        if intent and intent in [Intent.GREETING_EXCITED, Intent.GREETING_FORMAL, Intent.GREETING_CASUAL, Intent.GREETING_RETURNING_USER]:
            try:
                # Use asyncio to run the async version
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, we can't use run()
                    logger.warning("Cannot generate dynamic greeting in sync context within async loop, using static")
                else:
                    return asyncio.run(self.get_greeting_async(lang, user_timezone, intent, user_context))
            except Exception as e:
                logger.warning(f"Dynamic greeting failed: {e}, falling back to static")
        
        # Fallback to existing static greeting system
        time_period = self.get_time_period(user_timezone)
        
        # Handle Aklanon by using Tagalog greetings
        if lang == "akl":
            lang = "tl"
        
        # Get time-aware greetings
        greetings_dict = self.messages["greeting"].get(lang, self.messages["greeting"]["en"])
        
        # If the structure is the old flat list format, use default behavior
        if isinstance(greetings_dict, list):
            return random.choice(greetings_dict)
        
        # Use time-specific greetings
        greetings = greetings_dict.get(time_period, greetings_dict.get("default", greetings_dict["morning"]))
        return random.choice(greetings)

    def get_followup(self, lang: str = "en") -> str:
        # For Aklanon, use Tagalog follow-up
        if lang == "akl":
            lang = "tl"
        followups = self.messages["follow_up"].get(lang, self.messages["follow_up"]["en"])
        return random.choice(followups) if isinstance(followups, list) else followups

    def _detect_mood_from_query(self, query: str) -> str:
        """Detect user mood from their greeting message for dynamic personalization"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["awesome", "fantastic", "amazing", "great", "wonderful", "excited", "super"]):
            return "excited"
        elif any(word in query_lower for word in ["tired", "stressed", "busy", "difficult", "hard"]):
            return "supportive"
        elif any(word in query_lower for word in ["help", "need", "question", "confused", "lost"]):
            return "helpful"
        else:
            return "neutral"

    def get_goodbye(self, lang: str) -> str:
        messages = {
            "en": "Thank you for chatting! Goodbye 👋",
            "tl": "Maraming salamat sa pakikipag-usap! Paalam 👋"
        }
        return messages.get(lang, messages["en"])
    
    async def translate(self, text: str, source: str = "auto", target: str = "en", context: str = None) -> str:
        """Enhanced translation with context awareness for better fluency."""
        try:
            # For Aklanon-related translations to Tagalog, use more natural language
            if target == "tl" and any(word in text.lower() for word in ['school', 'location', 'fatima', 'teacher', 'principal']):
                logger.info("🔄 Using context-aware translation for school-related content")
                
                # Use OpenAI for more natural translation of school content
                try:
                    system_prompt = (
                        "Translate the following English text to natural, fluent Filipino/Tagalog. "
                        "This is about a school in the Philippines. Use appropriate Filipino terms for "
                        "school positions and locations. Make it sound natural and conversational."
                    )
                    
                    from openai import OpenAI
                    client = OpenAI()
                    
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": text}
                        ],
                        temperature=0.3
                    )
                    return response.choices[0].message.content.strip()
                except Exception as e:
                    logger.warning(f"OpenAI context-aware translation failed: {e}, using GoogleTranslator")
            
            # Default translation using GoogleTranslator
            return GoogleTranslator(source=source, target=target).translate(text)
            
        except Exception as e:
            logger.warning(f"deep_translator failed {source}->{target}: {e}")
            try:
                # Fallback to OpenAI with enhanced prompt
                system_prompt = f"Translate from {source} to {target}. Make the translation natural and fluent."
                if context:
                    system_prompt += f" Context: {context}"
                    
                from openai import OpenAI
                client = OpenAI()
                    
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.2
                )
                return response.choices[0].message.content.strip()
            except Exception as e2:
                logger.error(f"OpenAI translation failed: {e2}")
                return text
    
    def get_message(self, key: str, lang: str) -> str:
        """Return a localized message for the given key and lang."""
        if key not in self.messages:
            return ""
        if lang not in self.messages[key]:
            lang = "en"  # fallback
        value = self.messages[key][lang]
        if isinstance(value, list):
            return random.choice(value)  # random greeting
        return value  # fixed follow-up

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters for English)."""
        return len(text) // 4
    
    def _check_token_budget(self, query: str, context: str, lang: str = "en", user_timezone: str = None) -> dict:
        """Check if we're within token budget and suggest optimizations."""
        system_prompt = self.get_time_aware_system_prompt(lang, "", user_timezone)
        user_message = f"Context: {context}\nQuestion: {query}"
        
        estimated_input_tokens = self.estimate_tokens(system_prompt + user_message)
        max_output_tokens = 150
        total_estimated = estimated_input_tokens + max_output_tokens
        
        # Groq llama-3.1-8b-instant has ~8k context limit
        context_limit = 8000
        
        status = {
            "input_tokens": estimated_input_tokens,
            "total_estimated": total_estimated,
            "within_budget": total_estimated < context_limit * 0.8,  # 80% safety margin
            "context_reduction_needed": estimated_input_tokens > context_limit * 0.6,
            "emergency_mode_needed": total_estimated > context_limit * 0.9
        }
        
        logger.info(f"📊 Token budget: {total_estimated}/{context_limit} (~{(total_estimated/context_limit)*100:.1f}%)")
        
        return status

    async def detect_language(self, text: str) -> str:
        """Detect language with Aklanon markers triggering special handling."""
        try:
            # Explicit English markers for common words
            english_markers = [
                "where", "what", "when", "who", "why", "how", "the", "is", "are", 
                "school", "location", "address", "teacher", "principal", "student",
                "class", "grade", "program", "office", "information", "contact",
                "phone", "email", "time", "schedule", "hours", "enrollment",
                "good morning", "good afternoon", "good evening", "hello", "hi",
                "thanks", "thank you", "please", "sorry", "excuse me"
            ]
            
            # Aklanon markers that trigger Aklanon detection
            aklanon_markers = [
                "di", "du", "eun", "tanan", "dun", "don", "it", "nga", "ro", 
                "eon", "baga", "man", "hay", "sang", "sa", "kag", "kay", 
                "amo", "ini", "ina", "siin", "diin", "pila", "ano", "sin-o", 
                "kan-o", "ham-an", "gani", "guid", "gid", "lang", "man", 
                "bisan", "hasta", "para", "kon", "kung", "pero", "kundi",
                "maayong", "aga", "hapon", "gab-i", "adlaw"  # Aklanon greetings and time words
            ]
            
            # Filipino/Tagalog markers for better detection  
            tagalog_markers = [
                "sino", "saan", "ano", "kailan", "bakit", "paano", "ilan", 
                "ang", "ng", "sa", "si", "ni", "kay", "para", "para sa",
                "mga", "na", "ay", "po", "opo", "hindi", "oo", "wala",
                "meron", "may", "yung", "yun", "ito", "iyan", "iyon",
                "ako", "ikaw", "siya", "kami", "kayo", "sila", "tayo",
                "kumusta", "kamusta", "magandang", "salamat", "pasensya"
            ]
            
            text_lower = text.lower()
            
            # Check for explicit English phrases first (highest priority)
            english_phrases = ["good morning", "good afternoon", "good evening", "hello", "hi there"]
            for phrase in english_phrases:
                if phrase in text_lower:
                    logger.info(f"🔎 English phrase detected ('{phrase}') → en")
                    return "en"
            
            # Check for explicit English markers (word boundaries for better matching)
            english_count = 0
            for marker in english_markers:
                if len(marker.split()) > 1:  # Skip phrases (already checked above)
                    continue
                # Use word boundaries to avoid substring matches
                if f" {marker} " in f" {text_lower} " or text_lower.startswith(f"{marker} ") or text_lower.endswith(f" {marker}"):
                    english_count += 1
            
            # Count other language markers with word boundaries
            aklanon_count = 0
            for marker in aklanon_markers:
                if f" {marker} " in f" {text_lower} " or text_lower.startswith(f"{marker} ") or text_lower.endswith(f" {marker}"):
                    aklanon_count += 1
                    
            tagalog_count = 0  
            for marker in tagalog_markers:
                if len(marker.split()) > 1:  # Multi-word markers
                    if marker in text_lower:
                        tagalog_count += 1
                else:  # Single word markers with word boundaries
                    if f" {marker} " in f" {text_lower} " or text_lower.startswith(f"{marker} ") or text_lower.endswith(f" {marker}"):
                        tagalog_count += 1
            
            # If English markers dominate, it's English
            if english_count > 0 and english_count >= aklanon_count and english_count >= tagalog_count:
                logger.info(f"🔎 English markers detected ({english_count}) → en")
                return "en"
            
            # Check for Aklanon markers
            if aklanon_count > 0:
                logger.info(f"🔎 Aklanon markers detected ({aklanon_count}) → akl")
                return "akl"
            
            # Check for Tagalog markers
            if tagalog_count > 0:
                logger.info(f"🔎 Tagalog markers detected ({tagalog_count}) → tl")
                return "tl"
            
            # Use langid for other languages
            lang, prob = langid.classify(text)
            if lang.startswith("tl"):
                return "tl"
            if lang.startswith("en"):
                return "en"
            return "en"  # fallback to English for all others
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "en"  # safe fallback
    
    def translate_aklanon_query_keywords(self, query: str) -> str:
        """Translate Aklanon words in query to English for better search matching."""
        import re
        
        if not aklanon_dict:
            logger.warning("⚠️ Aklanon dictionary is empty or not loaded")
            return query
        
        logger.info(f"📚 Using dictionary with {len(aklanon_dict)} entries")
        
        # First, handle specific patterns that are common in questions
        query_lower = query.lower()
        
        # Handle "sin-o si [name]" pattern specifically
        if "sin-o si" in query_lower:
            # Extract the name part after "sin-o si"
            name_match = re.search(r'sin-o\s+si\s+([^?]+)', query_lower)
            if name_match:
                name_part = name_match.group(1).strip()
                # Return "who is [name]" format for better search
                translated = f"who is {name_part}"
                logger.info(f"🔄 Aklanon pattern translation: '{query}' → '{translated}'")
                return translated
        
        # Handle other Aklanon patterns
        if "sin-o ang" in query_lower:
            name_match = re.search(r'sin-o\s+ang\s+([^?]+)', query_lower)
            if name_match:
                name_part = name_match.group(1).strip()
                translated = f"who is the {name_part}"
                logger.info(f"🔄 Aklanon pattern translation: '{query}' → '{translated}'")
                return translated
        
        # Handle location patterns
        if any(word in query_lower for word in ['siin', 'diin', 'asa']) and any(word in query_lower for word in ['lokasyon', 'tomas', 'elementary', 'school', 'paaralan']):
            translated = "where is the school location"
            logger.info(f"🔄 Aklanon location pattern translation: '{query}' → '{translated}'")
            return translated
        
        # Handle teacher/staff patterns
        teacher_aklanon_words = ['maestra', 'maestro', 'guro', 'nagtuturo', 'staff', 'faculty']
        who_words = ['sin-o', 'sino']
        
        if any(who_word in query_lower for who_word in who_words) and any(teacher_word in query_lower for teacher_word in teacher_aklanon_words):
            translated = "who are the teachers"
            logger.info(f"🔄 Aklanon teacher pattern translation: '{query}' → '{translated}'")
            return translated
        
        # Fallback: word-by-word translation
        words = query.split()
        translated_words = []
        
        # Aklanon particles - some should be converted, others should be removed
        aklanon_particles = {
            "nga": "",      # emphasis particle: remove in translation (just emphasis)
            "kag": "and",   # and: "kag" → "and"
            "it": "the",    # article: "it" → "the"
            "sa": "in",     # preposition: "sa" → "in/at"
            "si": "",       # personal marker: remove (no English equivalent)
        }
        
        # Common spelling variations for Aklanon words
        aklanon_variations = {
            "mayad": "maayad",  # mayad → maayad (good)
            "gabi": "gabi-i",   # gabi → gabi-i (evening)
            "sino": "sin-o",    # sino → sin-o (who)
        }
        
        logger.info(f"🔍 Translating words: {words}")
        
        for word in words:
            clean_word = word.lower().strip('.,!?-')
            logger.info(f"🔍 Checking word: '{clean_word}'")
            
            # Check for Aklanon particles first
            if clean_word in aklanon_particles:
                particle_translation = aklanon_particles[clean_word]
                if particle_translation:  # Only add if not empty string
                    translated_words.append(particle_translation)
                    logger.info(f"🔄 Particle translation: '{clean_word}' → '{particle_translation}'")
                else:
                    logger.info(f"🔄 Particle removed: '{clean_word}' (emphasis/marker only)")
            # Check for spelling variations first
            elif clean_word in aklanon_variations:
                canonical_word = aklanon_variations[clean_word]
                if canonical_word in aklanon_dict:
                    english_meaning = aklanon_dict[canonical_word]
                    translated_words.append(english_meaning)
                    logger.info(f"🔄 Variation translated: '{clean_word}' → '{canonical_word}' → '{english_meaning}'")
                else:
                    translated_words.append(word)
                    logger.info(f"🔍 Variation found but no translation for '{canonical_word}'")
            # Check for exact match in main dictionary
            elif clean_word in aklanon_dict:
                english_meaning = aklanon_dict[clean_word]
                translated_words.append(english_meaning)
                logger.info(f"🔄 Translated '{clean_word}' → '{english_meaning}'")
            # Check for word with hyphen (like "sin-o")
            elif f"{clean_word}-" in aklanon_dict:
                english_meaning = aklanon_dict[f"{clean_word}-"]
                translated_words.append(english_meaning)
                logger.info(f"🔄 Translated '{clean_word}' → '{english_meaning}'")
            # Check without hyphen if word has hyphen
            elif "-" in word and clean_word.replace("-", "") in aklanon_dict:
                english_meaning = aklanon_dict[clean_word.replace("-", "")]
                translated_words.append(english_meaning)
                logger.info(f"🔄 Translated '{clean_word}' → '{english_meaning}'")
            else:
                translated_words.append(word)
                logger.info(f"🔍 No translation for '{clean_word}', keeping original")
        
        translated_query = " ".join(translated_words)
        if translated_query != query:
            logger.info(f"📝 Query translation: '{query}' → '{translated_query}'")
        else:
            logger.info(f"📝 No translation changes made to: '{query}'")
        
        return translated_query
    def _is_person_query(self, query: str) -> bool:
        """Detect if user is asking about a specific person/staff member."""
        query_lower = query.lower().strip()
        
        # EXCLUSIONS: These are NOT person queries even if they might seem like it
        location_patterns = [
            "where is", "where can i find", "location of", "saan ang", "nasaan ang",
            "office", "room", "building", "classroom", "library", "clinic", "guidance office"
        ]
        
        # Family/enrollment context patterns - these are NOT person queries about staff
        family_patterns = [
            "her name is", "his name is", "my daughter", "my son", "my child", 
            "she's", "he's", "years old", "grade", "enroll", "student"
        ]
        
        # If it's asking about location/place, it's NOT a person query
        if any(pattern in query_lower for pattern in location_patterns):
            return False
            
        # If it's about family/enrollment context, it's NOT a staff person query
        if any(pattern in query_lower for pattern in family_patterns):
            return False
        
        # Specific patterns that indicate person queries (more restrictive)
        person_patterns = [
            "who is",
            "sino si", "sin-o si", "sino ang", "sin-o ang",
        ]
        
        # Check if query matches person inquiry patterns
        for pattern in person_patterns:
            if pattern in query_lower:
                return True
        
        # Check for "tell me about [name]" patterns
        # but be more restrictive to avoid false positives  
        if "tell me about" in query_lower:
            remaining = query_lower.replace("tell me about", "").strip()
            # Only consider it a person query if the remaining part looks like a name
            # and doesn't contain school-related words
            school_words = ["school", "program", "class", "grade", "curriculum", "enrollment", "admission"]
            if not any(word in remaining for word in school_words):
                words = remaining.split()
                if len(words) >= 1 and words[0].isalpha() and len(words[0]) > 2:
                    # Additional check: does it contain known name patterns?
                    known_names = [ "meliza", "delgado", "johnson"] 
                    if any(name in remaining for name in known_names):
                        return True
        
        # Very restrictive check for names - only if query is very short and contains potential names
        # BUT exclude if it's in family/enrollment context
        words = query_lower.split()
        if len(words) == 2 or len(words) == 3:  # Only short queries
            # Check if it contains common name indicators from our known staff
            known_names = [ "meliza", "delgado", "nelda", "annalyn", "lezil", "michelle", "thedy", "jessica", "leny"]
            for name in known_names:
                if name in query_lower:
                    return True
        
        return False
    
    async def _extract_entities_with_nlu(self, user_message: str) -> dict:
        """Extract entities using both NLU engine and entity extractor"""
        try:
            # Use the advanced entity extractor directly for better results
            extracted_entities = self.entity_extractor.extract_entities(user_message)
            
            # Get intent from NLU engine
            nlu_result = await self.nlu_engine.analyze_intent(user_message)
            
            # Return entities in a format compatible with the rest of the system
            return {
                'entities': extracted_entities,  # List of ExtractedEntity objects
                'intent': nlu_result.intent.value,
                'confidence': nlu_result.confidence
            }
        except Exception as e:
            print(f"Error in NLU entity extraction: {e}")
            return {'entities': [], 'intent': 'unknown', 'confidence': 0.0}

    def _extract_name_from_query(self, query: str) -> str:
        """Extract user's name from the current query using regex patterns."""
        import re
        
        if not query:
            return ""
            
        query_lower = query.lower()
        
        name_patterns = [
            r"hi[,\s]*i['\s]*m\s+(\w+)",           # "Hi, I'm John" 
            r"hi[,\s]+i\s+am\s+(\w+)",             # "Hi, I am John"
            r"hello[,\s]*i['\s]*m\s+(\w+)",        # "Hello, I'm John"
            r"hello[,\s]+i\s+am\s+(\w+)",          # "Hello, I am John"
            r"my\s+name\s+is\s+(\w+)",             # "my name is John"
            r"i['\s]*m\s+(\w+)",                   # "I'm John"
            r"i\s+am\s+(\w+)",                     # "I am John"
            r"call\s+me\s+(\w+)",                  # "call me John"
            r"this\s+is\s+(\w+)",                  # "this is John"
            r"ako\s+si\s+(\w+)",                   # "ako si John" (Tagalog)
            r"ako\s+ay\s+(\w+)",                   # "ako ay John" (Tagalog)
            r"kumusta[,\s]+ako\s+si\s+(\w+)",      # "kumusta ako si John" (Aklanon)
            r"kamusta[,\s]+ako\s+si\s+(\w+)",      # "kamusta ako si John" (Aklanon)
            r"maayong[,\s]+ako\s+si\s+(\w+)",      # "maayong ako si John" (Aklanon greeting)
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                name = match.group(1).strip().title()
                # Enhanced filtering for common non-names, adjectives, and emotional words
                excluded_words = [
                    'not', 'from', 'here', 'good', 'fine', 'okay', 'yes', 'no',
                    'super', 'really', 'very', 'so', 'quite', 'pretty', 'extremely',
                    'excited', 'happy', 'sad', 'tired', 'busy', 'confused', 'lost',
                    'interested', 'curious', 'wondering', 'looking', 'asking',
                    'back', 'again', 'returning', 'new', 'first', 'time',
                    'the', 'a', 'an', 'this', 'that', 'these', 'those'
                ]
                
                # Also check if the word appears in context that suggests it's not a name
                if name.lower() not in excluded_words:
                    # Additional check: if the word is followed by typical adjective contexts
                    context_check = query_lower.lower()
                    adjective_contexts = [
                        f"am {name.lower()} excited", f"am {name.lower()} happy", 
                        f"am {name.lower()} interested", f"am {name.lower()} curious",
                        f"am {name.lower()} looking", f"am {name.lower()} asking"
                    ]
                    
                    if not any(context in context_check for context in adjective_contexts):
                        return name
        
        return ""

    async def _extract_user_name_async(self, conversation_history: list) -> str:
        """Extract user's name from conversation history - async version with NLU first."""
        if not conversation_history:
            return ""
        
        # Try NLU approach first for recent messages
        for message in reversed(conversation_history[-3:]):  # Check last 3 messages with NLU
            if message.get("role") == "user":
                content = message.get("content", "").strip()
                try:
                    entities = await self._extract_entities_with_nlu(content)
                    if entities.get('person_name'):
                        return entities['person_name'].capitalize()
                except Exception:
                    pass  # Fall back to regex
        
        # Fallback to regex patterns
        return self._extract_user_name_regex(conversation_history)
    
    def _extract_user_name_regex(self, conversation_history: list) -> str:
        """Extract user's name using regex patterns only."""
        import re
        
        name_patterns = [
            r"hi[,\s]*i['\s]*m\s+(\w+)",           # "Hi, I'm John" 
            r"hi[,\s]+i\s+am\s+(\w+)",             # "Hi, I am John"
            r"hello[,\s]*i['\s]*m\s+(\w+)",        # "Hello, I'm John"
            r"hello[,\s]+i\s+am\s+(\w+)",          # "Hello, I am John"
            r"my\s+name\s+is\s+(\w+)",             # "my name is John"
            r"i['\s]*m\s+(\w+)",                   # "I'm John"
            r"i\s+am\s+(\w+)",                     # "I am John"
            r"call\s+me\s+(\w+)",                  # "call me John"
            r"this\s+is\s+(\w+)",                  # "this is John"
        ]
        
        # Search through ALL conversation history
        for message in conversation_history:
            if message.get("role") == "user":
                content = message.get("content", "").lower().strip()
                
                for pattern in name_patterns:
                    match = re.search(pattern, content)
                    if match:
                        name = match.group(1).strip()
                        # Filter out common words that aren't names
                        if name and len(name) > 1 and name not in ["the", "a", "an", "and", "or", "but", "to", "for", "of", "in", "on", "at", "with", "by"]:
                            return name.capitalize()
        
        return ""

    def _extract_user_name(self, conversation_history: list) -> str:
        """Extract user's name from conversation history - uses NLU first, regex as fallback."""
        if not conversation_history:
            return ""
        
        # For sync calls, try regex directly (async version available as _extract_user_name_async)
        try:
            # Try to use existing event loop if available
            import asyncio
            loop = asyncio.get_running_loop()
            # If we're in an async context, we can't create a new loop
            return self._extract_user_name_regex(conversation_history)
        except RuntimeError:
            # No event loop running, we can create one
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self._extract_user_name_async(conversation_history))
                loop.close()
                return result
            except Exception:
                # Fall back to regex only
                return self._extract_user_name_regex(conversation_history)
    
    async def _extract_child_name_async(self, conversation_history: List[Dict]) -> str:
        """Extract child's name from conversation history - async version with NLU first."""
        if not conversation_history:
            return ""
        
        # Try NLU approach first for recent messages
        for message in reversed(conversation_history[-3:]):  # Check last 3 messages with NLU
            if message.get("role") == "user":
                content = message.get("content", "").strip()
                try:
                    entities = await self._extract_entities_with_nlu(content)
                    if entities.get('child_name'):
                        return entities['child_name'].capitalize()
                except Exception:
                    pass  # Fall back to regex
        
        # Fallback to regex patterns
        return self._extract_child_name_regex(conversation_history)
    
    def _extract_child_name_regex(self, conversation_history: List[Dict]) -> str:
        """Extract child's name using regex patterns only."""
        import re
        
        child_patterns = [
            r"my\s+son['\s]*s?\s+name\s+is\s+(\w+)",      # "my son's name is Lucio"
            r"my\s+daughter['\s]*s?\s+name\s+is\s+(\w+)",  # "my daughter's name is Maria"
            r"my\s+child['\s]*s?\s+name\s+is\s+(\w+)",     # "my child's name is Alex"
            r"his\s+name\s+is\s+(\w+)",                    # "his name is Lucio"
            r"her\s+name\s+is\s+(\w+)",                    # "her name is Maria"
            r"their\s+name\s+is\s+(\w+)",                  # "their name is Alex"
            r"i\s+got\s+a\s+(?:son|daughter|child)\s+named\s+(\w+)",     # "i got a daughter named gret"
            r"i\s+have\s+a\s+(?:son|daughter|child)\s+named\s+(\w+)",    # "i have a son named john"
            r"(?:son|daughter|child)\s+named\s+(\w+)",                   # "daughter named gret"
        ]
        
        # Check conversation from most recent to oldest
        for message in reversed(conversation_history):
            if message.get("role") == "user":
                content = message.get("content", "").lower().strip()
                
                for pattern in child_patterns:
                    match = re.search(pattern, content)
                    if match:
                        name = match.group(1).strip()
                        if name and len(name) > 1:
                            return name.capitalize()
        
        return ""

    def _extract_child_name(self, conversation_history: List[Dict]) -> str:
        """Extract child's name from conversation history - uses NLU first, regex as fallback."""
        if not conversation_history:
            return ""
        
        # For sync calls, try regex directly (async version available as _extract_child_name_async)
        try:
            # Try to use existing event loop if available
            import asyncio
            loop = asyncio.get_running_loop()
            # If we're in an async context, we can't create a new loop
            return self._extract_child_name_regex(conversation_history)
        except RuntimeError:
            # No event loop running, we can create one
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self._extract_child_name_async(conversation_history))
                loop.close()
                return result
            except Exception:
                # Fall back to regex only
                return self._extract_child_name_regex(conversation_history)
    
    def _get_personalized_enrollment_response(self, user_name: str, child_name: str, lang: str) -> str:
        """Generate personalized enrollment response based on extracted names."""
        
        # Build personalized greeting
        greeting_parts = []
        if user_name:
            greeting_parts.append(user_name)
        if child_name:
            if user_name:
                greeting_parts.append(f"and {child_name}")
            else:
                greeting_parts.append(child_name)
        
        if greeting_parts:
            names_str = ", ".join(greeting_parts)
            if lang == "en":
                return f"Hi {names_str}! 😊 Ready to join our school family? 🎒 For enrollment information and all the details you need, please visit the school office during regular hours. They'll guide you through everything!"
            elif lang == "tl":
                return f"Hi {names_str}! 😊 Ready na ba kayong sumali sa pamilya namin? 🎒 Para sa enrollment information at lahat ng kailangan ninyong detalye, pumunta sa school office sa regular hours. Gabayan nila kayo sa lahat!"
            else:
                return f"Hi {names_str}! For enrollment information, please visit the school office during regular hours."
        else:
            # Fallback to generic response if no names extracted
            if lang == "en":
                return "Ready to join our school family? 🎒 Head to the office for all the enrollment info - they'll guide you through everything!"
            elif lang == "tl":
                return "Ready na ba kayong sumali sa pamilya namin? 🎒 Punta sa office para sa enrollment info - gabayan nila kayo sa lahat!"
            else:
                return "For enrollment information, please visit the school office."

    async def _handle_intent_based_response(self, nlu_result: NLUResult, query: str, lang: str, conversation_history: List[Dict] = None, user_timezone: str = None) -> str:
        """
        Handle responses based on NLU intent classification instead of keyword matching
        """
        intent = nlu_result.intent
        entities = nlu_result.entities
        
        # Extract names from entities or conversation history
        user_name = self._extract_user_name(conversation_history or [])
        child_name = self._extract_child_name(conversation_history or [])
        
        # Extract names from current query if not found in conversation history
        if not user_name:
            user_name = self._extract_name_from_query(query)
        
        # Extract names from current entities
        for entity in entities:
            if entity.type == "person_name" and not user_name:
                user_name = entity.value
            elif entity.type == "child_name" and not child_name:
                child_name = entity.value
        
        logger.info(f"🎯 Handling intent: {intent.value} with entities: {[f'{e.type}:{e.value}' for e in entities]}")
        
        # Handle each intent intelligently
        if intent == Intent.GREETING_WITH_NAME:
            return self._handle_greeting_with_name(user_name, child_name, lang, user_timezone)
            
        elif intent in [Intent.GREETING_SIMPLE, Intent.GREETING_EXCITED, Intent.GREETING_FORMAL, Intent.GREETING_CASUAL, Intent.GREETING_RETURNING_USER]:
            # Create user context for dynamic greetings
            user_context = {
                "name": user_name,
                "conversation_history": conversation_history or [],  # Use actual conversation history
                "mood": self._detect_mood_from_query(query) if intent == Intent.GREETING_EXCITED else None
            }
            return await self.get_greeting_async(lang, user_timezone, intent, user_context)
            
        elif intent == Intent.ENROLLMENT_INQUIRY:
            return self._get_personalized_enrollment_response(user_name, child_name, lang)
            
        elif intent == Intent.NAME_INTRODUCTION:
            return self._handle_name_introduction(user_name, lang)
            
        elif intent == Intent.CHILD_INTRODUCTION:
            return self._handle_child_introduction(user_name, child_name, lang)
            
        elif intent == Intent.NAME_QUERY:
            return self._handle_name_query(user_name, lang)
            
        elif intent == Intent.DENIAL or intent == Intent.CLARIFICATION:
            return self._handle_clarification(query, lang)
            
        elif intent == Intent.STAFF_INQUIRY:
            # Let AI handle with database context for staff information
            return None
            
        elif intent == Intent.SCHOOL_INFO:
            # Let AI handle with database context for school information
            return None
            
        elif intent == Intent.CONTACT_INFO:
            # Let AI handle with database context for contact information
            return None
            
        elif intent == Intent.GOODBYE:
            return self.get_goodbye(lang)
            
        elif intent == Intent.FACILITIES_INQUIRY:
            # Use intelligent facilities inquiry with database search
            return await self._handle_facilities_inquiry_intelligent(query, lang)
            
        elif intent == Intent.FINANCIAL_INQUIRY:
            # Let AI handle with database context - no hardcoded responses
            return None
            
        elif intent == Intent.GENERAL_INFO:
            # Let AI handle with database context - no hardcoded responses
            return None
            
        elif intent == Intent.LOCATION_INQUIRY:
            # Let AI handle with database context - no hardcoded responses
            return None
            
        elif intent == Intent.HELP_REQUEST:
            # Let AI handle with database context - no hardcoded responses
            return None
            
        elif intent == Intent.APPRECIATION:
            return self._handle_appreciation(lang, user_name)
            
        elif intent == Intent.CONFIRMATION:
            return self._handle_confirmation(lang, conversation_history)
            
        else:
            # For unknown or general intents, fall back to AI processing
            return None  # Will trigger normal AI flow
    
    def _handle_greeting_with_name(self, user_name: str, child_name: str, lang: str, user_timezone: str = None) -> str:
        """Handle greeting with name introduction"""
        time_period = self.get_time_period(user_timezone)
        
        if lang == "tl" or lang == "akl":
            if time_period == "morning":
                base_greeting = f"Magandang umaga, {user_name}!" if user_name else "Magandang umaga!"
            elif time_period == "afternoon": 
                base_greeting = f"Magandang hapon, {user_name}!" if user_name else "Magandang hapon!"
            elif time_period == "evening":
                base_greeting = f"Magandang gabi, {user_name}!" if user_name else "Magandang gabi!"
            else:
                base_greeting = f"Hello, {user_name}!" if user_name else "Hello!"
            
            return f"{base_greeting} Natutuwa akong makilala kayo! Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Ano ang maitutulong ko sa inyo ngayon?"
        else:
            if time_period == "morning":
                base_greeting = f"Good morning, {user_name}!" if user_name else "Good morning!"
            elif time_period == "afternoon":
                base_greeting = f"Good afternoon, {user_name}!" if user_name else "Good afternoon!" 
            elif time_period == "evening":
                base_greeting = f"Good evening, {user_name}!" if user_name else "Good evening!"
            else:
                base_greeting = f"Hello, {user_name}!" if user_name else "Hello!"
            
            return f"{base_greeting} Nice to meet you! I'm TOMAS, the chatbot representative of Tomas SM. Bautista Elementary School! What can I help you with today?"
    
    def _handle_name_introduction(self, user_name: str, lang: str) -> str:
        """Handle when user introduces their name"""
        if lang == "tl" or lang == "akl":
            return f"Salamat, {user_name}! 😊 Natutuwa akong makilala kayo. Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School. Paano ko kayo matutulungan?"
        else:
            return f"Nice to meet you, {user_name}! 😊 I'm TOMAS, the chatbot representative of Tomas SM. Bautista Elementary School. How can I help you today?"
    
    def _handle_child_introduction(self, user_name: str, child_name: str, lang: str) -> str:
        """Handle when user introduces their child"""
        if lang == "tl" or lang == "akl":
            if user_name and child_name:
                return f"Salamat sa pagpapakilala, {user_name}! 😊 Nice to know about {child_name}. Ano ang maitutulong ko sa inyo?"
            elif child_name:
                return f"Nice to know about {child_name}! 😊 Ano ang maitutulong ko sa inyo?"
            else:
                return "Salamat sa pagpapakilala! 😊 Ano ang maitutulong ko sa inyo?"
        else:
            if user_name and child_name:
                return f"Thank you for the introduction, {user_name}! 😊 Nice to know about {child_name}. How can I help you?"
            elif child_name:
                return f"Nice to know about {child_name}! 😊 How can I help you?"
            else:
                return "Thank you for the introduction! 😊 How can I help you?"
    
    def _handle_name_query(self, user_name: str, lang: str) -> str:
        """Handle when user asks about their own name"""
        if user_name:
            # We know their name - respond accordingly
            if lang == "tl" or lang == "akl":
                return f"Oo, {user_name}! Natatandaan ko kayo 😊 Ikaw nga si {user_name}, tama ba?"
            else:
                return f"Yes, I remember! Your name is {user_name} 😊 How can I help you today?"
        else:
            # We don't have their name in conversation history
            if lang == "tl" or lang == "akl":
                return "Hindi ko pa alam ang pangalan ninyo 😊 Maaari ninyong sabihin sa akin ang inyong pangalan?"
            else:
                return "I don't know your name yet 😊 Could you please tell me your name?"
    
    def _handle_clarification(self, query: str, lang: str) -> str:
        """Handle clarifications and denials"""
        if lang == "tl" or lang == "akl":
            return "Paumanhin sa pagkakamali! 😊 Malinaw naman. Ano nga ang maitutulong ko sa inyo?"
        else:
            return "I apologize for the misunderstanding! 😊 I understand now. What can I help you with?"
    
    def _handle_staff_inquiry(self, query: str, lang: str) -> str:
        """Handle staff-related questions"""
        # This could be enhanced to search for specific staff members
        if lang == "tl" or lang == "akl":
            return "Para sa impormasyon ng mga guro at staff, maaari kayong pumunta sa school office o tumawag sa (036) 269-6345."
        else:
            return "For information about our teachers and staff, please visit the school office or call (036) 269-6345."
    
    def _handle_school_info_inquiry(self, query: str, lang: str) -> str:
        """Handle general school information questions"""
        if lang == "tl" or lang == "akl":
            return "Para sa mga detalye tungkol sa school programs at curriculum, maaari kayong makipag-ugnayan sa school office."
        else:
            return "For details about our school programs and curriculum, please contact the school office."
    
    def _handle_contact_inquiry(self, lang: str) -> str:
        """Handle contact information requests"""
        if lang == "tl" or lang == "akl":
            return "Makipag-ugnayan sa amin: School Office - (036) 269-6345. Nasa Tomas SM. Bautista Elementary School kami."
        else:
            return "Contact us: School Office - (036) 269-6345. We're located at Tomas SM. Bautista Elementary School."
    
    async def _handle_facilities_inquiry_intelligent(self, query: str, lang: str) -> str:
        """Handle facilities-related questions by searching database first, then providing intelligent responses"""
        try:
            # Search the database/summarized text for facility information
            facility_info = await self.enhanced_search_supabase(query)
            
            if facility_info and facility_info.strip():
                # Found information in database - return it
                logger.info(f"🏫 Found facility information in database for: {query}")
                return facility_info
            
            # If no specific information found, extract facility type from query and provide appropriate response
            return self._generate_no_facility_response(query, lang)
            
        except Exception as e:
            logger.warning(f"Error searching for facility information: {e}")
            return self._generate_no_facility_response(query, lang)
    
    def _generate_no_facility_response(self, query: str, lang: str) -> str:
        """Generate appropriate 'no information found' response based on query and language"""
        
        # Extract facility type from query using NLP patterns
        query_lower = query.lower()
        
        # Common facility types that might be asked about
        facility_patterns = {
            "cafeteria": ["cafeteria", "canteen", "food", "lunch", "dining"],
            "library": ["library", "books", "reading", "study"],
            "gymnasium": ["gym", "gymnasium", "sports", "physical education", "pe", "basketball"],
            "playground": ["playground", "play area", "outdoor", "recreation"],
            "science lab": ["science", "laboratory", "experiments", "science lab"],  # Fixed: moved before computer lab
            "computer lab": ["computer", "lab", "technology", "it"],
            "clinic": ["clinic", "health", "medical", "nurse"],
            "guidance office": ["guidance", "counseling", "counselor"],
            "faculty room": ["faculty", "teachers room", "staff room"],
            "classroom": ["classroom", "class", "room"],
            "comfort room": ["comfort room", "cr", "restroom", "bathroom", "toilet"]
        }
        
        # Find which facility type is being asked about
        detected_facility = "facility"
        for facility_type, keywords in facility_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_facility = facility_type
                break
        
        # Generate response based on language
        if lang == "tl" or lang == "akl":
            return f"As of now, walang nakarecord na {detected_facility} sa school database namin. Maaari kayong makipag-ugnayan sa school office para sa mas detalyadong impormasyon tungkol sa mga facilities."
        else:
            return f"As of now, there are no recorded {detected_facility} in the school database. You can contact the school office for more information about our facilities."

    def _handle_facilities_inquiry(self, query: str, lang: str) -> str:
        """DEPRECATED: Old hardcoded method - now redirects to intelligent version"""
        # This method is kept for backward compatibility but should use the intelligent version
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, we can't easily call async method
            return self._generate_no_facility_response(query, lang)
        except RuntimeError:
            # No event loop running, we can create one for this call
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self._handle_facilities_inquiry_intelligent(query, lang))
                loop.close()
                return result
            except Exception:
                loop.close()
                return self._generate_no_facility_response(query, lang)
    
    def _handle_financial_inquiry(self, query: str, lang: str) -> str:
        """Handle financial/tuition-related questions"""
        if lang == "tl" or lang == "akl":
            return "Para sa tuition fees at iba pang bayarin, makipag-ugnayan sa school office."
        else:
            return "For tuition fees and other charges, please contact the school office."
    def _handle_general_info_inquiry(self, query: str, lang: str) -> str:
        """Handle general school information questions"""
        if lang == "tl" or lang == "akl":
            return "Ang Tomas SM. Bautista Elementary School ay isang educational institution na nag-aalaga sa holistic development ng mga bata. Mayroon kaming experienced teachers at modern facilities."
        else:
            return "Tomas SM. Bautista Elementary School is an educational institution dedicated to the holistic development of children. We have experienced teachers and modern facilities."
    
    async def _handle_location_inquiry(self, lang: str) -> str:
        """Handle location and directions questions by fetching from database"""
        try:
            # Search for location information in the database
            location_info = await self.enhanced_search_supabase("location")
            
            if location_info:
                # We found specific location information in the database
                return location_info
            else:
                # Fallback to basic information if database search fails
                if lang == "tl" or lang == "akl":
                    return "Nasa Tomas SM. Bautista Elementary School kami. Para sa specific directions, tumawag sa (036) 269-6345 o bisitahin ang school office."
                else:
                    return "We're located at Tomas SM. Bautista Elementary School. For specific directions, call (036) 269-6345 or visit the school office."
        except Exception as e:
            logger.warning(f"Error fetching location from database: {e}")
            # Fallback response if there's any error
            if lang == "tl" or lang == "akl":
                return "Nasa Tomas SM. Bautista Elementary School kami. Para sa specific directions, tumawag sa (036) 269-6345 o bisitahin ang school office."
            else:
                return "We're located at Tomas SM. Bautista Elementary School. For specific directions, call (036) 269-6345 or visit the school office."
    
    def _handle_help_request(self, lang: str) -> str:
        """Handle general help requests"""
        if lang == "tl" or lang == "akl":
            return "Nandito ako para tumulong! 😊 Maaari kayong magtanong tungkol sa enrollment, school programs, facilities, o anumang school-related na impormasyon."
        else:
            return "I'm here to help! 😊 You can ask me about enrollment, school programs, facilities, or any school-related information."
    
    def _handle_appreciation(self, lang: str, user_name: str = "") -> str:
        """Handle thank you messages with personalized response"""
        if user_name:
            if lang == "tl" or lang == "akl":
                return f"Walang anuman, {user_name}! 😊 Masaya akong makatulong. May iba pa bang kailangan ninyo?"
            else:
                return f"You're welcome, {user_name}! 😊 I'm happy to help. Is there anything else you need?"
        else:
            if lang == "tl" or lang == "akl":
                return "Walang anuman! 😊 Masaya akong makatulong. May iba pa bang kailangan ninyo?"
            else:
                return "You're welcome! 😊 I'm happy to help. Is there anything else you need?"
    
    def _handle_confirmation(self, lang: str, conversation_history: list = None) -> str:
        """Handle yes/confirmation responses with context awareness"""
        
        # Check if there's recent context that would make "yes" meaningful
        has_context = False
        if conversation_history and len(conversation_history) > 0:
            # Look at the last few messages to see if there was a question or proposal
            recent_messages = conversation_history[-3:]  # Last 3 messages
            for msg in recent_messages:
                content = msg.get('content', '').lower()
                # Check if the assistant asked a question or made a proposal
                if any(indicator in content for indicator in [
                    '?', 'would you like', 'do you want', 'are you', 'is that', 
                    'correct', 'right', 'gusto mo', 'nais mo', 'tama ba'
                ]):
                    has_context = True
                    break
        
        if has_context:
            # There's context - respond as confirmation
            if lang == "tl" or lang == "akl":
                return "Salamat sa confirmation! Ano ang susunod na maitutulong ko sa inyo?"
            else:
                return "Thank you for confirming! What can I help you with next?"
        else:
            # No clear context - ask for clarification
            if lang == "tl" or lang == "akl":
                return "Oo? Ano pong ibig ninyong sabihin? Paano ko kayo matutulungan ngayon?"
            else:
                return "Yes? I'm not sure what you're referring to. How can I help you today?"

    def _get_personalized_name_response(self, user_name: str, child_name: str, lang: str) -> str:
        """Generate warm, personalized response when user asks about their own name."""
        
        if user_name:
            # We know their name - respond warmly
            if lang == "tl" or lang == "akl":
                responses = [
                    f"Oo, {user_name}! 😊 Natatandaan ko kayo. Ikaw nga si {user_name}, tama ba?",
                    f"Si {user_name} nga! 😊 Hindi ko nalilimutan ang pangalan ninyo.",
                    f"Alam ko! Ikaw si {user_name}! 😊 Kumusta ka naman?",
                ]
            else:
                responses = [
                    f"Of course! Your name is {user_name}! 😊 How could I forget?",
                    f"Yes, I remember! You're {user_name}! 😊 How are you doing?",
                    f"That's {user_name}! 😊 Nice to chat with you again!",
                ]
            
            import random
            return random.choice(responses)
        else:
            # We don't have their name in conversation history
            if lang == "tl" or lang == "akl":
                return "Hindi ko pa narinig ang pangalan ninyo sa usapan natin 😊 Pwede bang malaman kung ano ang tawag sa inyo?"
            else:
                return "I don't think you've mentioned your name yet in our conversation 😊 Could you remind me what I should call you?"

    def _get_personalized_child_response(self, user_name: str, child_name: str, lang: str) -> str:
        """Generate warm, personalized response when user asks about their child's name."""
        
        if child_name:
            # Warm responses about their child
            if lang == "tl" or lang == "akl":  # Both Tagalog and Aklanon queries get Tagalog responses
                responses = [
                    f"Si {child_name}! 😊 Ang anak ninyo nga si {child_name}, tama ba?",
                    f"Oo nga! Si {child_name} ang pangalan ng anak ninyo 😊 Cute name!",
                    f"Si {child_name} nga! 😊 Kamusta naman siya?",
                ]
                if user_name:
                    responses.extend([
                        f"Si {child_name} nga, {user_name}! 😊 Proud parent ka talaga!",
                        f"Ang anak mo si {child_name}, tama {user_name}? 😊"
                    ])
            else:  # English
                responses = [
                    f"That's {child_name}! 😊 Your child's name is {child_name}, right?",
                    f"Of course! Your son/daughter is {child_name}! 😊 Such a lovely name!",
                    f"Yes! {child_name}! 😊 How is {child_name} doing?",
                ]
                if user_name:
                    responses.extend([
                        f"That's {child_name}, {user_name}! 😊 You must be so proud!",
                        f"Your child {child_name}, right {user_name}? 😊 Great kid!"
                    ])
            
            import random
            return random.choice(responses)
        else:
            # Gentle response if child name not found
            if lang == "tl" or lang == "akl":  # Both Tagalog and Aklanon queries get Tagalog responses
                return "Hindi ko pa narinig ang pangalan ng anak ninyo 😊 Ano nga ulit ang tawag sa kanya?"
            else:
                return "I don't think you've mentioned your child's name yet 😊 Could you remind me what their name is?"

    def _get_unknown_person_response(self, lang: str = "en") -> str:
        """Generate a helpful response for unknown person queries without listing all staff."""
        
        if lang == "tl":
            return ("Hindi ko nakilala ang taong iyon sa aming paaralan. Para sa mga katanungan "
                   "tungkol sa mga guro at staff, maaari kayong makipag-ugnayan kay Meliza A. Delgado, "
                   "ang aming Head Teacher, o tumawag sa school office sa (036) 269-6345.")
        elif lang == "akl":
            return ("Wala ko kakilala nga tawo na ina sa amon eskwelahan. Para sa mga pamangkot "
                   "parte sa mga maestro kag staff, pwede kamo mag-contact kay Meliza A. Delgado, ")
        else:  # English
            return ("I don't have information about that person in our school records. "
                   "For inquiries about our teachers and staff, you may contact our Head Teacher, "
                   "Meliza A. Delgado")

    def _get_known_staff_list(self, lang: str = "en") -> str:
        """Generate a helpful list of known staff members."""
        staff_info = {
            "Meliza A. Delgado": "Head Teacher",
            "Nelda B. Delos Santos": "Kindergarten Teacher", 
            "Annalyn B. Andrade": "Grade 1 Teacher",
            "Lezil V. Villanueva": "Grade 2 Teacher",
            "Michelle V. Pastrana": "Grade 3 Teacher",
            "Thedy Mae P. Ruiz": "Grade 4 Teacher",
            "Jessica Z. Go": "LSA Teacher",
            "Leny Mae D. Patani": "Grade 6 Teacher",
            "Feliciano C. Bustamante Jr.": "School Division Superintendent",
            "Ramon D. Paras Jr.": "Assistant Superintendent",
            "Ariel Z. Zubiaga": "District Supervisor"
        }
        
        if lang == "tl":
            header = "Narito ang mga kilalang miyembro ng staff ng TOMAS Elementary School:\n\n"
            footer = "\n\nPara sa iba pang impormasyon, maaari kayong tumawag sa school office sa ."
        elif lang == "akl":
            header = "Ara ini it mga kilaea nga staff sa TOMAS Elementary School:\n\n"  
            footer = "\n\nPara sa iban nga impormasyon, pwede kamo mag-tawag sa school office sa ."
        else:  # English
            header = "Here are the known staff members at TOMAS Elementary School:\n\n"
            footer = "\n\nFor other inquiries, you may contact the school office at ."
        
        staff_list = ""
        for name, position in staff_info.items():
            staff_list += f"• {name} - {position}\n"
        
        return header + staff_list + footer

    async def enhanced_search_supabase(self, query: str) -> str:
        """Enhanced search strategy prioritizing full-text search via search_tsv."""
        import re
        
        # 🛡️ SAFETY CHECK: Handle None or empty query
        if not query or query is None:
            logger.warning("⚠️ Enhanced search received None or empty query")
            return ""
        
        # Ensure query is a string
        query = str(query).strip()
        if not query:
            logger.warning("⚠️ Enhanced search received empty string after cleanup")
            return ""

        # 🏠 PRIORITY CHECK: Address/location queries should search for "location" keyword first
        # BUT: Specific facility queries (like guidance office) should NOT use general location
        query_lower = query.lower()
        
        # Specific facility patterns - these should NOT use general location search
        specific_facility_patterns = [
            "guidance office", "guidance room", "clinic", "library", "classroom", 
            "computer room", "faculty room", "office location", "comfort room", "cr"
        ]
        
        # Only use general location search if it's NOT asking about a specific facility
        is_specific_facility = any(facility in query_lower for facility in specific_facility_patterns)
        
        address_patterns = [
            "address", "where is", "location", "located", "school address", 
            "what's the address", "where is the school", "school location",
            "where is tomas", "where can i find", "saan ang", "nasaan ang"
        ]
        
        if any(pattern in query_lower for pattern in address_patterns) and not is_specific_facility:
            logger.info("🏠 General address query detected - prioritizing 'location' search")
            location_result = await self.fetch_prompts_from_supabase("location")
            if location_result:
                logger.info("✅ Found address via 'location' keyword")
                return location_result
        elif is_specific_facility:
            logger.info(f"🏢 Specific facility query detected - skipping general location search")
        
        # 1. PRIORITY: Try full-text search first (most comprehensive)
        logger.info(f"🔍 Trying full-text search: '{query}'")
        result = await self._try_full_text_search(query)
        if result:
            logger.info("✅ Found result with full-text search")
            return result
        
        # 2. Try exact keyword search (fallback)
        logger.info(f"🔍 Trying exact search: '{query}'")
        result = await self.fetch_prompts_from_supabase(query)
        if result:
            logger.info("✅ Found result with exact search")
            return result
        
        # 3. Try extracting and searching for names (capitalized words)
        names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
        if names:
            for name in names:
                logger.info(f"🔍 Searching for name: {name}")
                name_result = await self.fetch_prompts_from_supabase(name)
                if name_result:
                    logger.info(f"✅ Found context for name: {name}")
                    return name_result

        # 3.5. Enhanced address/location query mapping
        query_lower = query.lower()
        address_patterns = [
            "address", "where is", "location", "located", "school address", 
            "what's the address", "where is the school", "school location",
            "where is tomas", "where can i find", "saan ang", "nasaan ang"
        ]
        
        if any(pattern in query_lower for pattern in address_patterns):
            logger.info("🏠 Address/location query detected - searching for 'location' keyword")
            # Try searching for the specific 'location' keyword which has the address
            location_result = await self.fetch_prompts_from_supabase("location")
            if location_result:
                logger.info("✅ Found location information")
                return location_result
            
            # Fallback to other location-related searches
            location_keywords = ["fatima", "new washington", "aklan", "where"]
            for keyword in location_keywords:
                location_result = await self.fetch_prompts_from_supabase(keyword)
                if location_result:
                    logger.info(f"✅ Found location via keyword: {keyword}")
                    return location_result
        
        # 4. Enhanced name-to-role mapping for common staff
        query_lower = query.lower()
        name_role_mappings = {
            # Staff name to their role/position
            ("meliza", "delgado"): ["head teacher", ],
            ("meliza a delgado", "meliza a. delgado"): ["head teacher"],
            
            # Mrs. Nelda B. Delos Santos - Teacher 3 - Kindergarten Jude
            ("nelda", "delos santos"): ["teacher", "kindergarten teacher"],
            ("nelda b delos santos", "nelda delos santos"): ["teacher", "kindergarten teacher"],
            
            # Mrs. Annalyn B. Andrade - Teacher 1 - Grade 1 - Andrew
            ("annalyn", "andrade"): ["teacher", "grade 1 teacher"],
            ("annalyn b andrade", "annalyn andrade"): ["teacher", "grade 1 teacher"],
            
            # Mrs. Lezil V. Villanueva - Teacher 1 - Grade 2 James
            ("lezil", "villanueva"): ["teacher", "grade 2 teacher"],
            ("lezil v villanueva", "lezil villanueva"): ["teacher", "grade 2 teacher"],
            
            # Mrs. Michelle V. Pastrana - Teacher 3 - Grade 3 - John
            ("michelle", "pastrana"): ["teacher", "grade 3 teacher"],
            ("michelle v pastrana", "michelle pastrana"): ["teacher", "grade 3 teacher"],
            
            # Ms. Thedy Mae P. Ruiz - Teacher 1 - Grade 4 - Peter
            ("thedy mae", "ruiz"): ["teacher", "grade 4 teacher"],
            ("thedy mae p ruiz", "thedy mae ruiz"): ["teacher", "grade 4 teacher"],
            
            # Ms. Jessica Z. Go - LSA Teacher
            ("jessica", "go"): ["teacher", "lsa teacher"],
            ("jessica z go", "jessica go"): ["teacher", "lsa teacher"],
            
            # Mrs. Leny Mae D. Patani - Teacher 1 - Grade 6 - Timothy
            ("leny mae", "patani"): ["teacher", "grade 6 teacher"],
            ("leny mae d patani", "leny mae patani"): ["teacher", "grade 6 teacher"],
            
            # District and Division Officials
            # Feliciano C. Bustamante Jr., Ceso VI - School Division Superintendent
            ("feliciano", "bustamante"): ["superintendent", "school division superintendent"],
            ("feliciano c bustamante", "feliciano bustamante jr"): ["superintendent", "school division superintendent"],
            ("bustamante", "feliciano bustamante"): ["superintendent", "school division superintendent"],
            
            # Ramon D. Paras Jr., EdP - OIC, Asst. Schools division superintendent
            ("ramon", "paras"): ["assistant superintendent", "oic assistant superintendent"],
            ("ramon d paras", "ramon paras jr"): ["assistant superintendent", "oic assistant superintendent"],
            ("paras", "ramon paras"): ["assistant superintendent", "oic assistant superintendent"],
            
            # Ariel Z. Zubiaga - Public Schools district Supervisor
            ("ariel", "zubiaga"): ["district supervisor", "public schools district supervisor"],
            ("ariel z zubiaga", "ariel zubiaga"): ["district supervisor", "public schools district supervisor"],
            ("zubiaga", "ariel zubiaga"): ["district supervisor", "public schools district supervisor"],
        }
        
        # Check if query contains any known names and search by their roles
        for name_patterns, roles in name_role_mappings.items():
            if any(name_pattern in query_lower for name_pattern in name_patterns):
                logger.info(f"🎯 Detected known name, searching by roles: {roles}")
                for role in roles:
                    role_result = await self.fetch_prompts_from_supabase(role)
                    if role_result:
                        logger.info(f"✅ Found context via role mapping: {role}")
                        return role_result
        
        # 5. Try searching within response content (not just keywords)
        # This searches the actual response text for names
        if names:
            for name in names:
                logger.info(f"🔍 Searching in response content for: {name}")
                content_result = await self._search_in_response_content(name)
                if content_result:
                    logger.info(f"✅ Found in response content: {name}")
                    return content_result
        
        # 6. For "who is" or "sino si" questions, try searching for job titles
        if any(pattern in query_lower for pattern in ["who is", "sino si", "sin-o si", "sino ang", "sin-o ang"]):
            job_title_searches = [
                "head teacher",
                "principal", 
                "teacher",
                "staff",
                "guidance counselor",
                "nurse",
                "librarian"
            ]
            for job_title in job_title_searches:
                logger.info(f"🔍 Searching for job title: {job_title}")
                job_result = await self.fetch_prompts_from_supabase(job_title)
                if job_result:
                    logger.info(f"✅ Found context for job title: {job_title}")
                    return job_result
        
        # 7. Try keyword-based search (remove function words)
        key_terms = []
        words = query_lower.split()
        stop_words = {"who", "is", "the", "what", "where", "when", "how", "a", "an", "and", "or", "but", 
                     "sino", "si", "ang", "sa", "ng", "sin-o", "may"}
        for word in words:
            clean_word = word.strip('.,!?')
            if clean_word not in stop_words and len(clean_word) > 2:
                key_terms.append(clean_word)
        
        if key_terms:
            key_search = " ".join(key_terms)
            logger.info(f"🔍 Searching with key terms: {key_search}")
            key_result = await self.fetch_prompts_from_supabase(key_search)
            if key_result:
                logger.info("✅ Found context with key terms search")
                return key_result
        
        # 8. Try individual words from the query
        for word in key_terms:
            if len(word) > 3:  # Only try longer words
                logger.info(f"🔍 Searching for individual word: {word}")
                word_result = await self.fetch_prompts_from_supabase(word)
                if word_result:
                    logger.info(f"✅ Found context for word: {word}")
                    return word_result
        
        logger.info("❌ No results found with enhanced search")
        return ""

    async def _search_in_response_content(self, search_term: str) -> str:
        """Search for names/terms within the response content, not just keywords."""
        try:
            # Use Supabase to search in the response content using ILIKE
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                logger.warning("Supabase credentials missing")
                return ""
            
            # Search in the response field using ILIKE (case-insensitive)
            search_pattern = f"%{search_term}%"
            
            # Make API call to search in response content
            async with httpx.AsyncClient() as client:
                headers = {
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": "application/json"
                }
                
                # Search where response content contains the search term
                params = {
                    "select": "keywords,response",
                    "response": f"ilike.{search_pattern}"
                }
                
                url = f"{supabase_url}/rest/v1/chatbot_prompts"
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        # Return the first matching result
                        result = data[0]
                        return f"Q: {result['keywords']}\nA: {result['response']}"
                        
        except Exception as e:
            logger.warning(f"Error searching response content: {e}")
        
        return ""
    
    async def fetch_summarized_file(self) -> str:
        now = time.time()

        if self._cached_summary and now - self._last_fetched < self.cache_ttl:
            return self._cached_summary

        # Correct private bucket fetch (with service_role key)
        url = f"{SUPABASE_URL}/storage/v1/object/{self.bucket}/{self.file}"
        headers = {"Authorization": f"Bearer {SUPABASE_KEY}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code != 200:
                logger.error(f"❌ Failed to fetch file: {response.status_code} {response.text}")
                return ""

            text = response.text

        self._cached_summary = text
        self._last_fetched = now
        return text

    def _validate_response_against_facts(self, response: str, query: str, lang: str) -> str:
        """🛡️ Enhanced validation to prevent inappropriate responses and ensure school-appropriate language."""
        
        # DEBUG: Log validation entry
        logger.info(f"🛡️ VALIDATION: Checking response for hallucinations and inappropriate content")
        logger.info(f"📝 Response excerpt: {response[:100]}...")
        
        # Known staff members (ONLY these exist)
        known_staff = {
            "meliza a. delgado", "meliza delgado", "meliza", "delgado",
            "nelda b. delos santos", "nelda delos santos", "nelda", 
            "annalyn b. andrade", "annalyn andrade", "annalyn",
            "lezil v. villanueva", "lezil villanueva", "lezil",
            "michelle v. pastrana", "michelle pastrana", "michelle",
            "thedy mae p. ruiz", "thedy mae ruiz", "thedy",
            "jessica z. go", "jessica go", "jessica",
            "leny mae d. patani", "leny mae patani", "leny",
            "feliciano c. bustamante jr.", "feliciano bustamante", "feliciano",
            "ramon d. paras jr.", "ramon paras", "ramon",
            "ariel z. zubiaga", "ariel zubiaga", "ariel"
        }
        
        # Fictional people to block (common made-up names)
        # NOTE: Be specific to avoid blocking legitimate staff names
        forbidden_people = {
            "mrs. garcia", "garcia", "mrs garcia", "ms garcia", "ms. garcia",
            "mrs. rodriguez", "rodriguez", "mrs rodriguez", "ms rodriguez", "ms. rodriguez", 
            "principal martinez", "martinez", "mrs martinez", "ms martinez"
            # Removed "mrs. santos", "santos" - we have real staff member "Nelda B. Delos Santos"
            # Removed "tomas sm. bautista", "tomas bautista", "mr. bautista" - this is the school's actual name!
            # NOTE: "santos" alone removed to avoid blocking real staff "Nelda B. Delos Santos"
        }
        
        # School facts to validate
        known_facts = {
            "address": "fatima, new washington, aklan",
            "school_name": "tomas sm. bautista elementary school",
            "head_teacher": "meliza a. delgado"
        }
        
        response_lower = response.lower()
        current_hour = datetime.now().hour
        
        # 🚨 NEW: CHECK FOR INAPPROPRIATE TAGALOG/AKLANON VOCABULARY
        # These words are inappropriate or nonsensical in a school context
        inappropriate_tagalog_words = {
            # Physical/inappropriate contexts
            "nakatali": "tied up/bound - inappropriate for school context",
            "nakagapos": "bound/chained - inappropriate for school context", 
            "nakakulong": "imprisoned/locked up - inappropriate for school context",
            "nakapiit": "confined/trapped - inappropriate for school context",
            "nakabilanggo": "jailed - inappropriate for school context",
            
            # Violent/harsh contexts
            "namatay": "died - too harsh for school context",
            "patay": "dead/death - inappropriate for school context",
            "nasaktan": "hurt/injured - concerning for school context",
            "nauntog": "hit head - concerning medical context",
            "nasugatan": "wounded - inappropriate for school context",
            
            # Romantic/adult contexts
            "nagmamahal": "loving romantically - inappropriate for school assistant",
            "nakipagrelasyon": "in a relationship - inappropriate context",
            "naging syota": "became boyfriend/girlfriend - inappropriate",
            "nagkakapit": "embracing intimately - inappropriate context",
            
            # Nonsensical school descriptions
            "nagiging masarap": "becoming delicious - weird for school description",
            "nalulunod": "drowning - alarming for school context",
            "nasusunog": "burning - alarming for school context",
            "nasisirang": "breaking/getting damaged - negative school image",
            
            # Inappropriate slang
            "ang galing": "amazing/cool - too casual for formal school responses",
            "astig": "cool/awesome - slang inappropriate for formal responses",
            "ang sarap": "so good/delicious - inappropriate context for school info",
            "grabe": "extreme/wow - too casual for professional responses"
        }
        
        # � NEW: CHECK FOR INAPPROPRIATE AKLANON VOCABULARY  
        inappropriate_aklanon_words = {
            "nakatali": "tied up - inappropriate for school context",
            "nakakulong": "imprisoned - inappropriate for school context",
            "namatay": "died - too harsh for school context", 
            "patay": "dead - inappropriate for school context",
            "nasaktan": "hurt - concerning for school context",
            "masarap": "delicious - weird descriptor for school",
            "grabe": "extreme - too casual for professional responses"
        }
        
        # Check for inappropriate words based on language
        inappropriate_words = {}
        if lang == "tl":
            inappropriate_words = inappropriate_tagalog_words
        elif lang == "akl":
            inappropriate_words = inappropriate_aklanon_words
        
        # Scan for inappropriate vocabulary
        for inappropriate_word, reason in inappropriate_words.items():
            if inappropriate_word in response_lower:
                logger.warning(f"🚨 INAPPROPRIATE LANGUAGE: Found '{inappropriate_word}' - {reason}")
                logger.info(f"📍 Inappropriate word context: {response_lower}")
                return self._get_safe_school_appropriate_response(query, lang)
        
        # 🚨 NEW: CHECK FOR NONSENSICAL TRANSLATIONS
        # Detect when AI is using words that don't make sense in school context
        nonsensical_patterns = {
            # School being described with inappropriate verbs
            "school.*na.*nakatali": "school being described as 'tied up'",
            "paaralan.*na.*nakatali": "school being described as 'tied up'", 
            "eskwelahan.*na.*nakatali": "school being described as 'tied up'",
            
            # Buildings/facilities with inappropriate descriptions
            "building.*na.*nakatali": "building described inappropriately",
            "office.*na.*nakatali": "office described inappropriately",
            "classroom.*na.*nakatali": "classroom described inappropriately",
            
            # Time/schedule with inappropriate descriptions
            "oras.*na.*nakatali": "time described as 'tied up'",
            "schedule.*na.*nakatali": "schedule described inappropriately"
        }
        
        import re
        for pattern, description in nonsensical_patterns.items():
            if re.search(pattern, response_lower):
                logger.warning(f"🚨 NONSENSICAL TRANSLATION: {description}")
                logger.info(f"📍 Nonsensical pattern: {pattern} in {response_lower}")
                return self._get_safe_school_appropriate_response(query, lang)
        
        # 🚨 NEW: CULTURAL APPROPRIATENESS CHECK
        # Ensure responses maintain professional, educational tone
        overly_casual_patterns = [
            "ay naku", "hay nako", "sus", "aba", "ay ewan", "basta", "eh ano ngayon",
            "pakialamerang", "walang kwenta", "ang galing talaga", "sobrang astig"
        ]
        
        for casual_phrase in overly_casual_patterns:
            if casual_phrase in response_lower:
                logger.warning(f"🚨 OVERLY CASUAL LANGUAGE: Found '{casual_phrase}' - too informal for school assistant")
                return self._get_safe_school_appropriate_response(query, lang)
        
        # �🕐 CHECK FOR INAPPROPRIATE TIME GREETINGS
        if current_hour >= 22 or current_hour < 5:  # Night time (10 PM - 5 AM)
            inappropriate_greetings = ["good morning", "good afternoon", "magandang umaga", "magandang hapon"]
            if any(greeting in response_lower for greeting in inappropriate_greetings):
                logger.warning(f"🚨 INAPPROPRIATE TIME GREETING: Using {inappropriate_greetings} at {current_hour}:XX")
                # Replace with appropriate neutral greeting
                if lang == "tl" or lang == "akl":
                    return "Kumusta! Ako si Tomas, ang inyong assistant. Paano ko kayo matutulungan?"
                else:
                    return "Hello! I'm Tomas, your school assistant. How can I help you?"
        
        # 🚨 CHECK FOR FORBIDDEN PEOPLE
        logger.info(f"🔍 Checking for forbidden people in response...")
        for forbidden_person in forbidden_people:
            if forbidden_person in response_lower:
                logger.warning(f"🚨 HALLUCINATION DETECTED: Mentioned non-existent person '{forbidden_person}'")
                logger.info(f"📍 Found '{forbidden_person}' in response: {response_lower[:200]}...")
                # Return a safe factual response instead
                if "teacher" in query.lower() or "staff" in query.lower() or "guro" in query.lower() or "maestra" in query.lower():
                    return self._get_known_staff_list(lang)
                else:
                    return self._get_safe_response_for_unknown_person(lang)
        logger.info(f"✅ No forbidden people found in response")
        
        # 🚨 CHECK FOR MADE-UP DATES/HISTORY  
        made_up_patterns = [
            "1990", "founded", "established", "built in", "since 19", "year 19", "century",
            "hero", "brave", "great tomas", "renowned educator", "community leader",
            "bustos, laguna", "laguna", "bustos", "insert year", "[insert year]",
            "dedicated his life", "served the people", "worked tirelessly",
            "san mateo, rizal", "rizal", "san mateo", "named after tomas", "strong advocate",
            "quality education", "legacy", "nurturing environment"
        ]
        if any(pattern in response_lower for pattern in made_up_patterns):
            logger.warning(f"🚨 HALLUCINATION DETECTED: Made-up historical/location information")
            if ("history" in query.lower() or "founded" in query.lower() or "when" in query.lower() or 
                "😊🎉🏫" in query or "tell me about" in query.lower() or "about tomas" in query.lower()):
                return self._get_safe_historical_response(lang)
            elif "location" in query.lower() or "address" in query.lower() or "saan" in query.lower() or "diin" in query.lower():
                return self._get_safe_address_response(lang)
        
        # 🚨 CHECK FOR FAKE ROLEPLAY ACTIONS
        roleplay_patterns = [
            "*checks calendar*", "*checks with", "*checking", "*looks at", "*reviews",
            "*checks schedule*", "*confirms", "*verifies", "let me check", "let me just check",
            "*walks to", "*goes to", "*searches through", "would you like me to escort",
            "*prepares", "*organizes", "*arranges", "8:30 am to 10:00 am", "specific time slots"
        ]
        if any(pattern in response_lower for pattern in roleplay_patterns):
            logger.warning(f"🚨 ROLEPLAY DETECTED: Fake actions and made-up schedules")
            if "enrollment" in query.lower() or "documents" in query.lower():
                return "For enrollment information and required documents, please visit the school office during regular hours."
            elif "schedule" in query.lower() or "time" in query.lower():
                return "For current schedules and specific timing, please contact the school office directly."
            else:
                return "For detailed information about school procedures, please visit the school office."
        
        # 🚨 CHECK FOR NON-EXISTENT STAFF MENTIONED
        # First check for specific fictional staff roles
        fictional_staff_patterns = [
            "guidance counselor", "school counselor", "librarian", "nurse", "security guard"
        ]
        
        # Special handling: Allow "guidance office" but block "guidance counselor"
        # Check if the response mentions guidance office location (which is OK) vs guidance counselor (which is not OK)
        guidance_office_ok = False
        if "guidance office" in response_lower:
            # If it's talking about the location/address of the office, that's okay
            if any(location_word in response_lower for location_word in ["located", "matatagpuan", "nasa", "sa loob", "malapit", "address", "location"]):
                guidance_office_ok = True
                logger.info("✅ Guidance office location mention is allowed")
        
        # ENHANCED: Check for guidance counselor claims more strictly
        counselor_claims = [
            "may guidance counselor", "we have a guidance counselor", "our guidance counselor",
            "guidance counselor ang", "guidance counselor na", "meron kaming guidance counselor",
            "ang guidance counselor", "si guidance counselor", "may counselor"
        ]
        
        for claim in counselor_claims:
            if claim in response_lower:
                logger.warning(f"🚨 GUIDANCE COUNSELOR CLAIM DETECTED: '{claim}'")
                if "teacher" in query.lower() or "staff" in query.lower() or "guro" in query.lower() or "maestra" in query.lower():
                    return self._get_known_staff_list(lang)
                else:
                    return self._get_safe_response_for_unknown_person(lang)
        
        # Only check for fictional staff if it's not an allowed guidance office mention
        if not guidance_office_ok and any(pattern in response_lower for pattern in fictional_staff_patterns):
            logger.warning(f"🚨 HALLUCINATION DETECTED: Mentioned non-existent staff role")
            if "teacher" in query.lower() or "staff" in query.lower() or "guro" in query.lower() or "maestra" in query.lower():
                return self._get_known_staff_list(lang)
            else:
                return self._get_safe_response_for_unknown_person(lang)
        
        # Additionally, if it mentions "counselor" alone (without "guidance office" context), block it
        if "counselor" in response_lower and not guidance_office_ok:
            logger.warning(f"🚨 HALLUCINATION DETECTED: Mentioned non-existent counselor")
            return self._get_safe_response_for_unknown_person(lang)
        
        # Then check for unknown staff names - BUT ONLY if response specifically mentions a name with title
        # Don't trigger on generic mentions of "teacher" or general office references
        words = response_lower.split()
        for i, word in enumerate(words):
            if word in ["mrs.", "mr.", "ms."] and i + 1 < len(words):
                mentioned_name = words[i + 1].strip(".,!?")
                # Only flag if it's actually claiming a specific person exists
                if mentioned_name not in [name.split()[-1].lower() for name in known_staff]:
                    logger.warning(f"🚨 HALLUCINATION DETECTED: Unknown staff member '{mentioned_name}'")
                    return self._get_safe_response_for_unknown_person(lang)
        
        logger.info("✅ Response passed all validation checks")
        return response
    
    def _get_safe_response_for_unknown_person(self, lang: str) -> str:
        """Safe response when asked about unknown people."""
        if lang == "tl" or lang == "akl":
            return "Hindi ko kilala ang taong iyon. Para sa impormasyon tungkol sa aming staff, makakausap ninyo ang school office."
        else:
            return "I don't have information about that person. For staff information, please contact the school office."
    
    def _get_safe_school_appropriate_response(self, query: str, lang: str) -> str:
        """Generate safe, contextually appropriate response for school setting."""
        query_lower = query.lower()
        
        # Determine the type of query to provide appropriate fallback
        if any(word in query_lower for word in ["location", "address", "saan", "diin", "nasa", "where"]):
            # Location queries
            if lang == "tl" or lang == "akl":
                return "Ang Tomas SM. Bautista Elementary School ay matatagpuan sa Fatima, New Washington, Aklan. Para sa mas detalyadong direksyon, tumawag sa (036) 269-6345."
            else:
                return "Tomas SM. Bautista Elementary School is located in Fatima, New Washington, Aklan. For detailed directions, please call (036) 269-6345."
        
        elif any(word in query_lower for word in ["teacher", "staff", "guro", "maestra", "maestro", "faculty"]):
            # Staff queries
            if lang == "tl" or lang == "akl":
                return "Para sa impormasyon tungkol sa aming mga guro at staff, makipag-ugnayan sa school office sa (036) 269-6345 o bumisita sa school premises."
            else:
                return "For information about our teachers and staff, please contact the school office at (036) 269-6345 or visit the school premises."
        
        elif any(word in query_lower for word in ["enrollment", "enroll", "register", "admission", "mag-enroll", "pag-enroll"]):
            # Enrollment queries
            if lang == "tl" or lang == "akl":
                return "Para sa enrollment information at requirements, pumunta sa school office sa regular na oras. Tutulungan kayo ng staff sa lahat ng kailangan."
            else:
                return "For enrollment information and requirements, please visit the school office during regular hours. Our staff will assist you with everything you need."
        
        elif any(word in query_lower for word in ["schedule", "time", "hours", "oras", "edulye", "iskedyul"]):
            # Schedule/timing queries
            if lang == "tl" or lang == "akl":
                return "Para sa mga schedule at oras ng klase, makipag-ugnayan sa school office sa (036) 269-6345."
            else:
                return "For class schedules and timing information, please contact the school office at (036) 269-6345."
        
        elif any(word in query_lower for word in ["facility", "facilities", "pasilidad", "building", "gusali", "room", "silid"]):
            # Facilities queries
            if lang == "tl" or lang == "akl":
                return "Para sa impormasyon tungkol sa mga facilities ng paaralan, makipag-ugnayan sa school office o bumisita sa school premises."
            else:
                return "For information about school facilities, please contact the school office or visit the school premises."
        
        else:
            # General fallback
            if lang == "tl" or lang == "akl":
                return "Para sa lahat ng mga katanungan tungkol sa paaralan, makipag-ugnayan sa Tomas SM. Bautista Elementary School office sa (036) 269-6345."
            else:
                return "For all school-related inquiries, please contact Tomas SM. Bautista Elementary School office at (036) 269-6345."
    
    def _get_safe_historical_response(self, lang: str) -> str:
        """Safe response for historical queries."""
        if lang == "tl" or lang == "akl":
            return "Hindi ko po alam ang eksaktong kasaysayan ng paaralan. Para sa historical information, makakausap ninyo ang school office."
        else:
            return "I don't have specific historical information about the school. Please contact the school office for detailed history."
    
    def _get_safe_address_response(self, lang: str) -> str:
        """Safe response for address/location queries."""
        if lang == "tl" or lang == "akl":
            return "Ang Tomas SM. Bautista Elementary School ay matatagpuan sa Fatima, New Washington, Aklan."
        else:
            return "Tomas SM. Bautista Elementary School is located in Fatima, New Washington, Aklan."

    async def ask_groq(self, query: str, context: str, lang: str, conversation_history: list = None, user_timezone: str = None) -> str:
        """Token-optimized Groq API call with emergency fallbacks."""
        # Extract user name from full conversation history before truncation
        user_name = self._extract_user_name(conversation_history) if conversation_history else ""
        
        # Start with friendly, conversational prompt
        system_prompt = self.get_time_aware_system_prompt(lang, user_name, user_timezone)
        
        # Emergency token management
        max_context_length = 1500
        emergency_context_length = 500
        critical_context_length = 100
        
        # Try progressively smaller contexts if needed
        context_attempts = [
            (max_context_length, "normal"),
            (emergency_context_length, "emergency"), 
            (critical_context_length, "critical"),
            (0, "no_context")
        ]
        
        for max_len, mode in context_attempts:
            try:
                # Prepare context for this attempt
                if max_len == 0:
                    # No context mode - ultra minimal
                    truncated_context = ""
                    user_message = query
                    max_tokens = 50  # Minimal response
                elif len(context) > max_len:
                    truncated_context = context[:max_len] + "..."
                    user_message = f"Context: {truncated_context}\nQ: {query}"
                    max_tokens = 100 if mode == "critical" else 150
                else:
                    truncated_context = context
                    user_message = f"Context: {truncated_context}\nQuestion: {query}"
                    max_tokens = 150
                
                # Calculate estimated tokens (rough: 4 chars = 1 token)
                estimated_tokens = (len(system_prompt) + len(user_message) + max_tokens) / 4
                
                logger.info(f"🔍 Token attempt ({mode}): ~{estimated_tokens:.0f} tokens estimated")
                
                # Build messages array with conversation history
                messages = [{"role": "system", "content": system_prompt}]
                
                # Add conversation history if provided (limit to last 8 messages to control token usage)
                if conversation_history and len(conversation_history) > 0:
                    # Take last 8 messages for context while staying within token limits
                    recent_history = conversation_history[-8:]
                    messages.extend(recent_history)
                    logger.info(f"💬 Including {len(recent_history)} conversation history messages")
                
                # Add current user message
                messages.append({"role": "user", "content": user_message})
                
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": max_tokens
                }
                
                headers = {
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json",
                }
                
                async with httpx.AsyncClient(timeout=30) as client:  # Shorter timeout for retries
                    response = await client.post(self.groq_api, json=payload, headers=headers)
                    response.raise_for_status()
                    ai_response = response.json()["choices"][0]["message"]["content"].strip()
                    
                    # 🛡️ VALIDATE RESPONSE TO PREVENT HALLUCINATION
                    validated_response = self._validate_response_against_facts(ai_response, query, lang)
                    
                    if mode != "normal":
                        logger.warning(f"⚠️ Used {mode} token mode for response")
                    
                    return validated_response
                    
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if it's a token limit error
                if any(keyword in error_msg for keyword in ["token", "limit", "exceeded", "too large", "context_length"]):
                    logger.warning(f"🚨 Token limit hit in {mode} mode: {e}")
                    
                    if mode == "no_context":
                        # Last resort - return template response
                        logger.error("🚨 All token strategies failed, using template response")
                        return await self._emergency_template_response(query, lang)
                    
                    # Try next smaller context
                    continue
                else:
                    # Non-token error, try emergency fallback
                    logger.error(f"❌ Groq API error in {mode} mode: {e}")
                    if mode == "no_context":
                        return await self._emergency_template_response(query, lang)
                    continue
        
        # If all attempts fail
        return await self._emergency_template_response(query, lang)

    async def _emergency_template_response(self, query: str, lang: str) -> str:
        """Emergency response when all token strategies fail."""
        logger.error("🚨 Emergency template response activated")
        
        # Ultra-basic keyword matching for common queries
        query_lower = query.lower()
        
        # Check for common names/keywords in query
        if any(name in query_lower for name in ["meliza", "delgado"]):
            response = "Meliza Delgado is the Head Teacher. Visit school office for details."
        elif any(word in query_lower for word in ["teacher", "staff", "faculty"]):
            response = "For staff information, please visit the school office."
        elif any(word in query_lower for word in ["contact", "phone", "email", "address"]):
            response = "For contact information, please visit the school office."
        elif any(word in query_lower for word in ["enrollment", "admission", "register"]):
            response = "For enrollment information, please visit the school office."
        else:
            response = "Please visit the school office for assistance with your inquiry."
        
        # 🛡️ Apply validation even to emergency responses
        return self._validate_response_against_facts(response, query, lang)

    async def _keyword_matching_response(self, query: str, lang: str, conversation_history: List[Dict] = None) -> str:
        """Enhanced keyword matching - zero token usage alternative with conversation context."""
        query_lower = query.lower()
        
        # Extract names from conversation for personalization
        user_name = self._extract_user_name(conversation_history or [])
        child_name = self._extract_child_name(conversation_history or [])
        
        # Expanded keyword database with conversational, playful responses
        keyword_responses = {
            # Staff Information - Playful responses
            ("meliza", "delgado"): {
                "en": "Oh, you're asking about Mrs. Meliza! 😊 She's our amazing Head Teacher - Meliza A. Delgado. She's the one who keeps everything running smoothly here at school!",
                "tl": "Ay, si Ms. Meliza! 😊 Siya ang aming napakagaling na Head Teacher - si Meliza A. Delgado. Siya ang nag-aasikaso para maayos ang lahat dito sa paaralan!",
                "default": "Si Meliza A. Delgado ang Head Teacher ng Tomas SM. Bautista Elementary School."
            },
            ("head teacher", "head_teacher"): {
                "en": "That would be Mrs. Meliza A. Delgado! 📚 She's fantastic at what she does - our Head Teacher extraordinaire!",
                "tl": "Si Mrs. Meliza A. Delgado yan! 📚 Napakagaling naming Head Teacher - talagang expert!",
                "default": "Si Meliza A. Delgado ang Head Teacher."
            },
            # TEACHERS QUERY - Return proper staff list (Enhanced patterns)
            ("guro", "teacher", "teachers", "mga", "staff", "faculty", "nagtuturo", "maestro", "maestra"): {
                "en": f"Here are our wonderful teachers at Tomas SM. Bautista Elementary School! 👩‍🏫👨‍🏫\n\n{self._get_known_staff_list('en')}",
                "tl": f"Narito ang aming mga guro sa Tomas SM. Bautista Elementary School! 👩‍🏫👨‍🏫\n\n{self._get_known_staff_list('tl')}",
                "default": f"Narito ang mga guro ng Tomas SM. Bautista Elementary School:\n\n{self._get_known_staff_list('tl')}"
            },
            # Additional teacher query patterns
            ("tell", "about", "staff"): {
                "en": f"Here are the known staff members at TOMAS Elementary School:\n\n{self._get_known_staff_list('en')}",
                "tl": f"Narito ang mga kilalang miyembro ng staff ng TOMAS Elementary School:\n\n{self._get_known_staff_list('tl')}",
                "default": f"Narito ang mga staff ng TOMAS Elementary School:\n\n{self._get_known_staff_list('tl')}"
            },
            ("list", "faculty", "members"): {
                "en": f"Here are the known staff members at TOMAS Elementary School:\n\n{self._get_known_staff_list('en')}",
                "tl": f"Narito ang mga kilalang miyembro ng staff ng TOMAS Elementary School:\n\n{self._get_known_staff_list('tl')}",
                "default": f"Narito ang mga faculty ng TOMAS Elementary School:\n\n{self._get_known_staff_list('tl')}"
            },
            ("who", "are", "teachers"): {
                "en": f"Here are the known staff members at TOMAS Elementary School:\n\n{self._get_known_staff_list('en')}",
                "tl": f"Narito ang mga kilalang miyembro ng staff ng TOMAS Elementary School:\n\n{self._get_known_staff_list('tl')}",
                "default": f"Narito ang mga guro ng TOMAS Elementary School:\n\n{self._get_known_staff_list('tl')}"
            },
            ("sino", "mga", "faculty"): {
                "en": f"Here are the known staff members at TOMAS Elementary School:\n\n{self._get_known_staff_list('en')}",
                "tl": f"Narito ang mga kilalang miyembro ng staff ng TOMAS Elementary School:\n\n{self._get_known_staff_list('tl')}",
                "default": f"Narito ang mga faculty ng TOMAS Elementary School:\n\n{self._get_known_staff_list('tl')}"
            },
            ("taong", "nagtuturo", "dito"): {
                "en": f"Here are our wonderful teachers at Tomas SM. Bautista Elementary School! 👩‍🏫👨‍🏫\n\n{self._get_known_staff_list('en')}",
                "tl": f"Narito ang aming mga guro sa Tomas SM. Bautista Elementary School! 👩‍🏫👨‍🏫\n\n{self._get_known_staff_list('tl')}",
                "default": f"Narito ang mga nagtuturo dito:\n\n{self._get_known_staff_list('tl')}"
            },
            # School Information - Friendly location response
            ("address", "location", "where", "siin", "diin", "asa", "saan"): {
                "en": "We're located in the beautiful area of Fatima, New Washington, Aklan! 🏫 It's a lovely spot for learning!",
                "tl": "Narito kami sa magandang lugar ng Fatima, New Washington, Aklan! 🏫 Napakagandang lugar para sa pag-aaral!",
                "default": "Ang lokasyon ng paaralan ay matatagpuan sa Fatima, New Washington, Aklan."
            },
            ("phone", "contact", "number"): {
                "en": "For our contact details, just drop by the school office! 📞 The staff there will be happy to help you out!",
                "tl": "Para sa contact namin, pumunta lang sa office ng paaralan! 📞 Matutuwa ang staff na tumulong sa inyo!",
                "default": "For contact information, please visit the school office."
            },

            # Language Questions - Aklanon
            ("speak", "aklanon", "language", "can you"): {
                "en": "Yes, I can understand some Aklanon! 😊 I have basic knowledge of Aklanon words and phrases. Feel free to ask me questions in Aklanon, English, or Tagalog - I'll do my best to help! Kumusta ka? 🤗",
                "tl": "Oo, nakakaintindi ako ng kaunting Aklanon! 😊 May alam akong mga salita at parirala sa Aklanon. Magtanong lang kayo sa Aklanon, English, o Tagalog - gagawin ko ang makakaya ko! Kumusta ka? 🤗",
                "default": "Oo, nakakaintindi ako ng kaunting Aklanon! Magtanong lang kayo! 😊"
            },

            # PERSONALIZED NAME QUERIES - Warm, contextual responses
            # English patterns
            ("whats", "my", "name"): "PERSONALIZED_NAME_QUERY",  # Special marker
            ("what", "is", "my", "name"): "PERSONALIZED_NAME_QUERY",  # Special marker
            ("my", "name", "again"): "PERSONALIZED_NAME_QUERY",  # Special marker
            ("remind", "me", "my", "name"): "PERSONALIZED_NAME_QUERY",  # Special marker
            ("tell", "me", "my", "name"): "PERSONALIZED_NAME_QUERY",  # Special marker
            ("do", "you", "remember", "my", "name"): "PERSONALIZED_NAME_QUERY",  # Special marker
            
            # Tagalog patterns for name queries
            ("ano", "ang", "pangalan", "ko"): "PERSONALIZED_NAME_QUERY",  # Special marker
            ("pangalan", "ko", "ulit"): "PERSONALIZED_NAME_QUERY",  # Special marker
            ("naaalala", "mo", "pangalan", "ko"): "PERSONALIZED_NAME_QUERY",  # Special marker
            ("sino", "ako"): "PERSONALIZED_NAME_QUERY",  # Special marker
            ("tawag", "sa", "akin"): "PERSONALIZED_NAME_QUERY",  # Special marker
            ("kung", "ano", "pangalan", "ko"): "PERSONALIZED_NAME_QUERY",  # Special marker
            
            # English child name patterns
            ("whats", "my", "sons", "name"): "PERSONALIZED_CHILD_QUERY",  # Special marker
            ("what", "is", "my", "sons", "name"): "PERSONALIZED_CHILD_QUERY",  # Special marker
            ("my", "sons", "name"): "PERSONALIZED_CHILD_QUERY",  # Special marker
            ("remind", "me", "my", "sons", "name"): "PERSONALIZED_CHILD_QUERY",  # Special marker
            ("whats", "my", "daughters", "name"): "PERSONALIZED_CHILD_QUERY",  # Special marker
            ("what", "is", "my", "daughters", "name"): "PERSONALIZED_CHILD_QUERY",  # Special marker
            ("my", "daughters", "name"): "PERSONALIZED_CHILD_QUERY",  # Special marker
            ("whats", "my", "childs", "name"): "PERSONALIZED_CHILD_QUERY",  # Special marker
            ("my", "childs", "name"): "PERSONALIZED_CHILD_QUERY",  # Special marker
            
            # Tagalog child name patterns
            ("ano", "pangalan", "ng", "anak", "ko"): "PERSONALIZED_CHILD_QUERY",  # Special marker
            ("pangalan", "ng", "anak", "ko"): "PERSONALIZED_CHILD_QUERY",  # Special marker
            ("sino", "ang", "anak", "ko"): "PERSONALIZED_CHILD_QUERY",  # Special marker
            ("tawag", "sa", "anak", "ko"): "PERSONALIZED_CHILD_QUERY",  # Special marker
            ("naaalala", "mo", "anak", "ko"): "PERSONALIZED_CHILD_QUERY",  # Special marker
            ("ano", "pangalan", "ng", "bata", "ko"): "PERSONALIZED_CHILD_QUERY",  # Special marker
            
            # Aklanon patterns for name queries  
            ("ano", "nga", "ngaean", "ko"): "PERSONALIZED_NAME_QUERY",  # What is my name
            ("sin-o", "ako"): "PERSONALIZED_NAME_QUERY",  # Who am I
            ("ngaean", "ko", "ulit"): "PERSONALIZED_NAME_QUERY",  # My name again
            ("nahanumdom", "mo", "ngaean", "ko"): "PERSONALIZED_NAME_QUERY",  # Do you remember my name
            
            # Aklanon patterns for child name queries
            ("ano", "ngaean", "sang", "imo", "unga"): "PERSONALIZED_CHILD_QUERY",  # What is my child's name
            ("sin-o", "ang", "unga", "ko"): "PERSONALIZED_CHILD_QUERY",  # Who is my child
            ("ngaean", "sang", "unga", "ko"): "PERSONALIZED_CHILD_QUERY",  # My child's name
            ("nahanumdom", "mo", "unga", "ko"): "PERSONALIZED_CHILD_QUERY",  # Do you remember my child
            
            # Academic Information - MOVED BEFORE LANGUAGE TO PRIORITIZE
            ("enrollment", "admission", "register", "help", "can you help"): "PERSONALIZED_ENROLLMENT",  # Special marker
            ("tuition", "fee", "payment"): "For tuition and fee information, please visit the school office.",
            ("curriculum", "subjects", "classes"): "For curriculum information, please visit the school office.",
            ("grade", "level"): "For grade level information, please visit the school office.",
            
            # Activities
            ("events", "activities", "programs"): "For school events and activities, please visit the school office.",
            ("sports", "athletics"): "For sports programs, please visit the school office.",
            ("clubs", "organizations"): "For club information, please visit the school office.",
            
            # Requirements
            ("requirements", "documents", "papers"): "For document requirements, please visit the school office.",
            ("uniform", "dress code"): "For uniform policies, please visit the school office.",
            ("supplies", "materials"): "For school supplies list, please visit the school office.",
        }
        
        # Find matching keywords with exact pattern matching for personalized responses
        best_match = None
        max_matches = 0
        best_response = None
        
        for keywords, response in keyword_responses.items():
            # For personalized patterns, require ALL keywords to be present for exact matching
            if response in ["PERSONALIZED_NAME_QUERY", "PERSONALIZED_CHILD_QUERY", "PERSONALIZED_ENROLLMENT"]:
                # For personalized responses, all keywords must be present in sequence or exact match
                query_words = query_lower.split()
                keyword_matches = 0
                for keyword in keywords:
                    if keyword in query_words:
                        keyword_matches += 1
                
                # Only match if ALL keywords in the pattern are found
                if keyword_matches == len(keywords):
                    matches = keyword_matches
                else:
                    matches = 0
            else:
                # For regular patterns, use the old partial matching
                matches = sum(1 for keyword in keywords if keyword in query_lower)
            
            if matches > max_matches:
                max_matches = matches
                best_match = keywords
                best_response = response
        
        if best_match and max_matches > 0:
            logger.info(f"🎯 Keyword match found ({max_matches} matches)")
            
            # Special handling for enrollment queries - generate personalized response
            if best_response == "PERSONALIZED_ENROLLMENT":
                logger.info("🎯 Generating personalized enrollment response")
                return self._get_personalized_enrollment_response(user_name, child_name, lang)
            
            # Special handling for name queries - generate warm, personalized response
            if best_response == "PERSONALIZED_NAME_QUERY":
                logger.info("🎯 Generating personalized name response")
                return self._get_personalized_name_response(user_name, child_name, lang)
            
            # Special handling for child name queries - generate warm, personalized response
            if best_response == "PERSONALIZED_CHILD_QUERY":
                logger.info("🎯 Generating personalized child name response")
                return self._get_personalized_child_response(user_name, child_name, lang)
            
            # Handle new dictionary format with language-specific responses
            if isinstance(best_response, dict):
                # Get language-specific response
                if lang == "akl":
                    # For Aklanon, use Tagalog response
                    response_text = best_response.get("tl", best_response.get("default", ""))
                else:
                    response_text = best_response.get(lang, best_response.get("default", ""))
                return response_text
            else:
                # Handle old string format (backward compatibility)
                # Translate to appropriate language if needed
                if lang == "tl" and not any(filipino_word in best_response for filipino_word in ["Si", "ang", "ng"]):
                    # Simple translation for common phrases
                    translated = await self._simple_translate_to_tagalog(best_response)
                    return f"Ayon sa aming records: {translated}"
                elif lang == "en" and any(filipino_word in best_response for filipino_word in ["Si", "ang", "ng"]):
                    # Special case: for location responses, return English version
                    if "Ang lokasyon ng paaralan ay matatagpuan sa Fatima, New Washington, Aklan" in best_response:
                        return "The school is located in Fatima, New Washington, Aklan."
                    # Convert Filipino response to English for other cases
                    translated = await self._simple_translate_to_english(best_response)
                    return translated
                else:
                    # Special handling for location responses - return as-is without prefix
                    if "Ang lokasyon ng paaralan ay matatagpuan sa Fatima, New Washington, Aklan" in best_response:
                        return best_response
                    # For other responses, add prefix for non-English
                    return best_response if lang == "en" else f"Ayon sa aming records: {best_response}"
        
        # Generic fallback
        fallback_msg = "Please visit the school office for assistance with your inquiry."
        return fallback_msg if lang == "en" else f"Ayon sa aming records: Pumunta po sa opisina ng paaralan para sa tulong."

    async def _simple_translate_to_tagalog(self, text: str) -> str:
        """Simple translation without API calls."""
        replacements = {
            "Head Teacher": "Head Teacher",  # Keep English titles
            "Principal": "Principal",
            "school office": "opisina ng paaralan",
            "visit": "pumunta sa",
            "for": "para sa",
            "information": "impormasyon",
            "please": "pakisuyo",
            "details": "detalye"
        }
        
        result = text
        for english, tagalog in replacements.items():
            result = result.replace(english, tagalog)
        return result
    
    async def _simple_translate_to_english(self, text: str) -> str:
        """Simple translation without API calls."""
        replacements = {
            "Si": "",
            "ang": "the",
            "ng": "of",
            "paaralan": "school",
            "Head Teacher": "Head Teacher",
            "Principal": "Principal"
        }
        
        result = text
        for tagalog, english in replacements.items():
            result = result.replace(tagalog, english)
        return result.strip()

            
    async def fetch_prompts_from_supabase(self, query: str) -> str:
        """Enhanced search using search_tsv full-text search first, then fallback methods."""
        try:
            # 🛡️ SAFETY CHECK: Handle None or empty query
            if not query or query is None:
                logger.warning("⚠️ Fetch prompts received None or empty query")
                return ""
            
            # Ensure query is a string
            query = str(query).strip()
            if not query:
                logger.warning("⚠️ Fetch prompts received empty string after cleanup")
                return ""
            
            # PRIORITY 1: Try full-text search using search_tsv (most powerful)
            result = await self._try_full_text_search(query)
            if result:
                logger.info("✅ Found result using full-text search (search_tsv)")
                return result
            
            # PRIORITY 2: Extract key search terms and try traditional methods
            search_terms = self._extract_search_terms(query)[:3]
            
            # Quick exact match (most token-efficient)
            result = await self._try_exact_match(search_terms)
            if result:
                return result
            
            # Then try ILIKE (moderate token usage)
            result = await self._try_ilike_search(search_terms)
            if result:
                return result
            
            # Only use fuzzy as last resort with strict limits
            result = await self._try_limited_fuzzy_search(query)
            return result
            
        except Exception as e:
            logger.error(f"Error in optimized fetch_prompts_from_supabase: {e}")
            return ""

    async def _try_full_text_search(self, query: str) -> str:
        """Use PostgreSQL full-text search via search_tsv column for names and content."""
        try:
            # 🛡️ SAFETY CHECK: Handle None or empty query
            if not query or query is None:
                logger.warning("⚠️ Full-text search received None or empty query")
                return ""
            
            # Ensure query is a string
            query = str(query).strip()
            if not query:
                logger.warning("⚠️ Full-text search received empty string after cleanup")
                return ""
            
            # Clean the query for full-text search
            import re
            
            # Remove punctuation and split into words
            clean_query = re.sub(r'[^\w\s]', ' ', query.lower())
            words = [word.strip() for word in clean_query.split() if len(word.strip()) > 2]
            
            # Remove common stop words
            stop_words = {"who", "is", "the", "what", "where", "when", "how", "and", "or", "but", 
                         "sino", "si", "ang", "sa", "ng", "may", "are", "was", "were", "have", "has"}
            search_words = [word for word in words if word not in stop_words]
            
            if not search_words:
                return ""
            
            # 🎯 STAFF QUERY PRIORITY: Check if this is a staff-related query
            staff_keywords = ["head", "teacher", "principal", "guidance", "nurse", "secretary", "director", "admin"]
            is_staff_query = any(word in staff_keywords for word in search_words)
            
            if is_staff_query:
                logger.info("🎯 Detected staff query - prioritizing exact staff matches")
                
                # For staff queries, prioritize exact matches in keywords field first
                staff_terms = ["head teacher", "principal", "guidance", "nurse", "secretary"]
                for staff_term in staff_terms:
                    try:
                        result = self.supabase.table("chatbot_prompts") \
                            .select("keywords, response") \
                            .ilike("keywords", f"%{staff_term}%") \
                            .execute()
                        
                        if result.data:
                            logger.info(f"✅ Found staff-specific match for '{staff_term}'")
                            best_match = result.data[0]
                            formatted_result = f"Q: {best_match['keywords']}\nA: {best_match['response']}"
                            return formatted_result
                    except Exception as e:
                        logger.warning(f"Staff search failed for '{staff_term}': {e}")
            
            # Try searching individual meaningful words first (simpler approach)
            for word in search_words:
                logger.info(f"🔍 Full-text search for: '{word}'")
                
                try:
                    # Use proper Supabase client methods with correct wildcard syntax
                    result = self.supabase.table("chatbot_prompts") \
                        .select("keywords, response") \
                        .ilike("keywords", f"%{word}%") \
                        .execute()
                    
                    # For staff queries, prioritize exact staff information over general school info
                    if is_staff_query and result.data:
                        # Filter out general school information for staff queries
                        filtered_results = []
                        for item in result.data:
                            keywords_lower = item['keywords'].lower()
                            # Skip general school descriptions when looking for staff
                            if not any(general in keywords_lower for general in ["what is tomas", "school is", "elementary school"]):
                                filtered_results.append(item)
                        
                        if filtered_results:
                            best_match = filtered_results[0]
                            formatted_result = f"Q: {best_match['keywords']}\nA: {best_match['response']}"
                            return formatted_result
                    
                    # If no results in keywords, try response field
                    if not result.data:
                        result = self.supabase.table("chatbot_prompts") \
                            .select("keywords, response") \
                            .ilike("response", f"%{word}%") \
                            .execute()
                    
                    if result.data:
                        logger.info(f"✅ Full-text search succeeded for '{word}' with {len(result.data)} results")
                        # Return the best match
                        best_match = result.data[0]
                        formatted_result = f"Q: {best_match['keywords']}\nA: {best_match['response']}"
                        return formatted_result
                        
                except Exception as e:
                    logger.warning(f"Full-text search failed for '{word}': {e}")
            
            logger.info("❌ No results found with full-text search")
            return ""
            
        except Exception as e:
            logger.warning(f"Error in full-text search: {e}")
            return ""

    async def _try_exact_match(self, search_terms: list) -> str:
        """Fast exact matching - most token efficient."""
        if not search_terms:
            return ""
        
        try:
            url = f"{SUPABASE_URL}/rest/v1/chatbot_prompts"
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            # Try exact matches for key terms using Supabase client
            for term in search_terms:
                try:
                    # Try exact match in keywords first
                    result = self.supabase.table("chatbot_prompts") \
                        .select("keywords, response") \
                        .eq("keywords", term) \
                        .limit(1) \
                        .execute()
                    
                    if result.data:
                        logger.info(f"✅ Exact match found for '{term}'")
                        row = result.data[0]
                        return f"Q: {row.get('keywords', '')}\nA: {row.get('response', '')}"
                    
                    # Try ilike in response if no exact match
                    result = self.supabase.table("chatbot_prompts") \
                        .select("keywords, response") \
                        .ilike("response", f"%{term}%") \
                        .limit(1) \
                        .execute()
                    
                    if result.data:
                        logger.info(f"✅ Response match found for '{term}'")
                        row = result.data[0]
                        return f"Q: {row.get('keywords', '')}\nA: {row.get('response', '')}"
                        
                except Exception as e:
                    logger.warning(f"Exact match search failed for '{term}': {e}")
                    continue
                            
        except Exception as e:
            logger.warning(f"Exact match search failed: {e}")
        
        return ""

    def _extract_search_terms(self, query: str) -> list:
        """Extract meaningful search terms from query using improved NLP."""
        import re
        
        # Remove common stop words and clean the query
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'can', 'you', 'me', 'who', 'what', 'where', 'when', 'why', 'how', 'tell'}
        
        # Extract all words and clean them
        words = re.findall(r'\w+', query.lower())
        meaningful_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Extract names (capitalized words) from original query for better name matching
        names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
        
        # Extract quoted phrases (if any)
        quoted_phrases = re.findall(r'"([^"]*)"', query)
        
        # Combine all meaningful terms
        search_terms = meaningful_words + [name.lower() for name in names] + quoted_phrases
        
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in search_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)
        
        logger.info(f"🔍 Extracted search terms from '{query}': {unique_terms}")
        return unique_terms

    async def debug_table_structure(self) -> dict:
        """Debug method to check table structure and sample data."""
        try:
            url = f"{SUPABASE_URL}/rest/v1/chatbot_prompts"
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            params = {
                "select": "*",
                "limit": 1
            }

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, params=params)
                logger.info(f"Debug - Table check status: {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        logger.info(f"Debug - Sample record: {data[0]}")
                        return {"success": True, "sample": data[0], "columns": list(data[0].keys())}
                    else:
                        logger.info("Debug - Table is empty")
                        return {"success": True, "sample": None, "columns": []}
                else:
                    logger.error(f"Debug - Table check failed: {resp.text}")
                    return {"success": False, "error": resp.text}
                    
        except Exception as e:
            logger.error(f"Debug - Exception: {e}")
            return {"success": False, "error": str(e)}

    async def _try_fts_search(self, search_terms: list) -> str:
        """Try Full Text Search with improved term matching."""
        if not search_terms:
            return ""
        
        try:
            # Try different search strategies
            for strategy in ["AND", "OR"]:
                if strategy == "AND":
                    search_query = " & ".join(search_terms[:3])  # AND search with top 3 terms
                else:
                    search_query = " | ".join(search_terms[:5])  # OR search with more terms
                
                url = f"{SUPABASE_URL}/rest/v1/chatbot_prompts"
                headers = {
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }

                params = {
                    "select": "keywords,response",
                    "keywords": f"fts.{search_query}",
                    "limit": 3
                }

                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, headers=headers, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data:
                            logger.info(f"✅ FTS search successful with {strategy} strategy, found {len(data)} results")
                            return "\n".join(
                                f"Q: {row.get('keywords', '')}\nA: {row.get('response', '')}"
                                for row in data
                            )
        except Exception as e:
            logger.warning(f"FTS search failed: {e}")
        
        return ""

    async def _try_ilike_search(self, search_terms: list) -> str:
        """Optimized ILIKE search using Supabase client to avoid URL encoding issues."""
        if not search_terms:
            return ""
        
        try:
            # Try only the most relevant term first using Supabase client
            for term in search_terms[:2]:  # Reduced from 5 to 2
                try:
                    # Use Supabase client instead of manual URL construction
                    result = self.supabase.table("chatbot_prompts") \
                        .select("keywords, response") \
                        .ilike("keywords", f"%{term}%") \
                        .limit(1) \
                        .execute()
                    
                    if result.data:
                        logger.info(f"✅ ILIKE match found for '{term}' in keywords")
                        row = result.data[0]
                        return f"Q: {row.get('keywords', '')}\nA: {row.get('response', '')}"
                    
                    # Try in response field if not found in keywords
                    result = self.supabase.table("chatbot_prompts") \
                        .select("keywords, response") \
                        .ilike("response", f"%{term}%") \
                        .limit(1) \
                        .execute()
                    
                    if result.data:
                        logger.info(f"✅ ILIKE match found for '{term}' in response")
                        row = result.data[0]
                        return f"Q: {row.get('keywords', '')}\nA: {row.get('response', '')}"
                        
                except Exception as e:
                    logger.warning(f"ILIKE search failed for '{term}': {e}")
                    continue
                            
        except Exception as e:
            logger.warning(f"ILIKE search failed: {e}")
        
        return ""

    async def _try_limited_fuzzy_search(self, query: str) -> str:
        """Token-efficient fuzzy search with strict limits."""
        try:
            url = f"{SUPABASE_URL}/rest/v1/chatbot_prompts"
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            params = {
                "select": "keywords,response",
                "limit": 20  # Reduced from 100 to save tokens
            }

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        # Simple fuzzy matching on keywords only (more efficient)
                        keywords_only = [row.get('keywords', '') for row in data]
                        matches = process.extract(query, keywords_only, limit=1, scorer=fuzz.partial_ratio)
                        
                        for match, score, idx in matches:
                            if score >= 70:  # Higher threshold for quality
                                row = data[idx]
                                logger.info(f"✅ Limited fuzzy match found (score: {score})")
                                return f"Q: {row.get('keywords', '')}\nA: {row.get('response', '')}"
                        
        except Exception as e:
            logger.warning(f"Limited fuzzy search failed: {e}")
        
        return ""

    async def extract_snippet(self, text: str, query: str, window: int = 200, threshold: int = 75) -> str:
        """
        Token-efficient snippet extraction.
        """
        if not text or not query:
            return ""
            
        lines = text.splitlines()
        
        # Strategy 1: Exact phrase matching (most efficient)
        query_lower = query.lower()
        for i, line in enumerate(lines):
            if query_lower in line.lower():
                logger.info(f"🎯 Exact phrase match found")
                start = max(0, text.find(line) - window)
                end = min(len(text), start + len(line) + (2 * window))
                return text[start:end].strip()
        
        # Strategy 2: Name matching only (reduced complexity)
        import re
        names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
        if names:
            name = names[0]  # Only check first name to save processing
            for line in lines:
                if name.lower() in line.lower():
                    logger.info(f"🎯 Name match found for '{name}'")
                    start = max(0, text.find(line) - window)
                    end = min(len(text), start + len(line) + (2 * window))
                    return text[start:end].strip()
        
        # Strategy 3: Single fuzzy match (simplified)
        best_match, score, idx = process.extractOne(query, lines, scorer=fuzz.partial_ratio)
        
        if best_match and score >= threshold:
            logger.info(f"🎯 Fuzzy match found (score: {score})")
            start = max(0, text.find(best_match) - window)
            end = min(len(text), start + len(best_match) + (2 * window))
            return text[start:end].strip()
        
        logger.info(f"⚠️ No match found in summarized text")
        return ""

    def _analyze_human_request_intent(self, query: str) -> dict:
        """
        Advanced NLP analysis to determine if user actually wants human support.
        Returns dict with 'wants_human': bool and 'confidence': float
        """
        query_lower = query.lower().strip()
        
        # Strong indicators of wanting human support (high confidence)
        strong_human_indicators = [
            "talk to a person", "talk to human", "live agent", "real person speaking",
            "speak to someone", "contact a person", "human representative",
            "makipag usap sa tao", "gusto ko ng tao", "kausapin ang tao",
            "can i talk to", "let me speak to", "transfer me to",
            "i need to speak", "connect me to"
        ]
        
        # Check for strong indicators first
        for indicator in strong_human_indicators:
            if indicator in query_lower:
                return {"wants_human": True, "confidence": 0.9}
        
        # Weak indicators that need context analysis
        weak_indicators = ["person", "tao", "human", "someone", "people"]
        
        # Check if weak indicators are present
        has_weak_indicator = any(word in query_lower for word in weak_indicators)
        
        if not has_weak_indicator:
            return {"wants_human": False, "confidence": 0.9}
        
        # Context analysis for weak indicators
        # Questions about people (not requesting human contact)
        question_patterns = [
            r"\b(who|what|where|when|how|why|sino|ano|saan|kailan|paano|bakit)\b",
            r"\b(is|are|was|were|does|do|did|can|will|would|sino|ano)\b.*\b(person|people|tao)\b",
            r"\b(how many|ilang|pila)\b.*\b(person|people|tao)\b",
            r"\b(what.*call.*person|ano.*tawag.*tao)\b"
        ]
        
        import re
        for pattern in question_patterns:
            if re.search(pattern, query_lower):
                return {"wants_human": False, "confidence": 0.8}
        
        # Information requests about people
        info_patterns = [
            r"\b(about|regarding|tungkol|mahitungod)\b.*\b(person|people|tao)\b",
            r"\b(list|mga|names|pangalan)\b.*\b(person|people|tao)\b",
            r"\b(information|impormasyon|detalye)\b.*\b(person|people|tao)\b"
        ]
        
        for pattern in info_patterns:
            if re.search(pattern, query_lower):
                return {"wants_human": False, "confidence": 0.7}
        
        # Check for explicit request verbs (higher chance of wanting human)
        request_verbs = [
            "connect", "transfer", "redirect", "forward", "escalate",
            "ikonekta", "ilipat", "ipadala", "iabot"
        ]
        
        if any(verb in query_lower for verb in request_verbs):
            return {"wants_human": True, "confidence": 0.8}
        
        # Check sentence structure for direct requests
        direct_request_patterns = [
            r"\bi (want|need|would like|gusto|kailangan)\b.*\b(person|tao|human)\b",
            r"\b(can you|pwede|maaari).*\b(connect|get|find).*\b(person|tao|human)\b",
            r"\b(please|pakisuyo).*\b(person|tao|human)\b"
        ]
        
        for pattern in direct_request_patterns:
            if re.search(pattern, query_lower):
                return {"wants_human": True, "confidence": 0.7}
        
        # Default: likely just mentioning people in context
        return {"wants_human": False, "confidence": 0.6}

    def _analyze_query_intent(self, query: str) -> dict:
        """
        Comprehensive intent analysis for better query understanding.
        """
        query_lower = query.lower().strip()
        
        # Greeting detection
        greeting_patterns = [
            r"^(hi|hello|hey|kamusta|kumusta|mayad|maayad)\s*[!.?]*$",
            r"^(good morning|good afternoon|good evening|mayad nga agahon|mayad nga hapon|mayad nga gabi)\s*[!.?]*$"
        ]
        
        import re
        for pattern in greeting_patterns:
            if re.search(pattern, query_lower):
                return {"intent": "greeting", "confidence": 0.9}
        
        # Goodbye detection
        goodbye_patterns = [
            r"^(bye|goodbye|see you|salamat|thank you|wala na|tapos na|done|finished)\s*[!.?]*$",
            r"^(that's all|ok na|okay na|wa na|waay na)\s*[!.?]*$"
        ]
        
        for pattern in goodbye_patterns:
            if re.search(pattern, query_lower):
                return {"intent": "goodbye", "confidence": 0.9}
        
        # Question detection
        question_indicators = [
            r"\b(who|what|where|when|how|why|sino|ano|saan|kailan|paano|bakit|sin-o|asa|ano)\b",
            r"^(is|are|was|were|does|do|did|can|will|would)\b",
            r"\?$"
        ]
        
        for pattern in question_indicators:
            if re.search(pattern, query_lower):
                return {"intent": "question", "confidence": 0.8}
        
        # Request detection
        request_indicators = [
            r"\b(please|pakisuyo|paki|help|tulong|bulig)\b",
            r"\b(can you|could you|pwede|maaari)\b",
            r"\b(i need|i want|kailangan|gusto)\b"
        ]
        
        for pattern in request_indicators:
            if re.search(pattern, query_lower):
                return {"intent": "request", "confidence": 0.7}
        
        # Default: general query
        return {"intent": "general", "confidence": 0.5}

    async def answer(self, query: str, context: str = None, conversation_history: list = None, user_timezone: str = None, session_id: str = None) -> str:
        lang = await self.detect_language(query)
        lowered = query.lower().strip()  # For backward compatibility
        
        # Generate user ID from conversation or use provided session ID
        user_id = session_id if session_id else self._generate_user_id(conversation_history)
        
        # --- SENTIMENT ANALYSIS & TONE DETECTION ---
        sentiment_result = sentiment_analyzer.analyze_sentiment(query, {
            'conversation_history': conversation_history,
            'user_id': user_id,
            'language': lang
        })
        
        logger.info(f"🎭 Sentiment: {sentiment_result.sentiment.value} (confidence: {sentiment_result.confidence:.2f})")
        if sentiment_result.emotion:
            logger.info(f"😊 Emotion: {sentiment_result.emotion.value}")
        logger.info(f"📈 Urgency: {sentiment_result.urgency_level}/5")
        logger.info(f"🎯 Recommended tone: {sentiment_result.recommended_tone}")
        
        # Get tone adjustment suggestions for response personalization
        tone_adjustments = sentiment_analyzer.get_tone_adjustment_suggestions(sentiment_result)
        
        # --- CONVERSATION MEMORY: Get context for personalized responses ---
        memory_context = self.conversation_memory.generate_context_summary(user_id)
        should_use_context = self.conversation_memory.should_provide_context_response(user_id, "general")
        
        if should_use_context:
            logger.info(f"💭 Using conversation memory context for user {user_id[:8]}...")
        
        # Check for returning user greeting personalization
        if any(greeting in lowered for greeting in ["hi", "hello", "hey", "kamusta", "kumusta"]):
            greeting_context = self.conversation_memory.get_personalized_greeting_context(user_id)
            if greeting_context.get("is_returning_user") and greeting_context.get("user_name"):
                logger.info(f"👋 Returning user detected: {greeting_context['user_name']}")

        # --- NEW: NLU-Based Intent Analysis ---
        try:
            # Pass Groq client to NLU engine for AI-powered classification
            if hasattr(self, 'groq_key'):
                # Create async Groq client for NLU
                import httpx
                nlu_client = httpx.AsyncClient()
                self.nlu_engine.groq_client = nlu_client
            
            nlu_result = await self.nlu_engine.analyze_intent(query, conversation_history)
            logger.info(f"🧠 NLU Intent: {nlu_result.intent.value} (confidence: {nlu_result.confidence:.2f})")
            
            # --- NEW: Try Intelligent Response Generation First ---
            extracted_entities = await self._extract_entities_with_nlu(query)
            entity_list = extracted_entities.get('entities', [])
            
            # Convert entities to dict format for response generator
            entities_for_generator = []
            for entity in entity_list:
                entities_for_generator.append({
                    'entity_type': entity.entity_type,
                    'value': entity.value,
                    'confidence': entity.confidence
                })
            
            # Try intelligent response generation
            intelligent_response = self._generate_intelligent_response(
                intent=nlu_result.intent.value,
                user_id=user_id,
                query=query,
                extracted_entities=entities_for_generator,
                conversation_history=conversation_history,
                sentiment_result=sentiment_result
            )
            
            if intelligent_response:
                logger.info("🎯 Using intelligent response generation")
                await self._store_conversation_turn(user_id, query, intelligent_response, lang, conversation_history)
                return intelligent_response
            
            # Try to handle with intelligent NLU-based routing (fallback)
            nlu_response = await self._handle_intent_based_response(nlu_result, query, lang, conversation_history, user_timezone)
            if nlu_response:
                return nlu_response
                
        except Exception as e:
            logger.warning(f"NLU processing failed, falling back to legacy system: {e}")
        
        # --- Legacy fallback for compatibility ---
        intent_analysis = self._analyze_query_intent(query)
        human_analysis = self._analyze_human_request_intent(query)
        
        logger.info(f"🔄 Fallback Intent: {intent_analysis['intent']} (confidence: {intent_analysis['confidence']:.2f})")
        logger.info(f"👤 Human request: {human_analysis['wants_human']} (confidence: {human_analysis['confidence']:.2f})")

        # --- Detect if user explicitly wants human support (with high confidence) ---
        if human_analysis['wants_human'] and human_analysis['confidence'] > 0.7:
            logger.info("👤 High confidence human request → triggering fallback handler.")
            return self.fallback_handler.generate_fallback_message(lang)

        # --- Detect goodbye / end of conversation ---
        if intent_analysis['intent'] == 'goodbye' and intent_analysis['confidence'] > 0.8:
            logger.info("👋 User ended the conversation.")
            return self.get_goodbye(lang)
        # --- Enhanced goodbye detection ---
        goodbye_keywords = [
            "goodbye", "bye", "see you", "farewell", "adios", "salamat", 
            "thanks", "thank you", "ok thanks", "got it", "wala na", 
            "wa eun", "waay na", "tapos na", "that's all", "finished", "done", "nope"
        ]
        if any(k in lowered for k in goodbye_keywords):
            logger.info("👋 User ended the conversation.")
            
            # Extract user name for personalized goodbye
            user_name = self._extract_user_name(conversation_history or [])
            if not user_name:
                user_name = self._extract_name_from_query(query)

            # Language overrides for more natural goodbye
            if "wala na" in lowered or "wa eun" in lowered or "waay na" in lowered:
                lang = "akl"
            elif "tapos na" in lowered:
                lang = "tl"
            elif any(k in lowered for k in ["done", "finished", "none", "no more", "that's all", "nope"]):
                lang = "en"

            # Return personalized goodbye if name is available
            if user_name:
                if lang == "tl" or lang == "akl":
                    return f"Salamat sa pakikipag-usap, {user_name}! Paalam! 👋"
                else:
                    return f"Thank you for chatting, {user_name}! Goodbye! 👋"
            else:
                return self.get_goodbye(lang)

        # --- Removed early keyword matching - only use when tokens are at limit ---

        # --- Detect if input is just a greeting (not greeting + question) ---
        greetings = ["hi", "hello", "hey", "kamusta", "kumusta",
                     "yo", "good morning", "good afternoon", "good evening"]
        
        # Check for greeting + introduction pattern first (e.g., "hi i am john")
        introduction_patterns = [
            r"^(hi|hello|hey)\s+i\s+am\s+\w+",
            r"^(hi|hello|hey)\s+i'm\s+\w+",
            r"^(hi|hello|hey)\s+my\s+name\s+is\s+\w+"
        ]
        
        is_introduction = False
        for pattern in introduction_patterns:
            if re.match(pattern, lowered):
                logger.info(f"👋 Greeting with name introduction detected: {lowered}")
                is_introduction = True
                break
        
        # For name introductions, process the name and give a personalized greeting
        if is_introduction:
            # Extract name from conversation history or query
            user_name = self._extract_user_name(conversation_history or [])
            child_name = self._extract_child_name(conversation_history or [])
            if not user_name:
                # Try to extract from current query
                name_match = re.search(r"my\s+name\s+is\s+(\w+)", lowered)
                if name_match:
                    user_name = name_match.group(1).title()
            
            # Give personalized greeting with time awareness
            time_period = self.get_time_period(user_timezone)
            if lang == "tl" or lang == "akl":
                if time_period == "morning":
                    base_greeting = f"Good morning, {user_name}!" if user_name else "Good morning!"
                elif time_period == "afternoon": 
                    base_greeting = f"Good afternoon, {user_name}!" if user_name else "Good afternoon!"
                elif time_period == "evening":
                    base_greeting = f"Good evening, {user_name}!" if user_name else "Good evening!"
                else:
                    base_greeting = f"Hello, {user_name}!" if user_name else "Hello!"
                
                return f"{base_greeting} 😊 Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School! Ano ang maitutulong ko sa inyo ngayon?"
            else:
                if time_period == "morning":
                    base_greeting = f"Good morning, {user_name}!" if user_name else "Good morning!"
                elif time_period == "afternoon":
                    base_greeting = f"Good afternoon, {user_name}!" if user_name else "Good afternoon!" 
                elif time_period == "evening":
                    base_greeting = f"Good evening, {user_name}!" if user_name else "Good evening!"
                else:
                    base_greeting = f"Hello, {user_name}!" if user_name else "Hello!"
                
                return f"{base_greeting} ☀️ I'm Tomas, your friendly school assistant! What can I help you with today?"
        
        # Only treat as greeting if it's ONLY a greeting (no additional content)
        is_greeting_only = False
        for greeting in greetings:
            if lowered.startswith(greeting):
                # Check if there's meaningful content after the greeting
                remaining = lowered[len(greeting):].strip()
                
                # If nothing after greeting, or just punctuation, it's a greeting only
                if not remaining or remaining in ["!", "?", ".", ","]:
                    is_greeting_only = True
                    break
                # If there's substantial content after greeting, it's a question with greeting
                elif len(remaining.split()) >= 2:  # At least 2 words after greeting
                    logger.info(f"🔍 Greeting detected but has question: '{remaining}' - processing full query")
                    break
        
        if is_greeting_only:
            logger.info("👋 User sent a greeting only.")
            return self.get_greeting(lang, user_timezone)

        # --- Early check for family/enrollment context to avoid irrelevant DB searches ---
        family_enrollment_patterns = [
            "my son", "my daughter", "my child", "his name", "her name", 
            "child's name", "son's name", "daughter's name", "child is",
            "son is", "daughter is", "years old", "grade"
            # Removed "enroll" from here - let it be handled by enrollment check below
        ]
        
        # --- Early check for enrollment queries (MOVED BEFORE FAMILY CHECK) ---
        enrollment_patterns = [
            "enroll", "enrollment", "admission", "register", "want to enroll", 
            "i want to enroll", "enroll my", "register my", "admission for",
            "apply", "application", "join the school", "join your school",
            "would like to register", "can you help with admission",
            "help with enrollment", "help with admission", "enrollment information",
            "admission information", "can you help me with enrollment",
            "help me with enrollment", "assist with enrollment"
        ]
        
        if any(pattern in lowered for pattern in enrollment_patterns):
            logger.info("🏫 Enrollment query detected - using keyword response")
            keyword_response = await self._keyword_matching_response(query, lang, conversation_history)
            if keyword_response:  # Use any enrollment response
                return self._validate_response_against_facts(keyword_response, query, lang)
        
        if any(pattern in lowered for pattern in family_enrollment_patterns):
            logger.info("👨‍👩‍👧‍👦 Family/enrollment context detected - avoiding generic database search")
            # For family context, use AI processing with minimal context to avoid irrelevant matches
            # Get minimal context to avoid token issues
            summarized_text = await self.fetch_summarized_file()
            
            # Only get specific enrollment-related context, not general DB search
            minimal_context = ""
            if summarized_text:
                snippet = await self.extract_snippet(summarized_text, "enrollment procedure")
                if snippet:
                    minimal_context += f"Enrollment Info: {snippet[:300]}...\n"
            
            # Force AI processing with conversation history but minimal context
            logger.info("🤖 Processing family context with AI and conversation history")
            return await self.ask_groq(query, minimal_context, lang, conversation_history, user_timezone)

        # --- Early check for teacher/staff queries to prevent AI hallucination ---
        teacher_patterns = [
            "mga guro", "mga teacher", "teachers", "who are the teachers", 
            "sino ang mga guro", "tell me about the teachers", "staff members",
            "mga staff", "faculty", "tell me about the staff", "about the staff",
            "list the faculty", "faculty members", "can you list the faculty",
            "sino ang mga faculty", "mga taong nagtuturo", "nagtuturo dito",
            "list ng mga guro", "nakikita ko ang mga teacher", "teachers of this school",
            "guro dito sa school", "the teachers", "our teachers", "teacher", "guro",
            "mga maestra", "maestra sa school", "maestra", "maestro", "mga maestro",
            "plural maestra", "maestra in school"
        ]
        
        # Check original query
        if any(pattern in lowered for pattern in teacher_patterns):
            logger.info("👩‍🏫 Teacher query detected - searching database for staff information")
            # Try database search for staff information first
            staff_result = await self.fetch_prompts_from_supabase("head teacher")
            if not staff_result:
                staff_result = await self.fetch_prompts_from_supabase("teacher")
            if not staff_result:
                staff_result = await self.fetch_prompts_from_supabase("staff")
            
            if staff_result:
                logger.info("✅ Found staff information in database")
                return self._validate_response_against_facts(staff_result, query, lang)
            else:
                # Fallback to hardcoded list if database has no results
                logger.info("⚠️ No staff info in database - using fallback staff list")
                response = self._get_known_staff_list(lang)
                return self._validate_response_against_facts(response, query, lang)
        
        # For Aklanon queries, also check the translated version
        if lang == "akl":
            translated_query = self.translate_aklanon_query_keywords(query)
            if any(pattern in translated_query.lower() for pattern in teacher_patterns):
                logger.info("👩‍🏫 Aklanon teacher query detected via translation - searching database")
                # Try database search for Aklanon staff queries too
                staff_result = await self.fetch_prompts_from_supabase("head teacher")
                if not staff_result:
                    staff_result = await self.fetch_prompts_from_supabase("teacher")
                if not staff_result:
                    staff_result = await self.fetch_prompts_from_supabase("staff")
                
                if staff_result:
                    logger.info("✅ Found staff information in database for Aklanon query")
                    return self._validate_response_against_facts(staff_result, query, lang)
                else:
                    # Fallback to hardcoded list if database has no results
                    logger.info("⚠️ No staff info in database for Aklanon - using fallback staff list")
                    response = self._get_known_staff_list(lang)
                    return self._validate_response_against_facts(response, query, lang)

        # --- Check for personalized queries BEFORE memory detection ---
        personalized_patterns = [
            "whats my name", "what is my name", "my name again", "remind me my name", 
            "tell me my name", "do you remember my name", "whats my sons name", 
            "what is my sons name", "my sons name", "remind me my sons name",
            "whats my daughters name", "what is my daughters name", "my daughters name"
        ]
        if any(pattern in lowered for pattern in personalized_patterns):
            logger.info("👤 Personalized name query detected - using keyword matching")
            keyword_response = await self._keyword_matching_response(query, lang, conversation_history)
            if keyword_response:
                return self._validate_response_against_facts(keyword_response, query, lang)

        # --- Early check for memory/conversation context queries ---
        memory_patterns = [
            "do you remember", "remember my", "what is my", "what was my", 
            "my daughter", "my child", "what did i tell you",  # Removed "my name" since it's handled above
            "naaalala mo ba", "naaalala mo", "ano ang pangalan ko", "nabanggit ko"
        ]
        if any(pattern in lowered for pattern in memory_patterns):
            logger.info("🧠 Memory/context query detected - forcing AI processing with conversation history")
            # Skip keyword matching completely for memory queries and force AI processing
            # This ensures conversation history is properly analyzed
            
            # Get minimal context to avoid token issues
            summarized_text = await self.fetch_summarized_file()
            supabase_prompts = await self.enhanced_search_supabase(query)
            
            # Build minimal context
            minimal_context = ""
            if supabase_prompts:
                minimal_context += f"DB: {supabase_prompts[:200]}...\n"
            if summarized_text:
                snippet = await self.extract_snippet(summarized_text, query)
                if snippet:
                    minimal_context += f"Summary: {snippet[:200]}...\n"
            
            # Force AI processing with conversation history
            logger.info("🤖 Processing memory query with AI and conversation history")
            return await self.ask_groq(query, minimal_context, lang, conversation_history, user_timezone)

        # --- Early check for language capability questions ---
        language_question_patterns = [
            "can you speak", "do you speak", "can you understand", "do you understand",
            "nakakaintindi ka", "marunong ka", "alam mo ba", "nakakaalam ka",
            "speak aklanon", "speak tagalog", "speak english", "understand aklanon",
            "can you speak aklanon", "can you understand aklanon"  # More specific patterns
        ]
        # Only match if it's clearly about language capability, not other "can you" questions
        is_language_question = False
        for pattern in language_question_patterns:
            if pattern in lowered:
                # Extra check: make sure it's not about school services
                if not any(service in lowered for service in ["admission", "enrollment", "help with"]):
                    is_language_question = True
                    break
        
        if is_language_question:
            logger.info("🗣️ Language capability question detected - using keyword response")
            keyword_response = await self._keyword_matching_response(query, lang, conversation_history)
            if keyword_response and "office" not in keyword_response:  # Avoid generic responses
                # 🛡️ Apply validation even to keyword responses
                return self._validate_response_against_facts(keyword_response, query, lang)

        # --- Special handling for Aklanon queries ---
        if lang == "akl":
            logger.info("🇵🇭 Aklanon query detected, responding in Tagalog with apology")
            
            # Translate Aklanon keywords to English for better search
            translated_query = self.translate_aklanon_query_keywords(query)
            logger.info(f"🔄 Original query: {query}")
            logger.info(f"🔄 Translated query: {translated_query}")
            
            # 🛡️ SAFETY CHECK: Ensure translation worked
            if not translated_query or translated_query is None:
                logger.warning("⚠️ Translation failed, using original query")
                translated_query = query
            
            # Enhanced search strategy for Aklanon queries using the new method
            supabase_prompts = await self.enhanced_search_supabase(translated_query)

            # Get other context sources
            summarized_text = await self.fetch_summarized_file()

            full_context = ""
            if context:
                full_context += f"External Context:\n{context}\n\n"
            if supabase_prompts:
                logger.info("✅ Found context in Supabase using enhanced Aklanon search")
                full_context += f"Database Context:\n{supabase_prompts}\n\n"
            if summarized_text:
                snippet = await self.extract_snippet(summarized_text, translated_query)
                if snippet:
                    logger.info("✅ Added snippet from summarized_text.md using translated query")
                    full_context += f"Summary Context:\n{snippet}"

            # If we found context, process with API
            if full_context.strip():
                # Get response in target language (Tagalog for Aklanon users)
                target_lang = "tl" if lang == "akl" else lang
                response = await self.ask_groq(translated_query, full_context, target_lang, conversation_history, user_timezone)
                
                logger.info(f"✅ Generated response in {target_lang} for Aklanon user")
                return response
            else:
                # No context found - return helpful message in fluent Tagalog
                response = "Hindi ko nahanap ang impormasyon tungkol sa inyong katanungan. Maaari po kayong magpunta sa opisina ng paaralan para sa dagdag na detalye. May iba pa po ba kayong katanungan sa Tagalog?"
                # 🛡️ Apply validation even to Aklanon fallback responses  
                return self._validate_response_against_facts(response, query, lang)

        # --- Removed aggressive token saving early keyword matching ---
        # Keyword matching will only be used when tokens are at their limit

        # Normal flow: Fetch context from summarized_text and Supabase, then send to Groq
        logger.info("📚 Starting normal flow: fetching context from summarized_text and Supabase")
        summarized_text = await self.fetch_summarized_file()
        supabase_prompts = await self.enhanced_search_supabase(query)

        full_context = ""
        context_sources = 0
        
        if context:
            logger.info("ℹ️ External context provided")
            full_context += f"External: {context}\n"
            context_sources += 1
            
        if supabase_prompts:
            logger.info("✅ Found context in Supabase")
            full_context += f"DB: {supabase_prompts}\n"
            context_sources += 1
            
        if summarized_text:
            snippet = await self.extract_snippet(summarized_text, query)
            if snippet:
                logger.info("✅ Found snippet in summary")
                full_context += f"Summary: {snippet}\n"
                context_sources += 1

        # Emergency context prioritization when too much context
        if len(full_context) > 1500 and context_sources > 1:
            logger.warning("🚨 Too much context, prioritizing sources")
            
            # Priority: DB > External > Summary
            priority_context = ""
            if supabase_prompts:
                priority_context = f"DB: {supabase_prompts}\n"
            elif context:
                priority_context = f"External: {context}\n"
            elif snippet:
                priority_context = f"Summary: {snippet[:500]}\n"
            
            full_context = priority_context

        # --- Only use keyword matching as last resort when tokens are at limit ---
        if full_context:
            budget = self._check_token_budget(query, full_context, lang, user_timezone)
            
            # Only use keyword matching if tokens are truly at their limit
            if budget['emergency_mode_needed'] or not budget['within_budget']:
                logger.warning("🚨 Token budget at limit - using keyword matching as emergency fallback")
                keyword_response = await self._keyword_matching_response(query, lang)
                
                # If keyword matching found a good match, use it (saves tokens)
                if keyword_response and "visit the school office" not in keyword_response.lower():
                    logger.info("✅ Using keyword matching emergency fallback due to token limit")
                    validated_response = self._validate_response_against_facts(keyword_response, query, lang)
                    return f"{validated_response.strip()}\n\n{self.get_followup(lang)}"
                else:
                    logger.warning("⚠️ Keyword matching didn't find good answer, proceeding with truncated context")
        
        # Normal processing: Use summarized_text and Supabase data -> send to Groq
        if not full_context.strip():
            # Check if this is a person/staff inquiry
            if self._is_person_query(query):
                logger.info("👤 No context found for person query - providing helpful guidance")
                response = self._get_unknown_person_response(lang)
                # 🛡️ Apply validation even to direct responses
                return self._validate_response_against_facts(response, query, lang)
            
            # Generic no context response for other queries
            english_response = (
                "I checked our records, but I wasn't able to find any information about "
                f"{query}. You may visit the school office for further details."
            )
            
            if lang == "tl":
                logger.info("🔄 Translating 'no context' message to Tagalog")
                try:
                    tagalog_response = await self.translate(english_response, source="en", target="tl")
                    final_response = f"Ayon sa aming records: {tagalog_response}"
                except Exception as e:
                    logger.warning(f"Translation failed: {e}, using fallback")
                    final_response = (
                        f"Tinignan ko ang aming mga record, pero hindi ko nahanap ang impormasyon tungkol sa "
                        f"{query}. Maaari kayong pumunta sa opisina ng paaralan para sa karagdagang detalye."
                    )
            else:
                final_response = english_response
                
            # 🛡️ Apply validation even to no-context responses
            validated_final_response = self._validate_response_against_facts(final_response, query, lang)
            return validated_final_response + f" {self.get_followup(lang)}"

        # Truncate before sending to Groq (token management)
        max_len = 1500  # Reduced from 4000 for token efficiency
        if len(full_context) > max_len:
            logger.warning("⚠️ Context too long, truncating for token efficiency")
            full_context = full_context[:max_len] + "\n...(truncated)..."

        logger.info("🤖 Normal flow: Sending query to Groq with context from summarized_text and Supabase")
        
        # Regular AI call - no special handling
        response = await self.ask_groq(query, full_context, lang, conversation_history, user_timezone)

        # --- CONVERSATION MEMORY: Store this interaction ---
        await self._store_conversation_turn(user_id, query, response, lang, conversation_history)

        # Return the response (no translation needed since it's already in the right language)
        return response
    
    def _generate_user_id(self, conversation_history: list = None) -> str:
        """Generate a user ID from conversation history or create a temporary one"""
        if not conversation_history:
            return f"temp_user_{int(time.time())}"
        
        # Try to extract a consistent identifier from conversation
        user_name = self._extract_user_name(conversation_history)
        if user_name:
            # Create hash from user name for consistent ID
            import hashlib
            return f"user_{hashlib.md5(user_name.lower().encode()).hexdigest()[:8]}"
        
        # Use hash of first message for consistency
        if conversation_history:
            first_msg = str(conversation_history[0])
            import hashlib
            return f"anon_{hashlib.md5(first_msg.encode()).hexdigest()[:8]}"
        
        return f"temp_user_{int(time.time())}"
    
    async def _store_conversation_turn(self, user_id: str, query: str, response: str, lang: str, conversation_history: list = None) -> None:
        """Store conversation turn in memory with entity extraction and intent analysis"""
        try:
            # Extract entities from the user query
            extracted_entities = await self._extract_entities_with_nlu(query)
            entity_list = extracted_entities.get('entities', [])
            
            # Convert to format expected by conversation memory
            entities_for_memory = []
            for entity in entity_list:
                entities_for_memory.append({
                    'entity_type': entity.entity_type,
                    'value': entity.value,
                    'confidence': entity.confidence
                })
            
            # Get intent from NLU analysis
            try:
                nlu_result = await self.nlu_engine.analyze_intent(query, conversation_history)
                detected_intent = nlu_result.intent.value
                confidence_score = nlu_result.confidence
            except:
                detected_intent = "general"
                confidence_score = 0.5
            
            # Store in conversation memory
            self.conversation_memory.add_conversation_turn(
                user_id=user_id,
                user_message=query,
                bot_response=response,
                detected_intent=detected_intent,
                extracted_entities=entities_for_memory,
                confidence_score=confidence_score
            )
            
            logger.info(f"💭 Stored conversation turn for user {user_id[:8]} with {len(entities_for_memory)} entities")
            
        except Exception as e:
            logger.warning(f"Failed to store conversation turn: {e}")
    
    def _generate_intelligent_response(self, 
                                     intent: str, 
                                     user_id: str, 
                                     query: str,
                                     extracted_entities: List[Dict] = None,
                                     conversation_history: List[Dict] = None,
                                     sentiment_result: SentimentResult = None) -> Optional[str]:
        """Generate intelligent response using Response Generation Engine with sentiment awareness"""
        try:
            # Special handling for intents that require database lookup
            if intent == "staff_inquiry":
                logger.info("🗄️ Staff inquiry detected - using database lookup instead of template")
                return None  # Let it fall through to database search
            
            # Get user profile and conversation context
            user_profile = self.conversation_memory.get_user_profile(user_id)
            conversation_context = self.conversation_memory.get_conversation_context(user_id)
            
            # Apply sentiment-based tone adjustment if available
            adjusted_tone = ResponseTone.FRIENDLY  # default
            if sentiment_result:
                if sentiment_result.emotion:
                    # Map emotions to response tones
                    emotion_to_tone = {
                        "frustrated": ResponseTone.APOLOGETIC,
                        "anxious": ResponseTone.REASSURING,
                        "confused": ResponseTone.PATIENT,
                        "disappointed": ResponseTone.EMPATHETIC,
                        "excited": ResponseTone.ENTHUSIASTIC,
                        "satisfied": ResponseTone.WARM,
                        "curious": ResponseTone.INFORMATIVE,
                        "happy": ResponseTone.FRIENDLY
                    }
                    adjusted_tone = emotion_to_tone.get(sentiment_result.emotion.value, ResponseTone.FRIENDLY)
                
                # Update user mood in conversation context based on sentiment
                conversation_context.user_mood = sentiment_result.emotion.value if sentiment_result.emotion else "neutral"
            
            # Build response context with sentiment awareness
            response_context = ResponseContext(
                user_name=user_profile.name,
                child_name=user_profile.child_name,
                child_age=user_profile.child_age,
                child_grade=user_profile.child_grade,
                user_language=user_profile.preferred_language,
                conversation_stage=conversation_context.conversation_stage,
                previous_topics=user_profile.previous_topics,
                user_mood=conversation_context.user_mood,
                communication_style=user_profile.communication_style,
                follow_up_needed=conversation_context.follow_up_needed,
                is_returning_user=len(self.conversation_memory.get_conversation_history(user_id)) > 0,
                preferred_tone=adjusted_tone  # Apply sentiment-based tone
            )
            
            # Generate intelligent response with sentiment-aware tone
            response_data = self.response_generator.generate_response(
                intent=intent,
                context=response_context,
                extracted_entities=extracted_entities or [],
                conversation_history=conversation_history or []
            )
            
            # Build complete response with follow-up if appropriate
            response_text = response_data["response"]
            
            # Apply urgency-based adjustments if high urgency detected
            if sentiment_result and sentiment_result.urgency_level >= 4:
                # Add priority handling for urgent requests
                response_text = f"I understand this is urgent. {response_text}"
                logger.info(f"🚨 High urgency detected ({sentiment_result.urgency_level}/5) - priority response")
            
            if response_data.get("follow_up") and response_context.follow_up_needed:
                response_text += f"\n\n{response_data['follow_up']}"
            
            # Log sentiment-aware response generation
            sentiment_info = f" (sentiment: {sentiment_result.sentiment.value})" if sentiment_result else ""
            logger.info(f"🎯 Generated intelligent response using template '{response_data.get('template_id')}' with tone '{response_data.get('tone')}'{sentiment_info}")
            
            return response_text
            
        except Exception as e:
            logger.warning(f"Intelligent response generation failed: {e}")
            return None

if __name__ == "__main__":
    import asyncio
    
    async def test_chatbot():
        chatbot = ChatBot()
        
        print("🤖 Tomas Leo AI Chatbot Test")
        print("=" * 50)
        
        # Test queries
        test_queries = [
            "Who is Meliza Delgado?",
            "sino si meliza delgado?",
            "Who is the head teacher?",
            "What is the school's mission?",
            "hello"
        ]
        
        for query in test_queries:
            print(f"\n📝 Query: {query}")
            print("-" * 30)
            
            try:
                response = await chatbot.process_query(query)
                print(f"🤖 Response: {response}")
            except Exception as e:
                print(f"❌ Error: {e}")
                
            print("=" * 50)
    
    # Run the test
    asyncio.run(test_chatbot())
