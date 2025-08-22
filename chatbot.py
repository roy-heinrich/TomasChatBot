import os
import logging
import httpx
import fasttext
from dotenv import load_dotenv
from utils import fetch_summarized_text
from fallback import FallbackHandler

logger = logging.getLogger("chatbot")
load_dotenv()


class ChatBot:
    def __init__(self):
        # Fallback handler (when LLM fails)
        self.fallback_handler = FallbackHandler()

        # Language detection model
        model_path = os.path.join(os.path.dirname(__file__), "model", "lid.176.ftz")
        self.lang_model = fasttext.load_model(model_path)

        # OpenRouter API
        self.openrouter_api = "https://openrouter.ai/api/v1/chat/completions"
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")

    async def detect_language(self, text: str) -> str:
        """Detect the language of the input text (default: en)."""
        try:
            prediction = self.lang_model.predict(text.replace("\n", " "))
            lang = prediction[0][0].replace("__label__", "")
            return lang
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "en"

    async def ask_openrouter(self, query: str, context: str, lang: str) -> str:
        """Send query + context to OpenRouter and return the answer."""
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
        }

        # System prompt for polite school-specific chatbot
        system_prompt = (
            "You are the polite, respectful chatbot of Tomas SM. Bautista Elementary School. "
            "Always keep answers short, clear, and helpful. If the question is unrelated to the school, politely decline."
        )

        if lang == "tl":
            system_prompt = (
                "Ikaw ay isang magalang na chatbot ng Tomas SM. Bautista Elementary School. "
                "Sagutin nang malinaw at maikli. Kung hindi tungkol sa paaralan ang tanong, "
                "magalang na sabihin na hindi mo masasagot."
            )

        payload = {
            "model": "google/gemma-3n-e2b-it:free",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nUser: {query}"}
            ],
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(self.openrouter_api, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.error(f"OpenRouter request failed: {e}")
                return self.fallback_handler.get_fallback_message(lang)

    async def answer(self, query: str) -> str:
        """Main entrypoint: detect language, fetch Supabase context, ask OpenRouter."""
        lang = await self.detect_language(query)

        # Only fetch from Supabase summarized_text.md
        summarized_text = await fetch_summarized_text()

        if not summarized_text:
            logger.warning("No summarized_text.md found in Supabase.")
            return self.fallback_handler.get_fallback_message(lang)

        return await self.ask_openrouter(query, summarized_text, lang)
