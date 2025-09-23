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
        """Map detected language to our language codes"""
        # Aklanon detection (priority) - Enhanced word list
        aklanon_words = [
            "ngaean", "sin-o", "nahanumdom", "nga", "sang", "imo", "unga"
        ]
        if any(word in text_lower for word in aklanon_words):
            return "akl"
        
        # Tagalog detection - Enhanced word list
        tagalog_words = [
            "sino", "ano", "saan", "kumusta", "salamat", "mga", "ang", "ng", "sa", "na", 
            "ay", "ko", "mo", "niya", "namin", "ninyo", "nila", "ito", "iyan", "iyon",
            "dito", "doon", "kailan", "bakit", "paano", "saan", "alin", "kanino", "para"
        ]
        
        # English words that should override low-confidence Tagalog detection
        english_words = [
            "what", "where", "when", "why", "how", "who", "my", "name", "again", "the", "is", "are"
        ]
        
        # If confidence is very low and contains English words, prefer English
        if confidence < 0.3 and any(word in text_lower for word in english_words):
            return "en"
        
        # If langid detected Tagalog with reasonable confidence OR contains Tagalog words
        if (lang == "tl" and confidence > 0.4) or any(word in text_lower for word in tagalog_words):
            return "tl"
        
        # Default to English
        return "en"
    
    def _clean_cache(self):
        """Clean expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.language_cache.items()
            if current_time - timestamp > self.cache_ttl
        ]
        for key in expired_keys:
            del self.language_cache[key]
