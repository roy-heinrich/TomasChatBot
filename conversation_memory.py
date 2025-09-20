"""
Advanced Conversation Memory & Context System
===========================================

This module provides sophisticated conversation memory capabilities to:
- Track conversation history and context
- Maintain user profiles and preferences
- Enable context-aware responses
- Support multi-turn conversation understanding
- Provide conversation summarization
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class ConversationTurn:
    """Represents a single turn in conversation"""
    timestamp: datetime
    user_message: str
    bot_response: str
    detected_intent: str
    extracted_entities: List[Dict]
    confidence_score: float
    context_used: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationTurn':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class UserProfile:
    """User profile with extracted information"""
    user_id: str
    name: str = ""
    child_name: str = ""
    child_age: int = 0
    child_grade: str = ""
    contact_phone: str = ""
    contact_email: str = ""
    interests: List[str] = None
    previous_topics: List[str] = None
    communication_style: str = "neutral"  # formal, casual, excited
    preferred_language: str = "en"
    enrollment_status: str = "unknown"  # interested, enrolled, graduated
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.interests is None:
            self.interests = []
        if self.previous_topics is None:
            self.previous_topics = []
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    def update_from_entities(self, entities: List[Dict]):
        """Update profile from extracted entities"""
        for entity in entities:
            entity_type = entity.get('entity_type', '')
            value = entity.get('value', '')
            
            if entity_type == 'person_name' and not self.name:
                self.name = value
            elif entity_type == 'child_name' and not self.child_name:
                self.child_name = value
            elif entity_type == 'age' and not self.child_age:
                try:
                    self.child_age = int(value.split()[0])  # Extract number from "6 years old"
                except:
                    pass
            elif entity_type == 'grade_level' and not self.child_grade:
                self.child_grade = value
            elif entity_type == 'phone_number' and not self.contact_phone:
                self.contact_phone = value
            elif entity_type == 'email' and not self.contact_email:
                self.contact_email = value
            elif entity_type == 'academic_subject':
                if value not in self.interests:
                    self.interests.append(value)
        
        self.last_updated = datetime.now()

@dataclass
class ConversationContext:
    """Current conversation context"""
    current_topic: str = ""
    last_intent: str = ""
    pending_questions: List[str] = None
    follow_up_needed: bool = False
    conversation_stage: str = "greeting"  # greeting, information_gathering, problem_solving, closing
    user_mood: str = "neutral"
    clarification_needed: bool = False
    
    def __post_init__(self):
        if self.pending_questions is None:
            self.pending_questions = []

class ConversationMemory:
    """
    Advanced conversation memory system with context tracking
    """
    
    def __init__(self, max_history_length: int = 50):
        self.max_history_length = max_history_length
        self.conversations: Dict[str, List[ConversationTurn]] = defaultdict(list)
        self.user_profiles: Dict[str, UserProfile] = {}
        self.conversation_contexts: Dict[str, ConversationContext] = defaultdict(ConversationContext)
        self.topic_transitions: Dict[str, List[str]] = defaultdict(list)
        
    def add_conversation_turn(self, 
                            user_id: str,
                            user_message: str, 
                            bot_response: str,
                            detected_intent: str,
                            extracted_entities: List[Dict],
                            confidence_score: float) -> None:
        """Add a new conversation turn to memory"""
        
        turn = ConversationTurn(
            timestamp=datetime.now(),
            user_message=user_message,
            bot_response=bot_response,
            detected_intent=detected_intent,
            extracted_entities=extracted_entities,
            confidence_score=confidence_score,
            context_used=self._get_current_context(user_id)
        )
        
        # Add to conversation history
        self.conversations[user_id].append(turn)
        
        # Trim history if too long
        if len(self.conversations[user_id]) > self.max_history_length:
            self.conversations[user_id] = self.conversations[user_id][-self.max_history_length:]
        
        # Update user profile
        self._update_user_profile(user_id, extracted_entities, detected_intent)
        
        # Update conversation context
        self._update_conversation_context(user_id, detected_intent, user_message)
        
        logger.info(f"💭 Added conversation turn for user {user_id}: {detected_intent}")
    
    def get_conversation_history(self, user_id: str, last_n: int = 10) -> List[ConversationTurn]:
        """Get recent conversation history"""
        history = self.conversations.get(user_id, [])
        return history[-last_n:] if history else []
    
    def get_user_profile(self, user_id: str) -> UserProfile:
        """Get user profile, creating if doesn't exist"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id=user_id)
        return self.user_profiles[user_id]
    
    def get_conversation_context(self, user_id: str) -> ConversationContext:
        """Get current conversation context"""
        return self.conversation_contexts[user_id]
    
    def generate_context_summary(self, user_id: str) -> Dict[str, Any]:
        """Generate a summary of conversation context for use in responses"""
        profile = self.get_user_profile(user_id)
        context = self.get_conversation_context(user_id)
        history = self.get_conversation_history(user_id, last_n=5)
        
        return {
            "user_name": profile.name,
            "child_name": profile.child_name,
            "child_age": profile.child_age,
            "child_grade": profile.child_grade,
            "interests": profile.interests,
            "communication_style": profile.communication_style,
            "preferred_language": profile.preferred_language,
            "current_topic": context.current_topic,
            "conversation_stage": context.conversation_stage,
            "last_intent": context.last_intent,
            "recent_topics": [turn.detected_intent for turn in history],
            "follow_up_needed": context.follow_up_needed,
            "pending_questions": context.pending_questions
        }
    
    def should_provide_context_response(self, user_id: str, current_intent: str) -> bool:
        """Determine if we should provide context-aware response"""
        context = self.get_conversation_context(user_id)
        history = self.get_conversation_history(user_id, last_n=3)
        
        # Provide context if:
        # 1. User is asking follow-up questions
        # 2. Current intent relates to previous topic
        # 3. User has established conversation pattern
        
        if len(history) < 2:
            return False
        
        recent_intents = [turn.detected_intent for turn in history]
        
        # Check for follow-up patterns
        follow_up_patterns = {
            "enrollment_inquiry": ["schedule_inquiry", "contact_info", "location_inquiry"],
            "staff_inquiry": ["contact_info", "schedule_inquiry"],
            "facilities_inquiry": ["location_inquiry", "schedule_inquiry"]
        }
        
        for base_intent, follow_ups in follow_up_patterns.items():
            if base_intent in recent_intents and current_intent in follow_ups:
                return True
        
        return False
    
    def get_personalized_greeting_context(self, user_id: str) -> Dict[str, Any]:
        """Get context for personalized greetings"""
        profile = self.get_user_profile(user_id)
        history = self.get_conversation_history(user_id)
        
        is_returning = len(history) > 0
        last_visit = history[-1].timestamp if history else None
        
        return {
            "is_returning_user": is_returning,
            "user_name": profile.name,
            "child_name": profile.child_name,
            "last_visit": last_visit,
            "communication_style": profile.communication_style,
            "previous_topics": profile.previous_topics,
            "enrollment_status": profile.enrollment_status
        }
    
    def detect_conversation_patterns(self, user_id: str) -> Dict[str, Any]:
        """Detect patterns in user conversation behavior"""
        history = self.get_conversation_history(user_id, last_n=20)
        
        if not history:
            return {}
        
        patterns = {
            "most_common_intents": self._get_most_common_intents(history),
            "typical_session_length": self._calculate_session_length(history),
            "question_complexity": self._assess_question_complexity(history),
            "response_satisfaction": self._estimate_satisfaction(history),
            "preferred_topics": self._extract_preferred_topics(history)
        }
        
        return patterns
    
    def _get_current_context(self, user_id: str) -> Dict[str, Any]:
        """Get current context as dictionary"""
        context = self.get_conversation_context(user_id)
        return asdict(context)
    
    def _update_user_profile(self, user_id: str, entities: List[Dict], intent: str) -> None:
        """Update user profile based on entities and intent"""
        profile = self.get_user_profile(user_id)
        profile.update_from_entities(entities)
        
        # Update communication style based on intent patterns
        if intent in ["greeting_formal", "greeting_excited", "greeting_casual"]:
            style_mapping = {
                "greeting_formal": "formal",
                "greeting_excited": "excited", 
                "greeting_casual": "casual"
            }
            profile.communication_style = style_mapping.get(intent, "neutral")
        
        # Track interests and topics
        if intent not in profile.previous_topics:
            profile.previous_topics.append(intent)
            
        # Limit topic history
        if len(profile.previous_topics) > 10:
            profile.previous_topics = profile.previous_topics[-10:]
    
    def _update_conversation_context(self, user_id: str, intent: str, user_message: str) -> None:
        """Update conversation context based on current interaction"""
        context = self.conversation_contexts[user_id]
        
        # Update last intent
        context.last_intent = intent
        
        # Update current topic
        topic_mapping = {
            "enrollment_inquiry": "enrollment",
            "staff_inquiry": "staff_information",
            "facilities_inquiry": "school_facilities", 
            "location_inquiry": "school_location",
            "schedule_inquiry": "school_schedule",
            "contact_info": "contact_information"
        }
        
        if intent in topic_mapping:
            context.current_topic = topic_mapping[intent]
        
        # Update conversation stage
        if intent.startswith("greeting"):
            context.conversation_stage = "greeting"
        elif intent in ["enrollment_inquiry", "staff_inquiry", "facilities_inquiry"]:
            context.conversation_stage = "information_gathering"
        elif intent in ["clarification", "help_request"]:
            context.conversation_stage = "problem_solving"
        elif intent == "goodbye":
            context.conversation_stage = "closing"
        
        # Detect mood from message
        context.user_mood = self._detect_user_mood(user_message)
        
        # Check if follow-up is needed
        context.follow_up_needed = self._needs_follow_up(intent, user_message)
    
    def _detect_user_mood(self, message: str) -> str:
        """Detect user mood from message content"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["excited", "happy", "great", "awesome", "fantastic"]):
            return "positive"
        elif any(word in message_lower for word in ["frustrated", "confused", "help", "problem", "issue"]):
            return "needs_help"
        elif any(word in message_lower for word in ["urgent", "asap", "quickly", "important"]):
            return "urgent"
        else:
            return "neutral"
    
    def _needs_follow_up(self, intent: str, message: str) -> bool:
        """Determine if this interaction needs follow-up"""
        
        # Intents that typically need follow-up
        follow_up_intents = ["enrollment_inquiry", "contact_info", "help_request"]
        
        # Check for incomplete information
        incomplete_indicators = ["more", "also", "what about", "and", "additionally"]
        
        return (intent in follow_up_intents or 
                any(indicator in message.lower() for indicator in incomplete_indicators))
    
    def _get_most_common_intents(self, history: List[ConversationTurn]) -> List[str]:
        """Get most common intents from history"""
        intent_counts = defaultdict(int)
        for turn in history:
            intent_counts[turn.detected_intent] += 1
        
        return sorted(intent_counts.keys(), key=intent_counts.get, reverse=True)[:3]
    
    def _calculate_session_length(self, history: List[ConversationTurn]) -> float:
        """Calculate typical session length in minutes"""
        if len(history) < 2:
            return 0.0
        
        session_durations = []
        session_start = history[0].timestamp
        
        for i in range(1, len(history)):
            current_time = history[i].timestamp
            prev_time = history[i-1].timestamp
            
            # If gap > 30 minutes, consider new session
            if (current_time - prev_time).total_seconds() > 1800:
                session_duration = (prev_time - session_start).total_seconds() / 60
                session_durations.append(session_duration)
                session_start = current_time
        
        # Add final session
        final_duration = (history[-1].timestamp - session_start).total_seconds() / 60
        session_durations.append(final_duration)
        
        return sum(session_durations) / len(session_durations) if session_durations else 0.0
    
    def _assess_question_complexity(self, history: List[ConversationTurn]) -> str:
        """Assess typical question complexity"""
        if not history:
            return "simple"
        
        complex_indicators = ["multiple", "detailed", "specific", "comprehensive"]
        complex_count = 0
        
        for turn in history:
            message_lower = turn.user_message.lower()
            if any(indicator in message_lower for indicator in complex_indicators):
                complex_count += 1
            if len(turn.user_message.split()) > 15:  # Long messages
                complex_count += 1
        
        complexity_ratio = complex_count / len(history)
        
        if complexity_ratio > 0.3:
            return "complex"
        elif complexity_ratio > 0.1:
            return "moderate"
        else:
            return "simple"
    
    def _estimate_satisfaction(self, history: List[ConversationTurn]) -> str:
        """Estimate user satisfaction based on patterns"""
        if not history:
            return "unknown"
        
        positive_indicators = ["thank", "great", "helpful", "perfect", "excellent"]
        negative_indicators = ["frustrat", "confus", "help", "problem", "wrong"]
        
        positive_count = 0
        negative_count = 0
        
        for turn in history:
            message_lower = turn.user_message.lower()
            if any(indicator in message_lower for indicator in positive_indicators):
                positive_count += 1
            if any(indicator in message_lower for indicator in negative_indicators):
                negative_count += 1
        
        if positive_count > negative_count:
            return "satisfied"
        elif negative_count > positive_count:
            return "needs_improvement"
        else:
            return "neutral"
    
    def _extract_preferred_topics(self, history: List[ConversationTurn]) -> List[str]:
        """Extract user's preferred discussion topics"""
        topic_counts = defaultdict(int)
        
        for turn in history:
            intent = turn.detected_intent
            if not intent.startswith("greeting") and intent != "unknown":
                topic_counts[intent] += 1
        
        return sorted(topic_counts.keys(), key=topic_counts.get, reverse=True)[:3]