#!/usr/bin/env python3
"""
Start script for Tomas Chatbot - Runtime phase
Locks NLTK to local nltk_data folder
"""

import os
import sys

def main():
    """Start the web server"""
    print("🌐 Starting Tomas Chatbot Web Server...")

    # Configure NLTK data path for Railway deployment
    nltk_data_path = os.path.join(os.path.dirname(__file__), "nltk_data")
    
    # Set NLTK data path
    os.environ["NLTK_DATA"] = nltk_data_path
    
    # Configure NLTK data paths
    import nltk
    nltk.data.path.append(nltk_data_path)
    
    if os.path.exists(nltk_data_path):
        print(f"📂 nltk_data detected at {nltk_data_path}")
        files = sum([len(f) for _, _, f in os.walk(nltk_data_path)])
        print(f"✅ nltk_data contains ~{files} files. Looks good.")
        
        # Test NLTK data availability
        try:
            from nltk.corpus import stopwords
            from nltk.tokenize import word_tokenize
            print("✅ NLTK data paths configured:")
            print(f"   Local: {nltk_data_path}")
            print(f"   Current NLTK paths: {nltk.data.path}")
        except Exception as e:
            print(f"⚠️ NLTK data test failed: {e}")
    else:
        print("❌ WARNING: nltk_data folder not found. Expect runtime errors.")

    # Get port from environment or default
    port = os.environ.get("PORT", "8000")

    # Start uvicorn with main app
    cmd = f"python -m uvicorn app:app --host 0.0.0.0 --port {port}"
    print(f"▶ Running: {cmd}")

    try:
        os.system(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed: {e}")

if __name__ == "__main__":
    main()
