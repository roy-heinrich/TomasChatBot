"""
Multi-Provider AI System
Handles multiple AI providers with intelligent fallback
"""
import logging
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from abc import ABC, abstractmethod

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
            
            response = self.client.chat.completions.create(
                model=self.model or "llama-3.1-8b",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return AIResponse(
                content=response.choices[0].message.content,
                provider="groq",
                model=self.model or "llama-3.1-8b",
                tokens_used=response.usage.total_tokens if response.usage else 0,
                success=True
            )
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return AIResponse("", "groq", self.model or "llama-3.1-8b", success=False, error=str(e))
    
    def is_available(self) -> bool:
        return self.client is not None

class HuggingFaceProvider(AIProvider):
    """Hugging Face Inference API Provider"""
    
    def _initialize_client(self):
        if not self.api_key:
            logger.warning("Hugging Face API key not provided - using free tier")
            self.client = "free"  # Free tier doesn't require API key
        else:
            self.client = self.api_key
        logger.info("✅ Hugging Face client initialized")
    
    async def generate_response(self, prompt: str, system_prompt: str = None, 
                              max_tokens: int = 1000, temperature: float = 0.7) -> AIResponse:
        try:
            import requests
            
            # Use a good free model
            model = self.model or "microsoft/DialoGPT-medium"
            
            # Prepare the request
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers=headers,
                json={
                    "inputs": full_prompt,
                    "parameters": {
                        "max_length": max_tokens,
                        "temperature": temperature,
                        "return_full_text": False
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    content = result[0].get("generated_text", "")
                else:
                    content = str(result)
                
                return AIResponse(
                    content=content,
                    provider="huggingface",
                    model=model,
                    success=True
                )
            else:
                return AIResponse("", "huggingface", model, success=False, 
                                error=f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"Hugging Face API error: {e}")
            return AIResponse("", "huggingface", self.model or "microsoft/DialoGPT-medium", 
                            success=False, error=str(e))
    
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
            
            response = self.client.generate(
                model=self.model or "command",
                prompt=full_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return AIResponse(
                content=response.generations[0].text,
                provider="cohere",
                model=self.model or "command",
                success=True
            )
        except Exception as e:
            logger.error(f"Cohere API error: {e}")
            return AIResponse("", "cohere", self.model or "command", success=False, error=str(e))
    
    def is_available(self) -> bool:
        return self.client is not None

class MultiProviderAI:
    """Multi-provider AI system with intelligent fallback"""
    
    def __init__(self):
        self.providers: List[AIProvider] = []
        self._initialize_providers()
    
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
                "model": "microsoft/DialoGPT-medium"
            },
            {
                "class": CohereProvider,
                "api_key": os.environ.get("COHERE_API_KEY"),
                "model": "command"
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
            local_provider = LocalAIProvider()
            if local_provider.is_available():
                self.providers.append(local_provider)
                logger.info("✅ Local AI provider added (completely free)")
        except Exception as e:
            logger.warning(f"⚠️ Local AI provider not available: {e}")
        
        logger.info(f"🚀 Initialized {len(self.providers)} AI providers")
    
    async def generate_response(self, prompt: str, system_prompt: str = None, 
                              max_tokens: int = 1000, temperature: float = 0.7) -> AIResponse:
        """Generate response using the first available provider"""
        
        if not self.providers:
            return AIResponse("", "none", "none", success=False, 
                            error="No AI providers available")
        
        # Try each provider in order
        for i, provider in enumerate(self.providers):
            try:
                logger.info(f"🤖 Trying {provider.__class__.__name__} (attempt {i+1}/{len(self.providers)})")
                
                response = await provider.generate_response(
                    prompt, system_prompt, max_tokens, temperature
                )
                
                if response.success:
                    logger.info(f"✅ Success with {provider.__class__.__name__}")
                    return response
                else:
                    logger.warning(f"⚠️ {provider.__class__.__name__} failed: {response.error}")
                    
            except Exception as e:
                logger.error(f"❌ {provider.__class__.__name__} error: {e}")
                continue
        
        # If all providers failed
        return AIResponse("", "none", "none", success=False, 
                        error="All AI providers failed")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return [provider.__class__.__name__ for provider in self.providers]
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics about available providers"""
        return {
            "total_providers": len(self.providers),
            "available_providers": self.get_available_providers(),
            "primary_provider": self.providers[0].__class__.__name__ if self.providers else "None"
        }
