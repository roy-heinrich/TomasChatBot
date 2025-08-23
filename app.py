from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import asyncio

from summarizer import summarize_and_store  # updated function

# -----------------------
# FastAPI app setup
# -----------------------
app = FastAPI()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatbot")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict to frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Admin reload route
# -----------------------
@app.post("/admin/reload")
async def reload_sources():
    try:
        logger.info("🔄 Starting document summarization via /admin/reload...")

        # Call summarize_and_store with explicit input/output buckets
        # The function itself should handle listing all files in DOCS_BUCKET
        summary_text = await summarize_and_store(
            input_filename=None,   # None triggers "all files in DOCS_BUCKET"
            output_filename="summarized_text.md"  # store result in SUMMARY_BUCKET
        )

        if not summary_text:
            return JSONResponse(
                status_code=500,
                content={"message": "Summarization completed but returned empty result."}
            )

        logger.info("✅ All files summarized successfully into SUMMARY_BUCKET.")
        return JSONResponse(
            status_code=200,
            content={"message": "All documents summarized and stored successfully."}
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
