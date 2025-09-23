#!/usr/bin/env python3
"""
Startup script to download NLTK data and start the application
"""

import os
import sys
import subprocess

def download_nltk_data():
    """Download required NLTK data"""
    print("📥 Downloading NLTK data for deployment...")
    
    try:
        import nltk
        
        # Create NLTK data directory
        nltk_data_dir = os.path.join(os.getcwd(), 'nltk_data')
        os.makedirs(nltk_data_dir, exist_ok=True)
        
        # Set NLTK data path
        nltk.data.path.append(nltk_data_dir)
        
        # Download required resources
        resources = [
            'wordnet',
            'punkt',
            'averaged_perceptron_tagger',
            'stopwords'
        ]
        
        for resource in resources:
            try:
                print(f"Downloading {resource}...")
                nltk.download(resource, download_dir=nltk_data_dir, quiet=True)
                print(f"✅ {resource} downloaded successfully")
            except Exception as e:
                print(f"⚠️ Failed to download {resource}: {e}")
        
        print("🎉 NLTK data download complete!")
        return True
        
    except ImportError:
        print("⚠️ NLTK not available, skipping data download")
        return False
    except Exception as e:
        print(f"❌ NLTK data download failed: {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 Starting Tomas Chatbot...")
    
    # Download NLTK data
    download_nltk_data()
    
    # Start the application
    print("🌐 Starting web server...")
    os.system("uvicorn app:app --host 0.0.0.0 --port $PORT")

if __name__ == "__main__":
    main()
