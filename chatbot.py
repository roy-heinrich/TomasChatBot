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
        # Greeting options
        self.greetings_en = ["Good day!", "Hello!", "Hi there!", "Greetings!"]
        self.greetings_tl = ["Magandang araw po!", "Kumusta po!", "Mabuhay!", "Magandang umaga po!"]

        # Follow-up prompts
        self.followup_en = " What else can I do for you today?"
        self.followup_tl = " Ano pa po ang maitutulong ko sa inyo ngayon?"

        # Cache variables
        self._cached_summary = None
        self._last_fetched = 0
        self.cache_ttl = 300  # cache for 5 minutes (adjust as needed)

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
        system_prompt = "You are the polite, respectful chatbot of Tomas SM. Bautista Elementary School called TOMAS. Keep answers short, clear, and helpful. Always sound natural and conversational."
        if lang == "tl":
            system_prompt = "Ikaw ay isang magalang na chatbot ng Tomas SM. Bautista Elementary School na si TOMAS. Sagutin nang malinaw at maikli. Lagi kang magsimula sa isang maikling pagbati at panatilihing magalang ang tono."

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
                return self.fallback_handler.get_fallback_message(lang)
            


    async def fetch_prompts_from_supabase(self, query: str) -> str:
        """Search chatbot_prompts table in Supabase for matching context using FTS."""
        url = f"{SUPABASE_URL}/rest/v1/chatbot_prompts"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # ✅ Wrap query in quotes so PostgREST accepts it
        query_quoted = f'"{query}"'

        params = {
            "select": "prompt,response",
            "prompt": f"fts.english.{query_quoted}",  # correct syntax
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

        if not data:
            return ""

        return "\n".join(f"Q: {row['prompt']}\nA: {row['response']}" for row in data)

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
            return self.fallback_handler.get_fallback_message(lang)

        logger.info("🤖 Sending query to Groq with merged context.")
        return await self.ask_groq(query, full_context, lang)
