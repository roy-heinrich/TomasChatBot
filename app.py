from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import requests
import asyncio
from supabase import create_client, Client
from summarizer import summarize_and_store
import os, httpx
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "openai/gpt-oss-20b:free"

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Groq API credentials
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"  # replace with actual endpoint
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/admin/reload")
async def reload_sources():
    try:
        logger.info("🔄 Starting /admin/reload: summarizing all docs...")
        summary_text = await summarize_and_store()
        if not summary_text:
            return JSONResponse(
                status_code=500,
                content={"message": "Summarization failed or returned empty result."}
            )
        return JSONResponse(
            status_code=200,
            content={"message": "Sources reloaded and summarized successfully."}
        )
    except Exception as e:
        logger.exception("❌ /admin/reload failed")
        return JSONResponse(
            status_code=500,
            content={"message": f"Failed to reload sources: {str(e)}"}
        )

# -----------------------
# Optional logs endpoint
# -----------------------
@app.get("/admin/logs")
async def get_logs():
    return {"logs": "No logs available"}

# -----------------------
# Chat endpoint (placeholder)
# -----------------------
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    query = data.get("query", "").strip()

    if not query:
        return {"response": "No query provided."}

    # 1️⃣ Fetch context from Supabase
    result = supabase.table("chatbot_prompts").select("prompt, response").execute()
    context = ""
    if result.data:
        for row in result.data:
            context += f"Prompt: {row['prompt']}\nResponse: {row['response']}\n\n"

    # 2️⃣ Send query + context to Groq API (async)
    groq_payload = {
        "query": query,
        "context": context
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        groq_response = await client.post(GROQ_API_URL, json=groq_payload, headers=headers)

    if groq_response.status_code == 200:
        llm_answer = groq_response.json().get("answer", "Sorry, I couldn't generate a response.")
    else:
        llm_answer = f"Groq API error: {groq_response.text}"

    return {"response": llm_answer}

@app.get("/test_openrouter")
async def test_openrouter():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                json={
                    "model": OPENROUTER_MODEL,
                    "messages":[
                        {"role":"system","content":"You are a helpful assistant."},
                        {"role":"user","content":"Hello"}
                    ]
                }
            )
        return {"status_code": resp.status_code, "response_text": resp.text}
    except Exception as e:
        return {"error": str(e)}