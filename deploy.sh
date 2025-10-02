#!/bin/bash

# Deployment script with retry logic for network issues

echo "🚀 Starting deployment with optimized build..."

# Build with retry logic
for i in {1..3}; do
    echo "📦 Attempt $i/3: Building Docker image..."
    
    if docker build -f Dockerfile.optimized -t tomas-chatbot:latest .; then
        echo "✅ Build successful!"
        break
    else
        echo "❌ Build failed on attempt $i"
        if [ $i -eq 3 ]; then
            echo "💥 All build attempts failed. Exiting."
            exit 1
        fi
        echo "🔄 Retrying in 10 seconds..."
        sleep 10
    fi
done

echo "🎉 Deployment completed successfully!"
