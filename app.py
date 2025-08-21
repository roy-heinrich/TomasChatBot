import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from chatbot import ChatBotApp
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

app = FastAPI()

# Allow all origins (adjust for production if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost"] for stricter
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize chatbot
chatbot = ChatBotApp()

@app.on_event("startup")
async def startup_event():
    logger.info("Loading summary into ChromaDB...")
    await chatbot.load_summary_into_chroma()
    logger.info("Startup complete.")

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    message = data.get("message", "")
    context = data.get("context", "")
    try:
        response_text = await chatbot.get_response(message, context)
        return {"response": response_text}
    except Exception as e:
        logger.exception("Error in /chat endpoint")
        return {"response": f"Error: {str(e)}"}

@app.get("/admin/reload")
async def reload_sources():
    try:
        logger.info("Reloading documents and regenerating summary...")

        # Summarize docs and overwrite summarized_text.txt
        summary_text = await chatbot.summarize_docs()
    
        # Reload into ChromaDB
        await chatbot.load_summary_into_chroma()

        return {
            "message": "Sources reloaded successfully.",
            "content": summary_text  # Return updated content as well
        }
    except Exception as e:
        logger.exception("Error while reloading sources")
        return {"message": f"Reload failed: {str(e)}", "content": ""}
        
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))  # Render sets PORT env
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
