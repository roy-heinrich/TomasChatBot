# utils.py
import os
import io
from supabase import create_client, Client

# File readers
import docx2txt
import PyPDF2
import openpyxl
from pptx import Presentation

# -------------------------
# Shared Supabase constants
# -------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DOCS_BUCKET = "chatbot-docs"
SUMMARY_BUCKET = "summarized-text"
SUMMARY_FILENAME = "summarized_text.md"

# -------------------------
# Create Supabase client
# -------------------------
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# Fetch summarized text
# -------------------------
async def fetch_summarized_text() -> str:
    """
    Downloads the summarized_text.md file from Supabase.
    Returns the content as a string, or empty string if missing.
    """
    supabase = get_supabase_client()
    try:
        resp = supabase.storage.from_(SUMMARY_BUCKET).download(SUMMARY_FILENAME)
        return resp.decode("utf-8")
    except Exception as e:
        print(f"[utils] No summarized_text.md found: {e}")
        return ""

# -------------------------
# Extract text helpers
# -------------------------
def extract_text(filename: str, file_bytes: bytes) -> str:
    text = ""
    if filename.endswith(".pdf"):
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    elif filename.endswith(".docx"):
        temp_path = f"/tmp/{filename}"
        with open(temp_path, "wb") as f:
            f.write(file_bytes)
        text = docx2txt.process(temp_path)
        os.remove(temp_path)
    elif filename.endswith(".pptx"):
        prs = Presentation(io.BytesIO(file_bytes))
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
    elif filename.endswith(".xlsx"):
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes))
        for sheet in wb:
            for row in sheet.iter_rows(values_only=True):
                text += " ".join([str(cell) if cell else "" for cell in row]) + "\n"
    elif filename.endswith(".txt") or filename.endswith(".md"):
        text = file_bytes.decode("utf-8", errors="ignore")
    else:
        text = f"[utils] Unsupported file type: {filename}\n"
    return text.strip()

# -------------------------
# Compile docs and store
# -------------------------
async def summarize_and_store():
    """
    Reads documents from Supabase DOCS_BUCKET,
    extracts text without AI summarization,
    and saves compiled summarized_text.md into SUMMARY_BUCKET.
    """
    supabase = get_supabase_client()

    # List all files in chatbot-docs
    files = supabase.storage.from_(DOCS_BUCKET).list()
    if not files:
        print("[utils] No files found in chatbot-docs bucket")
        return

    compiled_parts = []

    for file in files:
        file_name = file["name"]
        print(f"[utils] Downloading {file_name}...")

        try:
            raw_bytes = supabase.storage.from_(DOCS_BUCKET).download(file_name)
            text = extract_text(file_name, raw_bytes)
            if text:
                compiled_parts.append(f"## {file_name}\n\n{text}")
        except Exception as e:
            print(f"[utils] Failed to process {file_name}: {e}")

    # Join all extracted text
    final_summary = "\n\n---\n\n".join(compiled_parts)

    # Upload to Supabase summarized-text bucket (with overwrite)
    try:
        supabase.storage.from_(SUMMARY_BUCKET).upload(
            SUMMARY_FILENAME,
            final_summary.encode("utf-8"),
            {
                "content-type": "text/markdown"
            },
            upsert=True   # ✅ This ensures overwrite instead of duplicate error
        )
        print(f"[utils] Uploaded summarized_text.md to {SUMMARY_BUCKET} (overwrite mode)")
    except Exception as e:
        print(f"[utils] Failed to upload summary: {e}")