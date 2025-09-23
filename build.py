#!/usr/bin/env python3
"""
Simple build script for deployment
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

def main():
    """Simple build process"""
    print("🚀 Starting Simple Build Process...")
    
    # Install requirements
    req_success = install_requirements()
    
    if req_success:
        print("✅ Build completed successfully!")
        print("🌐 Ready for deployment")
    else:
        print("❌ Build failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
