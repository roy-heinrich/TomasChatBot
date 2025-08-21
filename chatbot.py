import os
import aiofiles
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from aklstemmer import stem as aklanon_stem
import logging
from fallback import FallbackHandler
import httpx
import docx2txt
import PyPDF2
import openpyxl
from pptx import Presentation
from utils import extract_text_from_file
import psycopg2
import psycopg2.extras
import fasttext  # ✅ for language detection
import re
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatbot_app")

# ✅ Load fastText language detection model once

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "lid.176.ftz")
lid_model = fasttext.load_model(MODEL_PATH)


def detect_language(text: str) -> str:
    """Detect if input is English, Tagalog, or Aklanon. Returns normalized short code."""
    try:
        prediction = lid_model.predict(text)[0][0]  # e.g. "__label__en"
        lang_code = prediction.replace("__label__", "")

        if lang_code.startswith("tl"):  
            return "tl"        # Tagalog
        elif lang_code.startswith("akl") or lang_code == "ak":  
            return "ak"        # Aklanon
        else:
            return "en"        # English
    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        return "en"

class ChatBotApp:
    def __init__(self, session=None):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.summary_file = "docs/SummarizedText/summarized_text.txt"
        self.session = session if session is not None else {}
        self.fallback_handler = FallbackHandler(session=self.session)

        # Persistent ChromaDB
        self.chroma_client = chromadb.PersistentClient(path="chroma_db")
        self.collection = self.chroma_client.get_or_create_collection("school_docs")

    async def summarize_docs(self):
        docs_folder = "docs"
        collected_text = []

        for file_name in os.listdir(docs_folder):
            file_path = os.path.join(docs_folder, file_name)
            if not os.path.isfile(file_path) or file_name.startswith("~"):
                continue
            try:
                text = await extract_text_from_file(file_path)
                if text:
                    collected_text.append(text)
            except Exception as e:
                logger.error(f"Failed to extract {file_name}: {e}")

        combined_text = "\n".join(collected_text)

        # 🔹 Split into smaller chunks
        chunk_size = 3000
        chunks = [combined_text[i:i+chunk_size] for i in range(0, len(combined_text), chunk_size)]

        summaries = []
        for chunk in chunks:
            summary = await self.openrouter_answer(
                chunk,
                "Summarize the following document content into concise bullet points, grouped by category:"
            )
            summaries.append(summary)

        # Final merge pass
        final_summary = await self.openrouter_answer(
            "\n".join(summaries),
            "Combine these partial summaries into one clear, structured summary."
        )

        os.makedirs("docs/SummarizedText", exist_ok=True)
        with open("docs/SummarizedText/summarized_text.txt", "w", encoding="utf-8") as f:
            f.write(final_summary)

        return final_summary

    async def openrouter_answer(self, text: str, prompt: str):
        """Send summarization request to OpenRouter."""
        if not self.openrouter_api_key:
            raise ValueError("OpenRouter API key not found in environment variables.")

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "openai/gpt-oss-20b:free",  # summarizer model
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ]
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"].strip()

    async def clear_chroma(self):
        """Completely reset ChromaDB collection to avoid bloat."""
        try:
            self.chroma_client.delete_collection("school_docs")
            self.collection = self.chroma_client.get_or_create_collection("school_docs")
            logger.info("Cleared old ChromaDB collection.")
        except Exception as e:
            logger.error(f"Error clearing ChromaDB: {e}")

    async def load_summary_into_chroma(self):
        """Load summarized_text.txt into ChromaDB as semantic search chunks."""
        if not os.path.exists(self.summary_file):
            logger.warning("No summary file found. Skipping Chroma load.")
            return

        async with aiofiles.open(self.summary_file, "r", encoding="utf-8", errors="replace") as f:
            text = await f.read()

        if not text.strip():
            logger.warning("Summary file is empty. Skipping Chroma load.")
            return

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_text(text)

        ids = [f"summary_{i}" for i in range(len(chunks))]
        self.collection.add(documents=chunks, ids=ids)

        logger.info(f"Reloaded {len(chunks)} chunks into ChromaDB.")

    async def reload_sources(self):
        """Single-step: summarize → overwrite → clear Chroma → reload"""
        logger.info("Reloading sources...")
        await self.summarize_docs()
        await self.clear_chroma()
        await self.load_summary_into_chroma()
        logger.info("Reload complete.")

    async def chroma_search(self, query, top_k=3):
        """Perform semantic search on ChromaDB."""
        results = self.collection.query(query_texts=[query], n_results=top_k)
        return results.get("documents", [[]])[0]

    async def postgres_fallback(self, query):
        """Fallback to PostgreSQL search - returns matching responses."""
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # ✅ Correct way to use the function: embed it in the SQL query.
            # The `%s` placeholder is for the 'query' variable, not the function.
            sql_query = """
                SELECT response
                FROM chatbot_prompts
                WHERE to_tsvector('english', response) @@ plainto_tsquery('english', %s)
                OR to_tsvector('english', keywords) @@ plainto_tsquery('english', %s)
                LIMIT 5;
            """

            # Pass the user's query as the parameter to the prepared statement.
            cursor.execute(sql_query, (query, query))

            results = [row["response"] for row in cursor.fetchall() if row["response"]]
            cursor.close()
            conn.close()

            logger.info(f"PostgreSQL search found {len(results)} results for query: {query}")
            return results

        except Exception as e:
            logger.error(f"PostgreSQL search error: {e}")
            return []


    def stem_aklanon_text(self, text: str) -> str:
        """Apply Aklanon stemming."""
        words = text.split()
        stemmed_words = [aklanon_stem(word) for word in words]
        return " ".join(stemmed_words)

    async def groq_answer(self, context, query, lang="English"):
        """Get LLM answer from Groq in detected language."""
        prompt = f"Context:\n{context}\n\nQuestion: {query}\nAnswer in {lang}:"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "moonshotai/kimi-k2-instruct",
            "messages": [
                {"role": "system", "content": (
                    "You are TOMAS, a friendly and helpful school assistant for Tomas SM. Bautista Elementary School"
                    "Only answer based on the given context. "
                    "Be polite and clear. "
                    "Always ask if the user needs to know anything else."
                    "Don't give irrelevant information."
                    "Always greet the user warmly. "
                    "If unsure, say you don’t know politely. "
                    f"Always answer in the language specified: {lang}."
                )},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
        
    def format_response_dynamic(self, answer: str, lang: str = "en") -> str:
        """
        Dynamically formats the chatbot response:
        - Preserves natural paragraphing
        - Adds polite closings depending on answer length + language (en, tl, ak)
        """

        if not answer or not answer.strip():
            return "I'm sorry, I couldn't generate an answer right now."

        # Normalize whitespace
        answer = answer.strip()
        
        # Split into paragraphs
        sentences = answer.split(". ")
        formatted = ""
        buffer = []
        sentence_count = 0

        for sentence in sentences:
            buffer.append(sentence.strip())
            sentence_count += 1

            # Group ~2 sentences per paragraph for readability
            if sentence_count >= 2:
                formatted += " ".join(buffer).strip() + ".\n\n"
                buffer = []
                sentence_count = 0

        # Add leftover sentences
        if buffer:
            formatted += " ".join(buffer).strip()
            if not formatted.endswith("."):
                formatted += "."

        # Closing based on language + answer length
        word_count = len(answer.split())
        closing = ""

        if lang.startswith("tl"):
            if word_count < 25:
                closing = "\n\nMay iba pa po ba kayong nais itanong?"
            else:
                closing = "\n\nKung may iba pa po kayong kailangan, huwag po kayong mag-atubiling magtanong."
        elif lang.startswith("ak"):  # Aklanon
            if word_count < 25:
                closing = "\n\nMayda pa guid ba kamo nga buot ipamangkot?"
            else:
                closing = "\n\nKun mayda pa kamo kinahanglanon, indi kamo magduha-duha nga magpamangkot."
        else:  # Default English
            if word_count < 25:
                closing = "\n\nWould you like me to explain further?"
            else:
                closing = "\n\nIf you have more questions, feel free to ask."

        return formatted + closing

    async def get_response(self, query, lang=None):
        """Main chatbot logic with hybrid search approach."""
        query_lower = query.strip().lower()

        # ✅ Detect language automatically if not passed
        if not lang:
            lang = detect_language(query)
            logger.info(f"Detected language for query '{query}': {lang}")

        if self.fallback_handler.is_awaiting_confirmation():
            return self.fallback_handler.handle_confirmation_response(query)

        if self.fallback_handler.check_for_live_agent_trigger(query_lower):
            return self.fallback_handler.handle_fallback_request(query)

        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
        if any(greet in query_lower for greet in greetings):
            return "Hi! What can I do for you today?"

        chroma_context = "\n".join(await self.chroma_search(query))
        postgres_results = await self.postgres_fallback(query)
        postgres_context = "\n".join(postgres_results)

        if chroma_context.strip() and postgres_context.strip():
            combined_context = f"ChromaDB Results:\n{chroma_context}\n\nPostgres Results:\n{postgres_context}"
        elif chroma_context.strip():
            combined_context = chroma_context
        elif postgres_context.strip():
            combined_context = postgres_context
        else:
            return self.fallback_handler.handle_no_answer_fallback(query)


        # ✅ Pass answer through dynamic formatter
        answer = await self.groq_answer(combined_context, query, lang)

        return self.format_response_dynamic(answer, lang)

