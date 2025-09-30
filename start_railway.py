#!/usr/bin/env python3
"""
Railway-optimized start script for Tomas Chatbot
Handles heavy ML dependencies gracefully
"""

import os
import sys
import logging

def main():
    """Start the web server with Railway optimizations"""
    print("🚀 Starting Tomas Chatbot on Railway...")

    # Point to local nltk_data
    nltk_data_path = os.path.join(os.path.dirname(__file__), "nltk_data")
    os.environ["NLTK_DATA"] = nltk_data_path

    if os.path.exists(nltk_data_path):
        print(f"📂 nltk_data detected at {nltk_data_path}")
        files = sum([len(f) for _, _, f in os.walk(nltk_data_path)])
        print(f"✅ nltk_data contains ~{files} files. Looks good.")
    else:
        print("❌ WARNING: nltk_data folder not found. Expect runtime errors.")

    # Get port from Railway environment
    port = os.environ.get("PORT", "8080")
    print(f"🌐 Starting on port {port}")

    # Try to import and start the main app
    try:
        print("🔄 Attempting to start main app...")
        import app
        print("✅ Main app imported successfully")
        
        # Start uvicorn
        import uvicorn
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=int(port),
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        print(f"⚠️ Main app import failed: {e}")
        print("🔄 Falling back to simple version...")
        
        try:
            import app_simple
            print("✅ Simple app imported successfully")
            
            import uvicorn
            uvicorn.run(
                "app_simple:app",
                host="0.0.0.0",
                port=int(port),
                log_level="info",
                access_log=True
            )
            
        except Exception as e:
            print(f"❌ Simple app also failed: {e}")
            print("🔄 Starting minimal fallback...")
            
            # Minimal fallback
            from fastapi import FastAPI
            from fastapi.middleware.cors import CORSMiddleware
            
            app = FastAPI(title="Tomas Chatbot - Minimal Fallback")
            
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            
            @app.get("/")
            async def root():
                return {"message": "Tomas Chatbot - Minimal Fallback", "status": "running"}
            
            @app.get("/health")
            async def health():
                return {"status": "healthy", "message": "Minimal fallback running"}
            
            @app.post("/chat")
            async def chat(request: dict):
                return {
                    "response": ["I'm running in minimal mode. Please check the logs for issues."],
                    "detected_language": "en",
                    "language_confidence": 0.5,
                    "entities": [],
                    "intent": "fallback",
                    "is_split": False,
                    "message_count": 1
                }
            
            import uvicorn
            uvicorn.run(
                app,
                host="0.0.0.0",
                port=int(port),
                log_level="info",
                access_log=True
            )
            
    except Exception as e:
        print(f"❌ Server failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
