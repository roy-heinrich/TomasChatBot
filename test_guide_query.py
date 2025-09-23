#!/usr/bin/env python3
"""
Test the complete guide query
"""

import asyncio
import aiohttp

async def test_guide_query():
    async with aiohttp.ClientSession() as session:
        payload = {
            'query': 'Give me a complete guide to your cosmetics',
            'conversation_history': [],
            'user_timezone': 'Asia/Manila',
            'session_id': 'test_guide_query'
        }
        
        try:
            async with session.post('http://localhost:8000/chat', json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print('✅ Query successful!')
                    response_text = result.get('response', 'No response')
                    if isinstance(response_text, list):
                        response_text = ' '.join(response_text)
                    print(f'Response: {response_text[:300]}...')
                    print(f'Language: {result.get("detected_language", "Unknown")}')
                    print(f'Message Count: {result.get("message_count", 0)}')
                else:
                    print(f'❌ Error: HTTP {response.status}')
        except Exception as e:
            print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(test_guide_query())
