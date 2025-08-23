# summarizer.py
import os
import io
import logging
import httpx
from utils import get_supabase_client, DOCS_BUCKET, SUMMARY_BUCKET, SUMMARY_FILENAME

from docx import Document
import PyPDF2
import openpyxl
from pptx import Presentation

logger = logging.getLogger("summarizer")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "google/gemma-3n-e2b-it:free"

def extract_text(file_name: str, raw_bytes: bytes) -> str:
    """Extract text from multiple document formats."""
    text = ""
    try:
        if file_name.endswith(".txt"):
            text = raw_bytes.decode("utf-8", errors="ignore")
        elif file_name.endswith(".docx"):
            doc = Document(io.BytesIO(raw_bytes))
            text = "\n".join([p.text for p in doc.paragraphs])
        elif file_name.endswith(".pdf"):
            reader = PyPDF2.PdfReader(io.BytesIO(raw_bytes))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif file_name.endswith(".xlsx"):
            wb = openpyxl.load_workbook(io.BytesIO(raw_bytes), data_only=True)
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    text += " ".join([str(cell) if cell is not None else "" for cell in row]) + "\n"
        elif file_name.endswith(".pptx"):
            prs = Presentation(io.BytesIO(raw_bytes))
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
    except Exception as e:
        logger.warning(f"⚠ Failed to extract text from {file_name}: {e}")
    return text.strip()

async def summarize_and_store(output_filename: str = SUMMARY_FILENAME) -> str:
    """
    Summarize all documents in DOCS_BUCKET → OpenRouter → upload summary to SUMMARY_BUCKET.
    """
    try:
        supabase = get_supabase_client()

        logger.info(f"⬇ Listing all files in DOCS_BUCKET...")
        files_list = supabase.storage.from_(DOCS_BUCKET).list()
        if not files_list:
            logger.warning("⚠ No files found in DOCS_BUCKET")
            return ""

        # Download and combine all files
        combined_text = ""
        for file_obj in files_list:
            file_name = file_obj["name"]
            logger.info(f"⬇ Downloading {file_name}...")
            raw_data = supabase.storage.from_(DOCS_BUCKET).download(file_name)
            if raw_data:
                text = extract_text(file_name, raw_data)
                if text:
                    combined_text += text + "\n\n"

        if not combined_text.strip():
            logger.warning("⚠ All files in DOCS_BUCKET were empty or unsupported")
            return ""

        # ---- Chunk docs to avoid token limits ----
        CHUNK_SIZE = 3000
        chunks = [combined_text[i:i+CHUNK_SIZE] for i in range(0, len(combined_text), CHUNK_SIZE)]
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
                                "content": (
                                    "Summarize this document into clear Markdown with sections: "
                                    "Personnel, Departments, Events, Locations, Contact Info. "
                                    "Preserve names and titles."
                                )
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

        # Upload summary to SUMMARY_BUCKET
        logger.info(f"⬆ Uploading {output_filename} to SUMMARY_BUCKET...")
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
