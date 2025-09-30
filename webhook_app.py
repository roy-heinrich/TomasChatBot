#!/usr/bin/env python3
"""
Webhook App for Auto Embedding Generation
Standalone webhook server for deployment
"""
import os
import json
import logging
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import gc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Auto Embedding Webhook", version="1.0.0")

# Global model instance (loaded once)
_model = None

def get_embedding_model():
    """Get or load the embedding model"""
    global _model
    if _model is None:
        try:
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("🧠 Embedding model loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            return None
    return _model

def generate_embedding(text: str) -> list:
    """Generate embedding for text"""
    try:
        model = get_embedding_model()
        if not model:
            return None
        
        # Generate embedding
        embedding = model.encode([text], convert_to_tensor=False)
        return embedding[0].tolist()
        
    except Exception as e:
        logger.error(f"❌ Error generating embedding: {e}")
        return None

@app.post("/webhook/embedding")
async def handle_embedding_webhook(request: Request):
    """Handle Supabase webhook for new records"""
    try:
        # Get the webhook payload
        payload = await request.json()
        logger.info(f"📨 Received webhook: {payload.get('type', 'unknown')}")
        
        # Check if this is a new record
        if payload.get('type') == 'INSERT':
            record = payload.get('record', {})
            record_id = record.get('id')
            keywords = record.get('keywords', '')
            response = record.get('response', '')
            
            if record_id and (keywords or response):
                # Combine text for embedding
                combined_text = f"{keywords} {response}".strip()
                
                if combined_text:
                    logger.info(f"🔄 Generating embedding for record {record_id}")
                    
                    # Generate embedding
                    embedding = generate_embedding(combined_text)
                    
                    if embedding:
                        # Initialize Supabase client
                        supabase_url = os.getenv("SUPABASE_URL")
                        supabase_key = os.getenv("SUPABASE_KEY")
                        
                        if supabase_url and supabase_key:
                            supabase = create_client(supabase_url, supabase_key)
                            
                            # Update record with embedding
                            result = supabase.table("chatbot_prompts") \
                                .update({"embedding": embedding}) \
                                .eq("id", record_id) \
                                .execute()
                            
                            if result.data:
                                logger.info(f"✅ Generated and saved embedding for record {record_id}")
                                return {"status": "success", "record_id": record_id}
                            else:
                                logger.error(f"❌ Failed to save embedding for record {record_id}")
                                return {"status": "error", "message": "Failed to save embedding"}
                        else:
                            logger.error("❌ Supabase credentials not configured")
                            return {"status": "error", "message": "Supabase not configured"}
                    else:
                        logger.error(f"❌ Failed to generate embedding for record {record_id}")
                        return {"status": "error", "message": "Failed to generate embedding"}
                else:
                    logger.warning(f"⚠️ No text content for record {record_id}")
                    return {"status": "skipped", "message": "No text content"}
            else:
                logger.warning("⚠️ Invalid record data in webhook")
                return {"status": "skipped", "message": "Invalid record data"}
        else:
            logger.info(f"ℹ️ Webhook type {payload.get('type')} - no action needed")
            return {"status": "skipped", "message": "Not an INSERT operation"}
            
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "embedding-webhook"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Auto Embedding Webhook Server", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
