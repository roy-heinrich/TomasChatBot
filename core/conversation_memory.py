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
        import threading
        self.user_memories: Dict[str, UserMemory] = {}
        self.session_topics: Dict[str, List[str]] = {}  # session_id -> topics
        self._lock = threading.Lock()  # Thread safety for concurrent access
        
    def extract_user_name(self, conversation_history: List[Dict]) -> Optional[str]:
        """Enhanced user name extraction from conversation history"""
        try:
            if not conversation_history:
                return None
            
            # Look for name patterns in recent messages
            # 🎯 FIX: Made name patterns much more specific to avoid false positives
            # English name introduction patterns
            name_patterns = [
                r"my name is (\w+)",
                r"i'm (\w+)",
                r"i am (\w+)",
                r"call me (\w+)",
                r"this is (\w+)",
                # Only match if it's clearly a name introduction with proper context
                r"hello,?\s+(\w+)\s+here",
                r"hi,?\s+(\w+)\s+here",
                # Add more patterns for simple name introductions
                r"^(?:i'?m|im)\s+(\w+)$",  # Matches "im heinz" or "i'm heinz" as complete messages
                r"(?:hi|hello|hey)\s+(?:i'?m|im)\s+(\w+)",  # Matches "hi im heinz" or "hello i'm heinz"
                r"^(\w+)\s+here$",  # Matches "heinz here"
                
                # Tagalog name introduction patterns
                r"ako\s+(?:si|ay)\s+(\w+)",  # "Ako si Juan" or "Ako ay Juan"
                r"ako\s+(\w+)",  # "Ako Juan"
                r"si\s+(\w+)\s+(?:po|ito|ako)",  # "Si Juan po" or "Si Juan ito" or "Si Juan ako"
                r"ang\s+pangalan\s+ko\s+(?:ay|eh|po|ay si)\s+(\w+)",  # "Ang pangalan ko ay Juan"
                r"pangalan\s+ko\s+(?:ay|eh|po|ay si)\s+(\w+)",  # "Pangalan ko ay Juan"
                r"tawag\s+(?:sa akin|sakin)\s+(?:ay|eh|po|ay si)\s+(\w+)",  # "Tawag sa akin ay Juan"
                r"^(\w+)\s+(?:po|ako|ito)$"  # "Juan po" or "Juan ako" or "Juan ito"
            ]
            
            import re
            for message in reversed(conversation_history[-5:]):  # Check last 5 messages
                # Ensure message is a dictionary
                if isinstance(message, str):
                    message = {"role": "user", "content": message}
                elif not isinstance(message, dict):
                    continue
                    
                if message.get("role") == "user":
                    content = message.get("content", "").strip()
                    if content:
                        for pattern in name_patterns:
                            match = re.search(pattern, content, re.IGNORECASE)
                            if match:
                                name = match.group(1).strip()
                                # 🎯 FIX: Much more restrictive validation to avoid extracting common words as names
                                common_words = [
                                    'tell', 'explain', 'help', 'can', 'you', 'me', 'us', 'the', 'a', 'an', 'and', 'or', 'but', 
                                    'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 
                                    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 
                                    'may', 'might', 'must', 'shall', 'cannot', 'couldnt', 'wouldnt', 'shouldnt', 'wont', 
                                    'dont', 'doesnt', 'didnt', 'havent', 'hasnt', 'hadnt', 'what', 'where', 'when', 'why', 
                                    'how', 'who', 'which', 'show', 'find', 'get', 'need', 'want', 'know', 'see', 'look',
                                    'school', 'teacher', 'student', 'principal', 'office', 'class', 'grade', 'enroll',
                                    'information', 'about', 'activities', 'schedule', 'rules', 'policies', 'programs'
                                ]
                                
                                if (len(name) > 2 and name.isalpha() and 
                                    name.lower() not in common_words and
                                    not name.lower().endswith('ing') and
                                    not name.lower().endswith('ed') and
                                    not name.lower().endswith('er') and
                                    not name.lower().endswith('ly')):
                                    # logger.info(f"🎯 Extracted user name: {name}")
                                    return name
            
            return None
            
        except Exception as e:
            logger.error(f"User name extraction failed: {e}")
            return None
    
    def get_user_name(self, session_id: str = None) -> Optional[str]:
        """Get user name from memory for a specific session"""
        with self._lock:
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
        """Update user memory with new information, including multi-question support"""
        now = datetime.now()
        
        # If no user_name provided but we have conversation history, try to extract it
        if not user_name and conversation_history:
            extracted_name = self.extract_user_name(conversation_history)
            if extracted_name:
                user_name = extracted_name
                # logger.info(f"🧠 Extracted user name during memory update: {user_name}")
        
        # Thread-safe memory update
        with self._lock:
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
            
            # Store the current user message
            if not hasattr(user_memory, 'conversation_messages'):
                user_memory.conversation_messages = []
            
            user_memory.conversation_messages.append({
                "role": "user", 
                "content": query, 
                "timestamp": now.isoformat()  # Convert datetime to string
            })
            
            # Update name if provided
            if user_name and (not user_memory.name or user_name != user_memory.name):
                logger.info(f"🧠 Updating user name in memory: '{user_memory.name}' -> '{user_name}'")
                user_memory.name = user_name
        
        # Check if this is a multi-question session
        is_multi_question = "Multi-question session:" in query
        
        # Extract and update topics
        topics = self.extract_topics_from_query(query)
        
        # For multi-question sessions, add special topic tracking
        if is_multi_question:
            # Extract the actual question part (after the multi-question context)
            actual_query = query.split(": ", 1)[1] if ": " in query else query
            topics.extend(self.extract_topics_from_query(actual_query))
            
            # Add multi-question session topic
            topics.append("multi_question_session")
        
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
            # logger.info(f"Cleaned up {len(sessions_to_remove)} old user memories")
            pass
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        try:
            if session_id not in self.user_memories:
                return []
            
            user_memory = self.user_memories[session_id]
            
            # Return stored conversation messages if available
            if hasattr(user_memory, 'conversation_messages'):
                return user_memory.conversation_messages
            
            # Fallback: Convert topic-based history to the expected format
            history = []
            for topic, topic_info in user_memory.topics.items():
                # Add user messages
                if topic_info.user_messages:
                    for msg in topic_info.user_messages:
                        history.append({"role": "user", "content": msg})
                # Add assistant messages
                if topic_info.assistant_messages:
                    for msg in topic_info.assistant_messages:
                        history.append({"role": "assistant", "content": msg})
            
            # Sort by timestamp if available
            history.sort(key=lambda x: getattr(x, 'timestamp', 0))
            return history
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
    
    def clear_all_memories(self):
        """Clear all conversation memories (used when user explicitly clears context)"""
        try:
            memory_count = len(self.user_memories)
            self.user_memories.clear()
            self.session_topics.clear()
            # logger.info(f"🧹 Cleared all {memory_count} conversation memories")
        except Exception as e:
            logger.error(f"Failed to clear all memories: {e}")