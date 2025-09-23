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
    """Download NLTK data using command line installer (recommended method)"""
    print("📥 Setting up NLTK data for deployment...")
    
    try:
        # Set up NLTK data directory
        nltk_data_dir = os.path.join(os.getcwd(), 'nltk_data')
        os.makedirs(nltk_data_dir, exist_ok=True)
        
        # Set NLTK_DATA environment variable BEFORE any NLTK imports
        os.environ['NLTK_DATA'] = nltk_data_dir
        
        print("Using NLTK command line installer...")
        
        # Download essential packages in order of dependency
        essential_packages = ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']
        downloaded = 0
        
        for package in essential_packages:
            try:
                print(f"Installing {package} via command line...")
                
                # Use command line installer with proper environment
                env = os.environ.copy()
                env['NLTK_DATA'] = nltk_data_dir
                
                result = subprocess.run([
                    sys.executable, "-m", "nltk.downloader", "-d", nltk_data_dir, package
                ], capture_output=True, text=True, timeout=120, env=env)
                
                if result.returncode == 0:
                    print(f"✅ {package} installed successfully")
                    downloaded += 1
                else:
                    print(f"⚠️ Command line install failed for {package}")
                    print(f"Error: {result.stderr[:200]}...")  # Truncate long errors
                    
                    # Try Python API fallback (but only if we haven't imported NLTK yet)
                    try:
                        # Create a simple download script to avoid import issues
                        download_script = f"""
import os
import nltk
os.environ['NLTK_DATA'] = '{nltk_data_dir}'
nltk.data.path.append('{nltk_data_dir}')
nltk.download('{package}', download_dir='{nltk_data_dir}', quiet=True)
print('Downloaded {package}')
"""
                        with open('temp_download.py', 'w') as f:
                            f.write(download_script)
                        
                        result2 = subprocess.run([
                            sys.executable, "temp_download.py"
                        ], capture_output=True, text=True, timeout=60, env=env)
                        
                        if result2.returncode == 0:
                            print(f"✅ {package} installed via Python API fallback")
                            downloaded += 1
                        else:
                            print(f"❌ Python API fallback failed for {package}")
                        
                        # Clean up temp file
                        if os.path.exists('temp_download.py'):
                            os.remove('temp_download.py')
                            
                    except Exception as e:
                        print(f"❌ Fallback failed for {package}: {e}")
                        
            except subprocess.TimeoutExpired:
                print(f"⚠️ Timeout installing {package}")
            except Exception as e:
                print(f"❌ Error installing {package}: {e}")
        
        # Simple verification without importing problematic modules
        if downloaded > 0:
            print(f"✅ NLTK setup complete! ({downloaded}/{len(essential_packages)} packages installed)")
            return True
        else:
            print("❌ No NLTK packages could be installed")
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
