#!/usr/bin/env python3
"""
Auto Embedding System
Background service for automatic embedding generation
"""
import os
import sys
import asyncio
import logging
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_auto_embedding_system():
    """Run the auto embedding system"""
    try:
        from core.auto_embedding_generator import AutoEmbeddingGenerator
        
        generator = AutoEmbeddingGenerator()
        
        # Process any existing records without embeddings
        logger.info("🔄 Processing existing records without embeddings...")
        await generator.process_records_without_embeddings()
        
        # Start monitoring for new records
        logger.info("🔄 Starting auto embedding monitor...")
        await generator.monitor_new_records(check_interval=30)
        
    except KeyboardInterrupt:
        logger.info("🛑 Auto embedding system stopped by user")
    except Exception as e:
        logger.error(f"❌ Auto embedding system error: {e}")
        sys.exit(1)

def run_webhook_server():
    """Run the webhook server"""
    try:
        import uvicorn
        from core.webhook_embedding_generator import app
        
        logger.info("🚀 Starting embedding webhook server...")
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8001,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"❌ Webhook server error: {e}")
        sys.exit(1)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Auto Embedding System")
    parser.add_argument(
        "--mode", 
        choices=["monitor", "webhook", "process"], 
        default="monitor",
        help="Run mode: monitor (background), webhook (server), or process (one-time)"
    )
    parser.add_argument(
        "--check-interval", 
        type=int, 
        default=30,
        help="Check interval in seconds for monitor mode"
    )
    
    args = parser.parse_args()
    
    if args.mode == "monitor":
        logger.info("🔄 Starting auto embedding monitor...")
        asyncio.run(run_auto_embedding_system())
        
    elif args.mode == "webhook":
        logger.info("🚀 Starting webhook server...")
        run_webhook_server()
        
    elif args.mode == "process":
        logger.info("🔄 Processing existing records...")
        asyncio.run(process_existing_records())
    
    else:
        logger.error("❌ Invalid mode specified")
        sys.exit(1)

async def process_existing_records():
    """Process existing records without embeddings"""
    try:
        from core.auto_embedding_generator import AutoEmbeddingGenerator
        
        generator = AutoEmbeddingGenerator()
        success = await generator.process_records_without_embeddings()
        
        if success:
            logger.info("✅ All records processed successfully")
        else:
            logger.error("❌ Some records failed to process")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Error processing records: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
