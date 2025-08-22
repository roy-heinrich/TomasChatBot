# app.py
import logging
from fastapi import FastAPI
from utils import summarize_and_store, fetch_summarized_text

logger = logging.getLogger("chatbot")
app = FastAPI()


@app.get("/admin/reload")
async def reload_sources():
    """
    Trigger summarization pipeline:
    - Pull docs from Supabase 'chatbot-docs'
    - Stream them to OpenRouter for summarization
    - Store result in 'summarized-text/summarized_text.md'
    """
    try:
        logger.info("Reloading and summarizing docs from Supabase...")
        summary_text = await summarize_and_store()
        return {
            "message": "✅ Summarized and stored in Supabase.",
            "content": summary_text
        }
    except Exception as e:
        logger.exception("❌ Error during summarization")
        return {
            "message": f"Reload failed: {str(e)}",
            "content": ""
        }


@app.get("/summarized_text")
async def get_summarized_text():
    """
    Endpoint to fetch summarized text from Supabase
    """
    try:
        text = await fetch_summarized_text()
        return {"content": text}
    except Exception as e:
        logger.exception("❌ Failed to fetch summarized text")
        return {"content": "", "error": str(e)}
