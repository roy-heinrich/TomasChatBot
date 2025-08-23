from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import asyncio
from summarizer import summarize_and_store
import os, httpx
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "openai/gpt-oss-20b:free"

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
async def chat(request: dict):
    query = request.get("query", "")
    return {"response": f"Received query: {query}"}

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