"""
Enhanced Conversation Flow with Advanced NLU/NLP Integration
==========================================================

This module enhances conversation flow by:
- Better integration between NLU engine and conversation memory
- Context-aware intent classification
- Improved multi-turn conversation handling
- Enhanced entity extraction and memory
- Conversation state management
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# Import existing modules
try:
    from conversation_memory import ConversationMemory, ConversationContext, UserProfile
    from nlu_engine import NLUEngine, Intent, NLUResult, Entity
    from multilingual_nlp import multilingual_nlp
    CONVERSATION_MODULES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Conversation modules not available: {e}")
    CONVERSATION_MODULES_AVAILABLE = False

@dataclass
class ConversationState:
    """Enhanced conversation state tracking"""
    current_topic: str = ""
    conversation_stage: str = "greeting"  # greeting, information_gathering, problem_solving, closing
    last_intent: str = ""
    pending_questions: List[str] = None
    follow_up_needed: bool = False
    user_mood: str = "neutral"
    clarification_needed: bool = False
    conversation_depth: int = 0  # How deep into a topic we are
    topic_switches: int = 0  # Number of topic changes
    user_engagement_level: str = "medium"  # low, medium, high
    
    def __post_init__(self):
        if self.pending_questions is None:
            self.pending_questions = []

@dataclass
class ContextualIntent:
    """Intent with conversation context"""
    intent: str
    confidence: float
    entities: List[Entity]
    context_relevance: float  # How relevant to current conversation
    requires_follow_up: bool = False
    conversation_continuation: bool = False
    topic_switch: bool = False

class EnhancedConversationFlow:
    """
    Enhanced conversation flow manager with advanced NLU/NLP integration
    """
    
    def __init__(self):
        self.conversation_memory = ConversationMemory() if CONVERSATION_MODULES_AVAILABLE else None
        self.nlu_engine = NLUEngine() if CONVERSATION_MODULES_AVAILABLE else None
        self.conversation_states: Dict[str, ConversationState] = {}
        
        # Conversation flow patterns
        self.flow_patterns = {
            "enrollment_journey": [
                "enrollment_inquiry", "enrollment_documents", "enrollment_deadline", "enrollment_process"
            ],
            "school_exploration": [
                "school_info", "school_overview", "grade_levels", "school_programs", "facilities_inquiry"
            ],
            "information_gathering": [
                "location_inquiry", "contact_info", "schedule_inquiry", "staff_inquiry"
            ]
        }
        
        # Context-aware response templates
        self.context_templates = {
            "name_recall": [
                "Of course, {user_name}! How can I help you today?",
                "Yes {user_name}, I remember you. What would you like to know?",
                "Hello again {user_name}! What can I assist you with?"
            ],
            "topic_continuation": [
                "Continuing with {topic}, let me provide more details...",
                "As we were discussing {topic}, here's additional information...",
                "Building on our conversation about {topic}..."
            ],
            "follow_up": [
                "Based on your previous question about {previous_topic}, here's what you need to know...",
                "To follow up on {previous_topic}, let me explain...",
                "Regarding your earlier question about {previous_topic}..."
            ]
        }
    
    async def analyze_with_context(self, 
                                 user_input: str, 
                                 user_id: str, 
                                 conversation_history: List[Dict] = None) -> ContextualIntent:
        """
        Analyze user input with full conversation context
        """
        
        # Get current conversation state
        state = self._get_or_create_state(user_id)
        
        # Get conversation history
        history = self.conversation_memory.get_conversation_history(user_id) if self.conversation_memory else []
        
        # Perform NLU analysis
        nlu_result = await self.nlu_engine.analyze_intent(user_input) if self.nlu_engine else None
        
        if not nlu_result:
            return ContextualIntent(
                intent="unknown",
                confidence=0.0,
                entities=[],
                context_relevance=0.0
            )
        
        # Analyze context relevance
        context_relevance = self._calculate_context_relevance(
            nlu_result.intent.value, 
            state, 
            history
        )
        
        # Determine if this is a conversation continuation
        conversation_continuation = self._is_conversation_continuation(
            nlu_result.intent.value,
            state,
            history
        )
        
        # Check for topic switch
        topic_switch = self._is_topic_switch(
            nlu_result.intent.value,
            state
        )
        
        # Determine if follow-up is needed
        requires_follow_up = self._requires_follow_up(
            nlu_result.intent.value,
            user_input,
            state
        )
        
        # Update conversation state
        self._update_conversation_state(user_id, nlu_result.intent.value, user_input)
        
        return ContextualIntent(
            intent=nlu_result.intent.value,
            confidence=nlu_result.confidence,
            entities=nlu_result.entities,
            context_relevance=context_relevance,
            requires_follow_up=requires_follow_up,
            conversation_continuation=conversation_continuation,
            topic_switch=topic_switch
        )
    
    async def generate_contextual_response(self,
                                         contextual_intent: ContextualIntent,
                                         user_id: str,
                                         base_response: str) -> str:
        """
        Generate a response that incorporates conversation context
        """
        
        state = self._get_or_create_state(user_id)
        profile = self.conversation_memory.get_user_profile(user_id) if self.conversation_memory else None
        history = self.conversation_memory.get_conversation_history(user_id, last_n=3) if self.conversation_memory else []
        
        # Start with base response
        enhanced_response = base_response
        
        # Add context-aware elements
        if contextual_intent.conversation_continuation:
            enhanced_response = self._add_continuation_context(enhanced_response, state, history)
        
        if contextual_intent.requires_follow_up:
            enhanced_response = self._add_follow_up_context(enhanced_response, state, history)
        
        # Add personalization
        if profile and profile.name:
            enhanced_response = self._add_personalization(enhanced_response, profile, contextual_intent)
        
        # Add conversation flow elements
        enhanced_response = self._add_flow_elements(enhanced_response, state, contextual_intent)
        
        return enhanced_response
    
    def _get_or_create_state(self, user_id: str) -> ConversationState:
        """Get or create conversation state for user"""
        if user_id not in self.conversation_states:
            self.conversation_states[user_id] = ConversationState()
        return self.conversation_states[user_id]
    
    def _calculate_context_relevance(self, 
                                   intent: str, 
                                   state: ConversationState, 
                                   history: List) -> float:
        """Calculate how relevant the intent is to current conversation context"""
        
        if not history:
            return 0.5  # Neutral for new conversations
        
        # Check if intent matches current topic
        if intent == state.last_intent:
            return 0.9  # High relevance for same intent
        
        # Check conversation flow patterns
        for pattern_name, pattern_intents in self.flow_patterns.items():
            if intent in pattern_intents:
                # Check if we're in this flow
                recent_intents = [turn.detected_intent for turn in history[-3:]]
                if any(recent_intent in pattern_intents for recent_intent in recent_intents):
                    return 0.8  # High relevance for flow continuation
        
        # Check for follow-up patterns
        if self._is_follow_up_intent(intent, state, history):
            return 0.7  # Good relevance for follow-ups
        
        return 0.3  # Low relevance for new topics
    
    def _is_conversation_continuation(self, 
                                    intent: str, 
                                    state: ConversationState, 
                                    history: List) -> bool:
        """Determine if this is a continuation of current conversation"""
        
        if not history:
            return False
        
        # Same intent as last turn
        if intent == state.last_intent:
            return True
        
        # Check conversation flow patterns
        for pattern_name, pattern_intents in self.flow_patterns.items():
            if intent in pattern_intents:
                recent_intents = [turn.detected_intent for turn in history[-2:]]
                if any(recent_intent in pattern_intents for recent_intent in recent_intents):
                    return True
        
        return False
    
    def _is_topic_switch(self, intent: str, state: ConversationState) -> bool:
        """Determine if this is a topic switch"""
        
        if not state.last_intent:
            return False
        
        # Check if intent is in different flow pattern than last intent
        current_pattern = None
        last_pattern = None
        
        for pattern_name, pattern_intents in self.flow_patterns.items():
            if intent in pattern_intents:
                current_pattern = pattern_name
            if state.last_intent in pattern_intents:
                last_pattern = pattern_name
        
        return current_pattern != last_pattern and current_pattern is not None and last_pattern is not None
    
    def _requires_follow_up(self, intent: str, user_input: str, state: ConversationState) -> bool:
        """Determine if this interaction requires follow-up"""
        
        follow_up_intents = [
            "enrollment_inquiry", "contact_info", "help_request", 
            "clarification_request", "follow_up_question"
        ]
        
        follow_up_indicators = [
            "more", "also", "what about", "and", "additionally", 
            "can you tell me more", "what else", "anything else"
        ]
        
        return (intent in follow_up_intents or 
                any(indicator in user_input.lower() for indicator in follow_up_indicators))
    
    def _update_conversation_state(self, user_id: str, intent: str, user_input: str):
        """Update conversation state based on current interaction"""
        
        state = self._get_or_create_state(user_id)
        
        # Update last intent
        state.last_intent = intent
        
        # Update conversation stage
        if intent.startswith("greeting"):
            state.conversation_stage = "greeting"
        elif intent in ["enrollment_inquiry", "school_info", "staff_inquiry"]:
            state.conversation_stage = "information_gathering"
        elif intent in ["clarification", "help_request"]:
            state.conversation_stage = "problem_solving"
        elif intent == "goodbye":
            state.conversation_stage = "closing"
        
        # Update topic
        topic_mapping = {
            "enrollment_inquiry": "enrollment",
            "staff_inquiry": "staff_information",
            "facilities_inquiry": "school_facilities",
            "location_inquiry": "school_location",
            "schedule_inquiry": "school_schedule",
            "contact_info": "contact_information"
        }
        
        if intent in topic_mapping:
            if state.current_topic != topic_mapping[intent]:
                state.topic_switches += 1
            state.current_topic = topic_mapping[intent]
        
        # Update conversation depth
        if intent == state.last_intent:
            state.conversation_depth += 1
        else:
            state.conversation_depth = 1
        
        # Update user engagement
        if len(user_input.split()) > 10:
            state.user_engagement_level = "high"
        elif len(user_input.split()) > 5:
            state.user_engagement_level = "medium"
        else:
            state.user_engagement_level = "low"
    
    def _add_continuation_context(self, response: str, state: ConversationState, history: List) -> str:
        """Add context for conversation continuation"""
        
        if not state.current_topic:
            return response
        
        continuation_phrases = [
            f"Continuing with {state.current_topic}, ",
            f"As we were discussing {state.current_topic}, ",
            f"Building on our conversation about {state.current_topic}, "
        ]
        
        # Add continuation phrase
        import random
        continuation = random.choice(continuation_phrases)
        return continuation + response.lower()
    
    def _add_follow_up_context(self, response: str, state: ConversationState, history: List) -> str:
        """Add context for follow-up questions"""
        
        if not history:
            return response
        
        # Get previous topic
        previous_topic = state.current_topic or "your previous question"
        
        follow_up_phrases = [
            f"To follow up on {previous_topic}, ",
            f"Regarding {previous_topic}, ",
            f"Building on your question about {previous_topic}, "
        ]
        
        import random
        follow_up = random.choice(follow_up_phrases)
        return follow_up + response.lower()
    
    def _add_personalization(self, response: str, profile: UserProfile, contextual_intent: ContextualIntent) -> str:
        """Add personalization to response"""
        
        if not profile.name:
            return response
        
        # Check if this is a name recall situation
        if contextual_intent.intent in ["name_query", "greeting_with_name"]:
            name_phrases = [
                f"Of course, {profile.name}! ",
                f"Yes {profile.name}, ",
                f"Hello again {profile.name}! "
            ]
            
            import random
            name_greeting = random.choice(name_phrases)
            return name_greeting + response
        
        return response
    
    def _add_flow_elements(self, response: str, state: ConversationState, contextual_intent: ContextualIntent) -> str:
        """Add conversation flow elements"""
        
        # Add engagement elements based on user engagement level
        if state.user_engagement_level == "high":
            engagement_phrases = [
                "I appreciate your detailed questions. ",
                "Thank you for being so thorough. ",
                "I can see you're really interested in this topic. "
            ]
        elif state.user_engagement_level == "low":
            engagement_phrases = [
                "Let me know if you need more details. ",
                "Feel free to ask if you have other questions. ",
                "Is there anything specific you'd like to know? "
            ]
        else:
            engagement_phrases = [
                "I hope this helps! ",
                "Let me know if you need clarification. ",
                "Feel free to ask follow-up questions. "
            ]
        
        import random
        engagement = random.choice(engagement_phrases)
        
        # Add based on conversation stage
        if state.conversation_stage == "information_gathering":
            return response + " " + engagement
        elif state.conversation_stage == "problem_solving":
            return response + " " + engagement
        
        return response
    
    def _is_follow_up_intent(self, intent: str, state: ConversationState, history: List) -> bool:
        """Check if intent is a follow-up to previous conversation"""
        
        follow_up_patterns = {
            "enrollment_inquiry": ["enrollment_documents", "enrollment_deadline", "enrollment_process"],
            "staff_inquiry": ["contact_info", "schedule_inquiry"],
            "facilities_inquiry": ["location_inquiry", "schedule_inquiry"]
        }
        
        if not history:
            return False
        
        recent_intents = [turn.detected_intent for turn in history[-2:]]
        
        for base_intent, follow_ups in follow_up_patterns.items():
            if base_intent in recent_intents and intent in follow_ups:
                return True
        
        return False

# Global instance
enhanced_conversation_flow = EnhancedConversationFlow()
