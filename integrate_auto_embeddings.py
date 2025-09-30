"""
Integrate Auto Embeddings into Main Chatbot
Simple integration script to add auto embedding functionality
"""
import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def integrate_auto_embeddings():
    """Integrate auto embedding functionality into the main chatbot"""
    
    # Add auto embedding import to chatbot_refactored.py
    chatbot_file = "chatbot_refactored.py"
    
    if os.path.exists(chatbot_file):
        with open(chatbot_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if auto embedding is already integrated
        if "AutoEmbeddingGenerator" in content:
            logger.info("✅ Auto embedding already integrated")
            return True
        
        # Add import statement
        import_line = "from core.auto_embedding_generator import AutoEmbeddingGenerator"
        
        # Find the import section and add the new import
        lines = content.split('\n')
        import_section_end = 0
        
        for i, line in enumerate(lines):
            if line.startswith('from core.') and 'import' in line:
                import_section_end = i + 1
        
        # Insert the new import
        lines.insert(import_section_end, import_line)
        
        # Add auto embedding generator to ChatBot class
        init_section = None
        for i, line in enumerate(lines):
            if "def __init__(self, groq_key: str):" in line:
                init_section = i
                break
        
        if init_section:
            # Find the end of __init__ method
            init_end = init_section
            for i in range(init_section, len(lines)):
                if lines[i].strip() == "" and i > init_section + 10:
                    init_end = i
                    break
            
            # Add auto embedding generator initialization
            auto_embedding_init = """        
        # Initialize auto embedding generator
        self.auto_embedding = AutoEmbeddingGenerator()"""
            
            lines.insert(init_end, auto_embedding_init)
        
        # Write the updated content
        updated_content = '\n'.join(lines)
        
        with open(chatbot_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logger.info("✅ Auto embedding integrated into chatbot")
        return True
    
    else:
        logger.error(f"❌ Chatbot file {chatbot_file} not found")
        return False

async def test_auto_embeddings():
    """Test the auto embedding functionality"""
    try:
        from core.auto_embedding_generator import AutoEmbeddingGenerator
        
        generator = AutoEmbeddingGenerator()
        
        # Test processing existing records
        logger.info("🧪 Testing auto embedding functionality...")
        success = await generator.process_records_without_embeddings()
        
        if success:
            logger.info("✅ Auto embedding test successful")
            return True
        else:
            logger.error("❌ Auto embedding test failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Auto embedding test error: {e}")
        return False

def main():
    """Main integration function"""
    logger.info("🚀 Integrating auto embeddings into chatbot...")
    
    # Integrate auto embeddings
    if integrate_auto_embeddings():
        logger.info("✅ Auto embeddings integrated successfully")
        
        # Test the integration
        logger.info("🧪 Testing auto embedding functionality...")
        test_result = asyncio.run(test_auto_embeddings())
        
        if test_result:
            logger.info("🎉 Auto embedding integration complete!")
            logger.info("📋 Next steps:")
            logger.info("1. Run 'python auto_embedding_system.py --mode monitor' to start background processing")
            logger.info("2. Or run 'python auto_embedding_system.py --mode webhook' to start webhook server")
            logger.info("3. Add new records to Supabase and they will automatically get embeddings!")
        else:
            logger.error("❌ Auto embedding integration failed")
    else:
        logger.error("❌ Failed to integrate auto embeddings")

if __name__ == "__main__":
    main()
