import os
import logging
import httpx
import langid
import random
from utils import fetch_summarized_text
from fallback import FallbackHandler

logger = logging.getLogger("chatbot")

class ChatBot:
    def __init__(self, groq_key: str):
        self.fallback_handler = FallbackHandler()
        self.groq_key = groq_key  
        self.groq_api = "https://api.groq.com/openai/v1/chat/completions"

        # Greeting options
        self.greetings_en = ["Good day!", "Hello!", "Hi there!", "Greetings!"]
        self.greetings_tl = ["Magandang araw po!", "Kumusta po!", "Mabuhay!", "Magandang umaga po!"]

        # Follow-up prompts
        self.followup_en = " What else can I do for you today?"
        self.followup_tl = " Ano pa po ang maitutulong ko sa inyo ngayon?"

    async def detect_language(self, text: str) -> str:
        lang, _ = langid.classify(text)
        return lang if lang in ["en", "tl"] else "en"

    async def ask_groq(self, query: str, context: str, lang: str) -> str:
        system_prompt = "You are the polite, respectful chatbot of Tomas SM. Bautista Elementary School. Keep answers short, clear, and helpful. Always sound natural and conversational."
        if lang == "tl":
            system_prompt = "Ikaw ay isang magalang na chatbot ng Tomas SM. Bautista Elementary School. Sagutin nang malinaw at maikli. Lagi kang magsimula sa isang maikling pagbati at panatilihing magalang ang tono."

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

    async def answer(self, query: str, context: str) -> str:
        lang = await self.detect_language(query)
        if not context:
            return self.fallback_handler.get_fallback_message(lang)
        return await self.ask_groq(query, context, lang)
