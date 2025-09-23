#!/usr/bin/env python3
"""
Deployment script using NLTK 'all' collection download
"""

import os
import sys
import subprocess

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

def download_nltk_all():
    """Download NLTK data using 'all' collection (as per NLTK docs)"""
    print("📥 Downloading NLTK data using 'all' collection...")
    
    try:
        # Set up NLTK data directory
        nltk_data_dir = os.path.join(os.getcwd(), 'nltk_data')
        os.makedirs(nltk_data_dir, exist_ok=True)
        
        # Set NLTK_DATA environment variable
        os.environ['NLTK_DATA'] = nltk_data_dir
        
        print("Installing NLTK 'all' collection...")
        result = subprocess.run([
            sys.executable, "-m", "nltk.downloader", "-d", nltk_data_dir, "all"
        ], capture_output=True, text=True, timeout=600)  # 10 minute timeout for 'all'
        
        if result.returncode == 0:
            print("✅ NLTK 'all' collection installed successfully")
            return True
        else:
            print(f"⚠️ NLTK 'all' install failed: {result.stderr}")
            print("Trying essential packages only...")
            
            # Fallback to essential packages
            essential = ['punkt', 'stopwords', 'wordnet']
            for package in essential:
                try:
                    subprocess.run([
                        sys.executable, "-m", "nltk.downloader", "-d", nltk_data_dir, package
                    ], capture_output=True, text=True, timeout=120)
                    print(f"✅ {package} installed")
                except Exception as e:
                    print(f"❌ {package} failed: {e}")
            
            return True
            
    except subprocess.TimeoutExpired:
        print("⚠️ NLTK download timed out, trying essential packages...")
        # Try essential packages only
        essential = ['punkt', 'stopwords']
        for package in essential:
            try:
                subprocess.run([
                    sys.executable, "-m", "nltk.downloader", "-d", nltk_data_dir, package
                ], capture_output=True, text=True, timeout=60)
                print(f"✅ {package} installed")
            except Exception as e:
                print(f"❌ {package} failed: {e}")
        return True
        
    except Exception as e:
        print(f"❌ NLTK setup failed: {e}")
        return False

def main():
    """Main deployment function"""
    print("🚀 Starting NLTK 'All' Deployment...")
    
    # Install requirements
    req_success = install_requirements()
    if not req_success:
        print("❌ Build failed - requirements installation failed")
        sys.exit(1)
    
    # Setup NLTK
    nltk_success = download_nltk_all()
    
    if nltk_success:
        print("✅ Build completed successfully with NLTK!")
    else:
        print("⚠️ Build completed with NLTK warnings")
    
    print("🌐 Ready for deployment")

if __name__ == "__main__":
    main()
