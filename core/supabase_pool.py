#!/usr/bin/env python3
"""
Supabase Connection Pool Manager
Optimizes database connections for better performance
"""
import os
import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from supabase import create_client, Client
import time

logger = logging.getLogger(__name__)

class SupabaseConnectionPool:
    """Manages Supabase connections with pooling optimization"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.connection_stats = {
            'total_queries': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'avg_response_time': 0.0,
            'last_reset': time.time()
        }
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the connection pool"""
        try:
            # Get Supabase credentials
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
            
            if not supabase_url or not supabase_key:
                logger.error("❌ Supabase credentials not found")
                return False
            
            # Create client with TRANSACTION MODE connection pooling
            # Transaction mode is better for high-traffic applications like chatbots
            try:
                # Try transaction mode first (better for high traffic)
                if 'db.' in supabase_url:
                    transaction_url = supabase_url.replace('db.', 'db-transaction.')
                    logger.info("🔄 Attempting to use TRANSACTION MODE connection pooling")
                else:
                    # If no db. subdomain, use original URL
                    transaction_url = supabase_url
                    logger.info("🔄 Using original URL for connection pooling")
                
                self.client = create_client(
                    transaction_url,  # Use transaction mode URL
                    supabase_key
                )
                logger.info("✅ TRANSACTION MODE connection pooling enabled")
                
            except Exception as e:
                logger.warning(f"⚠️ Transaction mode failed, falling back to session mode: {e}")
                
                # Fallback to session mode
                self.client = create_client(
                    supabase_url,  # Use original URL (session mode)
                    supabase_key
                )
                logger.info("✅ SESSION MODE connection pooling enabled (fallback)")
            
            # Test connection
            await self._test_connection()
            
            self._initialized = True
            logger.info("✅ Supabase connection pool initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase pool: {e}")
            return False
    
    async def _test_connection(self):
        """Test the database connection"""
        try:
            # Simple test query
            result = self.client.table("chatbot_prompts").select("id").limit(1).execute()
            logger.info("✅ Database connection test successful")
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool"""
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Use the pooled client
            yield self.client
            self.connection_stats['pool_hits'] += 1
            
        except Exception as e:
            logger.error(f"❌ Database connection error: {e}")
            self.connection_stats['pool_misses'] += 1
            raise
        finally:
            # Update stats
            response_time = time.time() - start_time
            self.connection_stats['total_queries'] += 1
            self._update_avg_response_time(response_time)
    
    def _update_avg_response_time(self, response_time: float):
        """Update average response time"""
        total = self.connection_stats['total_queries']
        current_avg = self.connection_stats['avg_response_time']
        
        # Calculate rolling average
        self.connection_stats['avg_response_time'] = (
            (current_avg * (total - 1) + response_time) / total
        )
    
    async def execute_query(self, query_func, *args, **kwargs):
        """Execute a query with connection pooling"""
        async with self.get_connection() as client:
            return await query_func(client, *args, **kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return {
            **self.connection_stats,
            'pool_hit_rate': (
                self.connection_stats['pool_hits'] / 
                max(self.connection_stats['total_queries'], 1) * 100
            ),
            'uptime': time.time() - self.connection_stats['last_reset']
        }
    
    async def health_check(self) -> bool:
        """Check if the connection pool is healthy"""
        try:
            async with self.get_connection() as client:
                result = client.table("chatbot_prompts").select("id").limit(1).execute()
                return True
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False

# Global connection pool instance
connection_pool = SupabaseConnectionPool()

# Convenience functions
async def get_supabase_client():
    """Get a Supabase client from the pool"""
    if not connection_pool._initialized:
        await connection_pool.initialize()
    return connection_pool.client

async def execute_supabase_query(query_func, *args, **kwargs):
    """Execute a Supabase query with connection pooling"""
    return await connection_pool.execute_query(query_func, *args, **kwargs)

async def get_pool_stats():
    """Get connection pool statistics"""
    return connection_pool.get_stats()

async def check_pool_health():
    """Check connection pool health"""
    return await connection_pool.health_check()
