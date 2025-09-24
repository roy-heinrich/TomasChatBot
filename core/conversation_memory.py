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
        """Extract user name from conversation history using intelligent pattern matching"""
        for msg in reversed(conversation_history):
            if msg.get("role") == "user":
                content = msg.get("content", "").lower()
                # Enhanced name extraction patterns
                patterns = [
                    r"hi i am (\w+)",
                    r"hello i am (\w+)",
                    r"i am (\w+)",
                    r"ako si (\w+)",
                    r"ang pangalan ko ay (\w+)",
                    r"my name is (\w+)",
                    r"call me (\w+)"
                ]
                
                import re
                for pattern in patterns:
                    match = re.search(pattern, content)
                    if match:
                        potential_name = match.group(1).lower()
                        
                        # Skip common non-name words using basic heuristics
                        non_name_words = {
                            "here", "there", "back", "new", "old", "young", "tall", "short",
                            "good", "bad", "great", "fine", "okay", "ok", "well", "better",
                            "best", "worst", "nice", "cool", "awesome", "amazing", "wonderful"
                        }
                        
                        if potential_name in non_name_words:
                            continue
                            
                        name = match.group(1).title()
                        # Clean up name (remove punctuation)
                        name = ''.join(c for c in name if c.isalnum())
                        if name and len(name) > 1:
                            return name
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
        """Generate conversation context for Groq"""
        if session_id not in self.user_memories:
            return ""
        
        user_memory = self.user_memories[session_id]
        context_parts = []
        
        # Add user name context
        if user_memory.name:
            context_parts.append(f"User's name: {user_memory.name}")
        
        # Add recent topics context
        recent_topics = []
        for topic, topic_info in user_memory.topics.items():
            if topic_info.last_mentioned > datetime.now() - timedelta(hours=24):
                recent_topics.append(topic_info.topic)
        
        if recent_topics:
            context_parts.append(f"Recent topics discussed: {', '.join(recent_topics)}")
        
        # Add interaction history
        if user_memory.total_messages > 1:
            context_parts.append(f"User has sent {user_memory.total_messages} messages")
        
        return ". ".join(context_parts) + "." if context_parts else ""
    
    def get_personalized_greeting(self, session_id: str, user_name: str = None) -> str:
        """Generate personalized greeting based on memory"""
        if session_id not in self.user_memories:
            return ""
        
        user_memory = self.user_memories[session_id]
        
        if not user_memory.name:
            return ""
        
        # Get recent topics
        recent_topics = []
        for topic, topic_info in user_memory.topics.items():
            if topic_info.last_mentioned > datetime.now() - timedelta(hours=24):
                recent_topics.append(topic_info.topic.replace("_", " "))
        
        if recent_topics:
            topics_text = ", ".join(recent_topics[:3])  # Limit to 3 topics
            return f"Hi {user_memory.name}, yes I do remember you! You've been asking me about {topics_text}. What can I help you with?"
        else:
            return f"Hi {user_memory.name}, yes I do remember you! What can I help you with?"
    
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
