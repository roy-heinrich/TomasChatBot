"""
Local AI Provider - Completely Free
Uses local models and Hugging Face transformers
"""
import logging
import asyncio
from typing import Optional, Dict, Any
import requests
import json

logger = logging.getLogger(__name__)

# Import AIResponse from the main ai_providers module
try:
    from core.ai_providers import AIResponse
except ImportError:
    # Fallback if import fails
    from dataclasses import dataclass
    
    @dataclass
    class AIResponse:
        content: str
        provider: str
        model: str
        tokens_used: int = 0
        cost: float = 0.0
        success: bool = True
        error: Optional[str] = None

class LocalAIProvider:
    """Local AI provider using Hugging Face models - completely free"""
    
    def __init__(self):
        self.available_models = [
            "microsoft/DialoGPT-medium",
            "microsoft/DialoGPT-small", 
            "facebook/blenderbot-400M-distill",
            "microsoft/DialoGPT-large"
        ]
        self.current_model = "microsoft/DialoGPT-medium"
        logger.info("✅ Local AI provider initialized (completely free)")
    
    async def generate_response(self, prompt: str, system_prompt: str = None, 
                              max_tokens: int = 1000, temperature: float = 0.7) -> AIResponse:
        """Generate response using local Hugging Face models"""
        
        try:
            # Use Hugging Face Inference API (free tier)
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            # Try multiple models in order of preference
            for model in self.available_models:
                try:
                    response = await self._call_huggingface_model(model, full_prompt, max_tokens, temperature)
                    if response and response.get('success'):
                        return AIResponse(
                            content=response['content'],
                            provider='local_huggingface',
                            model=model,
                            success=True,
                            cost=0.0,
                            tokens_used=0
                        )
                except Exception as e:
                    logger.warning(f"Model {model} failed: {e}")
                    continue
            
            # If all models fail, return a simple response
            return AIResponse(
                content=self._get_simple_response(prompt),
                provider='local_fallback',
                model='simple',
                success=True,
                cost=0.0,
                tokens_used=0
            )
            
        except Exception as e:
            logger.error(f"Local AI generation failed: {e}")
            return AIResponse(
                content=self._get_simple_response(prompt),
                provider='local_fallback',
                model='simple',
                success=False,
                error=str(e),
                cost=0.0,
                tokens_used=0
            )
    
    async def _call_huggingface_model(self, model: str, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Call Hugging Face model via Inference API"""
        
        try:
            # Use Hugging Face Inference API (free tier)
            url = f"https://api-inference.huggingface.co/models/{model}"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": max_tokens,
                    "temperature": temperature,
                    "return_full_text": False,
                    "do_sample": True
                }
            }
            
            # Make async request
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        if isinstance(result, list) and len(result) > 0:
                            content = result[0].get("generated_text", "")
                            return {
                                'content': content,
                                'success': True
                            }
                        else:
                            return {
                                'content': str(result),
                                'success': True
                            }
                    else:
                        error_text = await response.text()
                        return {
                            'content': f"API Error: {response.status}",
                            'success': False,
                            'error': error_text
                        }
                        
        except Exception as e:
            return {
                'content': f"Request failed: {str(e)}",
                'success': False,
                'error': str(e)
            }
    
    def _get_simple_response(self, prompt: str) -> str:
        """Get a simple response when AI models fail"""
        
        # Simple keyword-based responses
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ["hello", "hi", "hey", "kumusta", "kamusta"]):
            return "Hello! How can I help you with school-related questions today?"
        
        elif any(word in prompt_lower for word in ["thank", "thanks", "salamat"]):
            return "You're welcome! Is there anything else I can help you with?"
        
        elif any(word in prompt_lower for word in ["enrollment", "enroll", "admission"]):
            return "For enrollment information, please contact the school office directly. They can provide you with the most up-to-date details."
        
        elif any(word in prompt_lower for word in ["schedule", "time", "when"]):
            return "For schedule information, please check with the school office or your teachers for the most current details."
        
        elif any(word in prompt_lower for word in ["contact", "phone", "number"]):
            return "You can contact the school office directly for contact information and assistance."
        
        else:
            return "I'm here to help with school-related questions. Please let me know what you need assistance with, or contact the school office for more specific information."
    
    def is_available(self) -> bool:
        """Check if local AI is available"""
        return True  # Local AI is always available
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models"""
        return {
            'available_models': self.available_models,
            'current_model': self.current_model,
            'cost': 0.0,
            'free_tier': True
        }
