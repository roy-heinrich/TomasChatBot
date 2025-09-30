#!/usr/bin/env python3
"""
Simple version of the chatbot for deployment without heavy dependencies
This version works without sentence-transformers and scikit-learn
"""

import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Tomas Chatbot - Simple Version", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000", 
        "http://localhost:8080",
        "http://localhost:5000",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080", 
        "http://127.0.0.1:5000",
        "http://127.0.0.1:8000",
        "https://tomaschatbot.onrender.com",
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    conversation_history: Optional[List[Dict]] = None
    user_timezone: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: List[str]
    detected_language: str
    language_confidence: float
    entities: List[Dict]
    intent: str
    is_split: bool
    message_count: int

@app.get("/")
async def root():
    return {
        "message": "Tomas Chatbot API is running!",
        "status": "healthy",
        "version": "simple"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Chatbot API is running",
        "version": "simple",
        "dependencies": {
            "fastapi": "✅",
            "supabase": "✅" if os.environ.get("SUPABASE_URL") else "❌",
            "groq": "✅" if os.environ.get("GROQ_API_KEY") else "❌",
            "sentence_transformers": "❌ (simple mode)",
            "scikit_learn": "❌ (simple mode)"
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Simple chat endpoint that works without heavy dependencies"""
    
    try:
        # Simple response without ML processing
        message = request.query.lower()
        
        # Basic keyword matching for common queries
        if any(word in message for word in ["bathroom", "cr", "comfort room", "banyo", "restroom"]):
            response = "Our comfort room (CR or banyo) is located inside the administration building. It's easily accessible for students and staff."
        elif any(word in message for word in ["enrollment", "enroll", "register"]):
            response = "For enrollment information, please visit our school office or contact our staff. They can provide you with the latest enrollment requirements and procedures."
        elif any(word in message for word in ["principal", "head teacher"]):
            response = "Our Head Teacher is Ma'am Meliza A. Delgado. She leads our school and is always ready to help parents and students with their needs."
        elif any(word in message for word in ["hours", "time", "schedule"]):
            response = "Our school hours are from 7:00 AM to 4:00 PM. For specific schedule information, please contact our office."
        elif any(word in message for word in ["hello", "hi", "hey", "kamusta", "kumusta"]):
            response = "Hello! I'm Tomas, your school assistant. How can I help you today?"
        else:
            response = "Thank you for your question! For more specific information, please visit our school office or contact our staff. They will be happy to help you with any inquiries about our school."
        
        return ChatResponse(
            response=[response],
            detected_language="en",
            language_confidence=0.8,
            entities=[],
            intent="general_inquiry",
            is_split=False,
            message_count=1
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(
            response=["I apologize, but I'm experiencing some technical difficulties. Please try again later or contact our school office for assistance."],
            detected_language="en",
            language_confidence=0.5,
            entities=[],
            intent="error",
            is_split=False,
            message_count=1
        )

@app.post("/clear-context")
async def clear_context():
    """Clear conversation context"""
    return {"message": "Context cleared successfully"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
