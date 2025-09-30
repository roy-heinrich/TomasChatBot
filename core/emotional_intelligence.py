"""
Emotional Intelligence Module
Advanced sentiment analysis and emotional understanding for the chatbot
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import re

logger = logging.getLogger(__name__)

@dataclass
class EmotionalAnalysis:
    """Comprehensive emotional analysis result"""
    primary_emotion: str
    emotion_intensity: float  # 0.0 to 1.0
    sentiment_score: float    # -1.0 to 1.0
    emotional_indicators: List[str]
    suggested_response_tone: str
    empathy_level: str  # low, medium, high
    stress_indicators: List[str]
    support_needed: bool

class EmotionalIntelligence:
    """
    Advanced emotional intelligence for understanding user emotions
    and responding appropriately
    """
    
    def __init__(self):
        self.emotion_patterns = self._build_emotion_patterns()
        self.stress_indicators = self._build_stress_indicators()
        self.empathy_responses = self._build_empathy_responses()
        
    async def analyze_emotions(self, 
                             current_query: str, 
                             conversation_history: List[Dict],
                             language: str = "en") -> EmotionalAnalysis:
        """
        Perform comprehensive emotional analysis
        """
        
        # 1. Primary emotion detection
        primary_emotion, emotion_intensity = await self._detect_primary_emotion(current_query, language)
        
        # 2. Sentiment analysis
        sentiment_score = await self._analyze_sentiment(current_query, conversation_history)
        
        # 3. Emotional indicators
        emotional_indicators = await self._extract_emotional_indicators(current_query, language)
        
        # 4. Response tone suggestion
        suggested_tone = await self._suggest_response_tone(primary_emotion, emotion_intensity, language)
        
        # 5. Empathy level assessment
        empathy_level = await self._assess_empathy_level(primary_emotion, emotion_intensity, conversation_history)
        
        # 6. Stress detection
        stress_indicators = await self._detect_stress_indicators(current_query, conversation_history)
        
        # 7. Support need assessment
        support_needed = await self._assess_support_need(primary_emotion, stress_indicators, conversation_history)
        
        return EmotionalAnalysis(
            primary_emotion=primary_emotion,
            emotion_intensity=emotion_intensity,
            sentiment_score=sentiment_score,
            emotional_indicators=emotional_indicators,
            suggested_response_tone=suggested_tone,
            empathy_level=empathy_level,
            stress_indicators=stress_indicators,
            support_needed=support_needed
        )
    
    async def _detect_primary_emotion(self, query: str, language: str) -> Tuple[str, float]:
        """Detect primary emotion and intensity"""
        
        query_lower = query.lower()
        emotion_scores = {}
        
        # English emotion patterns
        if language in ["en", "mixed"]:
            emotion_scores.update({
                'happy': self._score_emotion(query_lower, [
                    'happy', 'excited', 'thrilled', 'great', 'wonderful', 'amazing',
                    'fantastic', 'awesome', 'delighted', 'joyful', 'cheerful'
                ]),
                'sad': self._score_emotion(query_lower, [
                    'sad', 'depressed', 'down', 'unhappy', 'disappointed', 'upset',
                    'miserable', 'gloomy', 'melancholy', 'heartbroken'
                ]),
                'angry': self._score_emotion(query_lower, [
                    'angry', 'mad', 'furious', 'irritated', 'annoyed', 'frustrated',
                    'rage', 'livid', 'outraged', 'infuriated'
                ]),
                'worried': self._score_emotion(query_lower, [
                    'worried', 'anxious', 'nervous', 'concerned', 'stressed', 'tense',
                    'uneasy', 'apprehensive', 'fearful', 'scared'
                ]),
                'confused': self._score_emotion(query_lower, [
                    'confused', 'lost', 'don\'t understand', 'unclear', 'bewildered',
                    'perplexed', 'puzzled', 'mystified', 'baffled'
                ]),
                'excited': self._score_emotion(query_lower, [
                    'excited', 'thrilled', 'eager', 'enthusiastic', 'pumped', 'stoked',
                    'ecstatic', 'overjoyed', 'elated'
                ])
            })
        
        # Tagalog emotion patterns
        if language in ["tl", "mixed"]:
            emotion_scores.update({
                'happy': self._score_emotion(query_lower, [
                    'masaya', 'natutuwa', 'nagagalak', 'maligaya', 'saya',
                    'kasiyahan', 'kaligayahan', 'tuwa'
                ]),
                'sad': self._score_emotion(query_lower, [
                    'malungkot', 'nalulungkot', 'lungkot', 'kalungkutan',
                    'nalulumbay', 'lumbay', 'hinanakit'
                ]),
                'angry': self._score_emotion(query_lower, [
                    'galit', 'nagagalit', 'inis', 'naiinis', 'suya', 'nayayamot',
                    'pagkagalit', 'pagkainis'
                ]),
                'worried': self._score_emotion(query_lower, [
                    'nag-aalala', 'alala', 'nababahala', 'bahala', 'nervous',
                    'kinakabahan', 'kaba', 'takot'
                ]),
                'confused': self._score_emotion(query_lower, [
                    'nalilito', 'lito', 'hindi maintindihan', 'nalilito',
                    'hindi alam', 'di ko alam'
                ])
            })
        
        # Aklanon emotion patterns
        if language in ["akl", "mixed"]:
            emotion_scores.update({
                'happy': self._score_emotion(query_lower, [
                    'malipayon', 'nagakalipay', 'lipay', 'kalipay',
                    'nagakasaya', 'saya', 'kasaya'
                ]),
                'sad': self._score_emotion(query_lower, [
                    'malungkot', 'nalulungkot', 'lungkot', 'kalungkutan',
                    'nalulumbay', 'lumbay'
                ]),
                'worried': self._score_emotion(query_lower, [
                    'nagakabalaka', 'balaka', 'nervous', 'kinakabahan',
                    'kaba', 'takot'
                ])
            })
        
        # Find primary emotion
        if emotion_scores:
            primary_emotion = max(emotion_scores, key=emotion_scores.get)
            intensity = emotion_scores[primary_emotion]
        else:
            primary_emotion = 'neutral'
            intensity = 0.0
        
        return primary_emotion, intensity
    
    async def _analyze_sentiment(self, query: str, conversation_history: List[Dict]) -> float:
        """Analyze sentiment score (-1.0 to 1.0)"""
        
        # Current query sentiment
        query_sentiment = self._calculate_text_sentiment(query)
        
        # Conversation history sentiment
        history_sentiment = 0.0
        if conversation_history:
            recent_messages = conversation_history[-3:]  # Last 3 messages
            history_sentiments = [self._calculate_text_sentiment(msg.get('content', '')) 
                                for msg in recent_messages]
            history_sentiment = sum(history_sentiments) / len(history_sentiments)
        
        # Weighted combination (70% current, 30% history)
        combined_sentiment = (query_sentiment * 0.7) + (history_sentiment * 0.3)
        
        return max(-1.0, min(1.0, combined_sentiment))  # Clamp between -1 and 1
    
    def _calculate_text_sentiment(self, text: str) -> float:
        """Calculate sentiment score for a single text"""
        
        text_lower = text.lower()
        
        # Positive indicators
        positive_words = [
            'good', 'great', 'excellent', 'wonderful', 'amazing', 'fantastic',
            'awesome', 'perfect', 'love', 'like', 'enjoy', 'happy', 'pleased',
            'satisfied', 'thank you', 'thanks', 'appreciate', 'grateful'
        ]
        
        # Negative indicators
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike',
            'angry', 'frustrated', 'disappointed', 'upset', 'sad', 'worried',
            'problem', 'issue', 'trouble', 'difficult', 'hard', 'confused'
        ]
        
        # Intensifiers
        intensifiers = ['very', 'really', 'extremely', 'super', 'so', 'too', 'quite']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Check for intensifiers
        intensifier_count = sum(1 for word in intensifiers if word in text_lower)
        intensity_multiplier = 1.0 + (intensifier_count * 0.2)
        
        # Calculate sentiment
        if positive_count + negative_count == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / (positive_count + negative_count)
        return sentiment * intensity_multiplier
    
    async def _extract_emotional_indicators(self, query: str, language: str) -> List[str]:
        """Extract specific emotional indicators from query"""
        
        indicators = []
        query_lower = query.lower()
        
        # Emotional intensity indicators
        intensity_indicators = {
            'high': ['very', 'extremely', 'so', 'really', 'super', 'incredibly'],
            'medium': ['quite', 'pretty', 'somewhat', 'kind of'],
            'low': ['a little', 'slightly', 'somewhat', 'bit']
        }
        
        for level, words in intensity_indicators.items():
            if any(word in query_lower for word in words):
                indicators.append(f"intensity_{level}")
        
        # Emotional context indicators
        context_indicators = {
            'urgency': ['urgent', 'asap', 'immediately', 'now', 'quickly'],
            'uncertainty': ['maybe', 'perhaps', 'might', 'could', 'possibly'],
            'certainty': ['definitely', 'surely', 'certainly', 'absolutely'],
            'confusion': ['confused', 'don\'t understand', 'unclear', 'lost'],
            'frustration': ['frustrated', 'annoyed', 'upset', 'irritated']
        }
        
        for context, words in context_indicators.items():
            if any(word in query_lower for word in words):
                indicators.append(context)
        
        return indicators
    
    async def _suggest_response_tone(self, emotion: str, intensity: float, language: str) -> str:
        """Suggest appropriate response tone based on emotion analysis"""
        
        tone_mapping = {
            'happy': 'cheerful',
            'excited': 'enthusiastic',
            'sad': 'empathetic',
            'angry': 'calm_reassuring',
            'worried': 'supportive',
            'confused': 'patient_explanatory',
            'frustrated': 'understanding_helpful',
            'neutral': 'professional_friendly'
        }
        
        base_tone = tone_mapping.get(emotion, 'professional_friendly')
        
        # Adjust tone based on intensity
        if intensity > 0.7:
            if emotion in ['angry', 'frustrated']:
                return 'very_calm_reassuring'
            elif emotion in ['sad', 'worried']:
                return 'very_empathetic_supportive'
            elif emotion in ['happy', 'excited']:
                return 'very_enthusiastic'
        
        return base_tone
    
    async def _assess_empathy_level(self, emotion: str, intensity: float, conversation_history: List[Dict]) -> str:
        """Assess required empathy level for response"""
        
        # High empathy needed for negative emotions with high intensity
        if emotion in ['sad', 'angry', 'worried', 'frustrated'] and intensity > 0.6:
            return 'high'
        
        # Medium empathy for moderate negative emotions
        elif emotion in ['sad', 'angry', 'worried', 'frustrated'] and intensity > 0.3:
            return 'medium'
        
        # Check conversation history for emotional patterns
        if conversation_history:
            recent_emotional_content = any(
                any(emotion_word in msg.get('content', '').lower() 
                   for emotion_word in ['sad', 'angry', 'worried', 'frustrated', 'upset'])
                for msg in conversation_history[-3:]
            )
            
            if recent_emotional_content:
                return 'medium'
        
        return 'low'
    
    async def _detect_stress_indicators(self, query: str, conversation_history: List[Dict]) -> List[str]:
        """Detect stress indicators in current query and conversation"""
        
        stress_indicators = []
        query_lower = query.lower()
        
        # Stress indicators
        stress_patterns = {
            'time_pressure': ['urgent', 'asap', 'deadline', 'quickly', 'fast', 'now'],
            'uncertainty': ['confused', 'don\'t know', 'unclear', 'lost', 'help'],
            'overwhelm': ['too much', 'overwhelmed', 'can\'t handle', 'stressed'],
            'frustration': ['frustrated', 'annoyed', 'upset', 'irritated', 'angry'],
            'anxiety': ['worried', 'anxious', 'nervous', 'scared', 'afraid']
        }
        
        for stress_type, patterns in stress_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                stress_indicators.append(stress_type)
        
        # Check conversation history for stress patterns
        if conversation_history:
            for msg in conversation_history[-2:]:  # Last 2 messages
                content = msg.get('content', '').lower()
                for stress_type, patterns in stress_patterns.items():
                    if any(pattern in content for pattern in patterns):
                        if stress_type not in stress_indicators:
                            stress_indicators.append(f"historical_{stress_type}")
        
        return stress_indicators
    
    async def _assess_support_need(self, emotion: str, stress_indicators: List[str], conversation_history: List[Dict]) -> bool:
        """Assess if user needs additional support"""
        
        # High support need indicators
        if emotion in ['sad', 'angry', 'worried', 'frustrated'] and len(stress_indicators) > 1:
            return True
        
        # Check for escalation requests
        if conversation_history:
            recent_content = ' '.join([msg.get('content', '') for msg in conversation_history[-3:]])
            escalation_indicators = [
                'speak to', 'talk to', 'human', 'person', 'representative',
                'manager', 'supervisor', 'help me', 'assistance'
            ]
            
            if any(indicator in recent_content.lower() for indicator in escalation_indicators):
                return True
        
        return False
    
    def _score_emotion(self, text: str, emotion_words: List[str]) -> float:
        """Score emotion based on word presence and context"""
        
        score = 0.0
        text_lower = text.lower()
        
        for word in emotion_words:
            if word in text_lower:
                # Base score for word presence
                score += 0.3
                
                # Boost for word frequency
                word_count = text_lower.count(word)
                score += word_count * 0.1
                
                # Boost for intensifiers nearby
                words_before = text_lower.split(word)[0].split()[-2:] if word in text_lower else []
                words_after = text_lower.split(word)[1].split()[:2] if word in text_lower else []
                
                nearby_words = words_before + words_after
                intensifiers = ['very', 'really', 'so', 'extremely', 'super', 'quite']
                
                if any(intensifier in nearby_words for intensifier in intensifiers):
                    score += 0.2
        
        return min(1.0, score)  # Cap at 1.0
    
    def _build_emotion_patterns(self) -> Dict:
        """Build comprehensive emotion patterns"""
        return {
            'happy': ['happy', 'joy', 'excited', 'thrilled', 'delighted'],
            'sad': ['sad', 'depressed', 'down', 'unhappy', 'disappointed'],
            'angry': ['angry', 'mad', 'furious', 'irritated', 'annoyed'],
            'worried': ['worried', 'anxious', 'nervous', 'concerned', 'stressed'],
            'confused': ['confused', 'lost', 'unclear', 'bewildered', 'puzzled']
        }
    
    def _build_stress_indicators(self) -> Dict:
        """Build stress indicator patterns"""
        return {
            'time_pressure': ['urgent', 'asap', 'deadline', 'quickly'],
            'uncertainty': ['confused', 'don\'t know', 'unclear', 'lost'],
            'overwhelm': ['too much', 'overwhelmed', 'can\'t handle'],
            'frustration': ['frustrated', 'annoyed', 'upset', 'irritated']
        }
    
    def _build_empathy_responses(self) -> Dict:
        """Build empathy response templates"""
        return {
            'high_empathy': [
                "I understand this is difficult for you...",
                "I can see this is really important to you...",
                "I'm here to help you through this...",
                "I completely understand your concern..."
            ],
            'medium_empathy': [
                "I understand your concern...",
                "I can help you with that...",
                "Let me assist you with this...",
                "I'm here to help..."
            ],
            'low_empathy': [
                "I can help you with that.",
                "Let me assist you.",
                "I understand.",
                "I'm here to help."
            ]
        }
