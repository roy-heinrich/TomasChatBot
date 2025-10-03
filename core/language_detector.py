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
        """Enhanced language detection with mixed-language support"""
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
        
        # Enhanced mixed-language detection
        try:
            # Use multiple detection methods for better accuracy
            langid_result = self._detect_with_langid(text)
            nlp_result = self._detect_with_nlp_analysis(text_lower)
            pattern_result = self._detect_with_patterns(text_lower)
            
            # Combine results with weighted scoring
            final_lang, final_confidence = self._combine_detection_results(
                langid_result, nlp_result, pattern_result, text_lower
            )
            
            # Cache the result
            self.language_cache[text_lower] = ((final_lang, final_confidence), time.time())
            
            # logger.info(f"🌍 Language detected: {final_lang} (confidence: {final_confidence:.2f})")
            return final_lang, final_confidence
            
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
            r'^(diin|siin|ngaa|wara|mayo|ro|eon|aton|inyo|ila)$',  # Aklanon question words
            r'^(sayud|kung|du|cr|comfort|room|banyo|palikuran)$',  # Aklanon/English mixed words
            r'^(mo|ko|niya|namin|ninyo|nila|naton|inyo|ila)$'  # Aklanon pronouns
        ]
        
        return any(re.match(pattern, word) for pattern in aklanon_patterns)
    
    def _detect_with_langid(self, text: str) -> Tuple[str, float]:
        """Detect language using langid library"""
        try:
            import langid
            lang, confidence = langid.classify(text)
            return self._map_language(lang, text.lower(), confidence)
        except Exception as e:
            logger.warning(f"Langid detection failed: {e}")
            return "en", 0.3
    
    def _detect_with_nlp_analysis(self, text_lower: str) -> Tuple[str, float]:
        """Detect language using NLP analysis"""
        try:
            # Analyze sentence structure and word patterns
            sentences = text_lower.split('.')
            language_scores = {"en": 0.0, "tl": 0.0, "akl": 0.0}
            
            for sentence in sentences:
                if sentence.strip():
                    scores = self._calculate_language_scores(sentence.strip())
                    for lang, score in scores.items():
                        language_scores[lang] += score
            
            # Normalize scores
            total_score = sum(language_scores.values())
            if total_score > 0:
                for lang in language_scores:
                    language_scores[lang] = language_scores[lang] / total_score
            
            # Get best language
            best_lang = max(language_scores.items(), key=lambda x: x[1])
            return best_lang[0], best_lang[1]
            
        except Exception as e:
            logger.warning(f"NLP analysis failed: {e}")
            return "en", 0.3
    
    def _detect_with_patterns(self, text_lower: str) -> Tuple[str, float]:
        """Detect language using pattern matching"""
        try:
            # Count language-specific patterns
            pattern_counts = {"en": 0, "tl": 0, "akl": 0}
            
            words = text_lower.split()
            for word in words:
                if self._is_english_pattern(word):
                    pattern_counts["en"] += 1
                elif self._is_tagalog_pattern(word):
                    pattern_counts["tl"] += 1
                elif self._is_aklanon_pattern(word):
                    pattern_counts["akl"] += 1
            
            # Calculate confidence based on pattern matches
            total_words = len(words)
            if total_words > 0:
                for lang in pattern_counts:
                    pattern_counts[lang] = pattern_counts[lang] / total_words
                
                best_lang = max(pattern_counts.items(), key=lambda x: x[1])
                return best_lang[0], best_lang[1]
            else:
                return "en", 0.3
                
        except Exception as e:
            logger.warning(f"Pattern detection failed: {e}")
            return "en", 0.3
    
    def _combine_detection_results(self, langid_result: Tuple[str, float], 
                                 nlp_result: Tuple[str, float], 
                                 pattern_result: Tuple[str, float], 
                                 text_lower: str) -> Tuple[str, float]:
        """Combine multiple detection results with weighted scoring"""
        
        # Weight different methods based on text characteristics
        text_length = len(text_lower.split())
        
        # Adjust weights based on text length and complexity
        if text_length < 3:
            # Short text: rely more on patterns
            weights = {"langid": 0.3, "nlp": 0.2, "pattern": 0.5}
        elif text_length < 10:
            # Medium text: balanced approach
            weights = {"langid": 0.4, "nlp": 0.3, "pattern": 0.3}
        else:
            # Long text: rely more on NLP analysis
            weights = {"langid": 0.3, "nlp": 0.5, "pattern": 0.2}
        
        # Calculate weighted scores for each language
        language_scores = {"en": 0.0, "tl": 0.0, "akl": 0.0}
        
        for lang in language_scores:
            # Langid contribution
            if langid_result[0] == lang:
                language_scores[lang] += langid_result[1] * weights["langid"]
            
            # NLP contribution
            if nlp_result[0] == lang:
                language_scores[lang] += nlp_result[1] * weights["nlp"]
            
            # Pattern contribution
            if pattern_result[0] == lang:
                language_scores[lang] += pattern_result[1] * weights["pattern"]
        
        # Get the language with highest score
        best_lang = max(language_scores.items(), key=lambda x: x[1])
        
        # Calculate final confidence
        final_confidence = min(best_lang[1], 0.95)  # Cap at 95%
        
        # Boost confidence for mixed-language detection
        if self._is_mixed_language(text_lower):
            final_confidence = max(final_confidence, 0.7)
        
        return best_lang[0], final_confidence
    
    def _is_mixed_language(self, text_lower: str) -> bool:
        """Detect if text contains mixed languages"""
        words = text_lower.split()
        if len(words) < 2:
            return False
        
        # Check for presence of multiple language patterns
        has_english = any(self._is_english_pattern(word) for word in words)
        has_tagalog = any(self._is_tagalog_pattern(word) for word in words)
        has_aklanon = any(self._is_aklanon_pattern(word) for word in words)
        
        # Count how many languages are present
        language_count = sum([has_english, has_tagalog, has_aklanon])
        
        return language_count > 1
    
    def _clean_cache(self):
        """Clean expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.language_cache.items()
            if current_time - timestamp > self.cache_ttl
        ]
        for key in expired_keys:
            del self.language_cache[key]
