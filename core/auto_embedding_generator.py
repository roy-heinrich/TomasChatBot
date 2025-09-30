"""
Auto Embedding Generator
Automatically generates embeddings for new database records
"""
import os
import logging
import asyncio
from typing import List, Dict, Optional, Any
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import gc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AutoEmbeddingGenerator:
    """Automatically generates embeddings for new database records"""
    
    def __init__(self):
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.model = None
        self.model_loaded = False
        
        logger.info("✅ Auto embedding generator initialized")
    
    def _load_model_if_needed(self):
        """Load model only when needed to save memory"""
        if not self.model_loaded:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                self.model_loaded = True
                logger.info("🧠 Embedding model loaded")
                
                # Force garbage collection to free memory
                gc.collect()
                
            except Exception as e:
                logger.error(f"❌ Failed to load embedding model: {e}")
                self.model = None
                self.model_loaded = False
    
    def _unload_model(self):
        """Unload model to free memory when not needed"""
        if self.model_loaded:
            self.model = None
            self.model_loaded = False
            gc.collect()
            logger.info("🧹 Embedding model unloaded to free memory")
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        try:
            self._load_model_if_needed()
            
            if not self.model:
                logger.warning("⚠️ Embedding model not available")
                return None
            
            # Generate embedding
            embedding = self.model.encode([text], convert_to_tensor=False)
            
            # Unload model immediately to free memory
            self._unload_model()
            
            return embedding[0].tolist()
            
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            self._unload_model()
            return None
    
    async def process_new_record(self, record_id: int, keywords: str, response: str):
        """Process a new record and generate embedding"""
        try:
            # Combine keywords and response for embedding
            combined_text = f"{keywords} {response}".strip()
            
            if not combined_text:
                logger.warning(f"⚠️ No text content for record {record_id}")
                return False
            
            # Generate embedding
            embedding = await self.generate_embedding(combined_text)
            
            if embedding is None:
                logger.error(f"❌ Failed to generate embedding for record {record_id}")
                return False
            
            # Update the record with embedding
            result = self.supabase.table("chatbot_prompts") \
                .update({"embedding": embedding}) \
                .eq("id", record_id) \
                .execute()
            
            if result.data:
                logger.info(f"✅ Generated and saved embedding for record {record_id}")
                return True
            else:
                logger.error(f"❌ Failed to save embedding for record {record_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error processing record {record_id}: {e}")
            return False
    
    async def process_records_without_embeddings(self):
        """Process all records that don't have embeddings yet"""
        try:
            # Get records without embeddings
            result = self.supabase.table("chatbot_prompts") \
                .select("id, keywords, response") \
                .is_("embedding", "null") \
                .execute()
            
            if not result.data:
                logger.info("✅ All records already have embeddings")
                return True
            
            logger.info(f"🔄 Processing {len(result.data)} records without embeddings...")
            
            success_count = 0
            for record in result.data:
                success = await self.process_new_record(
                    record['id'], 
                    record.get('keywords', ''), 
                    record.get('response', '')
                )
                if success:
                    success_count += 1
            
            logger.info(f"✅ Processed {success_count}/{len(result.data)} records successfully")
            return success_count == len(result.data)
            
        except Exception as e:
            logger.error(f"❌ Error processing records: {e}")
            return False
    
    async def monitor_new_records(self, check_interval: int = 30):
        """Monitor for new records and generate embeddings automatically"""
        logger.info(f"🔄 Starting auto embedding monitor (checking every {check_interval}s)")
        
        while True:
            try:
                # Check for new records without embeddings
                result = self.supabase.table("chatbot_prompts") \
                    .select("id, keywords, response") \
                    .is_("embedding", "null") \
                    .execute()
                
                if result.data:
                    logger.info(f"🆕 Found {len(result.data)} new records without embeddings")
                    
                    for record in result.data:
                        await self.process_new_record(
                            record['id'], 
                            record.get('keywords', ''), 
                            record.get('response', '')
                        )
                
                # Wait before next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(check_interval)

async def main():
    """Main function for testing"""
    generator = AutoEmbeddingGenerator()
    
    # Process any existing records without embeddings
    await generator.process_records_without_embeddings()
    
    # Start monitoring for new records
    await generator.monitor_new_records()

if __name__ == "__main__":
    asyncio.run(main())
