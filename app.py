#app.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from chatbot import ChatBot
from utils import summarize_and_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

app = FastAPI()
chatbot = ChatBot()

# ✅ Enable CORS (so frontend can call backend without 404 on OPTIONS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:8080",
        "http://localhost:3000",  
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
async def root():
    return {"status": "ok", "message": "Chatbot backend running"}

@app.post("/chat")
async def chat(payload: dict):
    """
    Main chatbot endpoint.
    Calls ChatBot.answer() instead of ask() directly.
    """
    query = payload.get("query", "").strip()
    logger.info(f"Incoming query: {query}")
    response = await chatbot.answer(query)   # ✅ now using answer()
    return {"response": response}

@app.get("/admin/reload")
async def reload_sources():
    """
    Summarizes docs from Supabase and saves summarized_text.md back to Supabase.
    """
    try:
        logger.info("Reloading and summarizing docs from Supabase...")
        summary_text = await summarize_and_store()
        return {"message": "Summarized and stored in Supabase.", "content": summary_text}
    except Exception as e:
        logger.exception("Error during summarization")
        return {"message": f"Reload failed: {str(e)}", "content": ""}