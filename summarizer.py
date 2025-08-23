# summarizer.py
import os
import logging
import httpx
from utils import get_supabase_client, DOCS_BUCKET, SUMMARY_BUCKET, SUMMARY_FILENAME

logger = logging.getLogger("summarizer")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "google/gemma-3n-e2b-it:free"


async def summarize_and_store(
    input_filename: str = SUMMARY_FILENAME,
    output_filename: str = SUMMARY_FILENAME
) -> str:
    """
    Streams docs from Supabase → OpenRouter (chunked summarization) →
    saves summary back to Supabase (summarized_text.md).
    """
    try:
        supabase = get_supabase_client()

        logger.info(f"⬇ Downloading {input_filename} from Supabase bucket {DOCS_BUCKET}...")

        # Download raw docs
        raw_data = supabase.storage.from_(DOCS_BUCKET).download(input_filename)
        if raw_data is None:
            logger.warning(f"⚠ {input_filename} not found in bucket {DOCS_BUCKET}.")
            return ""

        raw_text = raw_data.decode("utf-8")

        # ---- Chunk docs to avoid token limits ----
        CHUNK_SIZE = 3000
        chunks = [raw_text[i:i+CHUNK_SIZE] for i in range(0, len(raw_text), CHUNK_SIZE)]
        summaries = []

        async with httpx.AsyncClient(timeout=90.0) as client:
            for idx, chunk in enumerate(chunks):
                logger.info(f"📝 Summarizing chunk {idx+1}/{len(chunks)} ({len(chunk)} chars)...")

                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                    json={
                        "model": OPENROUTER_MODEL,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Summarize this document into clear Markdown with sections: Personnel, Departments, Events, Locations, Contact Info. Preserve names and titles."
                            },
                            {"role": "user", "content": chunk},
                        ],
                    },
                )

                if resp.status_code != 200:
                    logger.error(f"❌ OpenRouter failed on chunk {idx+1}")
                    continue

                data = resp.json()
                summary_part = data["choices"][0]["message"]["content"].strip()
                summaries.append(summary_part)

        final_summary = "\n\n".join(summaries)

        # Upload summary back to Supabase
        logger.info(f"⬆ Uploading {output_filename} to {SUMMARY_BUCKET}...")
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
