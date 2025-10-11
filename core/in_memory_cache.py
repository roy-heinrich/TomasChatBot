"""
In-Memory Cache Alternative
Works in any environment without external dependencies
"""
import time
import hashlib
from typing import Dict, Any, Optional
from collections import OrderedDict

class InMemoryCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.timestamps = {}
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self.timestamps:
            return True
        
        expiry_time = self.timestamps[key]
        return time.time() > expiry_time
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache and not self._is_expired(key):
            # Move to end (LRU)
            self.cache.move_to_end(key)
            return self.cache[key]
        
        # Remove expired entry
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        # Remove oldest entries if at capacity
        while len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
        
        # Set new entry
        self.cache[key] = value
        self.timestamps[key] = time.time() + ttl
        return True
    
    def clear(self) -> bool:
        """Clear all cache entries"""
        self.cache.clear()
        self.timestamps.clear()
        return True
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)
