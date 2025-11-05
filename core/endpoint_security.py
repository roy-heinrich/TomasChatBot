"""
Endpoint Security Module
Restricts access to admin and internal endpoints
"""
import os
import logging
from typing import Optional
from fastapi import HTTPException, Header, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class EndpointSecurity:
    """Security manager for API endpoints"""
    
    def __init__(self):
        # Get admin API key from environment (for production security)
        self.admin_api_key = os.environ.get("ADMIN_API_KEY", "change-this-in-production")
        
        # Public endpoints that don't require authentication
        self.public_endpoints = {
            "/",
            "/chat",
            "/clear-context",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc"
        }
        
        # Admin endpoints that require API key authentication
        self.admin_endpoints = {
            "/admin/logs",
            "/admin/metrics",
            "/admin/clear-cache",
            "/admin/cache-status",
            "/admin/connection-pool-stats",
            "/admin/preprocessing-cache-stats",
            "/metrics",
            "/comprehensive-test",
            "/test",
            "/clear-memory",
            "/clear-cache",
            "/cache-status"
        }
        
        # IP whitelist for admin endpoints (optional)
        self.admin_ip_whitelist = set(os.environ.get("ADMIN_IP_WHITELIST", "127.0.0.1,::1").split(","))
        
        logger.info(f"✅ Endpoint security initialized with {len(self.admin_endpoints)} protected endpoints")
    
    def is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public"""
        # Remove query parameters
        clean_path = path.split("?")[0]
        return clean_path in self.public_endpoints
    
    def is_admin_endpoint(self, path: str) -> bool:
        """Check if endpoint requires admin authentication"""
        # Remove query parameters
        clean_path = path.split("?")[0]
        return clean_path in self.admin_endpoints or clean_path.startswith("/admin/")
    
    def verify_admin_access(self, api_key: Optional[str], client_ip: str) -> tuple[bool, str]:
        """Verify admin access with API key and optionally IP whitelist"""
        
        # Check API key
        if not api_key:
            return False, "Missing API key"
        
        if api_key != self.admin_api_key:
            logger.warning(f"Invalid API key attempt from {client_ip}")
            return False, "Invalid API key"
        
        # Optional: Check IP whitelist (disabled by default, enable in production)
        # Uncomment the following lines to enable IP whitelisting:
        # if client_ip not in self.admin_ip_whitelist:
        #     logger.warning(f"Unauthorized IP access attempt: {client_ip}")
        #     return False, "IP not whitelisted"
        
        return True, "Access granted"
    
    async def check_endpoint_access(self, request: Request, x_api_key: Optional[str] = Header(None)) -> bool:
        """Middleware function to check endpoint access"""
        path = request.url.path
        
        # Allow public endpoints
        if self.is_public_endpoint(path):
            return True
        
        # Check admin endpoints
        if self.is_admin_endpoint(path):
            client_ip = request.client.host if request.client else "unknown"
            
            is_valid, message = self.verify_admin_access(x_api_key, client_ip)
            
            if not is_valid:
                logger.warning(f"Unauthorized access attempt to {path} from {client_ip}: {message}")
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Access Forbidden",
                        "message": "You don't have permission to access this endpoint. Admin API key required.",
                        "endpoint": path
                    }
                )
            
            return True
        
        # Default: allow access (for any new endpoints not yet categorized)
        return True

# Global instance
endpoint_security = EndpointSecurity()


# Dependency function for FastAPI
async def require_admin_access(request: Request, x_api_key: Optional[str] = Header(None)):
    """FastAPI dependency to require admin access"""
    await endpoint_security.check_endpoint_access(request, x_api_key)


# Middleware function for global endpoint protection
async def endpoint_security_middleware(request: Request, call_next):
    """Middleware to protect all endpoints"""
    try:
        # Get API key from header
        x_api_key = request.headers.get("x-api-key")
        
        # Check access
        await endpoint_security.check_endpoint_access(request, x_api_key)
        
        # Process request
        response = await call_next(request)
        return response
        
    except HTTPException as e:
        # Return 403 Forbidden for unauthorized access
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
    except Exception as e:
        logger.error(f"Endpoint security middleware error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
