# app.py
import os, httpx
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from dotenv import load_dotenv
from chatbot import ChatBot
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
# Chat endpoint
# -----------------------
@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    query = data.get("query", "").strip()

    if not query:
        return {"response": "No query provided."}

    # Optional: fetch context from Supabase if needed
    result = supabase.table("chatbot_prompts").select("prompt, response").execute()
    context = ""
    if result.data:
        for row in result.data:
            context += f"Prompt: {row['prompt']}\nResponse: {row['response']}\n\n"

    answer = await chatbot.answer(query, context=context)
    return {"response": answer}

# -----------------------
# Admin reload endpoint
# -----------------------
@app.post("/admin/reload")
async def reload_sources():
    try:
        summary_text = await summarize_and_store()
        if not summary_text:
            return JSONResponse(status_code=500, content={"message": "Summarization failed."})
        return JSONResponse(status_code=200, content={"message": "Sources reloaded successfully."})
    except Exception as e:
        logger.exception("Reload failed")
        return JSONResponse(status_code=500, content={"message": str(e)})
