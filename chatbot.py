import os
import re
import logging
import httpx
import langid
import random
from supabase import create_client, Client
# Remove unused import: from utils import fetch_summarized_text  
from fallback import FallbackHandler
import time
from datetime import datetime
from rapidfuzz import fuzz, process
import json
from deep_translator import GoogleTranslator
import openai
import asyncio
import urllib.parse
from dotenv import load_dotenv

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
                        "Good morning! ☀️ I'm Tomas, your friendly school assistant! What can I help you with today?",
                        "Good morning! 😊 Welcome to Tomas SM. Bautista Elementary School! How can I assist you?",
                        "Morning! Great to see you here bright and early! What would you like to know about our school?",
                        "Good morning! 🏫 I'm here to help with any questions about our lovely school. What's on your mind?"
                    ],
                    "afternoon": [
                        "Good afternoon! ☀️ I'm Tomas, your friendly school assistant! What can I help you with today?",
                        "Good afternoon! � Welcome to Tomas SM. Bautista Elementary School! How can I assist you?",
                        "Afternoon! Great to see you here! What would you like to know about our school?",
                        "Good afternoon! 🏫 I'm here to help with any questions about our lovely school. What's on your mind?"
                    ],
                    "evening": [
                        "Good evening! 🌙 I'm Tomas, your friendly school assistant! What can I help you with today?",
                        "Good evening! 😊 Welcome to Tomas SM. Bautista Elementary School! How can I assist you?",
                        "Evening! Nice to see you here! What would you like to know about our school?",
                        "Good evening! 🏫 I'm here to help with any questions about our lovely school. What's on your mind?"
                    ],
                    "default": [
                        "Hello there! �👋 I'm Tomas, your friendly school assistant! What can I help you with today?",
                        "Hi! 😊 Welcome to Tomas SM. Bautista Elementary School! How can I assist you?",
                        "Hey! Great to see you here! What would you like to know about our school?",
                        "Hello! 🏫 I'm here to help with any questions about our lovely school. What's on your mind?"
                    ]
                },
                "tl": {
                    "morning": [
                        "Magandang umaga! ☀️ Ako si Tomas, ang inyong kaibigan dito sa paaralan! Paano ko kayo matutulungan ngayon?",
                        "Magandang umaga! 😊 Maligayang pagdating sa Tomas SM. Bautista Elementary School! Ano ang maitutulong ko?",
                        "Umaga! Masaya akong makita kayo dito nang maaga! Ano ang gusto ninyong malaman tungkol sa aming paaralan?",
                        "Magandang umaga po! 🏫 Nandito ako para tumulong sa inyong mga tanong. Ano ang nasa isip ninyo?"
                    ],
                    "afternoon": [
                        "Magandang hapon! ☀️ Ako si Tomas, ang inyong kaibigan dito sa paaralan! Paano ko kayo matutulungan ngayon?",
                        "Magandang hapon! 😊 Maligayang pagdating sa Tomas SM. Bautista Elementary School! Ano ang maitutulong ko?",
                        "Hapon! Masaya akong makausap kayo! Ano ang gusto ninyong malaman tungkol sa aming paaralan?",
                        "Magandang hapon po! 🏫 Nandito ako para tumulong sa inyong mga tanong. Ano ang nasa isip ninyo?"
                    ],
                    "evening": [
                        "Magandang gabi! 🌙 Ako si Tomas, ang inyong kaibigan dito sa paaralan! Paano ko kayo matutulungan ngayon?",
                        "Magandang gabi! 😊 Maligayang pagdating sa Tomas SM. Bautista Elementary School! Ano ang maitutulong ko?",
                        "Gabi! Masaya akong makausap kayo ngayong gabi! Ano ang gusto ninyong malaman tungkol sa aming paaralan?",
                        "Magandang gabi po! 🏫 Nandito ako para tumulong sa inyong mga tanong. Ano ang nasa isip ninyo?"
                    ],
                    "default": [
                        "Magandang araw! 👋 Ako si Tomas, ang inyong kaibigan dito sa paaralan! Paano ko kayo matutulungan ngayon?",
                        "Kamusta! 😊 Maligayang pagdating sa Tomas SM. Bautista Elementary School! Ano ang maitutulong ko?",
                        "Uy, kumusta! Masaya akong makausap kayo! Ano ang gusto ninyong malaman tungkol sa aming paaralan?",
                        "Hello po! 🏫 Nandito ako para tumulong sa inyong mga tanong. Ano ang nasa isip ninyo?"
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
    def reset_conversation(self, lang="en"):
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
                "content": self.get_greeting(lang),  # 👈 use your greeting helper
            },
        ]

    def get_time_period(self) -> str:
        """Determine the time of day based on current hour"""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            return "morning"
        elif 12 <= current_hour < 18:
            return "afternoon"
        elif 18 <= current_hour < 22:
            return "evening"
        else:
            return "default"  # Late night/early morning hours

    def get_time_aware_system_prompt(self, lang: str = "en"):
        """Generate a time-aware system prompt for Groq API"""
        current_hour = datetime.now().hour
        
        # Determine time context for the AI
        if 5 <= current_hour < 12:
            time_context = "It's morning time (school starts at 8 AM)."
        elif 12 <= current_hour < 18:
            time_context = "It's afternoon time (school day in progress or just ended)."
        elif 18 <= current_hour < 22:
            time_context = "It's evening time (school day has ended)."
        else:
            time_context = "It's late evening/night time (school is closed)."
        
        # Handle Aklanon by treating it as Tagalog
        if lang == "akl":
            lang = "tl"
        
        # Create language-specific system prompts
        if lang == "tl":
            return f"Ikaw si TOMAS! 😊 Isang masigasig at palakaibigan na assistant para sa Tomas SM. Bautista Elementary School. Parang nakakausap mo ang isang mainit na staff member ng paaralan na gustong tumulong! {time_context} Gamitin ang context na ibinigay para magbigay ng kapaki-pakinabang at makakausap na mga sagot sa TAGALOG. Magdagdag ng mga emoji at personalidad - gawin itong natural! 🏫✨"
        else:  # Default to English
            return f"You are TOMAS! 😊 A friendly, enthusiastic assistant for Tomas SM. Bautista Elementary School. You're like talking to a warm school staff member who loves helping! {time_context} Use the context provided to give helpful, conversational answers in ENGLISH. Add emojis and personality - make it feel natural! 🏫✨"

    def get_greeting(self, lang: str = "en") -> str:
        time_period = self.get_time_period()
        
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
    
    def _check_token_budget(self, query: str, context: str, lang: str = "en") -> dict:
        """Check if we're within token budget and suggest optimizations."""
        system_prompt = self.get_time_aware_system_prompt(lang)
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
        """Quick check if text seems to be in English based on common English words"""
        english_indicators = [
            "the", "and", "is", "are", "was", "were", "have", "has", "had", 
            "will", "would", "can", "could", "should", "must", "may", "might",
            "this", "that", "these", "those", "with", "for", "from", "about"
        ]
        text_lower = text.lower()
        english_word_count = sum(1 for word in english_indicators if f" {word} " in f" {text_lower} ")
        return english_word_count >= 2

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
                "bisan", "hasta", "para", "kon", "kung", "pero", "kundi"
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
                    known_names = ["garcia", "meliza", "delgado", "smith", "johnson"] 
                    if any(name in remaining for name in known_names):
                        return True
        
        # Very restrictive check for names - only if query is very short and contains potential names
        words = query_lower.split()
        if len(words) == 2 or len(words) == 3:  # Only short queries
            # Check if it contains common name indicators from our known staff
            known_names = ["garcia", "meliza", "delgado", "nelda", "annalyn", "lezil", "michelle", "thedy", "jessica", "leny"]
            for name in known_names:
                if name in query_lower:
                    return True
        
        return False
    
    def _get_unknown_person_response(self, lang: str = "en") -> str:
        """Generate a helpful response for unknown person queries without listing all staff."""
        
        if lang == "tl":
            return ("Hindi ko nakilala ang taong iyon sa aming paaralan. Para sa mga katanungan "
                   "tungkol sa mga guro at staff, maaari kayong makipag-ugnayan kay Meliza A. Delgado, "
                   "ang aming Head Teacher, o tumawag sa school office sa (036) 269-6345.")
        elif lang == "akl":
            return ("Wala ko kakilala nga tawo na ina sa amon eskwelahan. Para sa mga pamangkot "
                   "parte sa mga maestro kag staff, pwede kamo mag-contact kay Meliza A. Delgado, "
                   "ang amon Head Teacher, o mag-tawag sa school office sa (036) 269-6345.")
        else:  # English
            return ("I don't have information about that person in our school records. "
                   "For inquiries about our teachers and staff, you may contact our Head Teacher, "
                   "Meliza A. Delgado, or call the school office at (036) 269-6345.")

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
            footer = "\n\nPara sa iba pang impormasyon, maaari kayong tumawag sa school office sa (036) 269-6345."
        elif lang == "akl":
            header = "Ara ini it mga kilaea nga staff sa TOMAS Elementary School:\n\n"  
            footer = "\n\nPara sa iban nga impormasyon, pwede kamo mag-tawag sa school office sa (036) 269-6345."
        else:  # English
            header = "Here are the known staff members at TOMAS Elementary School:\n\n"
            footer = "\n\nFor other inquiries, you may contact the school office at (036) 269-6345."
        
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

    async def ask_groq(self, query: str, context: str, lang: str, conversation_history: list = None) -> str:
        """Token-optimized Groq API call with emergency fallbacks."""
        # Start with friendly, conversational prompt
        system_prompt = self.get_time_aware_system_prompt(lang)
        
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
                    
                    if mode != "normal":
                        logger.warning(f"⚠️ Used {mode} token mode for response")
                    
                    return ai_response
                    
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
            return "Meliza Delgado is the Head Teacher. Visit school office for details."  
        elif any(word in query_lower for word in ["teacher", "staff", "faculty"]):
            return "For staff information, please visit the school office."
        elif any(word in query_lower for word in ["contact", "phone", "email", "address"]):
            return "For contact information, please visit the school office."
        elif any(word in query_lower for word in ["enrollment", "admission", "register"]):
            return "For enrollment information, please visit the school office."
        else:
            return "Please visit the school office for assistance with your inquiry."

    async def _keyword_matching_response(self, query: str, lang: str) -> str:
        """Enhanced keyword matching - zero token usage alternative."""
        query_lower = query.lower()
        
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
            
            # Academic Information
            ("enrollment", "admission", "register"): {
                "en": "Ready to join our school family? 🎒 Head to the office for all the enrollment info - they'll guide you through everything!",
                "tl": "Ready na ba kayong sumali sa pamilya namin? 🎒 Punta sa office para sa enrollment info - gabayan nila kayo sa lahat!",
                "default": "For enrollment information, please visit the school office."
            },
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
        
        # Find matching keywords
        best_match = None
        max_matches = 0
        best_response = None
        
        for keywords, response in keyword_responses.items():
            matches = sum(1 for keyword in keywords if keyword in query_lower)
            if matches > max_matches:
                max_matches = matches
                best_match = keywords
                best_response = response
        
        if best_match and max_matches > 0:
            logger.info(f"🎯 Keyword match found ({max_matches} matches)")
            
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
            
            # Try searching individual meaningful words first (simpler approach)
            for word in search_words:
                logger.info(f"🔍 Full-text search for: '{word}'")
                
                try:
                    # Use proper Supabase client methods with correct wildcard syntax
                    result = self.supabase.table("chatbot_prompts") \
                        .select("keywords, response") \
                        .ilike("keywords", f"%{word}%") \
                        .execute()
                    
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

    async def answer(self, query: str, context: str = None, conversation_history: list = None) -> str:
        lang = await self.detect_language(query)
        lowered = query.lower().strip()  # For backward compatibility

        # --- Enhanced Intent Analysis ---
        intent_analysis = self._analyze_query_intent(query)
        human_analysis = self._analyze_human_request_intent(query)
        
        logger.info(f"🧠 Intent: {intent_analysis['intent']} (confidence: {intent_analysis['confidence']:.2f})")
        logger.info(f"👤 Human request: {human_analysis['wants_human']} (confidence: {human_analysis['confidence']:.2f})")

        # --- Detect if user explicitly wants human support (with high confidence) ---
        if human_analysis['wants_human'] and human_analysis['confidence'] > 0.7:
            logger.info("👤 High confidence human request → triggering fallback handler.")
            return self.fallback_handler.generate_fallback_message(lang)

        # --- Detect goodbye / end of conversation ---
        if intent_analysis['intent'] == 'goodbye' and intent_analysis['confidence'] > 0.8:
            logger.info("👋 User ended the conversation.")
            return self.get_goodbye(lang)

        # --- Detect pure greetings ---
        if intent_analysis['intent'] == 'greeting' and intent_analysis['confidence'] > 0.8:
            logger.info("👋 Pure greeting detected.")
            return self.get_greeting(lang)
        # --- Enhanced goodbye detection ---
        goodbye_keywords = [
            "goodbye", "bye", "see you", "farewell", "adios", "salamat", 
            "thanks", "thank you", "ok thanks", "got it", "wala na", 
            "wa eun", "waay na", "tapos na", "that's all", "finished", "done", "nope"
        ]
        if any(k in lowered for k in goodbye_keywords):
            logger.info("👋 User ended the conversation.")

            # Language overrides for more natural goodbye
            if "wala na" in lowered or "wa eun" in lowered or "waay na" in lowered:
                lang = "akl"
            elif "tapos na" in lowered:
                lang = "tl"
            elif any(k in lowered for k in ["done", "finished", "none", "no more", "that's all", "nope"]):
                lang = "en"

            return self.get_goodbye(lang)

        # --- Removed early keyword matching - only use when tokens are at limit ---

        # --- Detect if input is just a greeting (not greeting + question) ---
        greetings = ["hi", "hello", "hey", "kamusta", "kumusta",
                     "yo", "good morning", "good afternoon", "good evening"]
        
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
            return self.get_greeting(lang)

        # --- Early check for language capability questions ---
        language_question_patterns = [
            "can you speak", "do you speak", "can you understand", "do you understand",
            "nakakaintindi ka", "marunong ka", "alam mo ba", "nakakaalam ka",
            "speak aklanon", "speak tagalog", "speak english", "understand aklanon"
        ]
        if any(pattern in lowered for pattern in language_question_patterns):
            logger.info("🗣️ Language capability question detected - using keyword response")
            keyword_response = await self._keyword_matching_response(query, lang)
            if keyword_response and "office" not in keyword_response:  # Avoid generic responses
                return keyword_response

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
                response = await self.ask_groq(translated_query, full_context, target_lang, conversation_history)
                
                logger.info(f"✅ Generated response in {target_lang} for Aklanon user")
                return response
            else:
                # No context found - return helpful message in fluent Tagalog
                return "Hindi ko nahanap ang impormasyon tungkol sa inyong katanungan. Maaari po kayong magpunta sa opisina ng paaralan para sa dagdag na detalye. May iba pa po ba kayong katanungan sa Tagalog?"

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
            budget = self._check_token_budget(query, full_context, lang)
            
            # Only use keyword matching if tokens are truly at their limit
            if budget['emergency_mode_needed'] or not budget['within_budget']:
                logger.warning("🚨 Token budget at limit - using keyword matching as emergency fallback")
                keyword_response = await self._keyword_matching_response(query, lang)
                
                # If keyword matching found a good match, use it (saves tokens)
                if keyword_response and "visit the school office" not in keyword_response.lower():
                    logger.info("✅ Using keyword matching emergency fallback due to token limit")
                    return f"{keyword_response.strip()}\n\n{self.get_followup(lang)}"
                else:
                    logger.warning("⚠️ Keyword matching didn't find good answer, proceeding with truncated context")
        
        # Normal processing: Use summarized_text and Supabase data -> send to Groq
        if not full_context.strip():
            # Check if this is a person/staff inquiry
            if self._is_person_query(query):
                logger.info("👤 No context found for person query - providing helpful guidance")
                return self._get_unknown_person_response(lang)
            
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
                
            return final_response + f" {self.get_followup(lang)}"

        # Truncate before sending to Groq (token management)
        max_len = 1500  # Reduced from 4000 for token efficiency
        if len(full_context) > max_len:
            logger.warning("⚠️ Context too long, truncating for token efficiency")
            full_context = full_context[:max_len] + "\n...(truncated)..."

        logger.info("🤖 Normal flow: Sending query to Groq with context from summarized_text and Supabase")
        # Get response in the user's detected language
        response = await self.ask_groq(query, full_context, lang, conversation_history)

        # Return the response (no translation needed since it's already in the right language)
        return response


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
