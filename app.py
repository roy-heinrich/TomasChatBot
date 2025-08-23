# app.py (FastAPI)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from summarizer import summarize_and_store

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
        summary_text = await summarize_and_store(chunk_delay=2.0)  # 2s delay between chunks
        if not summary_text.strip():
            return JSONResponse(
                status_code=200,
                content={"message": "Reload attempted but summarization returned empty (rate limit or empty docs)."}
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
# Optional /admin/logs route
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
