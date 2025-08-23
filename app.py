from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import asyncio

from summarizer import summarize_and_store
from utils import get_supabase_client, DOCS_BUCKET

# -----------------------
# FastAPI app setup
# -----------------------
app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatbot")

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
        logger.info("🔄 Starting /admin/reload: summarizing all docs...")

        # Get a Supabase client to list files
        supabase = get_supabase_client()
        files_list = supabase.storage.from_(DOCS_BUCKET).list()
        if not files_list:
            logger.warning("⚠ No files found in DOCS_BUCKET")
            return JSONResponse(
                status_code=500,
                content={"message": "No files found in DOCS_BUCKET."}
            )

        logger.info(f"📄 {len(files_list)} files found in DOCS_BUCKET:")
        for f in files_list:
            logger.info(f"  - {f['name']}")

        # Call the summarizer
        summary_text = await summarize_and_store()
        if not summary_text:
            logger.warning("⚠ Summarization returned empty result")
            return JSONResponse(
                status_code=500,
                content={"message": "Summarization completed but returned empty result."}
            )

        logger.info("✅ /admin/reload completed successfully")
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
