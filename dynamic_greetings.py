"""
Dynamic Greeting Generation System using NLP/NLU
Replaces hard-coded greeting arrays with intelligent, context-aware greetings
"""

import asyncio
import json
import random
from typing import Dict, List, Optional
from datetime import datetime
import pytz
from dataclasses import dataclass

@dataclass
class GreetingContext:
    """Context information for generating personalized greetings"""
    user_name: str = ""
    child_name: str = ""
    language: str = "en"
    time_period: str = "default"
    user_timezone: str = "Asia/Manila"
    conversation_history: List[Dict] = None
    user_mood: str = ""  # detected from previous messages
    returning_user: bool = False
    previous_topics: List[str] = None
    school_context: str = "general"  # enrollment, staff_inquiry, etc.

class DynamicGreetingGenerator:
    """
    Generates contextually appropriate greetings using NLP/NLU
    instead of hard-coded arrays
    """
    
    def __init__(self, groq_client=None, openai_client=None):
        self.groq_client = groq_client
        self.openai_client = openai_client
        
        # Core greeting templates for fallback
        self.core_templates = {
            "en": {
                "base": "I'm TOMAS, the chatbot representative of Tomas SM. Bautista Elementary School!",
                "help_phrases": [
                    "What can I help you with today?",
                    "How can I assist you?",
                    "What would you like to know about our school?",
                    "How may I help you?",
                    "What brings you here today?",
                    "What information are you looking for?"
                ],
                "time_greetings": {
                    "morning": ["Good morning", "Morning", "Great morning"],
                    "afternoon": ["Good afternoon", "Afternoon", "Great afternoon"],
                    "evening": ["Good evening", "Evening", "Great evening"],
                    "default": ["Hello", "Hi", "Hey there", "Greetings"]
                }
            },
            "tl": {
                "base": "Ako si TOMAS ang chatbot representative ng Tomas SM. Bautista Elementary School!",
                "help_phrases": [
                    "Paano ko kayo matutulungan ngayon?",
                    "Ano ang maitutulong ko?",
                    "Paano ko kayo matutulungan?",
                    "Paano ko kayo matutulong?",
                    "Ano ang kailangan ninyo?",
                    "Anong impormasyon ang hinahanap ninyo?"
                ],
                "time_greetings": {
                    "morning": ["Magandang umaga", "Umaga", "Maayong umaga"],
                    "afternoon": ["Magandang hapon", "Hapon", "Maayong hapon"],
                    "evening": ["Magandang gabi", "Gabi", "Maayong gabi"],
                    "default": ["Kamusta", "Kumusta", "Hello po", "Magandang araw"]
                }
            }
        }

    async def generate_greeting(self, context: GreetingContext) -> str:
        """
        Generate a dynamic, contextually appropriate greeting
        """
        try:
            # Try AI-generated greeting first
            ai_greeting = await self._generate_ai_greeting(context)
            if ai_greeting:
                return ai_greeting
                
        except Exception as e:
            print(f"AI greeting generation failed: {e}")
        
        # Fallback to enhanced template-based generation
        return self._generate_template_greeting(context)
    
    async def _generate_ai_greeting(self, context: GreetingContext) -> Optional[str]:
        """Generate greeting using AI (Groq/OpenAI) with context awareness"""
        
        prompt = self._create_greeting_prompt(context)
        
        try:
            if self.groq_client:
                response = await self._call_groq_greeting(prompt)
            elif self.openai_client:
                response = await self._call_openai_greeting(prompt)
            else:
                return None
                
            # Validate and clean the response
            return self._validate_greeting_response(response, context)
            
        except Exception as e:
            print(f"AI greeting generation error: {e}")
            return None
    
    def _create_greeting_prompt(self, context: GreetingContext) -> str:
        """Create a detailed prompt for AI greeting generation"""
        
        # Base context
        lang_name = "English" if context.language == "en" else "Tagalog/Filipino"
        time_context = f"It's {context.time_period} time"
        
        # Personalization context
        personal_context = ""
        if context.user_name:
            personal_context += f"The user's name is {context.user_name}. "
        if context.child_name:
            personal_context += f"They have a child named {context.child_name}. "
        if context.returning_user:
            personal_context += "This is a returning user. "
        
        # Conversation context
        history_context = ""
        if context.conversation_history:
            history_context = f"Previous conversation topics: {', '.join(context.previous_topics or [])}. "
        
        # Mood/tone context
        mood_context = ""
        if context.user_mood:
            mood_context = f"User seems {context.user_mood}. "
        
        prompt = f"""
        Generate a warm, welcoming greeting for TOMAS, the chatbot representative of Tomas SM. Bautista Elementary School.
        
        Context:
        - Language: {lang_name}
        - Time: {time_context}
        - {personal_context}
        - {history_context}
        - {mood_context}
        - School context: {context.school_context}
        
        Requirements:
        1. Always introduce as "TOMAS, the chatbot representative of Tomas SM. Bautista Elementary School"
        2. Include appropriate time-based greeting ({context.time_period})
        3. Include a helpful question or offer to assist
        4. Use emojis appropriately (1-2 max)
        5. Be warm, friendly, and professional
        6. Keep it conversational and natural
        7. Make it feel personal but not overly familiar
        
        {"Language: Respond in Tagalog/Filipino" if context.language == "tl" else "Language: Respond in English"}
        
        Generate ONE greeting response only, no explanations:
        """
        
        return prompt
    
    async def _call_groq_greeting(self, prompt: str) -> str:
        """Call Groq API for greeting generation"""
        # Implementation similar to existing Groq calls
        # but optimized for greeting generation
        pass
    
    async def _call_openai_greeting(self, prompt: str) -> str:
        """Call OpenAI API for greeting generation"""
        # Implementation for OpenAI greeting generation
        pass
    
    def _validate_greeting_response(self, response: str, context: GreetingContext) -> str:
        """Validate and clean AI-generated greeting"""
        if not response:
            return ""
        
        # Clean the response
        response = response.strip()
        
        # Validate required elements
        required_elements = ["TOMAS", "Tomas SM. Bautista Elementary School"]
        for element in required_elements:
            if element not in response:
                return ""  # Invalid response, fallback to template
        
        # Ensure reasonable length (50-200 characters)
        if len(response) < 50 or len(response) > 300:
            return ""
        
        return response
    
    def _generate_template_greeting(self, context: GreetingContext) -> str:
        """
        Enhanced template-based greeting generation with more variety
        """
        lang = context.language
        if lang == "akl":
            lang = "tl"  # Use Tagalog for Aklanon
        
        templates = self.core_templates.get(lang, self.core_templates["en"])
        
        # Build greeting components
        time_greeting = random.choice(templates["time_greetings"][context.time_period])
        emoji = self._get_time_emoji(context.time_period)
        base_intro = templates["base"]
        help_phrase = random.choice(templates["help_phrases"])
        
        # Add personalization
        personal_touch = ""
        if context.user_name:
            if context.returning_user:
                personal_touch = f"Welcome back, {context.user_name}! " if lang == "en" else f"Maligayang pagbabalik, {context.user_name}! "
            else:
                personal_touch = f"Nice to meet you, {context.user_name}! " if lang == "en" else f"Natutuwa akong makilala kayo, {context.user_name}! "
        
        # Assemble greeting with variations
        greeting_styles = [
            f"{time_greeting}! {emoji} {personal_touch}{base_intro} {help_phrase}",
            f"{time_greeting}! {personal_touch}I'm TOMAS, your digital assistant at Tomas SM. Bautista Elementary School! {emoji} {help_phrase}",
            f"{time_greeting}! {emoji} {personal_touch}{base_intro} Ready to help you today! {help_phrase}"
        ]
        
        return random.choice(greeting_styles)
    
    def _get_time_emoji(self, time_period: str) -> str:
        """Get appropriate emoji for time period"""
        emoji_map = {
            "morning": "☀️",
            "afternoon": "🌤️",
            "evening": "🌙",
            "default": "👋"
        }
        return emoji_map.get(time_period, "😊")
    
    def _detect_user_mood(self, conversation_history: List[Dict]) -> str:
        """Analyze conversation history to detect user mood/tone"""
        if not conversation_history:
            return ""
        
        # Simple mood detection based on keywords
        recent_messages = conversation_history[-3:]
        text = " ".join([msg.get("content", "") for msg in recent_messages if msg.get("role") == "user"])
        
        mood_indicators = {
            "excited": ["!", "great", "awesome", "wonderful", "excited"],
            "concerned": ["worried", "concern", "problem", "issue", "help"],
            "formal": ["please", "thank you", "sir", "ma'am", "po"],
            "casual": ["hey", "hi", "sup", "what's up"]
        }
        
        for mood, indicators in mood_indicators.items():
            if any(indicator in text.lower() for indicator in indicators):
                return mood
        
        return ""

# Usage example in ChatBot class
class EnhancedChatBot:
    def __init__(self, *args, **kwargs):
        # ... existing initialization
        self.greeting_generator = DynamicGreetingGenerator(
            groq_client=self.groq_client if hasattr(self, 'groq_client') else None
        )
    
    async def get_dynamic_greeting(self, lang: str = "en", user_timezone: str = None, 
                                 conversation_history: List[Dict] = None, 
                                 user_name: str = "", child_name: str = "") -> str:
        """
        Replace the old get_greeting method with dynamic generation
        """
        
        # Extract context from conversation and user data
        context = GreetingContext(
            user_name=user_name,
            child_name=child_name,
            language=lang,
            time_period=self.get_time_period(user_timezone),
            user_timezone=user_timezone or "Asia/Manila",
            conversation_history=conversation_history or [],
            user_mood=self.greeting_generator._detect_user_mood(conversation_history or []),
            returning_user=len(conversation_history or []) > 0,
            previous_topics=self._extract_previous_topics(conversation_history or []),
            school_context=self._determine_school_context(conversation_history or [])
        )
        
        # Generate dynamic greeting
        return await self.greeting_generator.generate_greeting(context)
    
    def _extract_previous_topics(self, conversation_history: List[Dict]) -> List[str]:
        """Extract main topics from conversation history"""
        # Simple topic extraction - could be enhanced with NLU
        topics = []
        for msg in conversation_history[-5:]:  # Last 5 messages
            if msg.get("role") == "user":
                content = msg.get("content", "").lower()
                if "enroll" in content:
                    topics.append("enrollment")
                elif any(word in content for word in ["teacher", "staff"]):
                    topics.append("staff")
                elif any(word in content for word in ["location", "address"]):
                    topics.append("location")
                # Add more topic detection logic
        return list(set(topics))
    
    def _determine_school_context(self, conversation_history: List[Dict]) -> str:
        """Determine the primary school-related context"""
        if not conversation_history:
            return "general"
        
        recent_topics = self._extract_previous_topics(conversation_history)
        if recent_topics:
            return recent_topics[0]  # Primary topic
        return "general"