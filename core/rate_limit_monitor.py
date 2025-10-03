"""
Rate Limit Monitor
Monitors and manages AI provider rate limits
"""

import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class RateLimitInfo:
    """Rate limit information for a provider"""
    provider_name: str
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    current_minute_requests: int = 0
    current_hour_requests: int = 0
    current_day_requests: int = 0
    last_reset_minute: float = 0
    last_reset_hour: float = 0
    last_reset_day: float = 0
    is_rate_limited: bool = False
    rate_limit_until: Optional[float] = None

class RateLimitMonitor:
    """Monitor and manage rate limits for AI providers"""
    
    def __init__(self):
        self.providers: Dict[str, RateLimitInfo] = {}
        self._initialize_default_limits()
    
    def _initialize_default_limits(self):
        """Initialize default rate limits for known providers"""
        # Groq limits (more realistic based on actual API limits)
        self.providers["GroqProvider"] = RateLimitInfo(
            provider_name="GroqProvider",
            requests_per_minute=30,  # Groq free tier allows 30 RPM
            requests_per_hour=1000,  # More realistic hourly limit
            requests_per_day=10000   # More realistic daily limit
        )
        
        # Hugging Face limits
        self.providers["HuggingFaceProvider"] = RateLimitInfo(
            provider_name="HuggingFaceProvider",
            requests_per_minute=1000,  # Free tier
            requests_per_hour=10000,
            requests_per_day=100000
        )
        
        # Together AI limits
        self.providers["TogetherAIProvider"] = RateLimitInfo(
            provider_name="TogetherAIProvider",
            requests_per_minute=60,
            requests_per_hour=2000,
            requests_per_day=20000
        )
        
        # Cohere limits (free tier: 1M tokens/month, no credit card required)
        self.providers["CohereProvider"] = RateLimitInfo(
            provider_name="CohereProvider",
            requests_per_minute=50,  # Conservative limit for free tier
            requests_per_hour=1000,
            requests_per_day=10000
        )
        
        # Local AI (no limits)
        self.providers["LocalAIProvider"] = RateLimitInfo(
            provider_name="LocalAIProvider",
            requests_per_minute=999999,
            requests_per_hour=999999,
            requests_per_day=999999
        )
    
    def can_make_request(self, provider_name: str) -> bool:
        """Check if a provider can make a request without hitting rate limits"""
        if provider_name not in self.providers:
            return True  # Unknown provider, assume it's okay
        
        provider = self.providers[provider_name]
        current_time = time.time()
        
        # Check if currently rate limited
        if provider.is_rate_limited and provider.rate_limit_until:
            if current_time < provider.rate_limit_until:
                logger.warning(f"🚫 {provider_name} is rate limited until {datetime.fromtimestamp(provider.rate_limit_until)}")
                return False
            else:
                # Rate limit expired, reset
                provider.is_rate_limited = False
                provider.rate_limit_until = None
        
        # Reset counters if needed
        self._reset_counters_if_needed(provider, current_time)
        
        # Check limits
        if provider.current_minute_requests >= provider.requests_per_minute:
            logger.warning(f"🚫 {provider_name} minute limit reached: {provider.current_minute_requests}/{provider.requests_per_minute}")
            return False
        
        if provider.current_hour_requests >= provider.requests_per_hour:
            logger.warning(f"🚫 {provider_name} hour limit reached: {provider.current_hour_requests}/{provider.requests_per_hour}")
            return False
        
        if provider.current_day_requests >= provider.requests_per_day:
            logger.warning(f"🚫 {provider_name} day limit reached: {provider.current_day_requests}/{provider.requests_per_day}")
            return False
        
        return True
    
    def record_request(self, provider_name: str, success: bool = True):
        """Record a request for rate limit tracking"""
        if provider_name not in self.providers:
            return
        
        provider = self.providers[provider_name]
        current_time = time.time()
        
        # Reset counters if needed
        self._reset_counters_if_needed(provider, current_time)
        
        # Increment counters
        provider.current_minute_requests += 1
        provider.current_hour_requests += 1
        provider.current_day_requests += 1
        
        # If request failed due to rate limit, mark as rate limited
        if not success:
            provider.is_rate_limited = True
            provider.rate_limit_until = current_time + 60  # Rate limited for 1 minute
        
        logger.debug(f"📊 {provider_name} requests: {provider.current_minute_requests}/{provider.requests_per_minute} per minute")
    
    def _reset_counters_if_needed(self, provider: RateLimitInfo, current_time: float):
        """Reset counters if time periods have passed"""
        # Reset minute counter
        if current_time - provider.last_reset_minute >= 60:
            provider.current_minute_requests = 0
            provider.last_reset_minute = current_time
        
        # Reset hour counter
        if current_time - provider.last_reset_hour >= 3600:
            provider.current_hour_requests = 0
            provider.last_reset_hour = current_time
        
        # Reset day counter
        if current_time - provider.last_reset_day >= 86400:
            provider.current_day_requests = 0
            provider.last_reset_day = current_time
    
    def get_provider_status(self, provider_name: str) -> Dict:
        """Get current status of a provider"""
        if provider_name not in self.providers:
            return {"status": "unknown", "available": True}
        
        provider = self.providers[provider_name]
        current_time = time.time()
        
        # Reset counters if needed
        self._reset_counters_if_needed(provider, current_time)
        
        # Check if rate limited
        if provider.is_rate_limited and provider.rate_limit_until:
            if current_time < provider.rate_limit_until:
                return {
                    "status": "rate_limited",
                    "available": False,
                    "rate_limit_until": provider.rate_limit_until,
                    "requests": {
                        "minute": f"{provider.current_minute_requests}/{provider.requests_per_minute}",
                        "hour": f"{provider.current_hour_requests}/{provider.requests_per_hour}",
                        "day": f"{provider.current_day_requests}/{provider.requests_per_day}"
                    }
                }
            else:
                # Rate limit expired
                provider.is_rate_limited = False
                provider.rate_limit_until = None
        
        # Check if approaching limits
        minute_usage = provider.current_minute_requests / provider.requests_per_minute
        hour_usage = provider.current_hour_requests / provider.requests_per_hour
        day_usage = provider.current_day_requests / provider.requests_per_day
        
        if minute_usage > 0.8 or hour_usage > 0.8 or day_usage > 0.8:
            status = "approaching_limit"
        else:
            status = "available"
        
        return {
            "status": status,
            "available": True,
            "requests": {
                "minute": f"{provider.current_minute_requests}/{provider.requests_per_minute}",
                "hour": f"{provider.current_hour_requests}/{provider.requests_per_hour}",
                "day": f"{provider.current_day_requests}/{provider.requests_per_day}"
            },
            "usage_percentages": {
                "minute": minute_usage * 100,
                "hour": hour_usage * 100,
                "day": day_usage * 100
            }
        }
    
    def get_all_provider_status(self) -> Dict[str, Dict]:
        """Get status of all providers"""
        return {name: self.get_provider_status(name) for name in self.providers.keys()}
    
    def set_rate_limit(self, provider_name: str, duration_seconds: int = 60):
        """Manually set a provider as rate limited"""
        if provider_name in self.providers:
            provider = self.providers[provider_name]
            provider.is_rate_limited = True
            provider.rate_limit_until = time.time() + duration_seconds
            logger.warning(f"🚫 Manually rate limited {provider_name} for {duration_seconds} seconds")
    
    def clear_rate_limit(self, provider_name: str):
        """Clear rate limit for a provider"""
        if provider_name in self.providers:
            provider = self.providers[provider_name]
            provider.is_rate_limited = False
            provider.rate_limit_until = None
            # logger.info(f"✅ Cleared rate limit for {provider_name}")

# Global rate limit monitor instance
rate_limit_monitor = RateLimitMonitor()
