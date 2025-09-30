#!/usr/bin/env python3
"""
Check if the deployed chatbot is working
"""

import requests
import json

def check_deployment():
    """Check if the deployed chatbot is accessible"""
    base_url = "https://tomaschatbot.onrender.com"
    
    print("🔍 Checking deployment status...")
    
    # Test health endpoint
    try:
        print("1. Testing health endpoint...")
        health_response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {health_response.status_code}")
        if health_response.status_code == 200:
            print(f"   Response: {health_response.json()}")
        else:
            print(f"   Error: {health_response.text}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
    
    # Test root endpoint
    try:
        print("\n2. Testing root endpoint...")
        root_response = requests.get(f"{base_url}/", timeout=10)
        print(f"   Status: {root_response.status_code}")
        if root_response.status_code == 200:
            print(f"   Response: {root_response.json()}")
        else:
            print(f"   Error: {root_response.text}")
    except Exception as e:
        print(f"   ❌ Root check failed: {e}")
    
    # Test CORS with OPTIONS request
    try:
        print("\n3. Testing CORS preflight...")
        cors_response = requests.options(
            f"{base_url}/chat",
            headers={
                'Origin': 'http://localhost',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            },
            timeout=10
        )
        print(f"   Status: {cors_response.status_code}")
        print(f"   Headers: {dict(cors_response.headers)}")
    except Exception as e:
        print(f"   ❌ CORS check failed: {e}")
    
    # Test actual chat endpoint
    try:
        print("\n4. Testing chat endpoint...")
        chat_response = requests.post(
            f"{base_url}/chat",
            json={
                "query": "Hello, test message",
                "conversation_history": [],
                "user_timezone": "UTC",
                "session_id": "test_session"
            },
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        print(f"   Status: {chat_response.status_code}")
        if chat_response.status_code == 200:
            print(f"   Response: {chat_response.json()}")
        else:
            print(f"   Error: {chat_response.text}")
    except Exception as e:
        print(f"   ❌ Chat test failed: {e}")

if __name__ == "__main__":
    check_deployment()
