#!/usr/bin/env python3
"""
Simple deployment script that avoids NLTK import issues
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

def download_nltk_simple():
    """Download NLTK data using a simple approach"""
    print("📥 Setting up NLTK data...")
    
    try:
        # Set up NLTK data directory
        nltk_data_dir = os.path.join(os.getcwd(), 'nltk_data')
        os.makedirs(nltk_data_dir, exist_ok=True)
        
        # Set NLTK_DATA environment variable
        os.environ['NLTK_DATA'] = nltk_data_dir
        
        # Create a simple NLTK download script
        download_script = """
import os
import sys
import nltk

# Set NLTK data path
nltk_data_dir = os.path.join(os.getcwd(), 'nltk_data')
os.environ['NLTK_DATA'] = nltk_data_dir
nltk.data.path.append(nltk_data_dir)

# Download essential packages
packages = ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']
downloaded = 0

for package in packages:
    try:
        print(f"Downloading {package}...")
        nltk.download(package, download_dir=nltk_data_dir, quiet=True)
        print(f"✅ {package} downloaded")
        downloaded += 1
    except Exception as e:
        print(f"❌ Failed to download {package}: {e}")

print(f"Downloaded {downloaded}/{len(packages)} packages")
"""
        
        # Write and execute the download script
        with open('nltk_download.py', 'w') as f:
            f.write(download_script)
        
        print("Executing NLTK download script...")
        result = subprocess.run([
            sys.executable, "nltk_download.py"
        ], capture_output=True, text=True, timeout=300)
        
        # Clean up
        if os.path.exists('nltk_download.py'):
            os.remove('nltk_download.py')
        
        if result.returncode == 0:
            print("✅ NLTK download script completed")
            print(result.stdout)
            return True
        else:
            print("⚠️ NLTK download script had issues")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ NLTK setup failed: {e}")
        return False

def main():
    """Main deployment function"""
    print("🚀 Starting Simple Deployment...")
    
    # Install requirements
    req_success = install_requirements()
    if not req_success:
        print("❌ Build failed - requirements installation failed")
        sys.exit(1)
    
    # Setup NLTK
    nltk_success = download_nltk_simple()
    
    if nltk_success:
        print("✅ Build completed successfully with NLTK!")
    else:
        print("⚠️ Build completed with NLTK warnings - chatbot will work with fallbacks")
    
    print("🌐 Ready for deployment")

if __name__ == "__main__":
    main()
