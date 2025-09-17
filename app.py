import os, httpx
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from dotenv import load_dotenv
from chatbot import ChatBot
from pydantic import BaseModel
from utils import summarize_and_store

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
#    key
# -----------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
chatbot = ChatBot(groq_key=GROQ_API_KEY)

# -----------------------
# FastAPI app
# -----------------------
app = FastAPI()

# ✅ Enhanced CORS config for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000", 
        "http://localhost:8080",
        "http://localhost:5000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080", 
        "http://127.0.0.1:5000",
        "https://tomaschatbot.onrender.com",
        "*"  # Allow all origins for now
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
)

# -----------------------
# Pydantic model for request
# -----------------------
class ChatRequest(BaseModel):
    query: str
    conversation_history: list = []

# -----------------------
# Supabase fetch helper
# -----------------------
async def fetch_supabase_context() -> str:
    import asyncio
    loop = asyncio.get_event_loop()

    def fetch_sync():
        result = supabase.table("chatbot_prompts").select("keywords, response").execute()
        context = ""
        if result.data:
            for row in result.data:
                context += f"Keywords: {row['keywords']}\nResponse: {row['response']}\n\n"
        return context

    return await loop.run_in_executor(None, fetch_sync)

# -----------------------
# Root endpoint for health check
# -----------------------
@app.get("/")
async def root():
    return {"message": "Tomas Chatbot API is running!", "status": "healthy"}

# -----------------------
# OPTIONS handler for CORS preflight
# -----------------------
@app.options("/chat")
async def chat_options():
    return {"message": "OK"}

# -----------------------
# Chat endpoint
# -----------------------
@app.post("/chat")
async def chat_endpoint(data: ChatRequest):
    try:
        logger.info(f"📥 Received chat request: {data.query[:50]}...")
        query = data.query.strip()
        if not query:
            logger.warning("⚠️ Empty query received")
            return {"response": "No query provided."}

        # Fetch context asynchronously
        supabase_context = await fetch_supabase_context()
        logger.info("📊 Context fetched from Supabase")

        # Ask ChatBot with the context and conversation history
        answer = await chatbot.answer(query, context=supabase_context, conversation_history=data.conversation_history)
        logger.info(f"✅ Generated response: {answer[:50]}...")
        
        return {"response": answer}
    
    except Exception as e:
        logger.error(f"❌ Error in chat endpoint: {str(e)}")
        return JSONResponse(
            content={"response": "I'm sorry, I encountered an error. Please try again."},
            status_code=500
        )

# -----------------------
# Clear context endpoint for session management
# -----------------------
@app.post("/clear-context")
async def clear_context():
    """Clear conversation context when user closes widget or navigates away"""
    try:
        logger.info("🧹 Conversation context cleared")
        return {"success": True, "message": "Context cleared"}
    except Exception as e:
        logger.error(f"❌ Error clearing context: {str(e)}")
        return JSONResponse(
            content={"success": False, "message": "Failed to clear context"},
            status_code=500
        )

# -----------------------
# Admin reload endpoint
# -----------------------
@app.post("/admin/reload")
async def reload_sources():
    try:
        result = await summarize_and_store()
        return JSONResponse(
            content={
                "success": True,
                "message": "Reload complete",
                "details": result
            },
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": f"Reload failed: {str(e)}"
            },
            status_code=500
        )
