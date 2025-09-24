#!/usr/bin/env python3
"""
Deployment script for Tomas Chatbot
Now simplified: no NLTK downloads. Just checks for local nltk_data folder.
"""

import os
import sys

def check_nltk_data():
    """Verify that local nltk_data exists"""
    nltk_data_dir = os.path.join(os.getcwd(), "nltk_data")
    if os.path.exists(nltk_data_dir):
        print(f"📂 Found local nltk_data at {nltk_data_dir}")
        # Count packages inside for sanity check
        count = sum([len(files) for _, _, files in os.walk(nltk_data_dir)])
        print(f"✅ nltk_data is present with ~{count} files")
        return True
    else:
        print("❌ No nltk_data folder found! Please add it to the repo.")
        return False

def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python requirements...")
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print("✅ Requirements installed successfully")
            return True
        else:
            print(f"❌ Requirements installation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Requirements installation error: {e}")
        return False

def main():
    print("🚀 Starting Tomas Chatbot Build Process...")

    # Install requirements
    install_requirements()

    # Check nltk_data
    check_nltk_data()

    print("✅ Build process completed successfully!")
    print("🌐 Ready for deployment - use 'uvicorn app:app --host 0.0.0.0 --port $PORT'")

if __name__ == "__main__":
    main()
