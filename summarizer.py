# summarizer.py
import os
import logging
import httpx
from utils import get_supabase_client, DOCS_BUCKET, SUMMARY_BUCKET, SUMMARY_FILENAME

logger = logging.getLogger("summarizer")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "google/gemma-3n-e2b-it:free"


async def summarize_and_store(output_filename: str = SUMMARY_FILENAME) -> str:
    """
    Summarizes all documents from DOCS_BUCKET and uploads the final summary to SUMMARY_BUCKET.
    """
    try:
        supabase = get_supabase_client()

        # List all raw docs in DOCS_BUCKET
        files = supabase.storage.from_(DOCS_BUCKET).list()
        if not files:
            logger.warning(f"⚠ No files found in bucket {DOCS_BUCKET}")
            return ""

        summaries = []

        async with httpx.AsyncClient(timeout=None) as client:
            for file in files:
                file_name = file["name"]
                logger.info(f"⬇ Downloading {file_name} for summarization...")

                raw_data = supabase.storage.from_(DOCS_BUCKET).download(file_name)
                text = raw_data.decode("utf-8", errors="ignore")

                # Chunk text to avoid token limits
                CHUNK_SIZE = 3000
                chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]

                for idx, chunk in enumerate(chunks, 1):
                    logger.info(f"📝 Summarizing chunk {idx}/{len(chunks)} of {file_name} ({len(chunk)} chars)...")

                    resp = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                        json={
                            "model": OPENROUTER_MODEL,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": (
                                        "Summarize this document into clear Markdown with sections: "
                                        "Personnel, Departments, Events, Locations, Contact Info. "
                                        "Preserve names and titles."
                                    ),
                                },
                                {"role": "user", "content": chunk},
                            ],
                        },
                    )

                    if resp.status_code != 200:
                        logger.error(f"❌ OpenRouter failed on chunk {idx} of {file_name}")
                        continue

                    data = resp.json()
                    summary_part = data["choices"][0]["message"]["content"].strip()
                    summaries.append(summary_part)

        final_summary = "\n\n".join(summaries)

        # Upload summary to SUMMARY_BUCKET
        logger.info(f"⬆ Uploading summary to {SUMMARY_BUCKET}/{output_filename}...")
        supabase.storage.from_(SUMMARY_BUCKET).upload(
            output_filename,
            final_summary.encode("utf-8"),
            {"content-type": "text/markdown", "upsert": "true"},
        )

        logger.info("✅ Summarization complete and stored in Supabase.")
        return final_summary

    except Exception as e:
        logger.exception("❌ Error during summarization pipeline")
        return ""
