from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import asyncio

# Initialize FastAPI app
app = FastAPI(title="Tomas Chatbot API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatbot")

# ---------------------
# Placeholder Chatbot
# ---------------------
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    query = data.get("query", "")
    if not query:
        return JSONResponse(content={"error": "No query provided"}, status_code=400)
    
    # TODO: Replace with your chatbot logic
    response_text = f"Received query: {query}"
    return {"response": response_text}

# ---------------------
# Reload summarized docs
# ---------------------
@app.post("/admin/reload")
async def reload_sources():
    try:
        logger.info("Reloading sources...")

        # TODO: Replace with your actual document summarization logic
        await asyncio.sleep(1)  # Simulate async work

        logger.info("Sources reloaded successfully")
        return {"message": "Sources reloaded successfully"}
    except Exception as e:
        logger.error(f"Failed to reload sources: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ---------------------
# Admin logs route (optional)
# ---------------------
@app.get("/admin/logs")
async def get_logs():
    # Placeholder: replace with actual log retrieval if needed
    return {"logs": "No logs available"}

# ---------------------
# Root route
# ---------------------
@app.get("/")
async def root():
    return {"message": "Tomas Chatbot API is running"}
