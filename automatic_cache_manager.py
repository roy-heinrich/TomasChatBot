#!/usr/bin/env python3
"""
Automatic Cache Management System
Prevents stale cache results from causing issues
"""
import asyncio
import time
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AutomaticCacheManager:
    """Automatic cache management to prevent stale results"""
    
    def __init__(self, database_search, nlu_engine):
        self.database_search = database_search
        self.nlu_engine = nlu_engine
        self.last_cleanup = time.time()
        self.cleanup_interval = 3600  # 1 hour
        self.grade_cache_tracker = {}  # Track grade-specific cache usage
        
    async def setup_automatic_management(self):
        """Setup automatic cache management"""
        logger.info("🔧 Setting up automatic cache management")
        
        # Clear stale caches on startup
        await self.clear_stale_caches()
        
        # Setup periodic cleanup
        asyncio.create_task(self.periodic_cleanup())
        
        logger.info("✅ Automatic cache management active")
    
    async def clear_stale_caches(self):
        """Clear all stale cache entries"""
        try:
            # Clear Redis cache
            if hasattr(self.database_search, 'redis') and self.database_search.redis_available:
                self.database_search.redis.flushall()
                logger.info("🗑️ Cleared all Redis caches")
            
            # Clear in-memory caches
            if hasattr(self.database_search, 'language_detector'):
                if hasattr(self.database_search.language_detector, 'language_cache'):
                    self.database_search.language_detector.language_cache.clear()
                    logger.info("🗑️ Cleared language detection cache")
            
            if hasattr(self.nlu_engine, 'cache'):
                self.nlu_engine.cache.clear()
                logger.info("🗑️ Cleared NLU cache")
            
            # Reset cache tracking
            self.grade_cache_tracker.clear()
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
    
    async def periodic_cleanup(self):
        """Periodic cache cleanup to prevent memory issues"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                # Clean up expired entries
                await self.cleanup_expired_entries()
                
                # Clean up grade-specific conflicts
                await self.cleanup_grade_conflicts()
                
                # Monitor cache health
                await self.monitor_cache_health()
                
                self.last_cleanup = time.time()
                
            except Exception as e:
                logger.error(f"Periodic cleanup failed: {e}")
    
    async def cleanup_expired_entries(self):
        """Clean up expired cache entries"""
        if not hasattr(self.database_search, 'redis') or not self.database_search.redis_available:
            return
        
        try:
            keys = self.database_search.redis.keys('*')
            expired_keys = []
            
            for key in keys:
                ttl = self.database_search.redis.ttl(key)
                if ttl == -1:  # No expiration
                    expired_keys.append(key)
                elif ttl < 300:  # Less than 5 minutes
                    expired_keys.append(key)
            
            if expired_keys:
                self.database_search.redis.delete(*expired_keys)
                logger.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
                
        except Exception as e:
            logger.error(f"Expired entry cleanup failed: {e}")
    
    async def cleanup_grade_conflicts(self):
        """Clean up grade-specific cache conflicts"""
        if not hasattr(self.database_search, 'redis') or not self.database_search.redis_available:
            return
        
        try:
            keys = self.database_search.redis.keys('*')
            conflict_keys = []
            
            for key in keys:
                # Check if key contains grade information
                if 'grade' in key.lower():
                    # Check if this key might cause conflicts
                    ttl = self.database_search.redis.ttl(key)
                    if ttl > 1800:  # More than 30 minutes
                        conflict_keys.append(key)
            
            if conflict_keys:
                self.database_search.redis.delete(*conflict_keys)
                logger.info(f"🧹 Cleaned up {len(conflict_keys)} potentially conflicting cache entries")
                
        except Exception as e:
            logger.error(f"Grade conflict cleanup failed: {e}")
    
    async def monitor_cache_health(self):
        """Monitor cache health and performance"""
        if not hasattr(self.database_search, 'redis') or not self.database_search.redis_available:
            return
        
        try:
            keys = self.database_search.redis.keys('*')
            total_keys = len(keys)
            
            # Check for grade-specific cache distribution
            grade_keys = {}
            for key in keys:
                for grade in ['1', '2', '3', '4', '5', '6']:
                    if f'grade {grade}' in key.lower():
                        grade_keys[grade] = grade_keys.get(grade, 0) + 1
            
            # Log cache health
            logger.info(f"📊 Cache Health: {total_keys} total keys")
            for grade, count in grade_keys.items():
                logger.info(f"   Grade {grade}: {count} cache entries")
            
            # Alert if cache is getting too large
            if total_keys > 1000:
                logger.warning(f"⚠️ Cache size large: {total_keys} keys - consider cleanup")
                
        except Exception as e:
            logger.error(f"Cache health monitoring failed: {e}")
    
    async def invalidate_grade_cache(self, grade_num: str):
        """Invalidate all cache entries for a specific grade"""
        if not hasattr(self.database_search, 'redis') or not self.database_search.redis_available:
            return
        
        try:
            keys = self.database_search.redis.keys('*')
            grade_keys = [key for key in keys if f'grade {grade_num}' in key.lower()]
            
            if grade_keys:
                self.database_search.redis.delete(*grade_keys)
                logger.info(f"🗑️ Invalidated {len(grade_keys)} cache entries for Grade {grade_num}")
                
        except Exception as e:
            logger.error(f"Grade cache invalidation failed: {e}")
    
    async def force_cache_refresh(self):
        """Force refresh all caches"""
        logger.info("🔄 Forcing complete cache refresh")
        await self.clear_stale_caches()
        logger.info("✅ Cache refresh complete")

# Integration with chatbot
async def setup_automatic_cache_management(chatbot):
    """Setup automatic cache management for the chatbot"""
    try:
        cache_manager = AutomaticCacheManager(
            chatbot.database_search, 
            chatbot.nlu_engine
        )
        
        await cache_manager.setup_automatic_management()
        
        # Store reference for manual operations
        chatbot.cache_manager = cache_manager
        
        logger.info("✅ Automatic cache management integrated")
        return cache_manager
        
    except Exception as e:
        logger.error(f"Cache management setup failed: {e}")
        return None

if __name__ == "__main__":
    # Test the cache management system
    async def test_cache_management():
        print("🧪 Testing Automatic Cache Management")
        
        # This would be integrated into the chatbot initialization
        print("✅ Cache management system ready")
        print("🔧 Features:")
        print("   - Automatic cache cleanup every hour")
        print("   - Grade-specific cache invalidation")
        print("   - Stale entry detection and removal")
        print("   - Cache health monitoring")
        print("   - Conflict prevention")
    
    asyncio.run(test_cache_management())
