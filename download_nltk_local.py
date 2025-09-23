#!/usr/bin/env python3
"""
Download NLTK data locally for inclusion in repository
"""

import nltk
import os

def download_nltk_data_locally():
    """Download NLTK data to include in repository"""
    print("📥 Downloading NLTK data locally...")
    
    # Create nltk_data directory
    nltk_data_dir = os.path.join(os.getcwd(), 'nltk_data')
    os.makedirs(nltk_data_dir, exist_ok=True)
    
    # Set NLTK data path
    nltk.data.path.append(nltk_data_dir)
    
    # Resources to download
    resources = [
        'punkt',
        'stopwords', 
        'wordnet',
        'averaged_perceptron_tagger'
    ]
    
    for resource in resources:
        try:
            print(f"Downloading {resource}...")
            nltk.download(resource, download_dir=nltk_data_dir, quiet=True)
            print(f"✅ {resource} downloaded successfully")
        except Exception as e:
            print(f"❌ Failed to download {resource}: {e}")
    
    print("🎉 NLTK data download complete!")
    print(f"📁 Data saved to: {nltk_data_dir}")

if __name__ == "__main__":
    download_nltk_data_locally()
