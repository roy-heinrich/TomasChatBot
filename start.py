#!/usr/bin/env python3
"""
Start script for Tomas Chatbot - Runtime phase
"""

import os
import sys

def main():
    """Start the web server"""
    print("🌐 Starting Tomas Chatbot Web Server...")
    
    # Get port from environment or use default
    port = os.environ.get('PORT', '8000')
    
    # Start uvicorn using python -m
    cmd = f"python -m uvicorn app:app --host 0.0.0.0 --port {port}"
    print(f"Running: {cmd}")
    
    try:
        os.system(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed: {e}")

if __name__ == "__main__":
    main()
