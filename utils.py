# utils.py
import os
import aiofiles
import httpx
from supabase import create_client, Client

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
# Summarize docs and store
# -------------------------
async def summarize_and_store():
    """
    Streams documents from Supabase DOCS_BUCKET,
    summarizes them in chunks with OpenRouter,
    then saves the final summarized_text.md into SUMMARY_BUCKET.
    """
    supabase = get_supabase_client()

    # List all files in chatbot-docs
    files = supabase.storage.from_(DOCS_BUCKET).list()
    if not files:
        print("[utils] No files found in chatbot-docs bucket")
        return

    # Collect and stream text content chunk by chunk
    collected_summary_parts = []

    async with httpx.AsyncClient(timeout=None) as client:
        for file in files:
            file_name = file["name"]
            print(f"[utils] Downloading {file_name}...")

            # Download each file
            raw_bytes = supabase.storage.from_(DOCS_BUCKET).download(file_name)
            text = raw_bytes.decode("utf-8", errors="ignore")

            # Split into safe chunks (4k chars each to avoid token issues)
            chunk_size = 4000
            chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

            for idx, chunk in enumerate(chunks, 1):
                prompt = (
                    "Summarize the following text into clear, structured bullet points. "
                    "Group information under categories like Personnel, Departments, "
                    "Events, Locations, and Contact Info. Keep names and titles intact.\n\n"
                    f"---\n{chunk}\n---"
                )

                # Send chunk to OpenRouter
                try:
                    response = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "openai/gpt-oss-20b:free",
                            "messages": [{"role": "user", "content": prompt}],
                        },
                    )
                    data = response.json()
                    summary_text = data["choices"][0]["message"]["content"]
                    print(f"[utils] Summarized chunk {idx}/{len(chunks)} of {file_name}")
                    collected_summary_parts.append(summary_text)
                except Exception as e:
                    print(f"[utils] Error summarizing chunk {idx} of {file_name}: {e}")

    # Join all summaries into one markdown
    final_summary = "\n\n".join(collected_summary_parts)

    # Upload to Supabase summarized-text bucket
    try:
        supabase.storage.from_(SUMMARY_BUCKET).upload(
            SUMMARY_FILENAME,
            final_summary.encode("utf-8"),
            {"content-type": "text/markdown"},
        )
        print(f"[utils] Uploaded summarized_text.md to {SUMMARY_BUCKET}")
    except Exception as e:
        print(f"[utils] Failed to upload summary: {e}")
