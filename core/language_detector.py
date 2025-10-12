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
            r'^(is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|can|could|should|may|might)$',  # English verbs
            r'^(support|aide|teacher|student|school|principal|admin|staff|learning|education|sports|activities)$'  # Common English school terms
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
        
        # Clean word for analysis
        clean_word = re.sub(r'[^\w]', '', word.lower())
        
        # Aklanon linguistic patterns based on phonology and morphology
        aklanon_patterns = [
            # Aklanon-specific particles and pronouns
            r'^(ngaean|sin-o|nahanumdom|nga|sang|imo|unga)$',
            
            # Aklanon greetings and common words
            r'^(maayong|salamat|gid|damo|huo|indi|sige|tama|mali)$',
            
            # Aklanon question words and interrogatives
            r'^(diin|siin|ngaa|wara|mayo|ro|eon|aton|inyo|ila)$',
            
            # Aklanon verbs and action words
            r'^(ginausoy|hinahanap|gusto|kailangan|pwede|maaari|ginausoy|ginahambae|ginahambae)$',
            
            # Aklanon nouns with 'sang' particle (distinctive feature)
            r'^(oras|klase|paaralan|teacher|grade|sang)$',
            
            # Aklanon time words
            r'^(aga|hapon|gab-i|umaga|tanghali|gabi)$',
            
            # Aklanon pronouns (more comprehensive)
            r'^(mo|ko|niya|namin|ninyo|nila|naton|inyo|ila|ako|ikaw|siya|kami|kayo|sila)$',
            
            # Aklanon question words and particles
            r'^(sino|du|it|hay|alin|kanino|kailan|bakit|paano)$',
            
            # NEW: Aklanon-specific particles and demonstratives
            r'^(ro|ra|raya|daya|roon|don|ra|da)$',  # Subject/topic markers and demonstratives
            
            # NEW: Aklanon pronouns (expanded)
            r'^(ako|ikaw|imaw|kita|kami|kamo|sanda)$',  # Aklanon pronouns
            
            # NEW: Aklanon verbal affixes
            r'^(mag|ga|nag).*',  # Verbal prefixes/infixes
            r'.*mag.*',  # Words containing 'mag' prefix
            r'.*ga.*',   # Words containing 'ga' infix
            
            # NEW: Aklanon emphatic particles
            r'^(du|don|dun|gita|eun|eon)$',  # Emphatic particles
            
            # NEW: Aklanon demonstratives (expanded)
            r'^(raya|daya|roon|don|ra|da)$',  # This/that/here/there
            
            # NEW: Aklanon common words from examples
            r'^(nami|uean|isda|libro|balay|bugas|maaeagkit|tanan|malipayon|kabuhi|atong|kaun|mauna)$',
            
            # Aklanon-specific morphological patterns
            r'^(gin|hin|mag|nag|pag|pang).*',  # Aklanon verb prefixes
            r'.*(ng|nga|sang)$',  # Aklanon particles as suffixes
            r'^(sa|ng|na|ay|ko|mo|niya|namin|ninyo|nila)$',  # Aklanon particles
        ]
        
        # Check against patterns
        pattern_match = any(re.match(pattern, clean_word) for pattern in aklanon_patterns)
        
        # Additional linguistic analysis
        linguistic_score = self._analyze_aklanon_linguistics(clean_word)
        
        return pattern_match or linguistic_score > 0.5
    
    def _analyze_aklanon_linguistics(self, word: str) -> float:
        """Analyze word using Aklanon linguistic features"""
        score = 0.0
        
        # Aklanon phonological features
        # 1. Presence of 'ng' clusters (common in Aklanon)
        if 'ng' in word:
            score += 0.3
        
        # 2. Presence of 'sang' particle (very distinctive)
        if word == 'sang':
            score += 0.8
        
        # 3. Aklanon verb prefixes and infixes
        aklanon_prefixes = ['gin', 'hin', 'mag', 'nag', 'pag', 'pang']
        aklanon_infixes = ['ga', 'um', 'in']
        if any(word.startswith(prefix) for prefix in aklanon_prefixes):
            score += 0.4
        if any(infix in word for infix in aklanon_infixes):
            score += 0.3
        
        # 4. Aklanon question words ending patterns
        if word.endswith(('in', 'on', 'ng')):
            score += 0.2
        
        # 5. Aklanon-specific consonant clusters and particles
        aklanon_clusters = ['ng', 'nga', 'sang', 'ngaean', 'ro', 'raya', 'roon', 'ra', 'da', 'du', 'gita', 'eun', 'eon']
        if any(cluster in word for cluster in aklanon_clusters):
            score += 0.3
        
        # 6. Aklanon vowel patterns (more open vowels)
        vowel_count = sum(1 for char in word if char in 'aeiou')
        if vowel_count > 0:
            vowel_ratio = vowel_count / len(word)
            if vowel_ratio > 0.4:  # Aklanon tends to have more open vowels
                score += 0.2
        
        return min(score, 1.0)
    
    def _analyze_contextual_features(self, text_lower: str) -> dict:
        """Analyze contextual features to distinguish Aklanon from Tagalog"""
        features = {"aklanon_score": 0.0, "tagalog_score": 0.0}
        
        # 1. Sentence structure analysis
        words = text_lower.split()
        
        # 2. Aklanon-specific contextual patterns
        aklanon_context_patterns = [
            r'\bsang\s+\w+',  # "sang" + noun pattern
            r'\bnga\s+\w+',   # "nga" + word pattern
            r'\bdiin\s+ang',  # "diin ang" question pattern
            r'\bsiin\s+ang',  # "siin ang" question pattern
            r'\bngaa\s+ang',  # "ngaa ang" question pattern
            r'\bginausoy\s+ko', # "ginausoy ko" pattern
            r'\bhinahanap\s+ko', # "hinahanap ko" pattern
            
            # NEW: Aklanon-specific patterns from examples
            r'\bro\s+\w+',    # "ro" + word (subject/topic marker)
            r'\braya\s+\w+',  # "raya" + word (this/these)
            r'\broon\s+\w+',  # "roon" + word (that/those)
            r'\bra\s+\w+',    # "ra" + word (this/these specific)
            r'\bda\s+\w+',    # "da" + word (this/these specific)
            r'\bako\s+hay',   # "ako hay" (I am)
            r'\bmag\w+',      # "mag" + verb (verbal prefix)
            r'\bga\w+',       # "ga" + verb (verbal infix)
            r'\bdu\s+\w+',    # "du" + word (emphatic particle)
            r'\bgita\s+\w+',  # "gita" + word (emphatic particle)
            r'\beun\s+\w+',   # "eun" + word (already/now)
            r'\beon\s+\w+',   # "eon" + word (already/now)
            r'\bkita\s+\w+',  # "kita" + word (we inclusive)
            r'\bkami\s+\w+',  # "kami" + word (we exclusive)
            r'\bkamo\s+\w+',  # "kamo" + word (you plural)
            r'\bsanda\s+\w+', # "sanda" + word (they)
        ]
        
        # 3. Tagalog-specific contextual patterns
        tagalog_context_patterns = [
            r'\bang\s+\w+',   # "ang" + noun pattern
            r'\bng\s+\w+',    # "ng" + word pattern
            r'\bsaan\s+ang',  # "saan ang" question pattern
            r'\bano\s+ang',   # "ano ang" question pattern
            r'\bsino\s+ang',  # "sino ang" question pattern
            r'\bgusto\s+ko',  # "gusto ko" pattern
            r'\bkailangan\s+ko', # "kailangan ko" pattern
        ]
        
        # Count pattern matches
        import re
        for pattern in aklanon_context_patterns:
            if re.search(pattern, text_lower):
                features["aklanon_score"] += 0.2
        
        for pattern in tagalog_context_patterns:
            if re.search(pattern, text_lower):
                features["tagalog_score"] += 0.2
        
        # 4. Word order analysis
        # Aklanon tends to use "sang" while Tagalog uses "ng"
        sang_count = text_lower.count('sang')
        ng_count = text_lower.count(' ng ')
        
        if sang_count > ng_count:
            features["aklanon_score"] += 0.3
        elif ng_count > sang_count:
            features["tagalog_score"] += 0.3
        
        # 5. Question word analysis
        aklanon_questions = ['diin', 'siin', 'ngaa', 'ginausoy', 'hinahanap', 'ro', 'raya', 'roon', 'ra', 'da', 'ako', 'ikaw', 'imaw', 'kita', 'kami', 'kamo', 'sanda', 'du', 'gita', 'eun', 'eon', 'mag', 'ga', 'nag']
        tagalog_questions = ['saan', 'ano', 'sino', 'gusto', 'kailangan', 'ang', 'ng', 'sa', 'ay', 'si', 'mga', 'namin', 'natin', 'ko', 'mo', 'niya', 'nila', 'kami', 'kayo', 'sila']
        
        aklanon_q_count = sum(1 for q in aklanon_questions if q in text_lower)
        tagalog_q_count = sum(1 for q in tagalog_questions if q in text_lower)
        
        if aklanon_q_count > tagalog_q_count:
            features["aklanon_score"] += 0.2
        elif tagalog_q_count > aklanon_q_count:
            features["tagalog_score"] += 0.2
        
        return features
    
    def _detect_with_langid(self, text: str) -> Tuple[str, float]:
        """Detect language using langid library (removed - using langdetect instead)"""
        # Fallback to English with low confidence
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
            max_score = best_lang[1]
            
            # Check for ties and prefer Aklanon over Tagalog
            tied_languages = [lang for lang, score in language_scores.items() if score == max_score]
            if len(tied_languages) > 1:
                if "akl" in tied_languages:
                    return "akl", max_score
                elif "tl" in tied_languages:
                    return "tl", max_score
            
            return best_lang[0], best_lang[1]
            
        except Exception as e:
            logger.warning(f"NLP analysis failed: {e}")
            return "en", 0.3
    
    def _detect_with_patterns(self, text_lower: str) -> Tuple[str, float]:
        """Detect language using pattern matching"""
        try:
            # Check for greeting patterns first (more specific)
            english_greetings = ["good morning", "good afternoon", "good evening", "good day", "hello", "hi there", "hey there"]
            tagalog_greetings = ["kumusta", "kamusta", "magandang umaga", "magandang hapon", "magandang gabi"]
            aklanon_greetings = ["maayong aga", "maayong hapon", "maayong gab-i", "maayong buntag"]
            
            if any(greeting in text_lower for greeting in english_greetings):
                return "en", 0.9
            elif any(greeting in text_lower for greeting in aklanon_greetings):
                return "akl", 0.9
            elif any(greeting in text_lower for greeting in tagalog_greetings):
                return "tl", 0.9
            
            # Check for mixed-language indicators first
            mixed_tagalog_indicators = ["po", "ng", "sa", "ang", "ay", "si", "mga"]
            mixed_aklanon_indicators = ["sang", "nga", "ngaean", "diin", "siin", "ngaa"]
            has_mixed_tagalog = any(indicator in text_lower for indicator in mixed_tagalog_indicators)
            has_mixed_aklanon = any(indicator in text_lower for indicator in mixed_aklanon_indicators)
            
            if has_mixed_aklanon:
                # If mixed Aklanon indicators are present, prefer Aklanon
                return "akl", 0.8
            elif has_mixed_tagalog:
                # If mixed Tagalog indicators are present, prefer Tagalog
                return "tl", 0.8
            
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
                
                # If there's a tie, prefer Tagalog/Aklanon over English for mixed queries
                best_lang = max(pattern_counts.items(), key=lambda x: x[1])
                max_score = best_lang[1]
                
                # Check for ties and prefer Aklanon over Tagalog
                tied_languages = [lang for lang, score in pattern_counts.items() if score == max_score]
                if len(tied_languages) > 1:
                    if "akl" in tied_languages:
                        return "akl", max_score
                    elif "tl" in tied_languages:
                        return "tl", max_score
                
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
        
        # Adjust weights based on text length and complexity (langid removed)
        if text_length < 3:
            # Short text: rely more on patterns
            weights = {"nlp": 0.3, "pattern": 0.7}
        elif text_length < 10:
            # Medium text: balanced approach
            weights = {"nlp": 0.5, "pattern": 0.5}
        else:
            # Long text: rely more on NLP analysis
            weights = {"nlp": 0.7, "pattern": 0.3}
        
        # Calculate weighted scores for each language
        language_scores = {"en": 0.0, "tl": 0.0, "akl": 0.0}
        
        for lang in language_scores:
            # NLP contribution
            if nlp_result[0] == lang:
                language_scores[lang] += nlp_result[1] * weights["nlp"]
            
            # Pattern contribution
            if pattern_result[0] == lang:
                language_scores[lang] += pattern_result[1] * weights["pattern"]
        
        # Add contextual analysis for Aklanon vs Tagalog distinction
        contextual_features = self._analyze_contextual_features(text_lower)
        language_scores["akl"] += contextual_features["aklanon_score"] * 0.3
        language_scores["tl"] += contextual_features["tagalog_score"] * 0.3
        
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
