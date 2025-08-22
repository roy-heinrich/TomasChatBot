import os
import sys
import logging
import aiofiles
import httpx
import fasttext
import pymysql
from dotenv import load_dotenv
from utils import fetch_summarized_text
from fallback import FallbackHandler

logger = logging.getLogger("chatbot")
load_dotenv()

class ChatBot:
    def __init__(self):
        # MySQL
        self.mysql_conn = pymysql.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "tomasdb"),
            cursorclass=pymysql.cursors.DictCursor
        )

        # Fallback
        self.fallback_handler = FallbackHandler()

        # Language detection
        self.lang_model = fasttext.load_model("lid.176.ftz")

        # OpenRouter
        self.openrouter_api = "https://openrouter.ai/api/v1/chat/completions"
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")

    async def detect_language(self, text: str) -> str:
        try:
            prediction = self.lang_model.predict(text.replace("\n", " "))
            lang = prediction[0][0].replace("__label__", "")
            return lang
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "en"

    async def ask_openrouter(self, query: str, context: str, lang: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
        }
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
            "temperature": 0.7
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

    async def get_mysql_context(self, query: str) -> str:
        try:
            with self.mysql_conn.cursor() as cursor:
                cursor.execute("SELECT answer FROM chatbot_prompts WHERE question LIKE %s", (f"%{query}%",))
                result = cursor.fetchone()
                return result["answer"] if result else ""
        except Exception as e:
            logger.error(f"MySQL query failed: {e}")
            return ""

    async def answer(self, query: str) -> str:
        lang = await self.detect_language(query)

        # Fetch summarized knowledge from Supabase
        summarized_text = await fetch_summarized_text()

        # Also try MySQL
        mysql_context = await self.get_mysql_context(query)

        # Combine
        context = ""
        if mysql_context:
            context += f"MySQL:\n{mysql_context}\n\n"
        if summarized_text:
            context += f"Docs:\n{summarized_text}\n\n"

        if not context:
            return self.fallback_handler.get_fallback_message(lang)

        return await self.ask_openrouter(query, context, lang)
