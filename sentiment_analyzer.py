"""
Sentiment Analysis & Tone Detection System
Analyzes user emotions and adjusts response tone accordingly
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class SentimentType(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"

class EmotionType(Enum):
    HAPPY = "happy"
    EXCITED = "excited"
    ANXIOUS = "anxious"
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    SATISFIED = "satisfied"
    DISAPPOINTED = "disappointed"
    CURIOUS = "curious"
    CALM = "calm"

@dataclass
class SentimentResult:
    sentiment: SentimentType
    confidence: float
    emotion: Optional[EmotionType]
    tone_indicators: List[str]
    recommended_tone: str
    urgency_level: int  # 1-5 scale

class SentimentAnalyzer:
    def __init__(self):
        # Positive sentiment indicators
        self.positive_patterns = {
            'enthusiasm': [
                r'\b(amazing|awesome|fantastic|wonderful|great|excellent|love|excited|thrilled)\b',
                r'\b(perfect|brilliant|outstanding|impressive|superb)\b',
                r'[!]{2,}|😊|😍|🎉|👍|❤️|💖'
            ],
            'satisfaction': [
                r'\b(thank you|thanks|grateful|appreciate|helpful|satisfied|pleased)\b',
                r'\b(good|nice|fine|okay|alright)\b',
                r'👌|✅|😌'
            ],
            'curiosity': [
                r'\b(interesting|curious|wonder|explore|learn more|tell me about)\b',
                r'\?{2,}|🤔|💭'
            ]
        }
        
        # Negative sentiment indicators
        self.negative_patterns = {
            'frustration': [
                r'\b(frustrated|annoyed|upset|angry|mad|irritated)\b',
                r'\b(terrible|awful|horrible|worst|hate|dislike)\b',
                r'😡|😤|💢|🤬'
            ],
            'anxiety': [
                r'\b(worried|anxious|nervous|scared|concerned|stressed)\b',
                r'\b(problem|issue|trouble|difficulty|struggle)\b',
                r'😰|😨|😟|😧'
            ],
            'confusion': [
                r'\b(confused|lost|unclear|don\'t understand|not sure|help)\b',
                r'\b(what|how|why|when|where)\s+(\w+\s+){0,3}(\?|please)',
                r'🤷|❓|😕'
            ],
            'disappointment': [
                r'\b(disappointed|sad|unhappy|unsatisfied|expected more)\b',
                r'\b(not good|not great|not what I wanted)\b',
                r'😞|😢|😔|💔'
            ]
        }
        
        # Neutral patterns
        self.neutral_patterns = [
            r'\b(information|details|facts|data|schedule|time|location)\b',
            r'\b(what is|how much|when is|where is)\b',
            r'^\s*(?:hi|hello|hey|good morning|good afternoon)\s*[.!]?\s*$'
        ]
        
        # Urgency indicators
        self.urgency_patterns = {
            'high': [
                r'\b(urgent|emergency|immediately|asap|right now|quickly)\b',
                r'\b(deadline|due|soon|today|tomorrow)\b',
                r'[!]{3,}'
            ],
            'medium': [
                r'\b(need|want|should|would like|prefer)\b',
                r'\b(this week|next week|planning|considering)\b',
                r'[!]{2}'
            ],
            'low': [
                r'\b(maybe|perhaps|might|could|eventually|someday)\b',
                r'\b(just wondering|curious|thinking about)\b'
            ]
        }

    def analyze_sentiment(self, text: str, conversation_context: Optional[Dict] = None) -> SentimentResult:
        """
        Analyze sentiment and emotion in user text
        """
        text_lower = text.lower()
        
        # Count sentiment indicators
        positive_score = self._count_patterns(text_lower, self.positive_patterns)
        negative_score = self._count_patterns(text_lower, self.negative_patterns)
        neutral_score = self._count_patterns(text_lower, self.neutral_patterns)
        
        # Determine overall sentiment
        sentiment, confidence = self._determine_sentiment(positive_score, negative_score, neutral_score)
        
        # Detect specific emotion
        emotion = self._detect_emotion(text_lower, sentiment)
        
        # Extract tone indicators
        tone_indicators = self._extract_tone_indicators(text)
        
        # Recommend response tone
        recommended_tone = self._recommend_tone(sentiment, emotion, conversation_context)
        
        # Assess urgency
        urgency_level = self._assess_urgency(text_lower)
        
        return SentimentResult(
            sentiment=sentiment,
            confidence=confidence,
            emotion=emotion,
            tone_indicators=tone_indicators,
            recommended_tone=recommended_tone,
            urgency_level=urgency_level
        )

    def _count_patterns(self, text: str, pattern_dict) -> Dict[str, int]:
        """Count occurrences of sentiment patterns"""
        if isinstance(pattern_dict, list):
            # Handle simple list of patterns
            counts = {}
            total = 0
            for pattern in pattern_dict:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                total += matches
            return {'total': total}
        
        # Handle dictionary of categorized patterns
        counts = {}
        for category, patterns in pattern_dict.items():
            category_count = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                category_count += matches
            counts[category] = category_count
        
        counts['total'] = sum(counts.values())
        return counts

    def _determine_sentiment(self, positive: Dict, negative: Dict, neutral: Dict) -> Tuple[SentimentType, float]:
        """Determine overall sentiment with confidence score"""
        pos_total = positive.get('total', 0)
        neg_total = negative.get('total', 0)
        neu_total = neutral.get('total', 0)
        
        total_indicators = pos_total + neg_total + neu_total
        
        if total_indicators == 0:
            return SentimentType.NEUTRAL, 0.5
        
        # Calculate sentiment scores
        pos_ratio = pos_total / total_indicators
        neg_ratio = neg_total / total_indicators
        neu_ratio = neu_total / total_indicators
        
        # Determine primary sentiment
        if pos_ratio > neg_ratio and pos_ratio > neu_ratio:
            if neg_ratio > 0.3:  # Mixed sentiment
                return SentimentType.MIXED, min(0.9, pos_ratio + 0.1)
            return SentimentType.POSITIVE, min(0.95, pos_ratio + 0.2)
        elif neg_ratio > pos_ratio and neg_ratio > neu_ratio:
            if pos_ratio > 0.3:  # Mixed sentiment
                return SentimentType.MIXED, min(0.9, neg_ratio + 0.1)
            return SentimentType.NEGATIVE, min(0.95, neg_ratio + 0.2)
        else:
            return SentimentType.NEUTRAL, min(0.8, neu_ratio + 0.1)

    def _detect_emotion(self, text: str, sentiment: SentimentType) -> Optional[EmotionType]:
        """Detect specific emotion based on patterns and sentiment"""
        emotion_scores = {}
        
        # Check positive emotions
        if sentiment in [SentimentType.POSITIVE, SentimentType.MIXED]:
            for pattern in self.positive_patterns['enthusiasm']:
                if re.search(pattern, text, re.IGNORECASE):
                    emotion_scores[EmotionType.EXCITED] = emotion_scores.get(EmotionType.EXCITED, 0) + 1
            
            for pattern in self.positive_patterns['satisfaction']:
                if re.search(pattern, text, re.IGNORECASE):
                    emotion_scores[EmotionType.SATISFIED] = emotion_scores.get(EmotionType.SATISFIED, 0) + 1
            
            for pattern in self.positive_patterns['curiosity']:
                if re.search(pattern, text, re.IGNORECASE):
                    emotion_scores[EmotionType.CURIOUS] = emotion_scores.get(EmotionType.CURIOUS, 0) + 1
        
        # Check negative emotions
        if sentiment in [SentimentType.NEGATIVE, SentimentType.MIXED]:
            for pattern in self.negative_patterns['frustration']:
                if re.search(pattern, text, re.IGNORECASE):
                    emotion_scores[EmotionType.FRUSTRATED] = emotion_scores.get(EmotionType.FRUSTRATED, 0) + 1
            
            for pattern in self.negative_patterns['anxiety']:
                if re.search(pattern, text, re.IGNORECASE):
                    emotion_scores[EmotionType.ANXIOUS] = emotion_scores.get(EmotionType.ANXIOUS, 0) + 1
            
            for pattern in self.negative_patterns['confusion']:
                if re.search(pattern, text, re.IGNORECASE):
                    emotion_scores[EmotionType.CONFUSED] = emotion_scores.get(EmotionType.CONFUSED, 0) + 1
            
            for pattern in self.negative_patterns['disappointment']:
                if re.search(pattern, text, re.IGNORECASE):
                    emotion_scores[EmotionType.DISAPPOINTED] = emotion_scores.get(EmotionType.DISAPPOINTED, 0) + 1
        
        # Return most likely emotion
        if emotion_scores:
            return max(emotion_scores.keys(), key=lambda k: emotion_scores[k])
        
        # Default emotions based on sentiment
        if sentiment == SentimentType.POSITIVE:
            return EmotionType.HAPPY
        elif sentiment == SentimentType.NEGATIVE:
            return EmotionType.CONFUSED
        else:
            return EmotionType.CALM

    def _extract_tone_indicators(self, text: str) -> List[str]:
        """Extract specific indicators that suggest tone"""
        indicators = []
        
        # Punctuation indicators
        if re.search(r'[!]{2,}', text):
            indicators.append('high_excitement')
        elif '!' in text:
            indicators.append('excitement')
        
        if re.search(r'[?]{2,}', text):
            indicators.append('confusion')
        elif '?' in text:
            indicators.append('inquiry')
        
        # Capitalization indicators
        if re.search(r'[A-Z]{3,}', text):
            indicators.append('emphasis')
        
        # Emoji indicators
        if re.search(r'[😊😍🎉👍❤️💖]', text):
            indicators.append('positive_emoji')
        elif re.search(r'[😡😤💢🤬😰😨😟😧]', text):
            indicators.append('negative_emoji')
        
        # Politeness indicators
        if re.search(r'\b(please|thank you|thanks|excuse me|sorry)\b', text, re.IGNORECASE):
            indicators.append('polite')
        
        return indicators

    def _recommend_tone(self, sentiment: SentimentType, emotion: Optional[EmotionType], 
                       context: Optional[Dict] = None) -> str:
        """Recommend appropriate response tone based on analysis"""
        
        # Handle negative emotions first (priority)
        if emotion == EmotionType.FRUSTRATED:
            return 'apologetic_helpful'
        elif emotion == EmotionType.ANXIOUS:
            return 'reassuring_calm'
        elif emotion == EmotionType.CONFUSED:
            return 'patient_explanatory'
        elif emotion == EmotionType.DISAPPOINTED:
            return 'empathetic_solution_focused'
        
        # Handle positive emotions
        elif emotion == EmotionType.EXCITED:
            return 'enthusiastic_matching'
        elif emotion == EmotionType.SATISFIED:
            return 'warm_acknowledging'
        elif emotion == EmotionType.CURIOUS:
            return 'informative_engaging'
        
        # Default based on sentiment
        elif sentiment == SentimentType.POSITIVE:
            return 'friendly_positive'
        elif sentiment == SentimentType.NEGATIVE:
            return 'helpful_supportive'
        elif sentiment == SentimentType.MIXED:
            return 'balanced_understanding'
        else:
            return 'professional_informative'

    def _assess_urgency(self, text: str) -> int:
        """Assess urgency level from 1 (low) to 5 (high)"""
        urgency_score = 1
        
        # Check high urgency patterns
        for pattern in self.urgency_patterns['high']:
            if re.search(pattern, text, re.IGNORECASE):
                urgency_score = max(urgency_score, 5)
        
        # Check medium urgency patterns
        for pattern in self.urgency_patterns['medium']:
            if re.search(pattern, text, re.IGNORECASE):
                urgency_score = max(urgency_score, 3)
        
        # Check low urgency patterns
        for pattern in self.urgency_patterns['low']:
            if re.search(pattern, text, re.IGNORECASE):
                urgency_score = max(urgency_score, 1)
        
        return min(urgency_score, 5)

    def get_tone_adjustment_suggestions(self, sentiment_result: SentimentResult) -> Dict[str, str]:
        """Get specific suggestions for adjusting response tone"""
        suggestions = {}
        
        # Tone adjustments based on emotion
        if sentiment_result.emotion == EmotionType.FRUSTRATED:
            suggestions['opening'] = "I understand this might be frustrating. Let me help you with that."
            suggestions['style'] = "Use shorter, clearer sentences. Acknowledge the concern immediately."
            suggestions['closing'] = "I hope this helps resolve your concern. Please let me know if you need anything else."
        
        elif sentiment_result.emotion == EmotionType.ANXIOUS:
            suggestions['opening'] = "Don't worry, I'm here to help you through this."
            suggestions['style'] = "Use reassuring language. Provide step-by-step guidance."
            suggestions['closing'] = "Everything will be fine. Feel free to ask if you have more questions."
        
        elif sentiment_result.emotion == EmotionType.CONFUSED:
            suggestions['opening'] = "Let me help clarify that for you."
            suggestions['style'] = "Break down complex information. Use simple, clear explanations."
            suggestions['closing'] = "Does this help? Please ask if anything is still unclear."
        
        elif sentiment_result.emotion == EmotionType.EXCITED:
            suggestions['opening'] = "That's great! I'm excited to help you!"
            suggestions['style'] = "Match their enthusiasm. Use positive, energetic language."
            suggestions['closing'] = "This is going to be awesome! What else would you like to know?"
        
        else:
            suggestions['opening'] = "I'm happy to help you with that."
            suggestions['style'] = "Use a friendly, professional tone."
            suggestions['closing'] = "Let me know if you need any other information."
        
        return suggestions

# Global instance for easy access
sentiment_analyzer = SentimentAnalyzer()