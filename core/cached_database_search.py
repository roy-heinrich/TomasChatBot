"""
Cached Database Search with Redis
High-performance caching layer for database queries
"""
import logging
import json
import hashlib
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from core.database_search import DatabaseSearchEngine

logger = logging.getLogger(__name__)

class CachedDatabaseSearch(DatabaseSearchEngine):
    """Database search with Redis caching for improved performance"""
    
    def __init__(self, supabase_client, redis_url: str = None):
        # Initialize parent class with URL and key from environment
        import os
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        super().__init__(supabase_url, supabase_key)
        
        self.cache_ttl = 7200  # 2 hour cache (increased for better cache hit rate)
        self.redis = None
        self.redis_available = False
        
        # Memory management settings
        self.max_cache_entries = 1000  # Maximum cache entries
        self.memory_check_interval = 100  # Check memory every 100 cache operations
        self.cache_operations_count = 0
        
        # Initialize Redis connection
        self._initialize_redis(redis_url)
        
        # Track database changes for cache invalidation
        self._last_db_check = None
        self._db_hash_cache = {}
    
    def _initialize_redis(self, redis_url: str = None):
        """Initialize Redis connection with cloud-friendly fallback"""
        try:
            import redis
            import os
            
            # Priority order for Redis connection:
            # 1. Explicit redis_url parameter
            # 2. REDIS_URL environment variable (for cloud deployments)
            # 3. Local Redis (for development only)
            
            if redis_url:
                self.redis = redis.from_url(redis_url, decode_responses=True)
                logger.info("✅ Redis initialized from provided URL")
            elif os.environ.get('REDIS_URL'):
                self.redis = redis.from_url(os.environ.get('REDIS_URL'), decode_responses=True)
                logger.info("✅ Redis initialized from REDIS_URL environment variable")
            else:
                # Development fallback - try local Redis
                self.redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                logger.info("✅ Redis initialized for local development")
            
            # Test connection
            self.redis.ping()
            self.redis_available = True
            logger.info("✅ Redis cache initialized successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis not available, using database-only mode: {e}")
            logger.info("💡 To enable Redis caching:")
            logger.info("   - Development: Install Redis locally")
            logger.info("   - Production: Add REDIS_URL to environment variables")
            logger.info("   - Cloud: Use Redis Cloud (redis.com/try-free)")
            self.redis_available = False
    
    def _create_cache_key(self, query: str, intent: str = None, limit: int = None, 
                          conversation_history: List[Dict] = None, nlu_result = None) -> str:
        """Create cache key with grade-specific isolation to prevent context contamination"""
        """Create a unique cache key for the query"""
        # Normalize query for consistent caching
        normalized_query = query.lower().strip()
        
        # Include parameters that affect results
        key_parts = [normalized_query]
        if intent:
            key_parts.append(f"intent:{intent}")
        if limit:
            key_parts.append(f"limit:{limit}")
        
        # 🚨 CRITICAL FIX: Don't include conversation context for grade-specific queries
        # This prevents cache contamination between different grade queries
        import re
        if conversation_history and not re.search(r'grade\s*\d+', normalized_query):
            # Only include recent conversation topics for non-grade queries
            recent_topics = []
            for msg in conversation_history[-3:]:  # Last 3 messages only
                if isinstance(msg, dict) and 'content' in msg:
                    # Extract key topics, not full content
                    content = msg['content'].lower()
                    if any(word in content for word in ['teacher', 'principal', 'adviser']):
                        recent_topics.append('has_staff_context')
                        break
            if recent_topics:
                key_parts.append('ctx:' + ':'.join(recent_topics))
        
        # Include NLU confidence level (rounded to avoid key explosion)
        if nlu_result and hasattr(nlu_result, 'confidence'):
            confidence_level = round(nlu_result.confidence, 1)
            key_parts.append(f"conf:{confidence_level}")
        
        # Add cache version to invalidate old entries when algorithm changes
        key_parts.append("v2")  # Increment this when search algorithm changes
        
        # Create hash for consistent key length
        key_string = ":".join(key_parts)
        query_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"search:{query_hash}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[List[Dict]]:
        """Get data from Redis cache"""
        if not self.redis_available:
            return None
        
        try:
            cached_data = self.redis.get(cache_key)
            if cached_data:
                logger.info(f"🚀 Cache HIT for key: {cache_key[:20]}...")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Redis get error: {e}")
        
        return None
    
    def _store_in_cache(self, cache_key: str, data: List[Dict]) -> bool:
        """Store data in Redis cache"""
        if not self.redis_available:
            return False
        
        try:
            self.redis.setex(cache_key, self.cache_ttl, json.dumps(data))
            logger.info(f"💾 Cached result for key: {cache_key[:20]}...")
            return True
        except Exception as e:
            logger.warning(f"Redis store error: {e}")
            return False
    
    async def search_prompts_three_tier(self, query: str, limit: int = 20, intent: str = None, 
                                      conversation_history: List[Dict] = None,
                                      nlu_result = None) -> List[Dict[str, Any]]:
        """Search using three-tier search strategy with caching"""
        try:
            # Create cache key for three-tier search (use consistent 'search:' prefix for all searches)
            cache_key = self._create_cache_key(query, intent, limit, conversation_history, nlu_result)
            
            # Try to get from cache first
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"🚀 Three-tier cache HIT for: {query[:50]}...")
                return cached_result
            
            # Cache miss - perform three-tier search
            logger.info(f"💾 Three-tier cache MISS for: {query[:50]}...")
            
            # Use three-tier search from parent class
            results = await super().search_prompts_three_tier(query, limit, intent, conversation_history, nlu_result)
            
            # Store in cache
            if results:
                self._store_in_cache(cache_key, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Three-tier cached search failed: {e}")
            # Fallback to traditional search
            return await self.search_prompts(query, limit, intent, True, conversation_history, nlu_result)

    async def search_prompts(self, query: str, limit: int = 20, intent: str = None, 
                        use_semantic: bool = True, conversation_history: List[Dict] = None,
                        nlu_result = None) -> List[Dict[str, Any]]:
        """Search prompts with Redis caching and database change detection"""
        
        # Check if database has changed (only occasionally to avoid performance impact)
        if self._check_database_changes():
            self._invalidate_cache_on_db_change()
        
        # Create cache key including all parameters that affect results
        cache_key = self._create_cache_key(query, intent, limit, conversation_history, nlu_result)
        
        # Try to get from cache first
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            logger.info(f"💾 Cache HIT for key: {cache_key[:20]}...")
            return cached_result
        
        # Cache miss - call parent method
        logger.info(f"💾 Cache MISS for query: {query[:50]}...")
        results = await super().search_prompts(query, limit, intent, use_semantic, conversation_history, nlu_result)
        
        # Store in cache
        if results:
            self._store_in_cache(cache_key, results)
            
        # Check memory usage periodically
        self.cache_operations_count += 1
        if self.cache_operations_count % self.memory_check_interval == 0:
            self._check_memory_usage()
        
        # 🚨 AUTOMATIC CACHE INVALIDATION: Prevent stale results
        if any(word in query.lower() for word in ['grade', 'adviser', 'teacher', 'baitang']):
            # Extract grade number if present
            import re
            grade_match = re.search(r'grade\s*(\d+)', query.lower())
            if grade_match:
                grade_num = grade_match.group(1)
                # Invalidate old cache entries for this grade (but not the one we just created)
                self._invalidate_old_grade_cache(grade_num, cache_key)
                
                # 🚨 CRITICAL: Also invalidate OTHER grades to prevent cross-contamination
                for other_grade in ['1', '2', '3', '4', '5', '6']:
                    if other_grade != grade_num:
                        self._invalidate_grade_cache(other_grade)
        
        # 🚨 AUTOMATIC: Invalidate cache when database changes are detected
        if self._check_database_changes():
            logger.info("🔄 Database changes detected - invalidating all caches")
            self._invalidate_all_caches()
        
        # 🚨 AUTOMATIC: Periodic cache cleanup to prevent memory issues
        if self.cache_operations_count % 50 == 0:  # Every 50 operations
            self._cleanup_stale_cache_entries()
        
        return results
    
    def _invalidate_grade_cache(self, grade_num: str):
        """Invalidate all cache entries for a specific grade"""
        if not self.redis_available:
            return
        
        try:
            # Get all cache keys
            keys = self.redis.keys('*')
            grade_keys = [key for key in keys if f'grade {grade_num}' in key.lower()]
            
            if grade_keys:
                self.redis.delete(*grade_keys)
                logger.info(f"🗑️ Invalidated {len(grade_keys)} cache entries for Grade {grade_num}")
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")
    
    def _invalidate_all_caches(self):
        """Invalidate all cache entries"""
        if not self.redis_available:
            return
        
        try:
            self.redis.flushall()
            logger.info("🗑️ All caches invalidated")
        except Exception as e:
            logger.warning(f"Full cache invalidation failed: {e}")
    
    def _cleanup_stale_cache_entries(self):
        """Clean up stale cache entries to prevent memory issues"""
        if not self.redis_available:
            return
        
        try:
            # Get all keys and check TTL
            keys = self.redis.keys('*')
            stale_keys = []
            
            for key in keys:
                ttl = self.redis.ttl(key)
                if ttl == -1:  # No expiration set
                    stale_keys.append(key)
                elif ttl < 60:  # Less than 1 minute left
                    stale_keys.append(key)
            
            if stale_keys:
                self.redis.delete(*stale_keys)
                logger.info(f"🧹 Cleaned up {len(stale_keys)} stale cache entries")
        except Exception as e:
            logger.warning(f"Cache cleanup failed: {e}")
    
    def _check_database_changes(self) -> bool:
        """Check if database has changed since last check"""
        try:
            import time
            current_time = time.time()
            
            # Only check every 5 minutes to avoid excessive database calls
            if self._last_db_check and (current_time - self._last_db_check) < 300:
                return False
            
            self._last_db_check = current_time
            
            # Get a hash of all chatbot_prompts data
            result = self.supabase.table("chatbot_prompts") \
                .select("id,updated_at") \
                .order("updated_at", desc=True) \
                .limit(100) \
                .execute()
            
            if not result.data:
                return False
            
            # Create a hash of the data
            data_hash = hashlib.md5(str(result.data).encode()).hexdigest()
            
            # Check if this hash exists in our cache
            if data_hash in self._db_hash_cache:
                return False  # No changes
            
            # New hash - database has changed
            self._db_hash_cache[data_hash] = current_time
            
            # Clear old hash entries (keep only last 10)
            if len(self._db_hash_cache) > 10:
                oldest_hash = min(self._db_hash_cache.keys(), 
                                key=lambda k: self._db_hash_cache[k])
                del self._db_hash_cache[oldest_hash]
            
            logger.info("🔄 Database changes detected - cache will be invalidated")
            return True
            
        except Exception as e:
            logger.warning(f"Database change check failed: {e}")
            return False
    
    def _invalidate_cache_on_db_change(self):
        """Invalidate all cache entries when database changes"""
        if not self.redis_available:
            return False
        
        try:
            # Clear all search cache entries
            pattern = "search:*"
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                logger.info(f"🗑️ Invalidated {len(keys)} cache entries due to database changes")
                return True
            return False
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return False
    
    def force_cache_refresh(self) -> bool:
        """Force immediate cache refresh - use when you know database was updated"""
        if not self.redis_available:
            return False
        
        try:
            # Clear all cache entries
            result = self.clear_cache()
            
            # Reset database change tracking
            self._last_db_check = None
            self._db_hash_cache.clear()
            
            logger.info("🔄 Force cache refresh completed")
            return result
        except Exception as e:
            logger.error(f"Force cache refresh error: {e}")
            return False
    
    def _check_memory_usage(self):
        """Check Redis memory usage and clean up if necessary"""
        if not self.redis_available:
            return
        
        try:
            # Get Redis info
            info = self.redis.info()
            
            # Check memory usage percentage
            if info.get('maxmemory', 0) > 0:
                used_memory = info.get('used_memory', 0)
                max_memory = info.get('maxmemory', 0)
                usage_percent = (used_memory / max_memory) * 100
                
                # If memory usage is high, clean up
                if usage_percent > 80:
                    logger.warning(f"🚨 High Redis memory usage: {usage_percent:.1f}%")
                    self._emergency_cache_cleanup()
                elif usage_percent > 60:
                    logger.info(f"⚠️ Moderate Redis memory usage: {usage_percent:.1f}%")
                    self._preventive_cache_cleanup()
            
            # Check cache entry count
            search_keys = self.redis.keys("search:*")
            if len(search_keys) > self.max_cache_entries:
                logger.warning(f"🚨 Too many cache entries: {len(search_keys)}")
                self._emergency_cache_cleanup()
                
        except Exception as e:
            logger.warning(f"Memory check failed: {e}")
    
    def _emergency_cache_cleanup(self):
        """Emergency cache cleanup when memory is critically high"""
        try:
            # Clear all cache entries
            self.clear_cache()
            logger.warning("🚨 Emergency cache cleanup completed")
        except Exception as e:
            logger.error(f"Emergency cleanup failed: {e}")
    
    def _preventive_cache_cleanup(self):
        """Preventive cache cleanup when memory usage is moderate"""
        try:
            # Clear old cache entries (older than 30 minutes)
            import time
            current_time = time.time()
            
            search_keys = self.redis.keys("search:*")
            old_keys = []
            
            for key in search_keys:
                try:
                    # Get TTL for the key
                    ttl = self.redis.ttl(key)
                    if ttl > 0 and ttl < 1800:  # Less than 30 minutes left
                        old_keys.append(key)
                except:
                    continue
            
            if old_keys:
                self.redis.delete(*old_keys)
                logger.info(f"🧹 Preventive cleanup: removed {len(old_keys)} old cache entries")
                
        except Exception as e:
            logger.warning(f"Preventive cleanup failed: {e}")
    
    def clear_cache(self, pattern: str = None) -> bool:
        """Clear cache entries"""
        if not self.redis_available:
            return False
        
        try:
            if pattern:
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
                    logger.info(f"🗑️ Cleared {len(keys)} cache entries matching '{pattern}'")
            else:
                self.redis.flushdb()
                logger.info("🗑️ Cleared all cache entries")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def invalidate_query_cache(self, query: str) -> bool:
        """Invalidate cache for a specific query and its variations"""
        if not self.redis_available:
            return False
        
        try:
            # Clear cache for the exact query
            normalized_query = query.lower().strip()
            pattern = f"search:*"
            keys = self.redis.keys(pattern)
            
            # Filter keys that contain the query
            matching_keys = []
            for key in keys:
                # Decode the key to check if it contains our query
                try:
                    key_str = key.decode() if isinstance(key, bytes) else key
                    if normalized_query in key_str:
                        matching_keys.append(key)
                except:
                    continue
            
            if matching_keys:
                self.redis.delete(*matching_keys)
                logger.info(f"🗑️ Invalidated {len(matching_keys)} cache entries for query: '{query}'")
                return True
            return False
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return False
    
    def invalidate_grade_cache(self, grade: str) -> bool:
        """Invalidate cache for all queries related to a specific grade"""
        if not self.redis_available:
            return False
        
        try:
            pattern = f"search:*"
            keys = self.redis.keys(pattern)
            
            # Filter keys that contain grade-related queries
            matching_keys = []
            grade_patterns = [f"grade {grade}", f"grade{grade}", f"baitang {grade}"]
            
            for key in keys:
                try:
                    key_str = key.decode() if isinstance(key, bytes) else key
                    if any(pattern in key_str for pattern in grade_patterns):
                        matching_keys.append(key)
                except:
                    continue
            
            if matching_keys:
                self.redis.delete(*matching_keys)
                logger.info(f"🗑️ Invalidated {len(matching_keys)} cache entries for grade {grade}")
                return True
            return False
        except Exception as e:
            logger.error(f"Grade cache invalidation error: {e}")
            return False
    
    def _invalidate_old_grade_cache(self, grade: str, current_cache_key: str) -> bool:
        """Invalidate old cache entries for a grade, excluding the current one"""
        if not self.redis_available:
            return False
        
        try:
            pattern = f"search:*"
            keys = self.redis.keys(pattern)
            
            # Filter keys that contain grade-related queries but exclude current key
            matching_keys = []
            grade_patterns = [f"grade {grade}", f"grade{grade}", f"baitang {grade}"]
            
            for key in keys:
                try:
                    key_str = key.decode() if isinstance(key, bytes) else key
                    # Skip the current cache key
                    if key_str == current_cache_key:
                        continue
                    # Check if it's an old version (v1) or contains grade patterns
                    if "v1" in key_str or any(pattern in key_str for pattern in grade_patterns):
                        matching_keys.append(key)
                except:
                    continue
            
            if matching_keys:
                self.redis.delete(*matching_keys)
                logger.info(f"🗑️ Invalidated {len(matching_keys)} old cache entries for grade {grade}")
                return True
            return False
        except Exception as e:
            logger.error(f"Old grade cache invalidation error: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_available:
            return {"redis_available": False}
        
        try:
            info = self.redis.info()
            return {
                "redis_available": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"redis_available": False, "error": str(e)}
    
    def is_cache_available(self) -> bool:
        """Check if Redis cache is available"""
        return self.redis_available
