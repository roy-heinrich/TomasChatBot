"""
Context-Aware NLU Module
Advanced intent understanding with conversation context and user behavior analysis
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import re

logger = logging.getLogger(__name__)

@dataclass
class ContextualIntent:
    """Enhanced intent with context awareness"""
    intent: str
    confidence: float
    context_factors: List[str]
    user_behavior_pattern: str
    conversation_stage: str
    implied_goals: List[str]
    urgency_level: str
    complexity_level: str

class ContextAwareNLU:
    """
    Advanced NLU with deep context understanding
    """
    
    def __init__(self):
        self.conversation_stages = self._build_conversation_stages()
        self.behavior_patterns = self._build_behavior_patterns()
        self.context_factors = self._build_context_factors()
        
    async def analyze_contextual_intent(self, 
                                      query: str, 
                                      conversation_history: List[Dict],
                                      user_profile: Dict,
                                      current_context: Dict) -> ContextualIntent:
        """
        Analyze intent with deep context understanding
        """
        
        # 1. Base intent analysis
        base_intent = await self._analyze_base_intent(query)
        
        # 2. Context factor analysis
        context_factors = await self._analyze_context_factors(query, conversation_history, user_profile)
        
        # 3. User behavior pattern analysis
        behavior_pattern = await self._analyze_behavior_pattern(conversation_history, user_profile)
        
        # 4. Conversation stage detection
        conversation_stage = await self._detect_conversation_stage(conversation_history, query)
        
        # 5. Implied goals extraction
        implied_goals = await self._extract_implied_goals(query, conversation_history, context_factors)
        
        # 6. Urgency assessment
        urgency_level = await self._assess_urgency(query, conversation_history, context_factors)
        
        # 7. Complexity assessment
        complexity_level = await self._assess_complexity(query, conversation_history, user_profile)
        
        # 8. Confidence adjustment based on context
        adjusted_confidence = await self._adjust_confidence_with_context(
            base_intent['confidence'], context_factors, behavior_pattern
        )
        
        return ContextualIntent(
            intent=base_intent['intent'],
            confidence=adjusted_confidence,
            context_factors=context_factors,
            user_behavior_pattern=behavior_pattern,
            conversation_stage=conversation_stage,
            implied_goals=implied_goals,
            urgency_level=urgency_level,
            complexity_level=complexity_level
        )
    
    async def _analyze_base_intent(self, query: str) -> Dict[str, Any]:
        """Analyze base intent without context"""
        
        query_lower = query.lower()
        
        # Intent patterns with confidence scores
        intent_patterns = {
            'enrollment_inquiry': {
                'patterns': ['enroll', 'register', 'admission', 'application', 'sign up'],
                'confidence': 0.8
            },
            'staff_inquiry': {
                'patterns': ['teacher', 'principal', 'staff', 'guro', 'maestro', 'who is'],
                'confidence': 0.7
            },
            'schedule_inquiry': {
                'patterns': ['schedule', 'time', 'hours', 'when', 'what time', 'oras'],
                'confidence': 0.7
            },
            'location_inquiry': {
                'patterns': ['location', 'address', 'where', 'directions', 'saan', 'diin'],
                'confidence': 0.7
            },
            'contact_inquiry': {
                'patterns': ['contact', 'phone', 'number', 'email', 'numero', 'tawagan'],
                'confidence': 0.6
            },
            'facilities_inquiry': {
                'patterns': ['library', 'cafeteria', 'gym', 'playground', 'facilities'],
                'confidence': 0.6
            },
            'financial_inquiry': {
                'patterns': ['fees', 'payment', 'cost', 'tuition', 'bayad', 'gastos'],
                'confidence': 0.6
            },
            'general_inquiry': {
                'patterns': ['what', 'how', 'tell me', 'explain', 'information'],
                'confidence': 0.5
            }
        }
        
        best_intent = 'general_inquiry'
        best_confidence = 0.1
        
        for intent, data in intent_patterns.items():
            for pattern in data['patterns']:
                if pattern in query_lower:
                    if data['confidence'] > best_confidence:
                        best_intent = intent
                        best_confidence = data['confidence']
        
        return {
            'intent': best_intent,
            'confidence': best_confidence
        }
    
    async def _analyze_context_factors(self, query: str, conversation_history: List[Dict], user_profile: Dict) -> List[str]:
        """Analyze contextual factors affecting intent"""
        
        factors = []
        
        # 1. Conversation context
        if conversation_history:
            recent_topics = self._extract_recent_topics(conversation_history)
            if recent_topics:
                factors.append(f"recent_topics_{recent_topics}")
        
        # 2. User profile factors
        if user_profile:
            if user_profile.get('is_returning_user'):
                factors.append('returning_user')
            if user_profile.get('preferred_language'):
                factors.append(f"language_{user_profile['preferred_language']}")
            if user_profile.get('expertise_level'):
                factors.append(f"expertise_{user_profile['expertise_level']}")
        
        # 3. Query complexity factors
        query_complexity = self._assess_query_complexity(query)
        if query_complexity == 'high':
            factors.append('complex_query')
        elif query_complexity == 'low':
            factors.append('simple_query')
        
        # 4. Emotional context
        emotional_indicators = self._detect_emotional_context(query)
        if emotional_indicators:
            factors.extend([f"emotion_{emotion}" for emotion in emotional_indicators])
        
        # 5. Urgency indicators
        urgency_indicators = self._detect_urgency_indicators(query)
        if urgency_indicators:
            factors.extend([f"urgency_{urgency}" for urgency in urgency_indicators])
        
        # 6. Follow-up indicators
        if self._is_follow_up_query(query, conversation_history):
            factors.append('follow_up_query')
        
        return factors
    
    async def _analyze_behavior_pattern(self, conversation_history: List[Dict], user_profile: Dict) -> str:
        """Analyze user behavior patterns"""
        
        if not conversation_history:
            return 'new_user'
        
        # Analyze conversation patterns
        patterns = []
        
        # 1. Question pattern analysis
        question_count = sum(1 for msg in conversation_history if '?' in msg.get('content', ''))
        total_messages = len(conversation_history)
        question_ratio = question_count / total_messages if total_messages > 0 else 0
        
        if question_ratio > 0.7:
            patterns.append('inquisitive')
        elif question_ratio < 0.3:
            patterns.append('informational')
        
        # 2. Message length analysis
        avg_length = sum(len(msg.get('content', '')) for msg in conversation_history) / total_messages
        if avg_length > 100:
            patterns.append('detailed_communicator')
        elif avg_length < 30:
            patterns.append('concise_communicator')
        
        # 3. Topic consistency
        topic_consistency = self._analyze_topic_consistency(conversation_history)
        if topic_consistency > 0.8:
            patterns.append('focused')
        elif topic_consistency < 0.4:
            patterns.append('exploratory')
        
        # 4. Language usage
        language_consistency = self._analyze_language_consistency(conversation_history)
        if language_consistency == 'mixed':
            patterns.append('multilingual')
        elif language_consistency == 'consistent':
            patterns.append('language_consistent')
        
        # 5. Response time patterns (if available)
        if user_profile.get('response_patterns'):
            if user_profile['response_patterns'] == 'quick':
                patterns.append('quick_responder')
            elif user_profile['response_patterns'] == 'thoughtful':
                patterns.append('thoughtful_responder')
        
        return '_'.join(patterns) if patterns else 'standard'
    
    async def _detect_conversation_stage(self, conversation_history: List[Dict], current_query: str) -> str:
        """Detect current conversation stage"""
        
        if not conversation_history:
            return 'initial'
        
        message_count = len(conversation_history)
        
        # Stage detection based on message count and content
        if message_count == 1:
            return 'greeting'
        elif message_count <= 3:
            return 'exploration'
        elif message_count <= 8:
            return 'engagement'
        elif message_count <= 15:
            return 'deep_discussion'
        else:
            return 'extended_conversation'
        
        # Content-based stage detection
        recent_content = ' '.join([msg.get('content', '') for msg in conversation_history[-3:]])
        
        if any(word in recent_content.lower() for word in ['thank you', 'thanks', 'salamat']):
            return 'closing'
        elif any(word in recent_content.lower() for word in ['help', 'assistance', 'tulong']):
            return 'support_seeking'
        elif any(word in recent_content.lower() for word in ['enroll', 'register', 'application']):
            return 'enrollment_process'
        
        return 'ongoing'
    
    async def _extract_implied_goals(self, query: str, conversation_history: List[Dict], context_factors: List[str]) -> List[str]:
        """Extract implied goals from query and context"""
        
        goals = []
        query_lower = query.lower()
        
        # Direct goal indicators
        goal_indicators = {
            'get_information': ['what is', 'tell me', 'explain', 'how does', 'information'],
            'solve_problem': ['help', 'problem', 'issue', 'trouble', 'fix', 'resolve'],
            'make_decision': ['should i', 'which is better', 'recommend', 'advice', 'choose'],
            'complete_task': ['how to', 'steps', 'process', 'procedure', 'enroll', 'register'],
            'get_support': ['contact', 'speak to', 'human', 'person', 'representative'],
            'understand_requirements': ['requirements', 'needed', 'necessary', 'required'],
            'compare_options': ['compare', 'difference', 'better', 'which one', 'options']
        }
        
        for goal, indicators in goal_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                goals.append(goal)
        
        # Context-based goal inference
        if 'follow_up_query' in context_factors:
            goals.append('clarify_information')
        
        if 'urgency_high' in context_factors:
            goals.append('urgent_resolution')
        
        if 'emotion_frustrated' in context_factors or 'emotion_confused' in context_factors:
            goals.append('get_clear_guidance')
        
        return goals if goals else ['general_inquiry']
    
    async def _assess_urgency(self, query: str, conversation_history: List[Dict], context_factors: List[str]) -> str:
        """Assess urgency level of the query"""
        
        query_lower = query.lower()
        
        # High urgency indicators
        high_urgency_indicators = ['urgent', 'asap', 'immediately', 'now', 'emergency', 'help', 'quickly']
        if any(indicator in query_lower for indicator in high_urgency_indicators):
            return 'high'
        
        # Medium urgency indicators
        medium_urgency_indicators = ['soon', 'priority', 'important', 'need to know']
        if any(indicator in query_lower for indicator in medium_urgency_indicators):
            return 'medium'
        
        # Context-based urgency
        if 'urgency_high' in context_factors:
            return 'high'
        elif 'urgency_medium' in context_factors:
            return 'medium'
        
        # Conversation history urgency
        if conversation_history:
            recent_urgency = any(
                any(word in msg.get('content', '').lower() for word in high_urgency_indicators)
                for msg in conversation_history[-2:]
            )
            if recent_urgency:
                return 'medium'
        
        return 'low'
    
    async def _assess_complexity(self, query: str, conversation_history: List[Dict], user_profile: Dict) -> str:
        """Assess complexity level of the query"""
        
        # Query length and structure
        query_length = len(query.split())
        question_count = query.count('?')
        conjunction_count = sum(1 for word in ['and', 'or', 'but', 'however', 'although'] if word in query.lower())
        
        # Complexity scoring
        complexity_score = 0
        
        if query_length > 20:
            complexity_score += 2
        elif query_length > 10:
            complexity_score += 1
        
        if question_count > 1:
            complexity_score += 2
        elif question_count == 1:
            complexity_score += 1
        
        if conjunction_count > 2:
            complexity_score += 2
        elif conjunction_count > 0:
            complexity_score += 1
        
        # Technical terms
        technical_terms = ['requirements', 'procedures', 'documents', 'deadline', 'process', 'application']
        technical_count = sum(1 for term in technical_terms if term in query.lower())
        complexity_score += technical_count
        
        # User expertise consideration
        if user_profile.get('expertise_level') == 'beginner':
            complexity_score += 1
        elif user_profile.get('expertise_level') == 'advanced':
            complexity_score -= 1
        
        # Determine complexity level
        if complexity_score >= 5:
            return 'high'
        elif complexity_score >= 3:
            return 'medium'
        else:
            return 'low'
    
    async def _adjust_confidence_with_context(self, base_confidence: float, context_factors: List[str], behavior_pattern: str) -> float:
        """Adjust confidence based on context factors"""
        
        adjusted_confidence = base_confidence
        
        # Boost confidence for positive context factors
        positive_factors = ['returning_user', 'language_consistent', 'focused', 'follow_up_query']
        for factor in positive_factors:
            if factor in context_factors:
                adjusted_confidence += 0.1
        
        # Reduce confidence for negative context factors
        negative_factors = ['complex_query', 'emotion_confused', 'urgency_high']
        for factor in negative_factors:
            if factor in context_factors:
                adjusted_confidence -= 0.05
        
        # Behavior pattern adjustments
        if behavior_pattern == 'inquisitive':
            adjusted_confidence += 0.05
        elif behavior_pattern == 'exploratory':
            adjusted_confidence -= 0.05
        
        return max(0.1, min(1.0, adjusted_confidence))  # Clamp between 0.1 and 1.0
    
    def _extract_recent_topics(self, conversation_history: List[Dict]) -> List[str]:
        """Extract topics from recent conversation"""
        
        topics = []
        recent_messages = conversation_history[-3:] if len(conversation_history) >= 3 else conversation_history
        
        topic_keywords = {
            'enrollment': ['enroll', 'register', 'admission', 'application'],
            'staff': ['teacher', 'principal', 'staff', 'guro'],
            'schedule': ['schedule', 'time', 'hours', 'when'],
            'location': ['location', 'address', 'where', 'directions'],
            'financial': ['fees', 'payment', 'cost', 'tuition']
        }
        
        for msg in recent_messages:
            content = msg.get('content', '').lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in content for keyword in keywords):
                    if topic not in topics:
                        topics.append(topic)
        
        return topics
    
    def _assess_query_complexity(self, query: str) -> str:
        """Assess query complexity"""
        
        query_lower = query.lower()
        
        # Simple queries
        if len(query.split()) <= 5 and query.count('?') <= 1:
            return 'low'
        
        # Complex queries
        if (len(query.split()) > 15 or 
            query.count('?') > 2 or 
            any(word in query_lower for word in ['and', 'or', 'but', 'however', 'although'])):
            return 'high'
        
        return 'medium'
    
    def _detect_emotional_context(self, query: str) -> List[str]:
        """Detect emotional context in query"""
        
        emotions = []
        query_lower = query.lower()
        
        emotional_indicators = {
            'frustrated': ['frustrated', 'annoyed', 'upset', 'irritated'],
            'confused': ['confused', 'don\'t understand', 'unclear', 'lost'],
            'worried': ['worried', 'concerned', 'anxious', 'nervous'],
            'excited': ['excited', 'happy', 'thrilled', 'great']
        }
        
        for emotion, indicators in emotional_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                emotions.append(emotion)
        
        return emotions
    
    def _detect_urgency_indicators(self, query: str) -> List[str]:
        """Detect urgency indicators in query"""
        
        urgency_indicators = []
        query_lower = query.lower()
        
        urgency_patterns = {
            'high': ['urgent', 'asap', 'immediately', 'now', 'emergency'],
            'medium': ['soon', 'priority', 'important', 'need to know'],
            'low': ['whenever', 'eventually', 'later', 'sometime']
        }
        
        for level, indicators in urgency_patterns.items():
            if any(indicator in query_lower for indicator in indicators):
                urgency_indicators.append(f"urgency_{level}")
        
        return urgency_indicators
    
    def _is_follow_up_query(self, query: str, conversation_history: List[Dict]) -> bool:
        """Check if query is a follow-up to previous conversation"""
        
        if not conversation_history:
            return False
        
        # Follow-up indicators
        follow_up_indicators = [
            'what about', 'how about', 'also', 'additionally', 'furthermore',
            'and', 'but', 'however', 'what if', 'can you also'
        ]
        
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in follow_up_indicators)
    
    def _analyze_topic_consistency(self, conversation_history: List[Dict]) -> float:
        """Analyze topic consistency in conversation"""
        
        if len(conversation_history) < 2:
            return 1.0
        
        topics = self._extract_recent_topics(conversation_history)
        if not topics:
            return 0.5
        
        # Calculate consistency based on topic repetition
        topic_counts = {}
        for topic in topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        max_count = max(topic_counts.values())
        total_topics = len(topics)
        
        return max_count / total_topics if total_topics > 0 else 0.5
    
    def _analyze_language_consistency(self, conversation_history: List[Dict]) -> str:
        """Analyze language consistency in conversation"""
        
        if len(conversation_history) < 2:
            return 'consistent'
        
        # Simple language detection (in practice, use proper language detection)
        languages = []
        for msg in conversation_history[-5:]:  # Last 5 messages
            content = msg.get('content', '')
            
            # Simple heuristics for language detection
            if any(word in content.lower() for word in ['the', 'and', 'or', 'but', 'in', 'on', 'at']):
                languages.append('english')
            elif any(word in content.lower() for word in ['ang', 'ng', 'sa', 'ko', 'mo', 'niya']):
                languages.append('tagalog')
            elif any(word in content.lower() for word in ['sang', 'nga', 'gid', 'ro']):
                languages.append('aklanon')
        
        if not languages:
            return 'unknown'
        
        # Check consistency
        unique_languages = set(languages)
        if len(unique_languages) == 1:
            return 'consistent'
        elif len(unique_languages) > 1:
            return 'mixed'
        else:
            return 'unknown'
    
    def _build_conversation_stages(self) -> Dict:
        """Build conversation stage patterns"""
        return {
            'initial': ['greeting', 'hello', 'hi', 'kumusta', 'kamusta'],
            'exploration': ['what', 'how', 'tell me', 'explain'],
            'engagement': ['enroll', 'register', 'help', 'assistance'],
            'deep_discussion': ['requirements', 'process', 'procedures'],
            'closing': ['thank you', 'thanks', 'salamat', 'goodbye']
        }
    
    def _build_behavior_patterns(self) -> Dict:
        """Build behavior pattern templates"""
        return {
            'inquisitive': ['question_heavy', 'exploratory'],
            'informational': ['statement_heavy', 'factual'],
            'detailed_communicator': ['long_messages', 'comprehensive'],
            'concise_communicator': ['short_messages', 'direct'],
            'focused': ['topic_consistent', 'goal_oriented'],
            'exploratory': ['topic_diverse', 'curious']
        }
    
    def _build_context_factors(self) -> Dict:
        """Build context factor templates"""
        return {
            'user_factors': ['returning_user', 'new_user', 'expertise_level'],
            'conversation_factors': ['follow_up_query', 'topic_continuation'],
            'emotional_factors': ['emotion_positive', 'emotion_negative'],
            'urgency_factors': ['urgency_high', 'urgency_medium', 'urgency_low'],
            'complexity_factors': ['simple_query', 'complex_query']
        }
