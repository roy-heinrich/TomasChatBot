#!/usr/bin/env python3
"""
Embedding Population Script for TOMAS Chatbot
Populates vector embeddings for existing database records
"""
import asyncio
import os
import sys
import logging
from typing import List, Dict, Any
import numpy as np
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import aiohttp
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingPopulator:
    """Populates embeddings for existing chatbot prompts"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Initialize embedding model
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.embedding_dimension = 384
        logger.info("✅ Embedding model loaded successfully")
        
    async def populate_all_embeddings(self):
        """Populate embeddings for all records that don't have them"""
        try:
            # Get all records without embeddings
            result = self.supabase.table("chatbot_prompts") \
                .select("id, keywords, response") \
                .is_("embedding", "null") \
                .execute()
            
            if not result.data:
                logger.info("✅ All records already have embeddings")
                return
            
            logger.info(f"📊 Found {len(result.data)} records without embeddings")
            
            # Process in batches to avoid memory issues
            batch_size = 16  # Smaller batch size for stability
            total_batches = (len(result.data) + batch_size - 1) // batch_size
            
            for i in range(0, len(result.data), batch_size):
                batch = result.data[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                logger.info(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} records)")
                
                # Prepare texts for embedding
                texts = []
                for item in batch:
                    # Combine keywords and response for better semantic understanding
                    combined_text = f"{item['keywords']} {item['response']}"
                    texts.append(combined_text)
                
                # Generate embeddings
                try:
                    embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
                    logger.info(f"✅ Generated {len(embeddings)} embeddings for batch {batch_num}")
                    
                    # Update database with embeddings
                    for j, item in enumerate(batch):
                        if j < len(embeddings):
                            try:
                                # Convert numpy array to list for JSON serialization
                                embedding_list = embeddings[j].tolist()
                                
                                # Update the record
                                update_result = self.supabase.table("chatbot_prompts") \
                                    .update({"embedding": embedding_list}) \
                                    .eq("id", item["id"]) \
                                    .execute()
                                
                                if update_result.data:
                                    logger.info(f"✅ Updated embedding for record {item['id']}")
                                else:
                                    logger.warning(f"⚠️ Failed to update record {item['id']}")
                                    
                            except Exception as e:
                                logger.error(f"❌ Error updating record {item['id']}: {e}")
                    
                except Exception as e:
                    logger.error(f"❌ Error generating embeddings for batch {batch_num}: {e}")
                    continue
                
                # Small delay between batches to avoid overwhelming the system
                await asyncio.sleep(0.5)
            
            logger.info("🎉 Embedding population completed!")
            
        except Exception as e:
            logger.error(f"❌ Error in populate_all_embeddings: {e}")
    
    async def verify_embeddings(self):
        """Verify that embeddings were populated correctly"""
        try:
            # Check how many records have embeddings
            result = self.supabase.table("chatbot_prompts") \
                .select("id, keywords") \
                .not_.is_("embedding", "null") \
                .execute()
            
            total_result = self.supabase.table("chatbot_prompts") \
                .select("id") \
                .execute()
            
            if result.data and total_result.data:
                percentage = (len(result.data) / len(total_result.data)) * 100
                logger.info(f"📊 Embedding Status: {len(result.data)}/{len(total_result.data)} records have embeddings ({percentage:.1f}%)")
                
                if percentage == 100:
                    logger.info("✅ All records have embeddings!")
                else:
                    logger.warning(f"⚠️ {len(total_result.data) - len(result.data)} records still missing embeddings")
            
        except Exception as e:
            logger.error(f"❌ Error verifying embeddings: {e}")

async def main():
    """Main function to populate embeddings"""
    
    # Get environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("❌ Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        logger.info("Please set them in your .env file or environment")
        return
    
    logger.info("🚀 Starting embedding population process...")
    
    # Initialize populator
    populator = EmbeddingPopulator(supabase_url, supabase_key)
    
    # Populate embeddings
    await populator.populate_all_embeddings()
    
    # Verify results
    await populator.verify_embeddings()
    
    logger.info("🎉 Embedding population process completed!")

if __name__ == "__main__":
    asyncio.run(main())
