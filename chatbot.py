# chatbot.py
import os
import logging
import httpx
import langid
from utils import fetch_summarized_text
from fallback import FallbackHandler

logger = logging.getLogger("chatbot")

class ChatBot:
    def __init__(self, groq_key: str):
        self.fallback_handler = FallbackHandler()
        self.groq_key = groq_key
        self.openrouter_api = "https://api.groq.com/openai/v1/chat/completions"

    async def detect_language(self, text: str) -> str:
        lang, _ = langid.classify(text)
        return lang if lang in ["en", "tl"] else "en"

    async def ask_openrouter(self, query: str, context: str, lang: str) -> str:
        system_prompt = "You are the polite, respectful chatbot of Tomas SM. Bautista Elementary School. Keep answers short, clear, and helpful."
        if lang == "tl":
            system_prompt = "Ikaw ay isang magalang na chatbot ng Tomas SM. Bautista Elementary School. Sagutin nang malinaw at maikli."
        
        payload = {
            "model": "openai/gpt-oss-120b",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nUser: {query}"}
            ],
            "temperature": 0.7
        }

        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(self.openrouter_api, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.error(f"OpenRouter failed: {e}")
                return self.fallback_handler.get_fallback_message(lang)

    async def answer(self, query: str, context: str) -> str:
        # Use the context fetched from keywords + response
        lang = await self.detect_language(query)
        if not context:
            return self.fallback_handler.get_fallback_message(lang)
        return await self.ask_openrouter(query, context, lang)
