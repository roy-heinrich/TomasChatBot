#!/bin/bash
# Startup script for Render deployment
echo "🚀 Starting Tomas Chatbot API..."
echo "📦 Installing dependencies..."
pip install -r requirements.txt
echo "🔧 Starting server..."
uvicorn app:app --host 0.0.0.0 --port $PORT
