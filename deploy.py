#!/usr/bin/env python3
"""
Deployment script for Tomas Chatbot
Handles NLTK data download and requirements installation
"""

import os
import sys
import subprocess

NLTK_DIR = "/opt/render/nltk_data"

def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python requirements...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            print("✅ Requirements installed successfully")
            return True
        else:
            print(f"❌ Requirements installation failed: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"❌ Requirements installation error: {e}")
        return False

def download_nltk_data():
    """Download essential NLTK corpora into /opt/render/nltk_data"""
    print("📥 Setting up NLTK data...")
    os.makedirs(NLTK_DIR, exist_ok=True)
    os.environ["NLTK_DATA"] = NLTK_DIR

    essential_packages = ["punkt", "stopwords", "wordnet", "averaged_perceptron_tagger"]
    success = 0

    for package in essential_packages:
        print(f"➡ Installing {package}...")
        result = subprocess.run(
            [sys.executable, "-m", "nltk.downloader", "-d", NLTK_DIR, package],
            capture_output=True, text=True, timeout=120, env=os.environ
        )
        if result.returncode == 0:
            print(f"✅ {package} installed")
            success += 1
        else:
            print(f"⚠️ Failed to install {package}: {result.stderr[:200]}")

    print(f"📊 NLTK setup: {success}/{len(essential_packages)} packages installed")

def main():
    print("🚀 Starting Tomas Chatbot Build Process...")
    install_requirements()
    download_nltk_data()
    print("✅ Build process complete. Ready for deployment.")

if __name__ == "__main__":
    main()
