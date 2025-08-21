import os
import sys
import hashlib
import asyncio
from pathlib import Path
import logging
from typing import List, Tuple, Optional

import aiohttp
import aiofiles

# NOTE: these libraries are blocking. We'll call them inside asyncio.to_thread.
import fitz  # PyMuPDF
from docx import Document
from pptx import Presentation
import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------- Configuration ----------
KB_PATH = Path("./docs")
SUMMARY_FOLDER = KB_PATH / "SummarizedText"
SUMMARY_FILE = SUMMARY_FOLDER / "summarized_text.txt"
HASH_FILE = SUMMARY_FOLDER / ".kb_hash"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# FastText model path (lazy load)
_FASTTEXT_MODEL_PATH = None  # optionally set to a path, else resource_path used
_fasttext_model = None

# Live agent keywords (lowercase)
LIVE_AGENT_KEYWORDS = [
    "live agent", "live person", "talk to someone",
    "talk to a person", "human", "tao", "gusto ko ng tao",
    "kausapin ko ang admin", "kausap na admin", "agent", "representative"
]


# ---------- Small helpers ----------
def resource_path(relative_path: str) -> str:
    """Return absolute path for PyInstaller or normal runs."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


async def run_in_thread(fn, *args, **kwargs):
    """Helper to run blocking code in a threadpool."""
    return await asyncio.to_thread(fn, *args, **kwargs)


# ---------- File extraction (blocking code executed in thread) ----------
def _extract_text_from_pdf_sync(path: str) -> str:
    doc = fitz.open(path)
    texts = []
    for page in doc:
        texts.append(page.get_text())
    doc.close()
    return "\n".join(texts)


def _extract_text_from_docx_sync(path: str) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def _extract_text_from_pptx_sync(path: str) -> str:
    prs = Presentation(path)
    pieces = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text:
                pieces.append(shape.text)
    return "\n".join(pieces)


def _extract_text_from_csv_sync(path: str) -> str:
    df = pd.read_csv(path)
    return df.to_string(index=False)


def _extract_text_from_txt_sync(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


async def extract_text_from_file(path: str) -> str:
    """Async wrapper to extract text from supported file types."""
    path = str(path)
    if path.endswith(".pdf"):
        return await run_in_thread(_extract_text_from_pdf_sync, path)
    if path.endswith(".docx"):
        return await run_in_thread(_extract_text_from_docx_sync, path)
    if path.endswith(".pptx"):
        return await run_in_thread(_extract_text_from_pptx_sync, path)
    if path.endswith(".csv"):
        return await run_in_thread(_extract_text_from_csv_sync, path)
    if path.endswith(".txt"):
        return await run_in_thread(_extract_text_from_txt_sync, path)
    return ""


async def extract_docs_from_folder(folder_path: str = None) -> Tuple[List[str], List[dict], List[str]]:
    """
    Walk folder_path, extract text from supported files and return:
      (docs, metadatas, ids)
    This function is async-safe; heavy work is delegated to threads.
    """
    folder = Path(folder_path or KB_PATH)
    docs, metadatas, ids = [], [], []
    supported_extensions = (".pdf", ".docx", ".pptx", ".csv", ".txt")

    if not folder.exists():
        return docs, metadatas, ids

    for root, _, files in os.walk(folder):
        # skip summarized folder
        if "SummarizedText" in Path(root).parts:
            continue

        for f in sorted(files):
            if not f.lower().endswith(supported_extensions):
                continue
            fpath = os.path.join(root, f)
            try:
                text = await extract_text_from_file(fpath)
                if text and text.strip():
                    docs.append(text)
                    metadatas.append({"source": f})
                    ids.append(f"{f}-{len(docs)}")
            except Exception as e:
                logger.warning(f"Failed to extract {fpath}: {e}")

    return docs, metadatas, ids


# ---------- Text utilities ----------
def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping word chunks."""
    if not text:
        return []
    words = text.split()
    if chunk_size <= 0:
        return [text]
    chunks = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


# ---------- Change detection ----------
def compute_kb_hash(folder: str = None) -> str:
    """
    Compute a SHA256 hash representing current KB files (text and modification times).
    Deterministic ordering is enforced.
    """
    folder = Path(folder or KB_PATH)
    sha = hashlib.sha256()

    if not folder.exists():
        return sha.hexdigest()

    file_list = []
    for root, _, files in os.walk(folder):
        # skip SummarizedText
        if "SummarizedText" in Path(root).parts:
            continue
        for fname in sorted(files):
            if fname.startswith(".") or fname.startswith("~"):
                continue
            p = Path(root) / fname
            try:
                stat = p.stat()
                file_list.append(f"{p.relative_to(folder)}:{stat.st_size}:{int(stat.st_mtime)}")
            except Exception:
                continue

    for entry in sorted(file_list):
        sha.update(entry.encode("utf-8"))

    return sha.hexdigest()


# ---------- FastText (lazy) ----------
def _ensure_fasttext_loaded(model_path: Optional[str] = None):
    """Lazy-load fasttext model on first use."""
    global _fasttext_model, _FASTTEXT_MODEL_PATH
    if _fasttext_model is not None:
        return

    # allow override via argument or env
    if model_path:
        _FASTTEXT_MODEL_PATH = model_path
    if not _FASTTEXT_MODEL_PATH:
        _FASTTEXT_MODEL_PATH = resource_path("lid.176.ftz")

    try:
        import fasttext as _ft  # local import to avoid at module load time
        _fasttext_model = _ft.load_model(_FASTTEXT_MODEL_PATH)
        logger.info("Loaded FastText language model.")
    except Exception as e:
        logger.warning(f"Could not load fasttext model: {e}")
        _fasttext_model = None


def detect_language_fasttext(text: str) -> Tuple[str, float]:
    """
    Detect language using fastText (lazy-loaded).
    Returns (lang_code, confidence). Adds small Tagalog heuristic.
    """
    _ensure_fasttext_loaded()
    if not _fasttext_model:
        # fallback naive heuristic
        tagalog_keywords = {'po', 'nga', 'ulit', 'saan', 'kailan', 'paano', 'bakit', 'ay', 'si', 'ang', 'sa', 'ni', 'ng'}
        words = set(w.lower() for w in text.split())
        tag_score = len(words.intersection(tagalog_keywords))
        if tag_score >= 2:
            return "tl", 0.9
        return "en", 0.6

    try:
        labels, scores = _fasttext_model.predict(text.replace("\n", " ").strip().lower(), k=1)
        lang_code = labels[0].replace("__label__", "")
        conf = float(scores[0])
    except Exception:
        return "en", 0.6

    # heuristic override for Tagalog-like texts
    tagalog_keywords = {'po', 'nga', 'ulit', 'saan', 'kailan', 'paano', 'bakit', 'ay', 'si', 'ang', 'sa', 'ni', 'ng'}
    words = set(w.lower() for w in text.split())
    if lang_code == "en" and len(words.intersection(tagalog_keywords)) >= 2:
        return "tl", 0.99

    return lang_code, conf


# ---------- OpenRouter summarization (async) ----------
async def summarize_documents_via_openrouter(
    input_folder: str = None,
    output_file: str = None,
    force: bool = False,
    model: str = "openrouter/anthropic/claude-3-haiku",
    max_chars: int = 12000
) -> bool:
    """
    Summarize all documents in input_folder and save to output_file.
    Uses change-detection: if the KB hash matches saved hash and force is False, skips summarization.
    Returns True if summary was written (or already up-to-date), False on failure.
    """
    input_folder = Path(input_folder or KB_PATH)
    output_file = Path(output_file or SUMMARY_FILE)
    hash_file = Path(HASH_FILE)

    # compute current hash
    current_hash = await asyncio.to_thread(compute_kb_hash, input_folder)

    # skip if unchanged
    if hash_file.exists() and not force:
        async with aiofiles.open(hash_file, "r") as f:
            old_hash = (await f.read()).strip()
        if old_hash == current_hash and output_file.exists():
            logger.info("KB unchanged — skipping summarization.")
            return True

    # gather docs (async)
    docs, _, _ = await extract_docs_from_folder(str(input_folder))
    combined_text = "\n\n".join(docs)

    if not combined_text.strip():
        logger.warning("No content found to summarize.")
        await _write_summary_file(output_file, "Summary failed.")
        await _write_hash_file(hash_file, current_hash)
        return False

    # truncate for safety
    combined_text = combined_text[:max_chars]
    # craft prompt(s)
    system_msg = "You are an assistant that summarizes knowledge base documents for a helpful school chatbot. Keep details, names, and contact info when present. Produce a concise summary suitable for inclusion in an assistant context."
    user_msg = f"Please summarize the following knowledge base content. Keep it factual, grouped by categories if appropriate, and keep names/titles intact:\n\n{combined_text}"

    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY not set in environment.")
        return False

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        "max_tokens": 1200,
        "temperature": 0.0
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_URL, json=payload, headers=headers, timeout=120) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"OpenRouter summarization failed ({resp.status}): {text}")
                    return False
                data = await resp.json()

        # extract content (compat tolerant)
        summary = None
        try:
            # openrouter style: choices[0].message.content
            summary = data.get("choices", [{}])[0].get("message", {}).get("content")
        except Exception:
            pass
        if not summary:
            # fallback: try top-level 'response' or choices[0].text
            summary = data.get("response") or (data.get("choices", [{}])[0].get("text") if data.get("choices") else None)

        if not summary:
            logger.error("OpenRouter returned no usable summary payload.")
            return False

        # write summary and hash
        await _write_summary_file(output_file, summary)
        await _write_hash_file(hash_file, current_hash)
        logger.info(f"Summary saved to {output_file}")
        return True

    except Exception as e:
        logger.exception(f"Error calling OpenRouter: {e}")
        return False


async def _write_summary_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(content)


async def _write_hash_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(content)


# ---------- Convenience: synchronous wrapper for older code ----------
def summarize_documents_sync(*args, **kwargs) -> bool:
    """Run the async summarizer from sync code (blocking)."""
    return asyncio.run(summarize_documents_via_openrouter(*args, **kwargs))


