"""
Multi-Provider AI System
Handles multiple AI providers with intelligent fallback
"""
import logging
import asyncio
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class AIResponse:
    """Standardized AI response format"""
    content: str
    provider: str
    model: str
    tokens_used: int = 0
    cost: float = 0.0
    success: bool = True
    error: Optional[str] = None

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key
        self.model = model
        self.client = None
        self._initialize_client()
    
    @abstractmethod
    def _initialize_client(self):
        """Initialize the AI provider client"""
        pass
    
    @abstractmethod
    async def generate_response(self, prompt: str, system_prompt: str = None, 
                              max_tokens: int = 1000, temperature: float = 0.7) -> AIResponse:
        """Generate response from the AI provider"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available"""
        pass

class GroqProvider(AIProvider):
    """Groq AI Provider"""
    
    def _initialize_client(self):
        if not self.api_key:
            logger.warning("Groq API key not provided")
            return
        
        try:
            from groq import Groq
            # Initialize with custom timeout settings
            self.client = Groq(api_key=self.api_key)
            logger.info("✅ Groq client initialized")
        except ImportError:
            logger.error("❌ Groq library not installed")
        except Exception as e:
            logger.error(f"❌ Groq initialization failed: {e}")
    
    async def generate_response(self, prompt: str, system_prompt: str = None, 
                              max_tokens: int = 1000, temperature: float = 0.7) -> AIResponse:
        if not self.client:
            return AIResponse("", "groq", "llama-3.1-8b", success=False, error="Client not initialized")
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Add timeout and retry logic for rate limits
            import asyncio
            from groq import GroqError
            
            try:
                # Use asyncio.wait_for to implement custom timeout and rate limit detection
                def make_request():
                    return self.client.chat.completions.create(
                        model=self.model or "llama-3.1-8b-instant",
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                
                # Use asyncio.wait_for with short timeout to detect rate limits quickly
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, make_request),
                    timeout=3.0  # 3 second timeout to detect rate limits quickly
                )
                
                return AIResponse(
                    content=response.choices[0].message.content,
                    provider="groq",
                    model=self.model or "llama-3.1-8b",
                    tokens_used=response.usage.total_tokens if response.usage else 0,
                    success=True
                )
                
            except asyncio.TimeoutError:
                # Timeout likely means rate limit - switch to next provider
                logger.warning("🚫 Groq timeout (likely rate limited) - switching to next provider")
                return AIResponse("", "groq", self.model or "llama-3.1-8b", 
                               success=False, error="Timeout (likely rate limited)")
            
            except GroqError as e:
                # Handle specific Groq errors
                error_msg = str(e).lower()
                if any(rate_limit in error_msg for rate_limit in [
                    "rate limit", "429", "too many requests", "rate_limit_exceeded"
                ]):
                    logger.warning(f"🚫 Groq rate limited: {e}")
                    return AIResponse("", "groq", self.model or "llama-3.1-8b", 
                                   success=False, error=f"Rate limited: {e}")
                elif any(quota in error_msg for quota in [
                    "quota", "exceeded", "limit reached"
                ]):
                    logger.warning(f"🚫 Groq quota exceeded: {e}")
                    return AIResponse("", "groq", self.model or "llama-3.1-8b", 
                                   success=False, error=f"Quota exceeded: {e}")
                else:
                    logger.error(f"Groq API error: {e}")
                    return AIResponse("", "groq", self.model or "llama-3.1-8b", 
                                   success=False, error=str(e))
            
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                logger.warning(f"🚫 Groq rate limited (exception): {e}")
                return AIResponse("", "groq", self.model or "llama-3.1-8b", 
                               success=False, error=f"Rate limited: {e}")
            elif "timeout" in error_msg:
                logger.warning(f"⏰ Groq timeout: {e}")
                return AIResponse("", "groq", self.model or "llama-3.1-8b", 
                               success=False, error=f"Timeout: {e}")
            else:
                logger.error(f"Groq API error: {e}")
                return AIResponse("", "groq", self.model or "llama-3.1-8b", 
                               success=False, error=str(e))
    
    def is_available(self) -> bool:
        return self.client is not None

class HuggingFaceProvider(AIProvider):
    """Hugging Face Chat Completions API Provider"""
    
    def __init__(self, api_key: str = None, model: str = None):
        # Use environment variable if model not provided
        if not model:
            import os
            model = os.getenv('HUGGINGFACE_MODEL', 'deepseek-ai/DeepSeek-V3-0324')
        super().__init__(api_key, model)
    
    def _initialize_client(self):
        try:
            from huggingface_hub import InferenceClient
            
            if not self.api_key:
                logger.warning("Hugging Face API key not provided - using free tier")
                self.client = InferenceClient()  # Free tier
            else:
                self.client = InferenceClient(token=self.api_key)
            logger.info(f"✅ Hugging Face client initialized with model: {self.model}")
        except ImportError:
            logger.error("huggingface_hub not installed. Install with: pip install huggingface_hub")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Hugging Face client: {e}")
            self.client = None
    
    async def generate_response(self, prompt: str, system_prompt: str = None, 
                              max_tokens: int = 1000, temperature: float = 0.7) -> AIResponse:
        try:
            if not self.client:
                return AIResponse(
                    content="Hugging Face client not available",
                    provider="huggingface",
                    model=self.model,
                    success=False,
                    error="Client not initialized"
                )
            
            # Prepare messages for chat completion
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Use the working model
            model = self.model or "deepseek-ai/DeepSeek-V3-0324"
            
            try:
                # Use chat completion API
                response = self.client.chat_completion(
                    model=model,
                    messages=messages,
                    max_tokens=min(max_tokens, 100),  # Limit for free tier
                    temperature=temperature
                )
                
                if response and hasattr(response, 'choices') and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    if content.strip():
                        # Calculate tokens (estimate based on content length)
                        estimated_tokens = len(content.split()) * 1.3  # Rough estimation
                        
                        logger.info(f"✅ Hugging Face model {model} succeeded")
                        return AIResponse(
                            content=content,
                            provider="huggingface",
                            model=model,
                            success=True,
                            tokens_used=int(estimated_tokens)
                        )
                
            except Exception as e:
                logger.warning(f"⚠️ Hugging Face model {model} error: {e}")
            
            # If all models failed, return a simple response
            logger.info("🔄 All Hugging Face models failed, using enhanced fallback response")
            return AIResponse(
                content=self._generate_simple_response(prompt),
                provider="huggingface",
                model="fallback",
                success=True
            )
                
        except Exception as e:
            logger.error(f"Hugging Face API error: {e}")
            return AIResponse("", "huggingface", self.model or "microsoft/DialoGPT-medium", 
                            success=False, error=str(e))
    
    def _generate_simple_response(self, prompt: str) -> str:
        """Generate a simple response when AI models fail"""
        prompt_lower = prompt.lower()
        
        # Simple keyword-based responses
        if any(word in prompt_lower for word in ["hello", "hi", "hey", "kumusta", "kamusta", "good morning", "good afternoon"]):
            return "Hello! How can I help you with school-related questions today? I'm here to assist with information about enrollment, schedules, and other school matters."
        elif any(word in prompt_lower for word in ["thank", "thanks", "salamat", "appreciate"]):
            return "You're welcome! I'm glad I could help. Is there anything else you need assistance with regarding school information?"
        elif any(word in prompt_lower for word in ["enrollment", "enroll", "admission", "apply", "application"]):
            return "For enrollment information, please contact the school office directly. They can provide you with the most up-to-date enrollment requirements, deadlines, and procedures."
        elif any(word in prompt_lower for word in ["schedule", "time", "when", "class", "period", "timetable"]):
            return "For schedule information, please check with the school office or your teachers for the most current class schedules and timing details."
        elif any(word in prompt_lower for word in ["contact", "phone", "number", "email", "reach"]):
            return "You can contact the school office directly for contact information and assistance. They'll be able to provide you with the appropriate phone numbers and email addresses."
        elif any(word in prompt_lower for word in ["fee", "fees", "payment", "tuition", "cost"]):
            return "For information about school fees and payment details, please contact the school's finance office or main office for accurate and current pricing."
        elif any(word in prompt_lower for word in ["grade", "grades", "academic", "subject", "course"]):
            return "For academic information including grades and course details, please speak with your teachers or the academic office."
        else:
            return "I'm here to help with school-related questions. Please let me know what you need assistance with regarding enrollment, schedules, fees, or other school matters. For detailed information, you can always contact the school office directly."
    
    def is_available(self) -> bool:
        return True  # Hugging Face is always available (free tier)


class CohereProvider(AIProvider):
    """Cohere AI Provider"""
    
    def _initialize_client(self):
        if not self.api_key:
            logger.warning("Cohere API key not provided")
            return
        
        try:
            import cohere
            self.client = cohere.Client(self.api_key)
            logger.info("✅ Cohere client initialized")
        except ImportError:
            logger.error("❌ Cohere library not installed")
        except Exception as e:
            logger.error(f"❌ Cohere initialization failed: {e}")
    
    async def generate_response(self, prompt: str, system_prompt: str = None, 
                              max_tokens: int = 1000, temperature: float = 0.7) -> AIResponse:
        if not self.client:
            return AIResponse("", "cohere", "command", success=False, error="Client not initialized")
        
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            # Add timeout and better error handling
            import asyncio
            from cohere.errors import TooManyRequestsError, UnauthorizedError, BadRequestError
            
            try:
                # Use Chat API instead of deprecated Generate API
                # For Cohere, system messages should be passed as preamble
                preamble = system_prompt if system_prompt else None
                
                response = self.client.chat(
                    model=self.model or "command-a-03-2025",
                    message=prompt,
                    preamble=preamble,
                    max_tokens=min(max_tokens, 1000),  # Limit for free tier
                    temperature=temperature
                )
                
                # Calculate total tokens
                total_tokens = 0
                if hasattr(response.meta, 'tokens'):
                    tokens = response.meta.tokens
                    total_tokens = (tokens.input_tokens or 0) + (tokens.output_tokens or 0)
                
                return AIResponse(
                    content=response.text,
                    provider="cohere",
                    model=self.model or "command-a-03-2025",
                    tokens_used=total_tokens,
                    success=True
                )
                
            except (TooManyRequestsError, UnauthorizedError, BadRequestError) as e:
                # Handle specific Cohere errors
                error_msg = str(e).lower()
                if "rate limit" in error_msg or "429" in error_msg:
                    logger.warning(f"🚫 Cohere rate limited: {e}")
                    return AIResponse("", "cohere", self.model or "command", 
                                   success=False, error=f"Rate limited: {e}")
                elif "quota" in error_msg or "exceeded" in error_msg:
                    logger.warning(f"🚫 Cohere quota exceeded: {e}")
                    return AIResponse("", "cohere", self.model or "command", 
                                   success=False, error=f"Quota exceeded: {e}")
                elif "unauthorized" in error_msg or "invalid" in error_msg:
                    logger.error(f"🔑 Cohere authentication failed: {e}")
                    return AIResponse("", "cohere", self.model or "command", 
                                   success=False, error=f"Authentication failed: {e}")
                else:
                    logger.error(f"Cohere API error: {e}")
                    return AIResponse("", "cohere", self.model or "command", 
                                   success=False, error=str(e))
            
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                logger.warning(f"🚫 Cohere rate limited (exception): {e}")
                return AIResponse("", "cohere", self.model or "command", 
                               success=False, error=f"Rate limited: {e}")
            elif "timeout" in error_msg:
                logger.warning(f"⏰ Cohere timeout: {e}")
                return AIResponse("", "cohere", self.model or "command", 
                               success=False, error=f"Timeout: {e}")
            else:
                logger.error(f"Cohere API error: {e}")
                return AIResponse("", "cohere", self.model or "command", 
                               success=False, error=str(e))
    
    def is_available(self) -> bool:
        return self.client is not None

class MultiProviderAI:
    """Multi-provider AI system with intelligent fallback and rate limit monitoring"""
    
    def __init__(self):
        self.providers: List[AIProvider] = []
        self._initialize_providers()
        
        # Initialize rate limit monitor
        from core.rate_limit_monitor import rate_limit_monitor
        self.rate_monitor = rate_limit_monitor
    
    def _initialize_providers(self):
        """Initialize all available providers"""
        import os
        
        # Initialize providers in order of preference
        providers_config = [
            {
                "class": GroqProvider,
                "api_key": os.environ.get("GROQ_API_KEY"),
                "model": "llama-3.1-8b-instant"
            },
            {
                "class": HuggingFaceProvider,
                "api_key": os.environ.get("HUGGINGFACE_API_KEY"),  # Optional
                "model": "deepseek-ai/DeepSeek-V3-0324"
            },
            {
                "class": CohereProvider,
                "api_key": os.environ.get("COHERE_API_KEY"),
                "model": "command-a-03-2025"
            }
        ]
        
        for config in providers_config:
            try:
                provider = config["class"](
                    api_key=config["api_key"],
                    model=config["model"]
                )
                if provider.is_available():
                    self.providers.append(provider)
                    logger.info(f"✅ {config['class'].__name__} added to providers")
                else:
                    logger.warning(f"⚠️ {config['class'].__name__} not available")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {config['class'].__name__}: {e}")
        
        # Add local AI provider as final fallback (always available)
        try:
            from core.local_ai_provider import LocalAIProvider
            # Pass Hugging Face API key to local provider
            hf_key = os.getenv('HUGGINGFACE_API_KEY')
            local_provider = LocalAIProvider(api_key=hf_key)
            if local_provider.is_available():
                self.providers.append(local_provider)
                logger.info("✅ Local AI provider added (completely free)")
        except Exception as e:
            logger.warning(f"⚠️ Local AI provider not available: {e}")
        
        logger.info(f"🚀 Initialized {len(self.providers)} AI providers")
    
    async def generate_response(self, prompt: str, system_prompt: str = None, 
                              max_tokens: int = 1000, temperature: float = 0.7) -> AIResponse:
        """Generate response using intelligent provider fallback"""
        
        if not self.providers:
            return AIResponse("", "none", "none", success=False, 
                            error="No AI providers available")
        
        # Track provider performance for intelligent routing
        provider_errors = {}
        
        # Try each provider in order with intelligent fallback
        for i, provider in enumerate(self.providers):
            try:
                provider_name = provider.__class__.__name__
                
                # Check rate limits before attempting
                if not self.rate_monitor.can_make_request(provider_name):
                    logger.warning(f"🚫 Skipping {provider_name} - rate limited")
                    continue
                
                logger.info(f"🤖 Trying {provider_name} (attempt {i+1}/{len(self.providers)})")
                
                # Check if this provider has been failing recently (enhanced health monitoring)
                if provider_name in provider_errors and provider_errors[provider_name] > 2:
                    logger.warning(f"⚠️ Skipping {provider_name} - too many recent failures ({provider_errors[provider_name]})")
                    continue
                
                response = await provider.generate_response(
                    prompt, system_prompt, max_tokens, temperature
                )
                
                if response.success:
                    logger.info(f"✅ Success with {provider_name}")
                    # Record successful request
                    self.rate_monitor.record_request(provider_name, success=True)
                    # Reset error count on success
                    if provider_name in provider_errors:
                        del provider_errors[provider_name]
                    return response
                else:
                    # Check for specific error types
                    error_msg = response.error.lower() if response.error else ""
                    
                    if any(rate_limit in error_msg for rate_limit in [
                        "rate limit", "too many requests", "quota exceeded", 
                        "429", "rate_limit_exceeded", "requests per minute"
                    ]):
                        logger.warning(f"🚫 {provider_name} rate limited - switching to next provider")
                        # Record rate limit and set temporary block
                        self.rate_monitor.record_request(provider_name, success=False)
                        self.rate_monitor.set_rate_limit(provider_name, 60)  # Block for 1 minute
                        provider_errors[provider_name] = provider_errors.get(provider_name, 0) + 1
                        continue
                    elif any(auth_error in error_msg for auth_error in [
                        "unauthorized", "invalid api key", "authentication failed"
                    ]):
                        logger.error(f"🔑 {provider_name} authentication failed - skipping")
                        provider_errors[provider_name] = 999  # Mark as permanently failed
                        continue
                    else:
                        logger.warning(f"⚠️ {provider_name} failed: {response.error}")
                        provider_errors[provider_name] = provider_errors.get(provider_name, 0) + 1
                        continue
                    
            except Exception as e:
                error_msg = str(e).lower()
                provider_name = provider.__class__.__name__
                
                # Check for rate limiting exceptions
                if any(rate_limit in error_msg for rate_limit in [
                    "rate limit", "too many requests", "quota exceeded", 
                    "429", "rate_limit_exceeded", "requests per minute"
                ]):
                    logger.warning(f"🚫 {provider_name} rate limited (exception) - switching to next provider")
                    provider_errors[provider_name] = provider_errors.get(provider_name, 0) + 1
                    continue
                elif any(auth_error in error_msg for auth_error in [
                    "unauthorized", "invalid api key", "authentication failed"
                ]):
                    logger.error(f"🔑 {provider_name} authentication failed (exception) - skipping")
                    provider_errors[provider_name] = 999  # Mark as permanently failed
                    continue
                else:
                    logger.error(f"❌ {provider_name} error: {e}")
                    provider_errors[provider_name] = provider_errors.get(provider_name, 0) + 1
                    continue
        
        # Reset provider health after some time (every 10 minutes)
        self._reset_provider_health_if_needed()
        
        # If all providers failed, try to provide a helpful error message
        if provider_errors:
            failed_providers = [name for name, count in provider_errors.items() if count > 0]
            error_msg = f"All AI providers failed. Failed providers: {', '.join(failed_providers)}"
        else:
            error_msg = "All AI providers failed"
        
        return AIResponse("", "none", "none", success=False, error=error_msg)
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return [provider.__class__.__name__ for provider in self.providers]
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics about available providers"""
        return {
            "total_providers": len(self.providers),
            "available_providers": self.get_available_providers(),
            "primary_provider": self.providers[0].__class__.__name__ if self.providers else "None",
            "rate_limits": self.rate_monitor.get_all_provider_status()
        }
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get detailed status of all providers including rate limits"""
        status = {
            "providers": {},
            "summary": {
                "total": len(self.providers),
                "available": 0,
                "rate_limited": 0,
                "approaching_limit": 0
            }
        }
        
        for provider in self.providers:
            provider_name = provider.__class__.__name__
            provider_status = self.rate_monitor.get_provider_status(provider_name)
            
            status["providers"][provider_name] = {
                "available": provider.is_available(),
                "rate_limit_status": provider_status,
                "can_handle_request": self.rate_monitor.can_make_request(provider_name)
            }
            
            # Update summary
            if provider_status["available"]:
                status["summary"]["available"] += 1
            if provider_status["status"] == "rate_limited":
                status["summary"]["rate_limited"] += 1
            elif provider_status["status"] == "approaching_limit":
                status["summary"]["approaching_limit"] += 1
        
        return status
    
    def _reset_provider_health_if_needed(self):
        """Reset provider health after some time to allow retry of failed providers"""
        import time
        current_time = time.time()
        
        # Reset health every 10 minutes (600 seconds)
        if not hasattr(self, '_last_health_reset'):
            self._last_health_reset = current_time
            self._provider_health = {}
            return
        
        if current_time - self._last_health_reset > 600:  # 10 minutes
            self._last_health_reset = current_time
            self._provider_health = {}
            logger.info("🔄 Provider health reset - all providers can be retried")
