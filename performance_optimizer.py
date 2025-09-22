"""
Performance Optimizer for TomasChatBot
Optimizes response times while maintaining functionality
"""

import asyncio
import logging
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from collections import deque
import weakref
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    response_time: float
    cache_hit: bool
    operation_type: str
    timestamp: float

class PerformanceOptimizer:
    """
    Performance optimizer that improves response times through:
    - Intelligent caching
    - Parallel processing
    - Connection pooling
    - Timeout management
    """
    
    def __init__(self):
        self.response_cache = {}
        self.operation_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.max_cache_size = 1000
        
        # Performance tracking
        self.metrics = deque(maxlen=1000)  # Keep last 1000 operations
        self.performance_thresholds = {
            "fast": 1.0,      # < 1 second
            "medium": 3.0,    # < 3 seconds
            "slow": 10.0      # < 10 seconds
        }
        
        # Connection pooling
        self.connection_pool = deque(maxlen=10)
        self.pool_lock = threading.Lock()
        
        # Timeout management
        self.default_timeouts = {
            "supabase_search": 15.0,
            "summarized_text": 3.0,
            "groq_api": 30.0,
            "nlu_processing": 5.0
        }
        
    def _get_cache_key(self, operation: str, params: Dict[str, Any]) -> str:
        """Generate cache key for operation"""
        # Create a deterministic key from operation and parameters
        import json
        key_data = f"{operation}_{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        return time.time() - cache_entry.get("timestamp", 0) < self.cache_ttl
    
    async def cached_operation(self, operation_name: str, operation_func: Callable, 
                             params: Dict[str, Any], cache_ttl: Optional[int] = None) -> Any:
        """Execute operation with intelligent caching"""
        start_time = time.time()
        cache_key = self._get_cache_key(operation_name, params)
        
        # Check cache first
        if cache_key in self.operation_cache:
            cache_entry = self.operation_cache[cache_key]
            if self._is_cache_valid(cache_entry):
                response_time = time.time() - start_time
                self._record_metrics(PerformanceMetrics(
                    response_time=response_time,
                    cache_hit=True,
                    operation_type=operation_name,
                    timestamp=time.time()
                ))
                logger.info(f"✅ Cache hit for {operation_name} ({response_time:.3f}s)")
                return cache_entry["result"]
        
        # Execute operation
        try:
            result = await operation_func(**params)
            
            # Cache result
            if len(self.operation_cache) < self.max_cache_size:
                self.operation_cache[cache_key] = {
                    "result": result,
                    "timestamp": time.time()
                }
            
            response_time = time.time() - start_time
            self._record_metrics(PerformanceMetrics(
                response_time=response_time,
                cache_hit=False,
                operation_type=operation_name,
                timestamp=time.time()
            ))
            
            # Log performance
            if response_time > self.performance_thresholds["slow"]:
                logger.warning(f"⚠️ Slow operation: {operation_name} took {response_time:.3f}s")
            elif response_time > self.performance_thresholds["medium"]:
                logger.info(f"⏱️ Medium operation: {operation_name} took {response_time:.3f}s")
            else:
                logger.info(f"⚡ Fast operation: {operation_name} took {response_time:.3f}s")
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"❌ Operation {operation_name} failed after {response_time:.3f}s: {e}")
            raise
    
    async def parallel_operations(self, operations: List[Dict[str, Any]], 
                                max_concurrent: int = 3) -> List[Any]:
        """Execute multiple operations in parallel with concurrency control"""
        start_time = time.time()
        results = []
        
        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_semaphore(operation):
            async with semaphore:
                return await self.cached_operation(
                    operation["name"],
                    operation["func"],
                    operation["params"],
                    operation.get("cache_ttl")
                )
        
        try:
            # Execute operations in parallel
            tasks = [execute_with_semaphore(op) for op in operations]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"❌ Parallel operation {operations[i]['name']} failed: {result}")
                    processed_results.append(None)
                else:
                    processed_results.append(result)
            
            total_time = time.time() - start_time
            logger.info(f"🚀 Parallel operations completed in {total_time:.3f}s ({len(operations)} operations)")
            
            return processed_results
            
        except Exception as e:
            logger.error(f"❌ Parallel operations failed: {e}")
            return [None] * len(operations)
    
    async def timeout_operation(self, operation_func: Callable, timeout: float, 
                              operation_name: str, *args, **kwargs) -> Any:
        """Execute operation with timeout protection"""
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                operation_func(*args, **kwargs),
                timeout=timeout
            )
            
            response_time = time.time() - start_time
            logger.info(f"✅ {operation_name} completed in {response_time:.3f}s")
            return result
            
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            logger.error(f"⏰ {operation_name} timed out after {timeout}s (actual: {response_time:.3f}s)")
            raise
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"❌ {operation_name} failed after {response_time:.3f}s: {e}")
            raise
    
    def _record_metrics(self, metrics: PerformanceMetrics):
        """Record performance metrics"""
        self.metrics.append(metrics)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.metrics:
            return {"message": "No performance data available"}
        
        # Calculate statistics
        response_times = [m.response_time for m in self.metrics]
        cache_hits = sum(1 for m in self.metrics if m.cache_hit)
        total_operations = len(self.metrics)
        
        # Performance distribution
        fast_ops = sum(1 for t in response_times if t < self.performance_thresholds["fast"])
        medium_ops = sum(1 for t in response_times if self.performance_thresholds["fast"] <= t < self.performance_thresholds["medium"])
        slow_ops = sum(1 for t in response_times if t >= self.performance_thresholds["medium"])
        
        # Operation type breakdown
        operation_types = {}
        for metric in self.metrics:
            op_type = metric.operation_type
            if op_type not in operation_types:
                operation_types[op_type] = {"count": 0, "total_time": 0, "cache_hits": 0}
            operation_types[op_type]["count"] += 1
            operation_types[op_type]["total_time"] += metric.response_time
            if metric.cache_hit:
                operation_types[op_type]["cache_hits"] += 1
        
        # Calculate averages
        for op_type in operation_types:
            op_data = operation_types[op_type]
            op_data["avg_time"] = op_data["total_time"] / op_data["count"]
            op_data["cache_hit_rate"] = op_data["cache_hits"] / op_data["count"]
        
        return {
            "total_operations": total_operations,
            "cache_hit_rate": cache_hits / total_operations,
            "average_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "performance_distribution": {
                "fast": fast_ops,
                "medium": medium_ops,
                "slow": slow_ops
            },
            "operation_breakdown": operation_types,
            "cache_size": len(self.operation_cache)
        }
    
    def optimize_cache(self):
        """Optimize cache by removing old entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.operation_cache.items():
            if current_time - entry["timestamp"] > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.operation_cache[key]
        
        if expired_keys:
            logger.info(f"🧹 Removed {len(expired_keys)} expired cache entries")
    
    def clear_cache(self):
        """Clear all caches"""
        self.operation_cache.clear()
        self.response_cache.clear()
        logger.info("🧹 All caches cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "operation_cache_size": len(self.operation_cache),
            "response_cache_size": len(self.response_cache),
            "max_cache_size": self.max_cache_size,
            "cache_ttl": self.cache_ttl
        }

class ConnectionPool:
    """Optimized connection pool for database operations"""
    
    def __init__(self, pool_size: int = 5):
        self.pool_size = pool_size
        self.connections = deque(maxlen=pool_size)
        self.available_connections = deque(maxlen=pool_size)
        self.lock = threading.Lock()
        self.initialized = False
    
    def initialize_pool(self, create_connection_func: Callable):
        """Initialize connection pool"""
        with self.lock:
            if self.initialized:
                return
            
            try:
                for _ in range(self.pool_size):
                    conn = create_connection_func()
                    self.connections.append(conn)
                    self.available_connections.append(conn)
                self.initialized = True
                logger.info(f"✅ Connection pool initialized with {self.pool_size} connections")
            except Exception as e:
                logger.error(f"❌ Failed to initialize connection pool: {e}")
                raise
    
    async def get_connection(self):
        """Get connection from pool"""
        with self.lock:
            if self.available_connections:
                return self.available_connections.popleft()
            elif len(self.connections) < self.pool_size:
                # Create new connection if under limit
                conn = self.connections[0] if self.connections else None
                if conn:
                    self.connections.append(conn)
                    return conn
            return None
    
    def return_connection(self, connection):
        """Return connection to pool"""
        with self.lock:
            if len(self.available_connections) < self.pool_size:
                self.available_connections.append(connection)
    
    def close_all(self):
        """Close all connections"""
        with self.lock:
            self.connections.clear()
            self.available_connections.clear()
            self.initialized = False
            logger.info("🔒 All connections closed")

# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()
