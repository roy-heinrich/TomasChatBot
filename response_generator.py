"""
Advanced Response Generation Intelligence System
==============================================

This module provides sophisticated response generation capabilities including:
- NLP-based template matching and selection
- Context-aware response customization
- Intelligent follow-up question generation
- Dynamic response adaptation based on user profile
- Multi-turn conversation flow management
- Response tone and style adaptation
"""

import re
import logging
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ResponseTone(Enum):
    """Different response tones for adaptation"""
    FORMAL = "formal"
    FRIENDLY = "friendly"
    ENTHUSIASTIC = "enthusiastic"
    HELPFUL = "helpful"
    REASSURING = "reassuring"
    PROFESSIONAL = "professional"

class ResponseType(Enum):
    """Types of responses for different contexts"""
    GREETING = "greeting"
    INFORMATION = "information"
    ENROLLMENT_GUIDANCE = "enrollment_guidance"
    CLARIFICATION = "clarification"
    FOLLOW_UP = "follow_up"
    CONFIRMATION = "confirmation"
    GOODBYE = "goodbye"

@dataclass
class ResponseTemplate:
    """Template for generating contextual responses"""
    template_id: str
    response_type: ResponseType
    intent_pattern: str
    base_template: str
    personalization_slots: List[str]
    follow_up_questions: List[str]
    tone_variants: Dict[ResponseTone, str]
    conditions: Dict[str, Any]
    priority: int = 5

@dataclass
class ResponseContext:
    """Context information for response generation"""
    user_name: str = ""
    child_name: str = ""
    child_age: int = 0
    child_grade: str = ""
    user_language: str = "en"
    conversation_stage: str = "greeting"
    previous_topics: List[str] = None
    user_mood: str = "neutral"
    communication_style: str = "neutral"
    follow_up_needed: bool = False
    is_returning_user: bool = False
    
    def __post_init__(self):
        if self.previous_topics is None:
            self.previous_topics = []

class ResponseGenerationEngine:
    """
    Advanced response generation system with NLP-based intelligence
    """
    
    def __init__(self):
        self.response_templates = {}
        self.context_patterns = {}
        self.follow_up_strategies = {}
        self._initialize_templates()
        self._initialize_context_patterns()
        logger.info("🎯 Response Generation Intelligence initialized")
    
    def _initialize_templates(self):
        """Initialize response templates for different scenarios"""
        
        # Greeting templates with personalization
        greeting_templates = [
            ResponseTemplate(
                template_id="greeting_new_user",
                response_type=ResponseType.GREETING,
                intent_pattern="greeting.*",
                base_template="Hello{user_name}! 👋 I'm TOMAS, your friendly school assistant at Tomas SM. Bautista Elementary School! How can I help you today?",
                personalization_slots=["user_name"],
                follow_up_questions=[
                    "Are you interested in enrolling a child?",
                    "Would you like to know about our programs?",
                    "Do you have any questions about our school?"
                ],
                tone_variants={
                    ResponseTone.FRIENDLY: "Hi there{user_name}! 😊 I'm TOMAS, and I'm excited to help you learn about our amazing school!",
                    ResponseTone.FORMAL: "Good {time_period}{user_name}. I am TOMAS, the digital assistant for Tomas SM. Bautista Elementary School. How may I assist you today?",
                    ResponseTone.ENTHUSIASTIC: "Hey{user_name}! 🎉 Welcome to TOMAS! I'm super excited to help you discover everything awesome about our school!"
                },
                conditions={"is_returning_user": False}
            ),
            
            ResponseTemplate(
                template_id="greeting_returning_user",
                response_type=ResponseType.GREETING,
                intent_pattern="greeting.*",
                base_template="Welcome back{user_name}! 👋 Great to see you again! {context_reference} How can I help you today?",
                personalization_slots=["user_name", "context_reference"],
                follow_up_questions=[
                    "Would you like to continue where we left off?",
                    "Any new questions about {previous_topic}?",
                    "How can I assist you further?"
                ],
                tone_variants={
                    ResponseTone.FRIENDLY: "Hey there{user_name}! 😊 Nice to have you back! {context_reference}",
                    ResponseTone.PROFESSIONAL: "Welcome back{user_name}. {context_reference} How may I continue assisting you?"
                },
                conditions={"is_returning_user": True}
            )
        ]
        
        # Enrollment guidance templates
        enrollment_templates = [
            ResponseTemplate(
                template_id="enrollment_with_child_info",
                response_type=ResponseType.ENROLLMENT_GUIDANCE,
                intent_pattern="enrollment.*",
                base_template="I'd be happy to help you enroll {child_name}! {grade_info} Here's what you need to know about our enrollment process:",
                personalization_slots=["child_name", "grade_info"],
                follow_up_questions=[
                    "Would you like to know about the required documents?",
                    "Are you interested in our school schedule?",
                    "Do you have questions about tuition fees?"
                ],
                tone_variants={
                    ResponseTone.HELPFUL: "I'm here to make enrolling {child_name} as easy as possible! {grade_info}",
                    ResponseTone.ENTHUSIASTIC: "How exciting that {child_name} will be joining us! {grade_info} Let me guide you through everything!"
                },
                conditions={"has_child_name": True}
            ),
            
            ResponseTemplate(
                template_id="enrollment_general",
                response_type=ResponseType.ENROLLMENT_GUIDANCE,
                intent_pattern="enrollment.*",
                base_template="I'd be happy to help you with enrollment information! Our school welcomes students from Kindergarten to Grade 6. Here's what you need to know:",
                personalization_slots=[],
                follow_up_questions=[
                    "What grade level are you interested in?",
                    "Would you like to know about our admission requirements?",
                    "Do you have questions about the enrollment timeline?"
                ],
                tone_variants={
                    ResponseTone.PROFESSIONAL: "I can provide you with comprehensive enrollment information for Tomas SM. Bautista Elementary School.",
                    ResponseTone.FRIENDLY: "Let me help you get all the enrollment info you need! 😊"
                },
                conditions={"has_child_name": False}
            )
        ]
        
        # Information response templates
        info_templates = [
            ResponseTemplate(
                template_id="staff_inquiry_response",
                response_type=ResponseType.INFORMATION,
                intent_pattern="staff.*",
                base_template="Here's information about our dedicated school staff{context_addition}:",
                personalization_slots=["context_addition"],
                follow_up_questions=[
                    "Would you like to know about a specific teacher?",
                    "Are you interested in meeting our staff?",
                    "Do you have questions about our teaching approach?"
                ],
                tone_variants={
                    ResponseTone.PROFESSIONAL: "I can provide you with information about our qualified educational staff{context_addition}.",
                    ResponseTone.ENTHUSIASTIC: "We have an amazing team of educators{context_addition}! Let me tell you about them!"
                },
                conditions={}
            ),
            
            ResponseTemplate(
                template_id="facilities_inquiry_response",
                response_type=ResponseType.INFORMATION,
                intent_pattern="facilities.*",
                base_template="Our school has wonderful facilities to support your child's learning{child_reference}! Here's what we offer:",
                personalization_slots=["child_reference"],
                follow_up_questions=[
                    "Would you like to schedule a school tour?",
                    "Are you interested in our specific learning areas?",
                    "Do you have questions about accessibility features?"
                ],
                tone_variants={
                    ResponseTone.ENTHUSIASTIC: "You'll love our amazing facilities{child_reference}! 🏫",
                    ResponseTone.HELPFUL: "Let me show you all the great learning spaces we have{child_reference}."
                },
                conditions={}
            )
        ]
        
        # Store templates by response type
        for template_list in [greeting_templates, enrollment_templates, info_templates]:
            for template in template_list:
                if template.response_type not in self.response_templates:
                    self.response_templates[template.response_type] = []
                self.response_templates[template.response_type].append(template)
    
    def _initialize_context_patterns(self):
        """Initialize patterns for context-aware response selection"""
        
        self.context_patterns = {
            "has_child_info": lambda ctx: bool(ctx.child_name or ctx.child_age > 0 or ctx.child_grade),
            "is_enrollment_focused": lambda ctx: "enrollment" in ctx.previous_topics,
            "needs_encouragement": lambda ctx: ctx.user_mood in ["frustrated", "confused"],
            "prefers_detailed_info": lambda ctx: ctx.communication_style == "formal",
            "likes_casual_tone": lambda ctx: ctx.communication_style == "casual",
            "is_excited": lambda ctx: ctx.user_mood == "excited" or ctx.communication_style == "enthusiastic"
        }
    
    def generate_response(self, 
                         intent: str, 
                         context: ResponseContext, 
                         extracted_entities: List[Dict] = None,
                         conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Generate an intelligent, context-aware response
        """
        
        if extracted_entities is None:
            extracted_entities = []
        if conversation_history is None:
            conversation_history = []
        
        logger.info(f"🎯 Generating response for intent '{intent}' with context")
        
        # Determine response type from intent
        response_type = self._classify_response_type(intent)
        
        # Select best template for this context
        template = self._select_best_template(response_type, intent, context)
        
        if not template:
            return self._generate_fallback_response(intent, context)
        
        # Generate personalized response
        response_text = self._personalize_response(template, context, extracted_entities)
        
        # Select appropriate tone
        tone = self._determine_response_tone(context, conversation_history)
        if tone in template.tone_variants:
            response_text = self._apply_tone_variant(template.tone_variants[tone], context, extracted_entities)
        
        # Generate intelligent follow-up
        follow_up = self._generate_follow_up(template, context, conversation_history)
        
        # Add contextual enhancements
        response_text = self._add_contextual_enhancements(response_text, context, extracted_entities)
        
        return {
            "response": response_text,
            "follow_up": follow_up,
            "tone": tone.value,
            "template_id": template.template_id,
            "personalization_applied": True,
            "context_aware": True
        }
    
    def _classify_response_type(self, intent: str) -> ResponseType:
        """Classify the type of response needed based on intent"""
        
        intent_lower = intent.lower()
        
        if "greeting" in intent_lower:
            return ResponseType.GREETING
        elif "enrollment" in intent_lower:
            return ResponseType.ENROLLMENT_GUIDANCE
        elif any(word in intent_lower for word in ["staff", "teacher", "facilities", "school_info"]):
            return ResponseType.INFORMATION
        elif "clarification" in intent_lower:
            return ResponseType.CLARIFICATION
        elif "goodbye" in intent_lower:
            return ResponseType.GOODBYE
        else:
            return ResponseType.INFORMATION
    
    def _select_best_template(self, 
                            response_type: ResponseType, 
                            intent: str, 
                            context: ResponseContext) -> Optional[ResponseTemplate]:
        """Select the best template based on context and conditions"""
        
        templates = self.response_templates.get(response_type, [])
        if not templates:
            return None
        
        # Score templates based on context match
        scored_templates = []
        
        for template in templates:
            score = 0
            
            # Check intent pattern match
            if re.search(template.intent_pattern, intent, re.IGNORECASE):
                score += 10
            
            # Check condition matches
            for condition, expected_value in template.conditions.items():
                if hasattr(context, condition):
                    actual_value = getattr(context, condition)
                    if actual_value == expected_value:
                        score += 5
                elif condition == "has_child_name" and expected_value and context.child_name:
                    score += 5
                elif condition == "has_child_name" and not expected_value and not context.child_name:
                    score += 5
            
            # Bonus for personalization potential
            if template.personalization_slots and (context.user_name or context.child_name):
                score += 3
            
            scored_templates.append((score, template))
        
        # Sort by score and return best match
        scored_templates.sort(key=lambda x: x[0], reverse=True)
        
        if scored_templates and scored_templates[0][0] > 0:
            return scored_templates[0][1]
        
        # Return first template if no good match
        return templates[0] if templates else None
    
    def _personalize_response(self, 
                            template: ResponseTemplate, 
                            context: ResponseContext, 
                            entities: List[Dict]) -> str:
        """Personalize response using template and context"""
        
        response = template.base_template
        
        # Apply personalization slots
        personalizations = {
            "user_name": f" {context.user_name}" if context.user_name else "",
            "child_name": context.child_name if context.child_name else "your child",
            "grade_info": self._generate_grade_info(context),
            "context_reference": self._generate_context_reference(context),
            "context_addition": self._generate_context_addition(context),
            "child_reference": f" for {context.child_name}" if context.child_name else "",
            "time_period": self._get_time_period()
        }
        
        # Apply personalizations
        for slot, value in personalizations.items():
            placeholder = "{" + slot + "}"
            if placeholder in response:
                response = response.replace(placeholder, value)
        
        return response
    
    def _apply_tone_variant(self, 
                          tone_template: str, 
                          context: ResponseContext, 
                          entities: List[Dict]) -> str:
        """Apply tone variant with personalization"""
        
        personalizations = {
            "user_name": f" {context.user_name}" if context.user_name else "",
            "child_name": context.child_name if context.child_name else "your child",
            "grade_info": self._generate_grade_info(context),
            "context_reference": self._generate_context_reference(context),
            "child_reference": f" for {context.child_name}" if context.child_name else "",
            "time_period": self._get_time_period()
        }
        
        response = tone_template
        for slot, value in personalizations.items():
            placeholder = "{" + slot + "}"
            if placeholder in response:
                response = response.replace(placeholder, value)
        
        return response
    
    def _determine_response_tone(self, 
                               context: ResponseContext, 
                               conversation_history: List[Dict]) -> ResponseTone:
        """Determine appropriate response tone based on context"""
        
        # User mood-based tone selection
        if context.user_mood == "excited":
            return ResponseTone.ENTHUSIASTIC
        elif context.user_mood == "frustrated" or context.user_mood == "confused":
            return ResponseTone.REASSURING
        elif context.communication_style == "formal":
            return ResponseTone.PROFESSIONAL
        elif context.communication_style == "casual":
            return ResponseTone.FRIENDLY
        elif context.conversation_stage == "greeting":
            return ResponseTone.FRIENDLY
        else:
            return ResponseTone.HELPFUL
    
    def _generate_follow_up(self, 
                          template: ResponseTemplate, 
                          context: ResponseContext, 
                          conversation_history: List[Dict]) -> Optional[str]:
        """Generate intelligent follow-up questions"""
        
        if not template.follow_up_questions:
            return None
        
        # Select follow-up based on context
        available_questions = template.follow_up_questions.copy()
        
        # Filter based on conversation history to avoid repetition
        if conversation_history:
            recent_topics = [msg.get("content", "").lower() for msg in conversation_history[-3:]]
            available_questions = [
                q for q in available_questions 
                if not any(keyword in " ".join(recent_topics) for keyword in q.lower().split()[:3])
            ]
        
        if not available_questions:
            return None
        
        # Personalize follow-up if possible
        selected_question = random.choice(available_questions)
        
        # Apply personalization
        personalizations = {
            "child_name": context.child_name,
            "previous_topic": context.previous_topics[-1] if context.previous_topics else "our discussion"
        }
        
        for placeholder, value in personalizations.items():
            selected_question = selected_question.replace("{" + placeholder + "}", value or "the topic")
        
        return selected_question
    
    def _add_contextual_enhancements(self, 
                                   response: str, 
                                   context: ResponseContext, 
                                   entities: List[Dict]) -> str:
        """Add contextual enhancements to make response more intelligent"""
        
        enhancements = []
        
        # Add time-sensitive information
        if datetime.now().month in [5, 6]:  # Enrollment season
            if "enrollment" in response.lower() and not "deadline" in response.lower():
                enhancements.append("📅 Note: Enrollment for the upcoming school year is now open!")
        
        # Add encouragement for first-time users
        if not context.is_returning_user and context.conversation_stage == "greeting":
            if "help" in response.lower():
                enhancements.append("I'm here to make everything easy for you! 😊")
        
        # Add entity-specific enhancements
        for entity in entities:
            if entity.get("entity_type") == "age" and entity.get("value"):
                age_match = re.search(r"(\d+)", entity["value"])
                if age_match:
                    age = int(age_match.group(1))
                    if 5 <= age <= 12:
                        enhancements.append(f"Perfect age for elementary school! 🎒")
        
        # Combine response with enhancements
        if enhancements:
            response += " " + " ".join(enhancements)
        
        return response
    
    def _generate_grade_info(self, context: ResponseContext) -> str:
        """Generate grade-specific information"""
        
        if context.child_age > 0:
            if context.child_age <= 5:
                return "Kindergarten would be perfect!"
            elif context.child_age <= 12:
                estimated_grade = context.child_age - 5
                return f"Grade {estimated_grade} would be a great fit!"
        
        if context.child_grade:
            return f"Great choice for {context.child_grade}!"
        
        return ""
    
    def _generate_context_reference(self, context: ResponseContext) -> str:
        """Generate reference to previous conversation context"""
        
        if context.previous_topics:
            last_topic = context.previous_topics[-1]
            topic_references = {
                "enrollment": "I remember you were asking about enrollment",
                "staff": "You were interested in our teaching staff",
                "facilities": "You wanted to know about our facilities"
            }
            return topic_references.get(last_topic, f"We were discussing {last_topic}")
        
        return ""
    
    def _generate_context_addition(self, context: ResponseContext) -> str:
        """Generate contextual additions based on user profile"""
        
        if context.child_name:
            return f" for {context.child_name}"
        elif context.child_grade:
            return f" for {context.child_grade} students"
        
        return ""
    
    def _get_time_period(self) -> str:
        """Get current time period for greetings"""
        
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        else:
            return "evening"
    
    def _generate_fallback_response(self, intent: str, context: ResponseContext) -> Dict[str, Any]:
        """Generate fallback response when no template matches"""
        
        base_responses = [
            f"I'd be happy to help you{' ' + context.user_name if context.user_name else ''}! Let me assist you with that.",
            f"Thank you for your question{' ' + context.user_name if context.user_name else ''}! I'll do my best to help.",
            f"Great question{' ' + context.user_name if context.user_name else ''}! Let me provide you with the information you need."
        ]
        
        response = random.choice(base_responses)
        
        return {
            "response": response,
            "follow_up": "What specific information would you like to know?",
            "tone": "helpful",
            "template_id": "fallback",
            "personalization_applied": bool(context.user_name),
            "context_aware": False
        }
    
    def get_response_suggestions(self, 
                               context: ResponseContext, 
                               conversation_history: List[Dict] = None) -> List[str]:
        """Generate suggested responses/questions for the user"""
        
        if conversation_history is None:
            conversation_history = []
        
        suggestions = []
        
        # Context-based suggestions
        if not context.child_name and "enrollment" in context.previous_topics:
            suggestions.append("What is your child's name?")
        
        if context.child_name and not context.child_grade and not context.child_age:
            suggestions.append("What grade level are you interested in?")
        
        if "enrollment" in context.previous_topics and "fees" not in " ".join(context.previous_topics):
            suggestions.append("What are the tuition fees?")
        
        # Default suggestions
        if not suggestions:
            suggestions = [
                "Tell me about enrollment",
                "Who are the teachers?",
                "What facilities do you have?",
                "What are your school hours?"
            ]
        
        return suggestions[:3]  # Return top 3 suggestions