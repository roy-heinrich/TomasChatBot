import os
import re
import logging
import httpx
import langid
import random
from supabase import create_client, Client
from utils import fetch_summarized_text
from fallback import FallbackHandler
import time
from rapidfuzz import fuzz, process
import json
from deep_translator import GoogleTranslator
import openai
import asyncio
import urllib.parse
from translator import AklanonTranslator

logger = logging.getLogger("chatbot")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

dict_path = os.path.join(os.path.dirname(__file__), "aklanon_dict.json")
aklanon_translator = AklanonTranslator(dict_path)

def capitalize_sentences(text):
    """Capitalize the first letter of each sentence in the text."""
    return re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text.capitalize())

class ChatBot:
    def __init__(self, groq_key: str):
        self.aklanon_translator = aklanon_translator
        self.fallback_handler = FallbackHandler()
        self.groq_key = groq_key  
        self._cached_summary = None
        self._last_fetched = 0
        self.cache_ttl = 300  # e.g., 5 minutes
        self.groq_api = "https://api.groq.com/openai/v1/chat/completions"
        self.bucket = "summarized-text"
        self.file = "summarized_text.md"

        # ✅ Centralized greetings + followups
        self.messages = {
            "greeting": {
                "en": [
                    "Hello! How can I help you today?",
                    "Hi there! What can I do for you?"
                ],
                "tl": [
                    "Magandang araw! Paano po ako makakatulong?",
                    "Kamusta! Ano po ang maitutulong ko sa inyo?"
                ],
                "akl": [
                    "Hi! Unhon ko ikaw matabangan?",
                    "Kumusta! Ano ro mahimu ko para kimo?"
                ]
            },
            "follow_up": {
                "en": "Do you have any other questions?",
                "tl": "May iba pa po ba kayong katanungan?",
                "akl": "May ara pa baga ikaw it iba nga pamangkot?"
            }
    }
    def reset_conversation(self, lang="en"):
        """Reset chat history with a proper system prompt + greeting."""
        self.messages = [
            {
                "role": "system",
                "content": (
                    "You are TOMAS, a polite and helpful assistant for "
                    "Tomas SM. Bautista Elementary School. Always answer "
                    "clearly in the user's language (English, Tagalog, or Aklanon)."
                ),
            },
            {
                "role": "assistant",
                "content": self.get_greeting(lang),  # 👈 use your greeting helper
            },
        ]

    def get_greeting(self, lang: str = "en") -> str:
        greetings = self.messages["greeting"].get(lang, self.messages["greeting"]["en"])
        return random.choice(greetings)

    def get_followup(self, lang: str = "en") -> str:
        return self.messages["follow_up"].get(lang, self.messages["follow_up"]["en"])

    def get_goodbye(self, lang: str) -> str:
        messages = {
            "en": "Thank you for chatting! Goodbye 👋",
            "tl": "Maraming salamat sa pakikipag-usap! Paalam 👋",
            "akl": "Salamat gid sa pagpakig-angut! Paalam 👋"
        }
        return messages.get(lang, messages["en"])
    
    async def translate(self, text: str, source: str = "auto", target: str = "en") -> str:
        """Try deep_translator, fallback to OpenAI if needed."""
        try:
            return GoogleTranslator(source=source, target=target).translate(text)
        except Exception as e:
            logger.warning(f"deep_translator failed {source}->{target}: {e}")
            try:
                response = await openai.ChatCompletion.acreate(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": f"Translate from {source} to {target}."},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.2
                )
                return response["choices"][0]["message"]["content"].strip()
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

    async def detect_language(self, text: str) -> str:
        """Detect language with langid, with Aklanon override heuristics."""
        try:
            lang, prob = langid.classify(text)
            # --- Force Aklanon if text contains Aklanon markers ---
            akl_markers = ["it", "du", "nga", "ro", "eon", "baga", "man", "dun", "hay", "eun", "ngaron", "haron,", "pagid"]
            if any(m in text.lower() for m in akl_markers):
                logger.info("🔎 Heuristic override → detected as akl")
                return "akl"
            if lang.startswith("tl"):
                return "tl"
            if lang == "es" or lang.startswith("akl"):
                return "akl"
            if lang.startswith("en"):
                return "en"
            return lang
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "en"  # safe fallback
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

    async def ask_groq(self, query: str, context: str, lang: str) -> str:
        """Send query + context to Groq API with safe system prompt."""
        system_prompts = {
            "en": (
                "You are TOMAS, the school assistant for Tomas SM. Bautista Elementary School. "
                "You answer only using the provided context. "
                "and suggest visiting the school office. "
                "Do NOT ask the user for more details or clarification."
            ),
            "tl": (
                "Ikaw si TOMAS, ang school assistant ng Tomas SM. Bautista Elementary School. "
                "Sumasagot ka lang base sa context na ibinigay. "
                "lumapit sa opisina ng paaralan. "
                "Huwag humingi ng dagdag na detalye sa user."
            ),
            "akl": (
                "Ikaw si TOMAS, bulig nga assistant sang Tomas SM. Bautista Elementary School. "
                "Mag sabat ka lang base sa ginhatag nga context sa Aklanon language. "
                "Gamiton ang mga Aklanon nga pulong gikan sa dictionary reference. "
                "Kung wara ka makita sa context, mag-suggest nga mag-adto sa opisina it eskwelahan. "
                "Indi magpangayo it dugang nga detalye sa user."
            )
        }
        if lang not in system_prompts:
            logger.warning(f"⚠️ Unsupported language {lang}, defaulting to English")
            lang = "en"
        system_prompt = system_prompts[lang]

        # Add Aklanon dictionary reference and example sentences for Aklanon responses
        if lang == "akl":
            aklanon_words = list(self.aklanon_translator.dictionary.keys())[:50]
            aklanon_reference = ", ".join(aklanon_words)
            example_sentences = [
                "Siin du lokasyon it eskwelahan? Amo ina sa Fatima, New Washington, Aklan.",
                "Ano ro oras it klase? Nagsugod ro klase 7:30 AM hasta 4:15 PM.",
                "Sino ro principal it eskwelahan? Si Ma'am Meliza A. Delgado ro principal.",
                "Pwede ako mag-enroll bisan late? Pwede, bisitaha ro opisina para sa detalye.",
                "Ano ro requirements para sa enrollment? Bisitaha ro opisina para sa iba pa na mga detalye",
                "May uniform guid ro mga estudyante? Oo, may uniform guid.",
                "San-o ro graduation? Sa Marso ro graduation.",
                "Diin pwede magkuha it school ID? Sa opisina it eskwelahan.",
                "Salamat gid sa bulig!", 
                "May ara pa baga ikaw it iba nga pamangkot?"
            ]
            example_block = "\n\nAklanon Example Sentences (mimic these for natural phrasing):\n" + "\n".join(example_sentences)
            system_prompt += f"\n\nAklanon word reference (use these words when possible): {aklanon_reference}" + example_block

        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nUser: {query}"}
            ],
            "temperature": 0.7
        }
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(self.groq_api, json=payload, headers=headers)
                response.raise_for_status()
                ai_response = response.json()["choices"][0]["message"]["content"].strip()

                # ✅ Return only the AI answer; let answer() append greeting + follow-up
                return ai_response

            except Exception as e:
                logger.error(f"Groq failed: {e}")
                return self.fallback_handler.generate_fallback_message(lang)

            
    async def fetch_prompts_from_supabase(self, query: str) -> str:
        """Search chatbot_prompts table in Supabase for matching context using different methods."""
        try:
            # Clean and prepare search query
            search_terms = self._extract_search_terms(query)
            
            # Method 1: Try text search using textsearch (if FTS is configured)
            result = await self._try_fts_search(search_terms)
            if result:
                return result
            
            # Method 2: Try ILIKE pattern matching
            result = await self._try_ilike_search(search_terms)
            if result:
                return result
            
            # Method 3: Try fuzzy matching with all records (fallback)
            result = await self._try_fuzzy_search(query)
            return result
            
        except Exception as e:
            logger.error(f"Error in fetch_prompts_from_supabase: {e}")
            return ""

    def _extract_search_terms(self, query: str) -> list:
        """Extract meaningful search terms from query."""
        # Remove common stop words and clean the query
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'can', 'you', 'me', 'who', 'what', 'where', 'when', 'why', 'how', 'tell'}
        words = re.findall(r'\w+', query.lower())
        return [word for word in words if word not in stop_words and len(word) > 2]

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
        """Try Full Text Search - requires FTS to be properly configured in Supabase."""
        if not search_terms:
            return ""
        
        try:
            search_query = " & ".join(search_terms)  # AND search
            
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
                "limit": 2  # FIX 2: limit results
            }

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        logger.info(f"✅ FTS search successful, found {len(data)} results")
                        return "\n".join(
                            f"Q: {row.get('keywords', '')}\nA: {row.get('response', '')}"
                            for row in data[:2]  # FIX 2
                        )
        except Exception as e:
            logger.warning(f"FTS search failed: {e}")
        
        return ""

    async def _try_ilike_search(self, search_terms: list) -> str:
        """Try ILIKE pattern matching search."""
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

            for term in search_terms[:3]:
                params = {
                    "select": "keywords,response",
                    "or": f"keywords.ilike.%{term}%,response.ilike.%{term}%",
                    "limit": 2  # FIX 2: limit results
                }

                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, headers=headers, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data:
                            logger.info(f"✅ ILIKE search successful for term '{term}', found {len(data)} results")
                            return "\n".join(
                                f"Q: {row.get('keywords', '')}\nA: {row.get('response', '')}"
                                for row in data[:2]  # FIX 2
                            )
        except Exception as e:
            logger.warning(f"ILIKE search failed: {e}")
        
        return ""

    async def _try_fuzzy_search(self, query: str) -> str:
        """Fallback: fetch all records and do fuzzy matching locally."""
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
                "limit": 50  # FIX 2: smaller pull
            }

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        keywords = [row.get('keywords', '') for row in data]
                        matches = process.extract(query, keywords, limit=2, scorer=fuzz.partial_ratio)  # FIX 2
                        
                        results = []
                        for match, score, idx in matches:
                            if score >= 60:
                                row = data[idx]
                                results.append(f"Q: {row.get('keywords', '')}\nA: {row.get('response', '')}")
                        
                        if results:
                            logger.info(f"✅ Fuzzy search successful, found {len(results)} matches")
                            return "\n".join(results)
                        
        except Exception as e:
            logger.warning(f"Fuzzy search failed: {e}")
        
        return ""

    async def extract_snippet(self, text: str, query: str, window: int = 200, threshold: int = 80) -> str:
        """
        Extracts a relevant snippet from the summarized_text.md using fuzzy matching.
        Only returns a snippet if the match confidence >= threshold (default 80%).
        """
        lines = text.splitlines()
        best_match, score, idx = process.extractOne(query, lines, scorer=fuzz.partial_ratio)

        if best_match and score >= threshold:
            logger.info(f"🎯 Fuzzy match found in summary (score: {score}) → '{best_match[:50]}...'")
            
            # Find where in the text the match occurred
            start = max(0, text.find(best_match) - window)
            end = min(len(text), start + len(best_match) + (2 * window))
            return text[start:end].strip()
        else:
            logger.info(f"⚠️ No strong fuzzy match found in summarized_text.md (best score: {score if best_match else 'N/A'}).")
            return ""

    async def answer(self, query: str, context: str = None) -> str:
        lang = await self.detect_language(query)

        # --- Detect if user explicitly wants human support ---
        human_keywords = [
            "talk to a person", "talk to human", "live agent", "real person", "live person",
            "makipag usap sa tao", "tao", "gusto ko ng tao"
        ]
        lowered = query.lower().strip()
        if any(k in lowered for k in human_keywords):
            logger.info("👤 User requested live person → triggering fallback handler.")
            return self.fallback_handler.generate_fallback_message(lang)

        # --- Detect goodbye / end of conversation ---
        goodbye_keywords = [
            "wala na", "none", "no more", "wa eun", "tapos na",
            "that’s all", "finished", "done", "nope"
        ]
        if any(k in lowered for k in goodbye_keywords):
            logger.info("👋 User ended the conversation.")

            # Language overrides for more natural goodbye
            if "wala na" in lowered or "wa eun" in lowered or "waay na" in lowered:
                lang = "akl"
            elif "tapos na" in lowered:
                lang = "tl"
            elif any(k in lowered for k in ["done", "finished", "none", "no more", "that’s all", "nope"]):
                lang = "en"

            return self.get_goodbye(lang)

        # --- Detect if input is just a greeting ---
        greetings = ["hi", "hello", "hey", "kamusta", "kumusta",
                     "yo", "good morning", "good afternoon", "good evening"]
        if any(lowered.startswith(g) for g in greetings):
            logger.info("👋 User sent a greeting only.")
            return self.get_greeting(lang)

        # --- Get context from both sources ---
        summarized_text = await self.fetch_summarized_file()
        supabase_prompts = await self.fetch_prompts_from_supabase(query)

        full_context = ""
        if context:
            logger.info("ℹ️ External context provided, merging into sources.")
            full_context += f"External Context:\n{context}\n\n"
        if supabase_prompts:
            logger.info("✅ Found context in Supabase chatbot_prompts table.")
            full_context += f"Database Context:\n{supabase_prompts}\n\n"
        if summarized_text:
            snippet = await self.extract_snippet(summarized_text, query)
            if snippet:
                logger.info("✅ Added snippet from summarized_text.md")
                full_context += f"Summary Context:\n{snippet}"

        # --- No context at all → custom no record message ---
        if not full_context.strip():
            response = (
                "I checked our records, but I wasn't able to find any information about "
                f"{query}. You may visit the school office for further details."
            )
            if lang == "akl":
                response = self.aklanon_translator.to_aklanon(response, "en")
            return response + " " + self.get_followup(lang)

        # Truncate before sending to Groq
        max_len = 4000  # chars
        if len(full_context) > max_len:
            logger.warning("⚠️ Context too long, truncating before Groq call.")
            full_context = full_context[:max_len] + "\n...(truncated)..."

        logger.info("🤖 Sending query to Groq with trimmed context.")
        ai_reply = await self.ask_groq(query, full_context, lang)

        if lang == "akl":
            ai_reply = self.aklanon_translator.to_aklanon(ai_reply, "en")
            ai_reply = capitalize_sentences(ai_reply)

        # --- Always append follow-up consistently ---
        return f"{ai_reply.strip()}\n\n{self.get_followup(lang)}"

