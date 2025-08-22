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
    query = payload.get("query", "")
    logger.info(f"Incoming query: {query}")
    response = await chatbot.ask(query)
    return {"response": response}

@app.post("/admin/reload")
async def reload_sources():
    logger.info("Reloading and summarizing docs...")
    await summarize_and_store()  # fetch docs, summarize via OpenRouter, upload summarized_text.md
    return {"status": "ok", "message": "Docs reloaded and summarized"}
