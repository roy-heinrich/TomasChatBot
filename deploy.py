#!/usr/bin/env python3
"""
Deployment script for Tomas Chatbot
Handles NLTK data download and starts the application
"""

import os
import sys
import subprocess
import time

def download_nltk_data():
    """Download NLTK data with robust error handling"""
    print("📥 Setting up NLTK data for deployment...")
    
    try:
        import nltk
        
        # Set up NLTK data directory
        nltk_data_dir = os.path.join(os.getcwd(), 'nltk_data')
        os.makedirs(nltk_data_dir, exist_ok=True)
        
        # Add to NLTK data path
        nltk.data.path.append(nltk_data_dir)
        
        # Resources to download
        resources = [
            'wordnet',
            'punkt', 
            'stopwords',
            'averaged_perceptron_tagger'
        ]
        
        downloaded = 0
        for resource in resources:
            try:
                print(f"Checking {resource}...")
                nltk.data.find(f'corpora/{resource}' if resource != 'punkt' else f'tokenizers/{resource}')
                print(f"✅ {resource} already available")
                downloaded += 1
            except LookupError:
                try:
                    print(f"Downloading {resource}...")
                    nltk.download(resource, download_dir=nltk_data_dir, quiet=True)
                    print(f"✅ {resource} downloaded successfully")
                    downloaded += 1
                except Exception as e:
                    print(f"⚠️ Failed to download {resource}: {e}")
                    # Try default location
                    try:
                        nltk.download(resource, quiet=True)
                        print(f"✅ {resource} downloaded to default location")
                        downloaded += 1
                    except Exception as e2:
                        print(f"❌ Could not download {resource}: {e2}")
        
        print(f"🎉 NLTK setup complete! ({downloaded}/{len(resources)} resources available)")
        return downloaded > 0
        
    except ImportError:
        print("⚠️ NLTK not available")
        return False
    except Exception as e:
        print(f"❌ NLTK setup failed: {e}")
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
            
    except subprocess.TimeoutExpired:
        print("❌ Requirements installation timed out")
        return False
    except Exception as e:
        print(f"❌ Requirements installation error: {e}")
        return False

def main():
    """Main deployment function - Build phase only"""
    print("🚀 Starting Tomas Chatbot Build Process...")
    
    # Install requirements first
    print("📦 Installing requirements...")
    req_success = install_requirements()
    
    if not req_success:
        print("⚠️ Requirements installation failed, but continuing with build...")
    
    # Download NLTK data
    nltk_success = download_nltk_data()
    
    if not nltk_success:
        print("⚠️ NLTK data download failed, but continuing with build...")
    
    print("✅ Build process completed successfully!")
    print("🌐 Ready for deployment - use 'uvicorn app:app --host 0.0.0.0 --port $PORT' as start command")

if __name__ == "__main__":
    main()
