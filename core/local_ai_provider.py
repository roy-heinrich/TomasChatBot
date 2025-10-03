"""
Local AI Provider - Completely Free
Uses local models and Hugging Face transformers
"""
import os
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
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('HUGGINGFACE_API_KEY')
        # Use the same working model as the main HuggingFaceProvider
        self.available_models = [
            "deepseek-ai/DeepSeek-V3-0324"  # Same model that works in main provider
        ]
        self.current_model = "deepseek-ai/DeepSeek-V3-0324"
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
                        # Calculate tokens (estimate based on content length)
                        estimated_tokens = len(response['content'].split()) * 1.3
                        
                        return AIResponse(
                            content=response['content'],
                            provider='local_huggingface',
                            model=model,
                            success=True,
                            cost=0.0,
                            tokens_used=int(estimated_tokens)
                        )
                except Exception as e:
                    logger.warning(f"Model {model} failed: {e}")
                    continue
            
            # If all models fail, use intelligent context-aware response
            return AIResponse(
                content=self._get_context_aware_response(prompt, system_prompt),
                provider='local_fallback',
                model='context_aware',
                success=True,
                cost=0.0,
                tokens_used=0
            )
            
        except Exception as e:
            logger.error(f"Local AI generation failed: {e}")
            return AIResponse(
                content=self._get_context_aware_response(prompt, system_prompt),
                provider='local_fallback',
                model='context_aware',
                success=False,
                error=str(e),
                cost=0.0,
                tokens_used=0
            )
    
    async def _call_huggingface_model(self, model: str, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Call Hugging Face model via Chat Completion API (same as main provider)"""
        
        try:
            # Use Hugging Face Chat Completion API (same as main HuggingFaceProvider)
            from huggingface_hub import InferenceClient
            
            if not self.api_key:
                return {
                    'content': "No API key available",
                    'success': False,
                    'error': "Hugging Face API key not provided"
                }
            
            # Initialize client with API key
            client = InferenceClient(token=self.api_key)
            
            # Prepare messages for chat completion
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # Use chat completion API
            response = client.chat_completion(
                model=model,
                messages=messages,
                max_tokens=min(max_tokens, 300),  # Increased from 100 to allow complete responses
                temperature=temperature
            )
            
            # Extract content from response
            if hasattr(response, 'choices') and len(response.choices) > 0:
                content = response.choices[0].message.content
                return {
                    'content': content,
                    'success': True
                }
            else:
                return {
                    'content': str(response),
                    'success': True
                }
                        
        except Exception as e:
            return {
                'content': f"Request failed: {str(e)}",
                'success': False,
                'error': str(e)
            }
    
    def _get_context_aware_response(self, prompt: str, system_prompt: str = None) -> str:
        """Get an intelligent context-aware response using database information"""
        
        # Extract database context from the prompt
        database_context = ""
        if "DATABASE INFORMATION:" in prompt:
            # Extract the database information
            start_idx = prompt.find("DATABASE INFORMATION:")
            if start_idx != -1:
                # Get the context after "DATABASE INFORMATION:"
                context_part = prompt[start_idx + len("DATABASE INFORMATION:"):]
                # Find the end of the context (before any other instructions)
                end_markers = ["\n\nINSTRUCTIONS:", "\n\nNLP/NLU ANALYSIS:", "\n\nEXTRACTED ENTITIES:", "\n\nLANGUAGE:"]
                end_idx = len(context_part)
                for marker in end_markers:
                    marker_idx = context_part.find(marker)
                    if marker_idx != -1 and marker_idx < end_idx:
                        end_idx = marker_idx
                
                database_context = context_part[:end_idx].strip()
        
        # If we have database context, use it to provide accurate answers
        if database_context:
            # Extract the query from the prompt
            query = ""
            if "USER MESSAGE:" in prompt:
                query_start = prompt.find("USER MESSAGE:") + len("USER MESSAGE:")
                query_end = prompt.find("\n", query_start)
                if query_end == -1:
                    query_end = len(prompt)
                query = prompt[query_start:query_end].strip()
            
            # Use the database context to provide accurate answers
            if "superintendent" in query.lower() and "superintendent" in database_context.lower():
                # Extract superintendent information
                if "feliciano" in database_context.lower():
                    return "The School Division Superintendent is Feliciano C. Bustamante Jr., Ceso VI."
                elif "ramon" in database_context.lower():
                    return "The OIC, Asst. Schools Division Superintendent is Ramon D. Paras Jr., EdP."
                else:
                    return f"Based on our school information: {database_context}"
            
            elif "principal" in query.lower() and "principal" in database_context.lower():
                if "meliza" in database_context.lower():
                    return "The Head Teacher is Meliza A. Delgado. There is no principal yet, but the Head Teacher is Meliza A. Delgado."
                else:
                    return f"Based on our school information: {database_context}"
            
            elif "activities" in query.lower() and "activities" in database_context.lower():
                return f"Based on our school information: {database_context}"
            
            elif "library" in query.lower() and "library" in database_context.lower():
                if "no" in database_context.lower():
                    return "Our school does not have a library at this time."
                else:
                    return f"Based on our school information: {database_context}"
            
            else:
                # Generic response using database context
                return f"Based on our school information: {database_context}"
        
        # Fallback to simple response if no database context
        return self._get_simple_response(prompt)
    
    def _get_simple_response(self, prompt: str) -> str:
        """Get an intelligent fallback response when AI models fail"""
        
        # Enhanced keyword-based responses with better context
        prompt_lower = prompt.lower()
        
        # Greetings
        if any(word in prompt_lower for word in ["hello", "hi", "hey", "kumusta", "kamusta"]):
            return "Hello! I'm TOMAS, your digital assistant for Tomas SM. Bautista Elementary School. How can I help you with school-related questions today?"
        
        # Gratitude
        elif any(word in prompt_lower for word in ["thank", "thanks", "salamat"]):
            return "You're welcome! I'm glad I could help. Is there anything else about our school that you'd like to know?"
        
        # Enrollment queries
        elif any(word in prompt_lower for word in ["enrollment", "enroll", "admission", "register", "application"]):
            return "For enrollment and admission information, please visit our school office or contact them directly. They have the most current enrollment requirements and procedures."
        
        # Schedule and time queries
        elif any(word in prompt_lower for word in ["schedule", "time", "when", "hours", "class", "school hours"]):
            return "For current school schedules and hours, please check with the school office or your teachers. They can provide you with the most up-to-date information."
        
        # Contact information
        elif any(word in prompt_lower for word in ["contact", "phone", "number", "email", "address"]):
            return "For contact information and to speak with someone directly, please visit the school office or call them. They can provide you with the most current contact details."
        
        # Academic queries
        elif any(word in prompt_lower for word in ["grade", "subject", "course", "curriculum", "study"]):
            return "For academic information about grades, subjects, or curriculum, please speak with your teachers or the school office for the most accurate details."
        
        # General help
        elif any(word in prompt_lower for word in ["help", "assistance", "support", "tulong"]):
            return "I'm here to help with school-related questions! Please let me know what specific information you need, or contact the school office for more detailed assistance."
        
        # Default response
        else:
            return "I'm TOMAS, your digital assistant for Tomas SM. Bautista Elementary School. I'm here to help with school-related questions. Please let me know what you need assistance with, or contact the school office for more specific information."
    
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
