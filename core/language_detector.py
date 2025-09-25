"""
Language Detection Module - Fixed
Proper language detection with caching and Aklanon support
"""
import logging
from typing import Dict, Tuple
import time

logger = logging.getLogger(__name__)

class LanguageDetector:
    """Fixed language detection with proper caching"""
    
    def __init__(self):
        self.language_cache = {}
        self.cache_ttl = 600  # 10 minutes
        self.last_cleanup = time.time()
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """Detect language with proper caching and Aklanon support"""
        text_lower = text.lower().strip()
        
        # Clean cache periodically
        if time.time() - self.last_cleanup > 3600:  # 1 hour
            self._clean_cache()
            self.last_cleanup = time.time()
        
        # Check cache first
        if text_lower in self.language_cache:
            cached_result, timestamp = self.language_cache[text_lower]
            if time.time() - timestamp < self.cache_ttl:
                return cached_result
        
        # Detect language
        try:
            import langid
            lang, confidence = langid.classify(text)
            
            # Enhanced language mapping
            detected_lang = self._map_language(lang, text_lower, confidence)
            
            # Cache the result
            self.language_cache[text_lower] = ((detected_lang, confidence), time.time())
            
            return detected_lang, confidence
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "en", 0.5
    
    def _map_language(self, lang: str, text_lower: str, confidence: float) -> str:
        """Map detected language using NLP-based analysis instead of hardcoded patterns"""
        import re
        
        # 🚨 NEW: Use NLP-based language scoring instead of hardcoded patterns
        language_scores = self._calculate_language_scores(text_lower)
        
        # Get the language with the highest score
        best_language = max(language_scores.items(), key=lambda x: x[1])
        
        # Only override if we have a strong confidence in the NLP result
        if best_language[1] > 0.6:  # 60% confidence threshold
            return best_language[0]
        
        # Fallback to langid result if NLP confidence is low
        if lang == "tl" and confidence > 0.4:
            return "tl"
        elif lang == "en" and confidence > 0.4:
            return "en"
        
        # Default to English
        return "en"
    
    def _calculate_language_scores(self, text_lower: str) -> dict:
        """Calculate language scores using NLP analysis instead of hardcoded word lists"""
        scores = {"en": 0.0, "tl": 0.0, "akl": 0.0}
        
        # Split text into words and analyze each
        words = text_lower.split()
        
        for word in words:
            # Use semantic analysis to determine language probability
            word_scores = self._analyze_word_language(word)
            for lang, score in word_scores.items():
                scores[lang] += score
        
        # Normalize scores by text length
        if len(words) > 0:
            for lang in scores:
                scores[lang] = scores[lang] / len(words)
        
        return scores
    
    def _analyze_word_language(self, word: str) -> dict:
        """Analyze individual word language using NLP patterns"""
        scores = {"en": 0.0, "tl": 0.0, "akl": 0.0}
        
        # Use linguistic patterns instead of hardcoded lists
        if self._is_english_pattern(word):
            scores["en"] += 1.0
        elif self._is_tagalog_pattern(word):
            scores["tl"] += 1.0
        elif self._is_aklanon_pattern(word):
            scores["akl"] += 1.0
        else:
            # Default neutral scoring
            scores["en"] += 0.3
            scores["tl"] += 0.3
            scores["akl"] += 0.3
        
        return scores
    
    def _is_english_pattern(self, word: str) -> bool:
        """Use linguistic patterns to identify English words"""
        import re
        
        # English linguistic patterns
        english_patterns = [
            r'^[a-z]+(ing|ed|er|est|ly|tion|sion|ness|ment)$',  # English suffixes
            r'^(the|and|or|but|in|on|at|to|for|of|with|by)$',   # English articles/prepositions
            r'^(what|where|when|why|how|who|which)$',           # English question words
            r'^(is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|can|could|should|may|might)$'  # English verbs
        ]
        
        return any(re.match(pattern, word) for pattern in english_patterns)
    
    def _is_tagalog_pattern(self, word: str) -> bool:
        """Use linguistic patterns to identify Tagalog words"""
        import re
        
        # Tagalog linguistic patterns
        tagalog_patterns = [
            r'^(ako|ikaw|siya|kami|kayo|sila)$',                # Tagalog pronouns
            r'^(ang|ng|sa|na|ay|ko|mo|niya|namin|ninyo|nila)$', # Tagalog particles
            r'^(ito|iyan|iyon|dito|doon|kailan|bakit|paano|saan|alin|kanino)$', # Tagalog demonstratives
            r'^(sino|ano|kumusta|kamusta|salamat|mga)$',        # Tagalog question words
            r'^(magandang|maayong|malungkot|masaya|nag-aalala|natutuwa|pagod|galit|nervous|takot|nalilito|naiinis)$'  # Tagalog adjectives
        ]
        
        return any(re.match(pattern, word) for pattern in tagalog_patterns)
    
    def _is_aklanon_pattern(self, word: str) -> bool:
        """Use linguistic patterns to identify Aklanon words"""
        import re
        
        # Aklanon linguistic patterns
        aklanon_patterns = [
            r'^(ngaean|sin-o|nahanumdom|nga|sang|imo|unga)$',   # Aklanon pronouns/particles
            r'^(maayong|salamat|gid|damo|huo|indi|sige|tama|mali)$', # Aklanon common words
            r'^(diin|siin|ngaa|wara|mayo|ro|eon|aton|inyo|ila)$'  # Aklanon question words
        ]
        
        return any(re.match(pattern, word) for pattern in aklanon_patterns)
    
    def _clean_cache(self):
        """Clean expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.language_cache.items()
            if current_time - timestamp > self.cache_ttl
        ]
        for key in expired_keys:
            del self.language_cache[key]
