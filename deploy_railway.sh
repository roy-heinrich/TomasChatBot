#!/bin/bash

# Railway deployment script with ultra-minimal requirements
echo "🚀 Deploying Tomas Chatbot to Railway with ultra-minimal requirements..."

# Check if we're in the right directory
if [ ! -f "requirements_ultra_minimal.txt" ]; then
    echo "❌ requirements_ultra_minimal.txt not found!"
    exit 1
fi

# Build with ultra-minimal requirements
echo "📦 Building with ultra-minimal requirements..."
docker build -f Dockerfile -t tomas-chatbot:latest .

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful!"
    echo "🚀 Ready for Railway deployment!"
    echo ""
    echo "Next steps:"
    echo "1. git add ."
    echo "2. git commit -m 'Ultra-minimal requirements for Railway'"
    echo "3. git push origin main"
    echo "4. Railway will automatically deploy"
else
    echo "❌ Docker build failed!"
    exit 1
fi
