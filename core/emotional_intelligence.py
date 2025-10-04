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
        
        # Dynamic emotion learning from database
        self.dynamic_emotion_patterns = {}
        self.emotion_learning_enabled = True
        
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
        
        # English emotion patterns (now dynamic)
        if language in ["en", "mixed"]:
            emotion_scores.update({
                'happy': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('happy')),
                'sad': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('sad')),
                'angry': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('angry')),
                'worried': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('worried')),
                'confused': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('confused')),
                'excited': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('excited'))
            })
        
        # Tagalog emotion patterns (now dynamic)
        if language in ["tl", "mixed"]:
            emotion_scores.update({
                'happy': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('happy')),
                'sad': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('sad')),
                'angry': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('angry')),
                'worried': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('worried')),
                'confused': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('confused')),
                'excited': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('excited'))
            })
        
        # Aklanon emotion patterns (now dynamic)
        if language in ["akl", "mixed"]:
            emotion_scores.update({
                'happy': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('happy')),
                'sad': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('sad')),
                'angry': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('angry')),
                'worried': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('worried')),
                'confused': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('confused')),
                'excited': self._score_emotion(query_lower, self._get_dynamic_emotion_patterns('excited'))
            })
        
        # Find primary emotion
        if emotion_scores:
            primary_emotion = max(emotion_scores, key=emotion_scores.get)
            intensity = emotion_scores[primary_emotion]
            
            # Learn typo patterns from this interaction
            self._learn_typo_patterns(query, primary_emotion)
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
        """Score emotion based on word presence and context with fuzzy matching"""
        
        score = 0.0
        text_lower = text.lower()
        
        for word in emotion_words:
            # Check for exact match first
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
            else:
                # Intelligent fuzzy matching for typos and variations
                from difflib import SequenceMatcher
                best_similarity = 0.0
                best_match = None
                
                # Check each word in the text against the emotion word
                text_words = text_lower.split()
                for text_word in text_words:
                    if len(text_word) > 2 and len(word) > 2:  # Only match words longer than 2 chars
                        similarity = SequenceMatcher(None, text_word, word).ratio()
                        
                        # Dynamic threshold based on word characteristics
                        # Shorter words need higher similarity, longer words can be more flexible
                        if len(word) <= 4:
                            threshold = 0.8  # Higher threshold for short words
                        elif len(word) <= 8:
                            threshold = 0.7  # Medium threshold for medium words
                        else:
                            threshold = 0.6  # Lower threshold for long words
                        
                        if similarity > best_similarity and similarity > threshold:
                            best_similarity = similarity
                            best_match = text_word
                
                if best_match:
                    # Score based on similarity strength
                    fuzzy_score = 0.25 * best_similarity  # Slightly higher base score for fuzzy matches
                    score += fuzzy_score
                    
                    # Boost for word frequency
                    word_count = text_lower.count(best_match)
                    score += word_count * 0.08  # Slightly higher frequency boost for fuzzy matches
                    
                    # Boost for intensifiers nearby (for fuzzy matches)
                    words_before = text_lower.split(best_match)[0].split()[-2:] if best_match in text_lower else []
                    words_after = text_lower.split(best_match)[1].split()[:2] if best_match in text_lower else []
                    nearby_words = words_before + words_after
                    intensifiers = ['very', 'really', 'so', 'extremely', 'super', 'quite']
                    if any(intensifier in nearby_words for intensifier in intensifiers):
                        score += 0.1  # Reduced intensifier boost for fuzzy matches
        
        return min(1.0, score)  # Cap at 1.0
    
    async def _learn_emotion_patterns_from_database(self, database_results: List[Dict]) -> None:
        """Dynamically learn emotion patterns from database responses"""
        if not self.emotion_learning_enabled or not database_results:
            return
        
        try:
            for result in database_results:
                response = result.get('response', '').lower()
                keywords = result.get('keywords', '').lower()
                
                # Extract emotional indicators from database content
                emotional_indicators = self._extract_emotional_indicators_from_text(response + ' ' + keywords)
                
                # Update dynamic patterns
                for emotion, indicators in emotional_indicators.items():
                    if emotion not in self.dynamic_emotion_patterns:
                        self.dynamic_emotion_patterns[emotion] = set()
                    
                    for indicator in indicators:
                        self.dynamic_emotion_patterns[emotion].add(indicator)
                        
        except Exception as e:
            logger.warning(f"Failed to learn emotion patterns from database: {e}")
    
    def _extract_emotional_indicators_from_text(self, text: str) -> Dict[str, List[str]]:
        """Extract emotional indicators from text using NLP analysis"""
        indicators = {
            'happy': [],
            'sad': [],
            'angry': [],
            'worried': [],
            'confused': [],
            'excited': []
        }
        
        # Use semantic analysis to identify emotional words
        words = text.split()
        for word in words:
            if len(word) > 3:  # Only consider meaningful words
                # Check against base emotion patterns for semantic similarity
                for emotion, base_patterns in self.emotion_patterns.items():
                    if emotion in indicators:
                        for pattern in base_patterns:
                            # Use fuzzy matching to find similar emotional words
                            from difflib import SequenceMatcher
                            similarity = SequenceMatcher(None, word, pattern).ratio()
                            if similarity > 0.7:  # 70% similarity
                                indicators[emotion].append(word)
        
        return indicators
    
    def _get_dynamic_emotion_patterns(self, emotion: str) -> List[str]:
        """Get emotion patterns combining static and dynamic patterns"""
        static_patterns = self.emotion_patterns.get(emotion, [])
        dynamic_patterns = list(self.dynamic_emotion_patterns.get(emotion, set()))
        
        # PRIORITIZE static patterns (including typos) over dynamic ones
        # Static patterns should always be included and take precedence
        all_patterns = static_patterns.copy()  # Start with static patterns
        
        # Add dynamic patterns that don't conflict with static ones
        for dynamic_pattern in dynamic_patterns:
            if dynamic_pattern not in all_patterns:
                all_patterns.append(dynamic_pattern)
        
        return all_patterns
    
    def _learn_typo_patterns(self, user_input: str, detected_emotion: str) -> None:
        """Learn typo patterns from user interactions"""
        if not self.emotion_learning_enabled:
            return
        
        try:
            # Extract words from user input that might be typos
            words = user_input.lower().split()
            for word in words:
                if len(word) > 3:  # Only consider meaningful words
                    # Check if this word is similar to any known emotion words
                    for emotion, patterns in self.emotion_patterns.items():
                        for pattern in patterns:
                            from difflib import SequenceMatcher
                            similarity = SequenceMatcher(None, word, pattern).ratio()
                            
                            # If similarity is high but not exact, it might be a typo
                            if 0.6 <= similarity < 0.9:
                                # Add to dynamic patterns if it matches the detected emotion
                                if emotion == detected_emotion:
                                    if emotion not in self.dynamic_emotion_patterns:
                                        self.dynamic_emotion_patterns[emotion] = set()
                                    self.dynamic_emotion_patterns[emotion].add(word)
                                    
        except Exception as e:
            logger.warning(f"Failed to learn typo patterns: {e}")
    
    def _build_emotion_patterns(self) -> Dict:
        """Build base emotion patterns - typos handled by intelligent fuzzy matching"""
        return {
            'happy': [
                'happy', 'excited', 'thrilled', 'great', 'wonderful', 'amazing',
                'fantastic', 'awesome', 'delighted', 'joyful', 'cheerful',
                # Tagalog base patterns
                'masaya', 'natutuwa', 'nagagalak', 'maligaya', 'saya',
                'kasiyahan', 'kaligayahan', 'tuwa',
                # Aklanon base patterns
                'malipayon', 'nagakalipay', 'lipay', 'kalipay', 'nagakasaya', 'kasaya'
            ],
            'sad': [
                'sad', 'depressed', 'down', 'unhappy', 'disappointed', 'upset',
                'miserable', 'gloomy', 'melancholy', 'heartbroken',
                # Tagalog base patterns
                'malungkot', 'nalulungkot', 'lungkot', 'kalungkutan',
                'nalulumbay', 'lumbay', 'hinanakit',
                # Aklanon base patterns
                'malungkot', 'nalulungkot', 'lungkot', 'kalungkutan', 'nalulumbay', 'lumbay'
            ],
            'angry': [
                'angry', 'mad', 'furious', 'irritated', 'annoyed', 'frustrated',
                'rage', 'livid', 'outraged', 'infuriated',
                # Tagalog base patterns
                'galit', 'nagagalit', 'inis', 'naiinis', 'suya', 'nayayamot',
                'pagkagalit', 'pagkainis'
            ],
            'worried': [
                'worried', 'anxious', 'nervous', 'concerned', 'stressed', 'tense',
                'uneasy', 'apprehensive', 'fearful', 'scared',
                # Tagalog base patterns
                'nag-aalala', 'alala', 'nababahala', 'bahala', 'nervous',
                'kinakabahan', 'kaba', 'takot',
                # Aklanon base patterns
                'nagakabalaka', 'balaka', 'nervous', 'kinakabahan', 'kaba', 'takot'
            ],
            'confused': [
                'confused', 'lost', 'don\'t understand', 'unclear', 'bewildered',
                'perplexed', 'puzzled', 'mystified', 'baffled',
                # Tagalog base patterns
                'nalilito', 'lito', 'hindi maintindihan', 'hindi alam', 'di ko alam',
                # Looking for/lost patterns
                'hinahanap', 'hanap', 'naghahanap', 'nawawala', 'nasaan', 'saan'
            ],
            'excited': [
                'excited', 'thrilled', 'eager', 'enthusiastic', 'pumped', 'stoked',
                'ecstatic', 'overjoyed', 'elated'
            ]
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