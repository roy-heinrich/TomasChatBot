# app.py
import os, httpx
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from dotenv import load_dotenv
from chatbot import ChatBot
from pydantic import BaseModel
from summarizer import summarize_and_store

load_dotenv()
logger = logging.getLogger("chatbot")
logging.basicConfig(level=logging.INFO)

# -----------------------
# Supabase
# -----------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------
# Groq key
# -----------------------
GROQ_KEY = os.getenv("GROQ_API_KEY")
chatbot = ChatBot(groq_key=GROQ_KEY)

# -----------------------
# FastAPI app
# -----------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Pydantic model for request
# -----------------------
class ChatRequest(BaseModel):
    query: str
async def fetch_supabase_context() -> str:
    # Supabase python client is synchronous, so run in threadpool
    import asyncio
    loop = asyncio.get_event_loop()

    def fetch_sync():
        result = supabase.table("chatbot_prompts").select("prompt, response").execute()
        context = ""
        if result.data:
            for row in result.data:
                context += f"Prompt: {row['prompt']}\nResponse: {row['response']}\n\n"
        return context

    return await loop.run_in_executor(None, fetch_sync)

# -----------------------
# Chat endpoint
# -----------------------
@app.post("/chat")
async def chat_endpoint(data: ChatRequest):
    query = data.query.strip()
    if not query:
        return {"response": "No query provided."}

    # Fetch context asynchronously
    supabase_context = await fetch_supabase_context()

    # Ask ChatBot with the context
    answer = await chatbot.answer(query, context=supabase_context)
    return {"response": answer}

# -----------------------
# Admin reload endpoint
# -----------------------
@app.post("/admin/reload")
async def reload_sources():
    try:
        logger.info("🔄 Starting /admin/reload: summarizing all docs...")
        summary_text = await summarize_and_store()
        if not summary_text:
            return JSONResponse(status_code=500, content={"message": "Summarization failed."})
        return JSONResponse(status_code=200, content={"message": "Sources reloaded successfully."})
    except Exception as e:
        logger.exception("Reload failed")
        return JSONResponse(status_code=500, content={"message": str(e)})