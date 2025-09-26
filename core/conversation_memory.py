"""
Enhanced Conversation Memory System
Tracks user names, topics, and conversation context for personalized responses
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

@dataclass
class ConversationTopic:
    """Represents a topic discussed in conversation"""
    topic: str
    first_mentioned: datetime
    last_mentioned: datetime
    mention_count: int
    context: str

@dataclass
class UserMemory:
    """User's conversation memory"""
    name: str
    first_interaction: datetime
    last_interaction: datetime
    topics: Dict[str, ConversationTopic]
    total_messages: int

class ConversationMemory:
    """Enhanced conversation memory with topic tracking"""
    
    def __init__(self):
        self.user_memories: Dict[str, UserMemory] = {}
        self.session_topics: Dict[str, List[str]] = {}  # session_id -> topics
        
    def extract_user_name(self, conversation_history: List[Dict]) -> Optional[str]:
        """Enhanced user name extraction from conversation history"""
        try:
            if not conversation_history:
                return None
            
            # Look for name patterns in recent messages
            name_patterns = [
                r"my name is (\w+)",
                r"i'm (\w+)",
                r"i am (\w+)",
                r"call me (\w+)",
                r"i'm (\w+)",
                r"this is (\w+)",
                r"(\w+) here"
            ]
            
            import re
            for message in reversed(conversation_history[-5:]):  # Check last 5 messages
                if message.get("role") == "user":
                    content = message.get("content", "")
                    if content:
                        for pattern in name_patterns:
                            match = re.search(pattern, content, re.IGNORECASE)
                            if match:
                                name = match.group(1).strip()
                                if len(name) > 1 and name.isalpha():  # Valid name
                                    logger.info(f"🎯 Extracted user name: {name}")
                                    return name
            
            return None
            
        except Exception as e:
            logger.error(f"User name extraction failed: {e}")
            return None
    
    def get_user_name(self, session_id: str = None) -> Optional[str]:
        """Get user name from memory for a specific session"""
        if session_id and session_id in self.user_memories:
            return self.user_memories[session_id].name
        return None
    
    def extract_topics_from_query(self, query: str) -> List[str]:
        """Extract topics from user query using NLP"""
        topics = []
        query_lower = query.lower()
        
        # Topic keywords mapping
        topic_keywords = {
            "school_info": ["school", "grades", "curriculum", "subjects", "classes"],
            "staff_info": ["teacher", "head teacher", "principal", "adviser", "staff"],
            "location": ["where", "location", "address", "office", "building"],
            "financial": ["fees", "tuition", "payment", "cost", "money"],
            "enrollment": ["enroll", "admission", "register", "application"],
            "schedule": ["schedule", "time", "hours", "when", "calendar"],
            "uniform": ["uniform", "clothes", "dress code", "attire"],
            "safety": ["safety", "emergency", "drill", "security", "rules"],
            "activities": ["activities", "events", "programs", "clubs", "sports"]
        }
        
        # Extract topics based on keywords
        for topic, keywords in topic_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                topics.append(topic)
        
        # Extract specific entities as topics
        if "grade" in query_lower:
            import re
            grade_match = re.search(r"grade (\d+)", query_lower)
            if grade_match:
                topics.append(f"grade_{grade_match.group(1)}")
        
        if "teacher" in query_lower or "adviser" in query_lower:
            topics.append("teacher_inquiry")
        
        return topics
    
    def update_user_memory(self, session_id: str, user_name: str, query: str, 
                          conversation_history: List[Dict]) -> UserMemory:
        """Update user memory with new information"""
        now = datetime.now()
        
        # Get or create user memory
        if session_id not in self.user_memories:
            self.user_memories[session_id] = UserMemory(
                name=user_name,
                first_interaction=now,
                last_interaction=now,
                topics={},
                total_messages=0
            )
        
        user_memory = self.user_memories[session_id]
        user_memory.last_interaction = now
        user_memory.total_messages += 1
        
        # Update name if provided
        if user_name and user_name != user_memory.name:
            user_memory.name = user_name
        
        # Extract and update topics
        topics = self.extract_topics_from_query(query)
        for topic in topics:
            if topic in user_memory.topics:
                user_memory.topics[topic].last_mentioned = now
                user_memory.topics[topic].mention_count += 1
            else:
                user_memory.topics[topic] = ConversationTopic(
                    topic=topic,
                    first_mentioned=now,
                    last_mentioned=now,
                    mention_count=1,
                    context=query
                )
        
        # Update session topics
        if session_id not in self.session_topics:
            self.session_topics[session_id] = []
        
        for topic in topics:
            if topic not in self.session_topics[session_id]:
                self.session_topics[session_id].append(topic)
        
        return user_memory
    
    def get_conversation_context(self, session_id: str, user_name: str = None) -> str:
        """Enhanced conversation context generation with better memory retrieval"""
        try:
            if session_id not in self.user_memories:
                return ""
            
            user_memory = self.user_memories[session_id]
            context_parts = []
            
            # Add user name context with enhanced formatting
            if user_memory.name:
                context_parts.append(f"User's name: {user_memory.name}")
            
            # Add recent topics context with better organization
            recent_topics = []
            for topic, topic_info in user_memory.topics.items():
                if topic_info.last_mentioned > datetime.now() - timedelta(hours=24):
                    recent_topics.append(topic_info.topic.replace("_", " "))
            
            if recent_topics:
                context_parts.append(f"Recent topics discussed: {', '.join(recent_topics)}")
            
            # Add interaction history with more detail
            if user_memory.total_messages > 1:
                context_parts.append(f"User has sent {user_memory.total_messages} messages")
            
            # Add child information if available
            child_info = self._extract_child_information(session_id)
            if child_info:
                context_parts.append(f"Child information: {child_info}")
            
            # Add session-specific context
            session_context = self._get_session_context(session_id)
            if session_context:
                context_parts.append(f"Current session context: {session_context}")
            
            return ". ".join(context_parts) + "." if context_parts else ""
            
        except Exception as e:
            logger.error(f"Context generation failed: {e}")
            return ""
    
    def _extract_child_information(self, session_id: str) -> Optional[str]:
        """Extract child information from user memory"""
        try:
            if session_id not in self.user_memories:
                return None
            
            user_memory = self.user_memories[session_id]
            child_info = []
            
            # Look for child-related topics
            for topic, topic_info in user_memory.topics.items():
                if "child" in topic or "grade" in topic or "student" in topic:
                    child_info.append(topic_info.topic.replace("_", " "))
            
            return ", ".join(child_info) if child_info else None
            
        except Exception as e:
            logger.error(f"Child information extraction failed: {e}")
            return None
    
    def _get_session_context(self, session_id: str) -> Optional[str]:
        """Get session-specific context"""
        try:
            if session_id not in self.session_topics:
                return None
            
            topics = self.session_topics[session_id]
            if not topics:
                return None
            
            # Get the most recent topics for this session
            recent_topics = topics[-3:] if len(topics) > 3 else topics
            return ", ".join(recent_topics)
            
        except Exception as e:
            logger.error(f"Session context extraction failed: {e}")
            return None
    
    def get_personalized_greeting(self, session_id: str, user_name: str = None) -> str:
        """Enhanced personalized greeting with better memory integration"""
        try:
            if session_id not in self.user_memories:
                return ""
            
            user_memory = self.user_memories[session_id]
            
            if not user_memory.name:
                return ""
            
            # Get recent topics with better filtering
            recent_topics = []
            for topic, topic_info in user_memory.topics.items():
                if topic_info.last_mentioned > datetime.now() - timedelta(hours=24):
                    recent_topics.append(topic_info.topic.replace("_", " "))
            
            # Get child information for more personalized greeting
            child_info = self._extract_child_information(session_id)
            
            # Build personalized greeting
            greeting_parts = [f"Hi {user_memory.name}"]
            
            if child_info:
                greeting_parts.append(f"I remember you have a child in {child_info}")
            
            if recent_topics:
                topics_text = ", ".join(recent_topics[:3])  # Limit to 3 topics
                greeting_parts.append(f"you've been asking about {topics_text}")
            
            # Add interaction count for more context
            if user_memory.total_messages > 5:
                greeting_parts.append(f"we've had {user_memory.total_messages} conversations")
            
            greeting = ", ".join(greeting_parts) + ". What can I help you with today?"
            return greeting
            
        except Exception as e:
            logger.error(f"Personalized greeting generation failed: {e}")
            return ""
    
    def cleanup_old_memories(self, max_age_hours: int = 168):  # 7 days
        """Clean up old user memories"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        sessions_to_remove = []
        for session_id, user_memory in self.user_memories.items():
            if user_memory.last_interaction < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.user_memories[session_id]
            if session_id in self.session_topics:
                del self.session_topics[session_id]
        
        if sessions_to_remove:
            logger.info(f"Cleaned up {len(sessions_to_remove)} old user memories")
