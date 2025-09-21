"""
Clear both response cache and language detection cache systems
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot import ChatBot

def clear_all_caches():
    print("=== CLEARING ALL CACHE SYSTEMS ===")
    
    groq_key = os.getenv("GROQ_API_KEY", "")
    chatbot = ChatBot(groq_key=groq_key)
    
    # === 1. RESPONSE CACHE ANALYSIS ===
    print("\n1. 📊 Response Cache Analysis:")
    response_stats_before = chatbot.response_cache.get_stats()
    print(f"   Response cache stats before: {response_stats_before}")
    
    # === 2. LANGUAGE DETECTION CACHE ANALYSIS ===
    print("\n2. 🌍 Language Detection Cache Analysis:")
    language_cache_size = len(getattr(chatbot, 'language_cache', {}))
    print(f"   Language cache entries before: {language_cache_size}")
    
    if language_cache_size > 0:
        print("   Sample language cache entries:")
        sample_entries = list(chatbot.language_cache.items())[:3]
        for key, (result, timestamp) in sample_entries:
            print(f"     '{key[:50]}...' -> {result}")
    
    # === 3. CLEAR RESPONSE CACHE ===
    print("\n3. 🧹 Clearing Response Cache...")
    chatbot.response_cache.clear()
    print("   ✅ Response cache cleared!")
    
    # === 4. CLEAR LANGUAGE DETECTION CACHE ===
    print("\n4. 🧹 Clearing Language Detection Cache...")
    if hasattr(chatbot, 'language_cache'):
        chatbot.language_cache.clear()
        print("   ✅ Language detection cache cleared!")
    else:
        print("   ⚠️ Language cache not found (may not be initialized)")
    
    # === 5. VERIFY CLEARING ===
    print("\n5. ✅ Verification:")
    
    # Check response cache
    response_stats_after = chatbot.response_cache.get_stats()
    print(f"   Response cache stats after: {response_stats_after}")
    
    # Check language cache
    language_cache_size_after = len(getattr(chatbot, 'language_cache', {}))
    print(f"   Language cache entries after: {language_cache_size_after}")
    
    # === 6. FUNCTIONAL TEST ===
    print("\n6. 🧪 Functional Test:")
    
    # Test response cache
    test_query = "Hello test query for cache verification"
    cache_context = {
        'language': 'auto-detect',
        'context': 'Test context for verification'
    }
    
    cached_result = chatbot.response_cache.get(test_query, cache_context)
    print(f"   Response cache lookup result: {cached_result}")
    
    if cached_result is None:
        print("   ✅ Response cache is properly cleared!")
    else:
        print(f"   ❌ Response cache still contains data: {cached_result}")
    
    # Test language cache
    if hasattr(chatbot, 'language_cache'):
        if len(chatbot.language_cache) == 0:
            print("   ✅ Language detection cache is properly cleared!")
        else:
            print(f"   ❌ Language cache still has {len(chatbot.language_cache)} entries")
    
    print("\n" + "="*60)
    print("🎉 CACHE CLEARING COMPLETE!")
    print("📈 Both response cache and language detection cache have been cleared.")
    print("🚀 The chatbot will now rebuild caches from fresh requests.")
    print("="*60)

if __name__ == "__main__":
    clear_all_caches()