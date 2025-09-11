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
import urllib.parse

logger = logging.getLogger("chatbot")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class ChatBot:
    def __init__(self, groq_key: str):
        self.fallback_handler = FallbackHandler()
        self.groq_key = groq_key  
        self.groq_api = "https://api.groq.com/openai/v1/chat/completions"
        self.bucket = "summarized-text"
        self.file = "summarized_text.md"
        self.greetings_en = [
            "Hi, I’m TOMAS — the personal chatbot of Tomas SM. Bautista Elementary School. How can I help you today?",
            "Hello! I’m TOMAS, here to assist you with anything about Tomas SM. Bautista Elementary School. What do you need help with?",
            "Good day! I’m TOMAS, your school’s chatbot assistant. How may I help you?"
        ]
        self.greetings_tl = [
            "Magandang araw po! Ako si TOMAS — ang chatbot ng Tomas SM. Bautista Elementary School. Paano ko po kayo matutulungan?",
            "Kumusta po! Ako si TOMAS, handang tumulong sa inyong mga tanong tungkol sa Tomas SM. Bautista Elementary School. Ano pong maitutulong ko?",
            "Mabuhay! Ako si TOMAS, ang chatbot ng inyong paaralan. Ano po ang kailangan ninyo?"
        ]

        # Polite follow-ups
        self.followup_en = "Is there anything else I can help you with?"
        self.followup_tl = "May iba pa po ba akong maitutulong sa inyo?"

    def get_greeting(self, lang="en") -> str:
        return random.choice(self.greetings_tl if lang.startswith("tl") else self.greetings_en)

    def get_followup(self, lang="en") -> str:
        return self.followup_tl if lang.startswith("tl") else self.followup_en
        # Cache variables
        self._cached_summary = None
        self._last_fetched = 0
        self.cache_ttl = 300  # cache for 5 minutes (adjust as needed)
    def get_greeting(self, lang="en") -> str:
        if lang.startswith("tl"):
            return random.choice(self.greetings_tl)
        return random.choice(self.greetings_en)

    def get_followup(self, lang="en") -> str:
        return self.followup_tl if lang.startswith("tl") else self.followup_en
    async def detect_language(self, text: str) -> str:
        lang, _ = langid.classify(text)
        return lang if lang in ["en", "tl"] else "en"

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
        system_prompt = (
            "You are the polite, respectful chatbot of Tomas SM. Bautista Elementary School called TOMAS. "
            "Keep answers short, clear, and helpful. Always sound natural and conversational."
        )
        if lang == "tl":
            system_prompt = (
                "Ikaw ay isang magalang na chatbot ng Tomas SM. Bautista Elementary School na si TOMAS. "
                "Sagutin nang malinaw at maikli. Panatilihing magalang at natural ang tono."
            )

        payload = {
            "model": "openai/gpt-oss-120b",
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

        import httpx
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(self.groq_api, json=payload, headers=headers)
                response.raise_for_status()
                ai_response = response.json()["choices"][0]["message"]["content"].strip()

                # Decide whether to greet or follow-up
                if not self.session.get("greeted", False):
                    self.session["greeted"] = True
                    return f"{self.get_greeting(lang)}\n\n{ai_response}"
                else:
                    return f"{ai_response}\n\n{self.get_followup(lang)}"

            except Exception as e:
                logger.error(f"Groq failed: {e}")
                return self.fallback_handler.generate_fallback_message(lang)

        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(self.groq_api, json=payload, headers=headers)
                response.raise_for_status()
                ai_response = response.json()["choices"][0]["message"]["content"].strip()

                # Add random greeting + follow-up
                greeting = random.choice(self.greetings_tl if lang == "tl" else self.greetings_en)
                followup = self.followup_tl if lang == "tl" else self.followup_en

                return f"{greeting} {ai_response}{followup}"

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
            # Join search terms with & for AND search or | for OR search
            search_query = " & ".join(search_terms)  # AND search
            
            url = f"{SUPABASE_URL}/rest/v1/chatbot_prompts"
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            # Use proper FTS syntax
            params = {
                "select": "keywords,response",
                "keywords": f"fts.{search_query}",
                "limit": 5
            }

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        logger.info(f"✅ FTS search successful, found {len(data)} results")
                        return "\n".join(f"Q: {row.get('keywords', '')}\nA: {row.get('response', '')}" for row in data)
                else:
                    logger.warning(f"FTS search failed with status {resp.status_code}")
                    
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

            # Try each search term
            for term in search_terms[:3]:  # Limit to first 3 terms
                params = {
                    "select": "keywords,response",
                    "or": f"keywords.ilike.%{term}%,response.ilike.%{term}%",
                    "limit": 5
                }

                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, headers=headers, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data:
                            logger.info(f"✅ ILIKE search successful for term '{term}', found {len(data)} results")
                            return "\n".join(f"Q: {row.get('keywords', '')}\nA: {row.get('response', '')}" for row in data)
                    
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
                "limit": 100  # Limit to avoid huge responses
            }

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        # Use fuzzy matching to find best matches
                        keywords = [row.get('keywords', '') for row in data]
                        matches = process.extract(query, keywords, limit=3, scorer=fuzz.partial_ratio)
                        
                        results = []
                        for match, score, idx in matches:
                            if score >= 60:  # Minimum similarity threshold
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
        human_keywords = ["talk to a person", "talk to human", "live agent", 
                        "real person", "makipag usap sa tao", "tao", "gusto ko ng tao"]

        lowered = query.lower()
        if any(k in lowered for k in human_keywords):
            logger.info("👤 User requested live person → triggering fallback handler.")
            return self.fallback_handler.generate_fallback_message(lang)

        # --- Get context from both sources ---
        summarized_text = await self.fetch_summarized_file()
        supabase_prompts = await self.fetch_prompts_from_supabase(query)

        # Merge external context if provided
        full_context = ""
        if context:
            logger.info("ℹ️ External context provided, merging into sources.")
            full_context += f"External Context:\n{context}\n\n"
        if supabase_prompts:
            logger.info("✅ Found context in Supabase chatbot_prompts table.")
            full_context += f"Database Context:\n{supabase_prompts}\n\n"
        if summarized_text:
            logger.info("✅ Found context in summarized_text.md file.")
            full_context += f"Summary Context:\n{summarized_text}"

        # --- No context at all → fallback ---
        if not full_context.strip():
            return self.fallback_handler.generate_fallback_message(lang)

        logger.info("🤖 Sending query to Groq with merged context.")
        return await self.ask_groq(query, full_context, lang)
