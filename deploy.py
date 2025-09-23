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
        # Method 1: Use command line installer (recommended by NLTK docs)
        print("Using NLTK command line installer...")
        
        # Set up NLTK data directory
        nltk_data_dir = os.path.join(os.getcwd(), 'nltk_data')
        os.makedirs(nltk_data_dir, exist_ok=True)
        
        # Set NLTK_DATA environment variable
        os.environ['NLTK_DATA'] = nltk_data_dir
        
        # Use command line installer for essential packages
        essential_packages = ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']
        
        for package in essential_packages:
            try:
                print(f"Installing {package} via command line...")
                result = subprocess.run([
                    sys.executable, "-m", "nltk.downloader", "-d", nltk_data_dir, package
                ], capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    print(f"✅ {package} installed successfully")
                else:
                    print(f"⚠️ Command line install failed for {package}: {result.stderr}")
                    # Fallback to Python API
                    try:
                        import nltk
                        nltk.download(package, download_dir=nltk_data_dir, quiet=True)
                        print(f"✅ {package} installed via Python API fallback")
                    except Exception as e:
                        print(f"❌ All methods failed for {package}: {e}")
                        
            except subprocess.TimeoutExpired:
                print(f"⚠️ Timeout installing {package}, trying fallback...")
                try:
                    import nltk
                    nltk.download(package, download_dir=nltk_data_dir, quiet=True)
                    print(f"✅ {package} installed via fallback")
                except Exception as e:
                    print(f"❌ Fallback failed for {package}: {e}")
            except Exception as e:
                print(f"❌ Error installing {package}: {e}")
        
        # Verify installation
        try:
            import nltk
            nltk.data.path.append(nltk_data_dir)
            
            # Test essential resources
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            print("✅ NLTK data verification successful")
            return True
            
        except LookupError as e:
            print(f"⚠️ NLTK verification failed: {e}")
            return False
        
    except ImportError:
        print("❌ NLTK not available - install with: pip install nltk")
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
