#!/usr/bin/env python3
"""
Robust deployment script with better NLTK handling
"""

import os
import sys
import subprocess
import time

def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python requirements...")
    
    try:
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

def setup_nltk_robust():
    """Setup NLTK with multiple fallback strategies"""
    print("📥 Setting up NLTK data...")
    
    try:
        import nltk
        
        # Strategy 1: Try to use existing NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            print("✅ NLTK data already available")
            return True
        except LookupError:
            pass
        
        # Strategy 2: Download to current directory
        nltk_data_dir = os.path.join(os.getcwd(), 'nltk_data')
        os.makedirs(nltk_data_dir, exist_ok=True)
        nltk.data.path.append(nltk_data_dir)
        os.environ['NLTK_DATA'] = nltk_data_dir
        
        # Strategy 3: Download essential resources only
        essential_resources = ['punkt', 'stopwords']
        downloaded = 0
        
        for resource in essential_resources:
            try:
                print(f"Downloading {resource}...")
                nltk.download(resource, download_dir=nltk_data_dir, quiet=True)
                downloaded += 1
                print(f"✅ {resource} downloaded")
            except Exception as e:
                print(f"⚠️ Failed to download {resource}: {e}")
        
        if downloaded > 0:
            print(f"✅ NLTK setup complete! ({downloaded}/{len(essential_resources)} resources)")
            return True
        else:
            print("⚠️ NLTK setup failed, but chatbot will work with fallbacks")
            return False
            
    except ImportError:
        print("❌ NLTK not available")
        return False
    except Exception as e:
        print(f"❌ NLTK setup failed: {e}")
        return False

def main():
    """Main deployment function"""
    print("🚀 Starting Robust Deployment...")
    
    # Install requirements
    req_success = install_requirements()
    if not req_success:
        print("❌ Build failed - requirements installation failed")
        sys.exit(1)
    
    # Setup NLTK
    nltk_success = setup_nltk_robust()
    
    if nltk_success:
        print("✅ Build completed successfully with NLTK!")
    else:
        print("⚠️ Build completed with NLTK warnings - chatbot will work with fallbacks")
    
    print("🌐 Ready for deployment")

if __name__ == "__main__":
    main()
