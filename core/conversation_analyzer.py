"""
Advanced Conversation Context Analyzer
Enhances conversation understanding with deep NLP analysis
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import re

logger = logging.getLogger(__name__)

@dataclass
class ConversationContext:
    """Enhanced conversation context with NLP insights"""
    topic_flow: List[str]  # Topics discussed in sequence
    emotional_state: str   # Current emotional state
    user_personality: Dict[str, Any]  # User personality traits
    conversation_goals: List[str]  # What user is trying to achieve
    context_entities: List[Dict]  # Entities mentioned across conversation
    conversation_sentiment: float  # Overall sentiment (-1 to 1)
    urgency_level: str  # low, medium, high
    user_expertise: str  # beginner, intermediate, advanced

class ConversationAnalyzer:
    """
    Advanced conversation analysis using NLP techniques
    """
    
    def __init__(self):
        self.conversation_history = []
        self.topic_transitions = []
        self.emotional_tracking = []
        
    async def analyze_conversation_context(self, 
                                        current_query: str, 
                                        conversation_history: List[Dict],
                                        nlu_result: Any,
                                        entities: List[Any]) -> ConversationContext:
        """
        Perform deep conversation analysis using NLP
        """
        
        # 1. Topic Flow Analysis
        topic_flow = await self._analyze_topic_flow(conversation_history, current_query)
        
        # 2. Emotional State Detection
        emotional_state = await self._detect_emotional_state(current_query, conversation_history)
        
        # 3. User Personality Analysis
        user_personality = await self._analyze_user_personality(conversation_history)
        
        # 4. Conversation Goals Detection
        conversation_goals = await self._detect_conversation_goals(current_query, conversation_history)
        
        # 5. Context Entity Extraction
        context_entities = await self._extract_context_entities(conversation_history, entities)
        
        # 6. Sentiment Analysis
        conversation_sentiment = await self._analyze_conversation_sentiment(conversation_history)
        
        # 7. Urgency Detection
        urgency_level = await self._detect_urgency_level(current_query, nlu_result)
        
        # 8. User Expertise Assessment
        user_expertise = await self._assess_user_expertise(conversation_history, entities)
        
        return ConversationContext(
            topic_flow=topic_flow,
            emotional_state=emotional_state,
            user_personality=user_personality,
            conversation_goals=conversation_goals,
            context_entities=context_entities,
            conversation_sentiment=conversation_sentiment,
            urgency_level=urgency_level,
            user_expertise=user_expertise
        )
    
    async def _analyze_topic_flow(self, conversation_history: List[Dict], current_query: str) -> List[str]:
        """Analyze topic transitions and flow in conversation"""
        topics = []
        
        # Extract topics from conversation history
        for msg in conversation_history[-5:]:  # Last 5 messages
            if isinstance(msg, str):
                content = msg.lower()
            elif isinstance(msg, dict):
                content = msg.get('content', '').lower()
            else:
                content = ''
            
            # Topic detection patterns
            if any(word in content for word in ['enrollment', 'register', 'admission']):
                topics.append('enrollment')
            elif any(word in content for word in ['teacher', 'principal', 'staff']):
                topics.append('staff')
            elif any(word in content for word in ['schedule', 'time', 'hours']):
                topics.append('schedule')
            elif any(word in content for word in ['location', 'address', 'where']):
                topics.append('location')
            elif any(word in content for word in ['fees', 'payment', 'cost']):
                topics.append('financial')
        
        # Add current query topic
        current_topic = self._extract_current_topic(current_query)
        if current_topic:
            topics.append(current_topic)
        
        return topics
    
    async def _detect_emotional_state(self, current_query: str, conversation_history: List[Dict]) -> str:
        """Detect user's current emotional state using NLP"""
        
        # Emotional indicators
        emotional_indicators = {
            'frustrated': ['frustrated', 'annoyed', 'upset', 'angry', 'mad', 'irritated'],
            'confused': ['confused', 'lost', 'don\'t understand', 'unclear', 'help'],
            'worried': ['worried', 'concerned', 'anxious', 'nervous', 'scared'],
            'excited': ['excited', 'happy', 'thrilled', 'great', 'wonderful'],
            'sad': ['sad', 'disappointed', 'unhappy', 'depressed', 'down'],
            'neutral': ['okay', 'fine', 'good', 'alright']
        }
        
        # Analyze current query
        query_lower = current_query.lower()
        for emotion, indicators in emotional_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                return emotion
        
        # Analyze conversation history for emotional patterns
        recent_messages = conversation_history[-3:] if conversation_history else []
        for msg in recent_messages:
            if isinstance(msg, str):
                content = msg.lower()
            elif isinstance(msg, dict):
                content = msg.get('content', '').lower()
            else:
                content = ''
            for emotion, indicators in emotional_indicators.items():
                if any(indicator in content for indicator in indicators):
                    return emotion
        
        return 'neutral'
    
    async def _analyze_user_personality(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Analyze user personality traits from conversation patterns"""
        
        personality_traits = {
            'formality_level': 'medium',  # formal, medium, casual
            'communication_style': 'direct',  # direct, indirect, detailed
            'preferred_language': 'mixed',  # english, tagalog, aklanon, mixed
            'question_style': 'specific',  # specific, general, exploratory
            'urgency_tendency': 'medium'  # low, medium, high
        }
        
        if not conversation_history:
            return personality_traits
        
        # Analyze formality
        formal_indicators = ['please', 'thank you', 'sir', 'ma\'am', 'po', 'opo']
        casual_indicators = ['hey', 'hi', 'lol', 'haha', 'cool', 'awesome']
        
        formal_count = sum(1 for msg in conversation_history 
                          for indicator in formal_indicators 
                          if indicator in (msg.get('content', '') if isinstance(msg, dict) else str(msg)).lower())
        casual_count = sum(1 for msg in conversation_history 
                          for indicator in casual_indicators 
                          if indicator in (msg.get('content', '') if isinstance(msg, dict) else str(msg)).lower())
        
        if formal_count > casual_count:
            personality_traits['formality_level'] = 'formal'
        elif casual_count > formal_count:
            personality_traits['formality_level'] = 'casual'
        
        # Analyze communication style
        question_count = sum(1 for msg in conversation_history 
                           if '?' in (msg.get('content', '') if isinstance(msg, dict) else str(msg)))
        statement_count = len(conversation_history) - question_count
        
        if question_count > statement_count:
            personality_traits['communication_style'] = 'exploratory'
        elif len([msg for msg in conversation_history if len((msg.get('content', '') if isinstance(msg, dict) else str(msg))) > 100]) > len(conversation_history) / 2:
            personality_traits['communication_style'] = 'detailed'
        
        return personality_traits
    
    async def _detect_conversation_goals(self, current_query: str, conversation_history: List[Dict]) -> List[str]:
        """Detect what the user is trying to achieve in the conversation"""
        
        goals = []
        
        # Goal detection patterns
        goal_patterns = {
            'get_information': ['what is', 'tell me about', 'explain', 'how does', 'information'],
            'solve_problem': ['help', 'problem', 'issue', 'trouble', 'fix', 'resolve'],
            'make_decision': ['should i', 'which is better', 'recommend', 'advice', 'choose'],
            'complete_task': ['how to', 'steps', 'process', 'procedure', 'enroll', 'register'],
            'get_support': ['contact', 'speak to', 'human', 'person', 'representative']
        }
        
        query_lower = current_query.lower()
        for goal, patterns in goal_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                goals.append(goal)
        
        # Analyze conversation history for goal patterns
        for msg in conversation_history[-3:]:
            if isinstance(msg, str):
                content = msg.lower()
            elif isinstance(msg, dict):
                content = msg.get('content', '').lower()
            else:
                content = ''
            for goal, patterns in goal_patterns.items():
                if any(pattern in content for pattern in patterns):
                    if goal not in goals:
                        goals.append(goal)
        
        return goals if goals else ['general_inquiry']
    
    async def _extract_context_entities(self, conversation_history: List[Dict], current_entities: List[Any]) -> List[Dict]:
        """Extract entities mentioned across the entire conversation"""
        
        context_entities = []
        
        # Add current entities
        if current_entities:
            for entity in current_entities:
                context_entities.append({
                    'type': entity.entity_type,
                    'value': entity.value,
                    'confidence': entity.confidence,
                    'context': 'current'
                })
        
        # Extract entities from conversation history
        for msg in conversation_history[-5:]:  # Last 5 messages
            if isinstance(msg, str):
                content = msg
            elif isinstance(msg, dict):
                content = msg.get('content', '')
            else:
                content = ''
            
            # Simple entity extraction from history
            if 'grade' in content.lower():
                context_entities.append({
                    'type': 'grade_level',
                    'value': 'mentioned',
                    'confidence': 0.7,
                    'context': 'historical'
                })
            
            if any(name in content for name in ['teacher', 'principal', 'staff']):
                context_entities.append({
                    'type': 'staff_role',
                    'value': 'mentioned',
                    'confidence': 0.7,
                    'context': 'historical'
                })
        
        return context_entities
    
    async def _analyze_conversation_sentiment(self, conversation_history: List[Dict]) -> float:
        """Analyze overall conversation sentiment (-1 to 1)"""
        
        if not conversation_history:
            return 0.0
        
        # Simple sentiment analysis
        positive_words = ['good', 'great', 'excellent', 'wonderful', 'happy', 'satisfied', 'thank you']
        negative_words = ['bad', 'terrible', 'awful', 'frustrated', 'angry', 'disappointed', 'problem']
        
        sentiment_score = 0.0
        total_messages = len(conversation_history)
        
        for msg in conversation_history:
            if isinstance(msg, str):
                content = msg.lower()
            elif isinstance(msg, dict):
                content = msg.get('content', '').lower()
            else:
                content = ''
            
            positive_count = sum(1 for word in positive_words if word in content)
            negative_count = sum(1 for word in negative_words if word in content)
            
            message_sentiment = (positive_count - negative_count) / max(len(content.split()), 1)
            sentiment_score += message_sentiment
        
        return sentiment_score / total_messages if total_messages > 0 else 0.0
    
    async def _detect_urgency_level(self, current_query: str, nlu_result: Any) -> str:
        """Detect urgency level of current query"""
        
        if nlu_result and nlu_result.intent.value == 'emergency':
            return 'high'
        
        urgency_indicators = {
            'high': ['urgent', 'asap', 'immediately', 'now', 'emergency', 'help'],
            'medium': ['soon', 'quickly', 'fast', 'priority', 'important'],
            'low': ['whenever', 'eventually', 'later', 'sometime']
        }
        
        query_lower = current_query.lower()
        for level, indicators in urgency_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                return level
        
        return 'medium'  # Default
    
    async def _assess_user_expertise(self, conversation_history: List[Dict], entities: List[Any]) -> str:
        """Assess user's expertise level based on conversation patterns"""
        
        if not conversation_history:
            return 'beginner'
        
        # Expertise indicators
        beginner_indicators = ['what is', 'how do', 'explain', 'help', 'don\'t know', 'confused']
        advanced_indicators = ['specific', 'detailed', 'technical', 'requirements', 'process', 'procedure']
        
        beginner_count = 0
        advanced_count = 0
        
        for msg in conversation_history:
            if isinstance(msg, str):
                content = msg.lower()
            elif isinstance(msg, dict):
                content = msg.get('content', '').lower()
            else:
                content = ''
            beginner_count += sum(1 for indicator in beginner_indicators if indicator in content)
            advanced_count += sum(1 for indicator in advanced_indicators if indicator in content)
        
        if advanced_count > beginner_count:
            return 'advanced'
        elif beginner_count > advanced_count:
            return 'beginner'
        else:
            return 'intermediate'
    
    def _extract_current_topic(self, query: str) -> Optional[str]:
        """Extract topic from current query"""
        query_lower = query.lower()
        
        topic_keywords = {
            'enrollment': ['enroll', 'register', 'admission', 'application'],
            'staff': ['teacher', 'principal', 'staff', 'guro', 'maestro'],
            'schedule': ['schedule', 'time', 'hours', 'when', 'oras'],
            'location': ['location', 'address', 'where', 'directions', 'saan'],
            'financial': ['fees', 'payment', 'cost', 'tuition', 'bayad'],
            'facilities': ['library', 'cafeteria', 'gym', 'playground', 'facilities']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return topic
        
        return None
