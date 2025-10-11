#!/usr/bin/env python3
"""
Cache Management Utility
Manual cache refresh for database updates
"""
import os
import sys
import asyncio
from dotenv import load_dotenv
from chatbot_refactored import ChatBot

def main():
    """Main function for cache management"""
    load_dotenv()
    
    print("🔄 Cache Management Utility")
    print("=" * 40)
    
    try:
        chatbot = ChatBot(groq_key=os.environ.get('GROQ_API_KEY'))
        
        if not hasattr(chatbot.database_search, 'redis') or not chatbot.database_search.redis_available:
            print("❌ Redis not available - cache management disabled")
            return
        
        print("Available commands:")
        print("1. refresh - Force refresh all cache")
        print("2. clear - Clear all cache entries")
        print("3. stats - Show cache statistics")
        print("4. invalidate <query> - Invalidate specific query cache")
        print("5. invalidate-grade <grade> - Invalidate grade-specific cache")
        
        if len(sys.argv) < 2:
            print("\nUsage: python cache_manager.py <command> [args]")
            return
        
        command = sys.argv[1].lower()
        
        if command == "refresh":
            result = chatbot.database_search.force_cache_refresh()
            print(f"✅ Cache refresh: {'Success' if result else 'Failed'}")
            
        elif command == "clear":
            result = chatbot.database_search.clear_cache()
            print(f"✅ Cache clear: {'Success' if result else 'Failed'}")
            
        elif command == "stats":
            stats = chatbot.database_search.get_cache_stats()
            print(f"📊 Cache Statistics:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
                
        elif command == "invalidate" and len(sys.argv) > 2:
            query = sys.argv[2]
            result = chatbot.database_search.invalidate_query_cache(query)
            print(f"✅ Query cache invalidation: {'Success' if result else 'Failed'}")
            
        elif command == "invalidate-grade" and len(sys.argv) > 2:
            grade = sys.argv[2]
            result = chatbot.database_search.invalidate_grade_cache(grade)
            print(f"✅ Grade cache invalidation: {'Success' if result else 'Failed'}")
            
        else:
            print(f"❌ Unknown command: {command}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
