from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import asyncio

# Import your summarizer
from summarizer import summarize_and_store

# -----------------------
# FastAPI app setup
# -----------------------
app = FastAPI(title="Tomas Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict to frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatbot")

# -----------------------
# Admin reload route
# -----------------------
@app.post("/admin/reload")
async def reload_sources():
    """
    Summarizes all documents from Supabase DOCS_BUCKET using summarizer.py
    and uploads summarized_text.md to SUMMARY_BUCKET.
    """
    try:
        logger.info("🔄 Starting document summarization...")

        # Call the async summarizer from summarizer.py
        final_summary = await summarize_and_store()

        if final_summary:
            logger.info("✅ Summarization complete!")
            return {"message": "Sources reloaded and summarized successfully."}
        else:
            logger.warning("⚠ Summarization returned empty result.")
            return JSONResponse(
                content={"error": "Summarization completed but returned empty result."},
                status_code=500,
            )

    except Exception as e:
        logger.exception("❌ Failed to reload sources")
        return JSONResponse(
            content={"error": f"Failed to reload sources: {str(e)}"}, status_code=500
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
