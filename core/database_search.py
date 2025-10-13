"""
Clean Database Search Module
Handles database search operations with reliable scoring
"""
import logging
from typing import List, Dict, Optional, Any
from supabase import create_client, Client
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class ImprovedScorer:
    """Clean, reliable scoring system"""
    
    def __init__(self):
        # Define score weights (clean, reasonable values)
        self.weights = {
            'exact_match': 100,
            'keyword_match': 50,
            'word_overlap': 10,  # per word
            'response_match': 5,   # per word
            'length_bonus': 15,
            'semantic_similarity': 80,
            'intent_match': 40
        }
        
        # Intent keywords for classification
        self.intent_patterns = {
            'staff': ['who', 'sino', 'teacher', 'adviser', 'principal', 'staff', 'guro', 'head', 'director', 'administrator'],
            'schedule': ['hours', 'schedule', 'time', 'when', 'start', 'end'],
            'location': ['location of the', 'find the'],  # More specific location patterns
            'grade': ['grade', 'baitang']
        }
    
    def calculate_score(self, result: Dict, query: str) -> int:
        """Calculate relevance score using balanced approach"""
        score = 0
        
        query_lower = query.lower()
        keywords_lower = (result.get('keywords') or '').lower()
        response_lower = (result.get('response') or '').lower()
        
        # Clean query (remove question words)
        clean_query = self._clean_query(query_lower)
        
        # DEBUG: Log scoring for school activities queries (reduced) - removed verbose logging
        
        # 1. Exact match (highest priority)
        if clean_query == keywords_lower or query_lower == keywords_lower:
            score += self.weights['exact_match']
        
        # 2. Keyword containment
        if clean_query in keywords_lower or query_lower in keywords_lower:
            score += self.weights['keyword_match']
        
        # 2.5. Boost for exact phrase matches in keywords (highest priority)
        important_phrases = ['learning support aide', 'support aide', 'grade level', 'grade levels']
        for phrase in important_phrases:
            if phrase in query_lower and phrase in keywords_lower:
                score += 50  # High boost for exact phrase matches
        
        # 3. Word overlap scoring - require significant overlap to prevent false matches
        query_words = self._get_important_words(clean_query)
        # Clean keyword words by removing punctuation
        keyword_words_clean = [re.sub(r'[^\w]', '', word) for word in keywords_lower.split()]
        keyword_words = set(word for word in keyword_words_clean if word)
        response_words_clean = [re.sub(r'[^\w]', '', word) for word in response_lower.split()]
        response_words = set(word for word in response_words_clean if word)
        
        keyword_overlap = len(query_words & keyword_words)
        response_overlap = len(query_words & response_words)
        
        # Only apply word overlap scoring if there's significant overlap (avoid single-word matches)
        # For short queries (2-3 words), require high overlap to prevent false matches like "sports" vs "support"
        # For longer queries, use lower threshold to allow more flexible matching
        overlap_threshold = 0.75 if len(query_words) <= 3 else 0.5
        
        if keyword_overlap >= len(query_words) * overlap_threshold:
            score += keyword_overlap * self.weights['word_overlap']
        if response_overlap >= len(query_words) * overlap_threshold:
            score += response_overlap * self.weights['response_match']
        
        
        # 3.5. Enhanced word matching for activities
        if 'activ' in query_lower:
            # Check for activity-related words in keywords and response
            activity_words = ['activ', 'event', 'program', 'celebration', 'annual', 'major']
            for word in activity_words:
                if word in keywords_lower:
                    score += 15
                if word in response_lower:
                    score += 10
        
        # 4. Length bonus (concise answers preferred) - only if there's some relevance
        if len(result.get('response', '')) < 150 and score > 0:
            score += self.weights['length_bonus']
        
        # 5. Semantic similarity (simple fuzzy match) - with very strict threshold to prevent false matches
        similarity = SequenceMatcher(None, clean_query, keywords_lower).ratio()
        # Only apply similarity bonus if similarity is extremely high (>0.95) to prevent false matches like "sports" vs "support"
        if similarity > 0.95:
            similarity_score = int(similarity * self.weights['semantic_similarity'])
            score += similarity_score
        
        # 5.5. Enhanced semantic matching for activities
        if 'activ' in query_lower and 'activ' in keywords_lower:
            score += 30  # Boost for activity-related queries
        if 'school' in query_lower and 'school' in keywords_lower:
            score += 20  # Boost for school-related queries
        
        # 5.6. Enhanced scoring for CR/comfort room queries
        if any(word in query_lower for word in ['cr', 'comfort', 'banyo', 'toilet', 'restroom']):
            if any(word in keywords_lower for word in ['cr', 'comfort', 'banyo', 'toilet', 'restroom']):
                score += 50  # Major boost for CR-related keywords
            if any(word in response_lower for word in ['cr', 'comfort', 'banyo', 'toilet', 'restroom']):
                score += 30  # Boost for CR-related response content
        
        # DEBUG: Log final score for school activities queries (reduced) - removed verbose logging
        
        # DEBUG: Log scoring for CR queries (reduced) - removed verbose logging
        
        # 🚨 REMOVED: No hardcoded boosting - let the algorithm work naturally
        
        # DEBUG: Log semantic similarity for school activities queries (disabled for deployment)
        # if 'school' in query_lower and 'activ' in query_lower:
        #     logger.info(f"🔍 SEMANTIC DEBUG: Similarity: {similarity:.3f}, Score: {similarity_score}, Total: {score}")
        
        # 6. Intent matching
        query_intent = self._detect_intent(query_lower)
        content_intent = self._detect_intent(keywords_lower + ' ' + response_lower)
        
        if query_intent and query_intent == content_intent:
            score += self.weights['intent_match']
        
        # 🚨 REMOVED: No hardcoded penalties - let the algorithm work naturally
        
        # 7. Grade-specific matching
        score += self._score_grade_match(query_lower, keywords_lower, response_lower)
        
        # 7.5. Kindergarten fuzzy matching
        if 'kinder' in query_lower and 'kindergarten' in keywords_lower:
            score += 20  # Boost for kinder -> kindergarten match
        elif 'kindergarten' in query_lower and 'kinder' in keywords_lower:
            score += 20  # Boost for kindergarten -> kinder match
        
        # 7.6. School leadership fuzzy matching
        # Special handling for "school head" -> "Head Teacher" (only for school context)
        # Exclude department heads, foreign affairs, academic departments, etc.
        department_keywords = ['department', 'foreign', 'math', 'science', 'english', 'history', 'geography', 'economics', 'politics', 'affairs', 'ministry', 'bureau', 'office']
        
        is_department_head = any(keyword in query_lower for keyword in department_keywords)
        
        if ('school head' in query_lower or 
            ('head' in query_lower and not is_department_head)):
            if 'head teacher' in keywords_lower or 'head teacher' in response_lower:
                score += 50  # Higher boost for school head -> head teacher match
                # logger.info(f"🎯 SCHOOL HEAD MATCH: school head -> head teacher (score: {score})")
            elif 'principal' in keywords_lower or 'principal' in response_lower:
                score += 20  # Lower boost for principal
                # logger.info(f"🎯 SCHOOL HEAD PARTIAL: school head -> principal (score: {score})")
        
        # General leadership fuzzy matching
        leadership_terms = {
            'principal': ['principal', 'head teacher', 'director', 'administrator'],
            'director': ['head teacher', 'principal', 'director', 'administrator'],
            'administrator': ['head teacher', 'principal', 'director', 'administrator']
        }
        
        for query_term, db_terms in leadership_terms.items():
            if query_term in query_lower and 'school head' not in query_lower:  # Don't apply to school head queries
                for db_term in db_terms:
                    if db_term in keywords_lower or db_term in response_lower:
                        score += 30  # Boost for leadership term matches
                        # logger.info(f"🎯 LEADERSHIP FUZZY MATCH: {query_term} -> {db_term} (score: {score})")
                        break
        
        # 8. Penalties
        score -= self._calculate_penalties(result)
        
        # 8.5. Department head penalty - reduce score if department query matches Head Teacher
        department_keywords = ['department', 'foreign', 'math', 'science', 'english', 'history', 'geography', 'economics', 'politics', 'affairs', 'ministry', 'bureau', 'office']
        is_department_query = any(keyword in query_lower for keyword in department_keywords)
        
        if is_department_query and ('head teacher' in keywords_lower or 'head teacher' in response_lower):
            score -= 50  # Heavy penalty for department queries matching Head Teacher
            # logger.info(f"🎯 DEPARTMENT HEAD PENALTY: department query matched Head Teacher (score: {score})")
        
        # DEBUG: Log final score for school activities queries (disabled for deployment)
        # if 'school' in query_lower and 'activ' in query_lower:
        #     logger.info(f"🔍 FINAL SCORE: {score} for '{keywords_lower[:50]}...'")
        
        return max(0, score)  # Never negative
    
    def _clean_query(self, query: str) -> str:
        """Remove question words and punctuation"""
        # Remove question words
        query = re.sub(r'^(who|what|where|when|why|how|sino|ano|saan|kailan|bakit|paano)\s+(is|are|was|were)\s+(the|a|an)?\s*', '', query)
        # Remove punctuation
        query = re.sub(r'[?.!,]', '', query)
        return query.strip()
    
    def _get_important_words(self, text: str) -> set:
        """Extract important words (filter out common words)"""
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
                     'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were',
                     'ang', 'ng', 'sa', 'mga', 'ko', 'mo'}
        
        words = text.split()
        return {w for w in words if len(w) > 2 and w not in stopwords}
    
    def _detect_intent(self, text: str) -> str:
        """Detect primary intent from text"""
        for intent, keywords in self.intent_patterns.items():
            if any(kw in text for kw in keywords):
                return intent
        return 'general'
    
    def _score_grade_match(self, query: str, keywords: str, response: str) -> int:
        """Score grade-specific matches"""
        score = 0
        
        # Extract grade from query
        grade_match = re.search(r'grade\s+(\d+|one|two|three|four|five|six)', query)
        if not grade_match:
            return 0
        
        grade_value = grade_match.group(1)
        
        # Check if keywords/response contain the same grade
        combined_text = keywords + ' ' + response
        
        # Direct match
        if f'grade {grade_value}' in combined_text:
            score += 50
        
        # Handle number/word conversion
        number_map = {'1': 'one', '2': 'two', '3': 'three', '4': 'four', 
                      '5': 'five', '6': 'six'}
        
        if grade_value.isdigit() and grade_value in number_map:
            if f'grade {number_map[grade_value]}' in combined_text:
                score += 50
        elif grade_value in number_map.values():
            # Reverse lookup
            num = [k for k, v in number_map.items() if v == grade_value][0]
            if f'grade {num}' in combined_text:
                score += 50
        
        return score
    
    def _calculate_penalties(self, result: Dict) -> int:
        """Calculate penalty points for undesirable results"""
        penalty = 0
        response = result.get('response', '').lower()
        
        # Generic responses
        generic_phrases = ['you must be looking', 'visit the school office', 
                          'contact the school', 'grade levels are offered']
        if any(phrase in response for phrase in generic_phrases):
            penalty += 30
        
        # Very long responses
        if len(response) > 300:
            penalty += 10
        
        return penalty

class DatabaseSearchEngine:
    """Clean database search engine with reliable scoring and three-tier search"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self._improved_scorer = ImprovedScorer()
        
        # Initialize three-tier search system
        try:
            from core.three_tier_search import ThreeTierSearch
            self.three_tier_search = ThreeTierSearch(self.supabase)
            self.use_three_tier = True
            logger.info("✅ Three-tier search system initialized")
        except ImportError as e:
            logger.warning(f"Three-tier search not available: {e}")
            self.three_tier_search = None
            self.use_three_tier = False
    
    def _clean_query_for_tsquery(self, query: str) -> str:
        """Clean query for PostgreSQL tsquery syntax to avoid syntax errors"""
        # Remove problematic characters that cause tsquery syntax errors
        cleaned = query.strip()
        
        # Remove ALL punctuation and special characters that cause tsquery issues
        cleaned = re.sub(r'[!@#$%^&*()_+=\[\]{}|;:"<>?/~`\\]', '', cleaned)
        
        # Remove exclamation marks and other problematic characters
        cleaned = re.sub(r'[!?]', '', cleaned)
        
        # Remove escaped characters and backslashes
        cleaned = re.sub(r'\\', '', cleaned)
        
        # Remove single characters and very short words
        words = cleaned.split()
        valid_words = [word for word in words if len(word) > 1]
        
        if not valid_words:
            return None
            
        # Join with & for tsquery syntax
        return ' & '.join(valid_words)
    
    def _validate_grade_level(self, query: str) -> Dict[str, Any]:
        """Validate if a grade level exists in the school by checking database"""
        import re
        
        # Look for grade patterns including negative numbers
        grade_match = re.search(r'grade\s*(-?\d+)', query.lower())
        if grade_match:
            grade_num = int(grade_match.group(1))
            
            # Handle negative grades and zero
            if grade_num <= 0:
                return {
                    'is_valid': False,
                    'grade': grade_num,
                    'message': f"Grade {grade_num} is not a valid grade level. Grade levels must be positive numbers (1-6).",
                    'available_grades': 'Kindergarten through Grade 6'
                }
            
            # Handle obviously invalid grades (too high)
            if grade_num > 12:
                return {
                    'is_valid': False,
                    'grade': grade_num,
                    'message': f"Grade {grade_num} is not a valid grade level. Elementary schools typically offer grades 1-6.",
                    'available_grades': 'Kindergarten through Grade 6'
                }
            
            # Check database for available grade levels
            try:
                # Search for grade level information in database
                result = self.supabase.table("chatbot_prompts") \
                    .select("keywords, response") \
                    .text_search("search_tsv", "grade level OR grade OR kindergarten") \
                    .execute()
                
                if result.data:
                    # Extract available grades from database responses
                    available_grades = self._extract_available_grades(result.data)
                    
                    if available_grades:
                        max_grade = max(available_grades)
                        if grade_num > max_grade:
                            return {
                                'is_valid': False,
                                'grade': grade_num,
                                'message': f"Grade {grade_num} is not offered at this school. We only offer {self._format_grade_range(available_grades)}.",
                                'available_grades': self._format_grade_range(available_grades)
                            }
                        else:
                            return {
                                'is_valid': True,
                                'grade': grade_num,
                                'message': f"Grade {grade_num} is available."
                            }
                
                # Fallback: if no grade info found in database, assume K-6
                if grade_num > 6:
                    return {
                        'is_valid': False,
                        'grade': grade_num,
                        'message': f"Grade {grade_num} is not offered at this school. We only offer Kindergarten through Grade 6.",
                        'available_grades': 'Kindergarten through Grade 6'
                    }
                else:
                    return {
                        'is_valid': True,
                        'grade': grade_num,
                        'message': f"Grade {grade_num} is available."
                    }
                    
            except Exception as e:
                logger.warning(f"Grade validation database check failed: {e}")
                # Fallback to basic validation
                if grade_num > 6:
                    return {
                        'is_valid': False,
                        'grade': grade_num,
                        'message': f"Grade {grade_num} is not offered at this school. We only offer Kindergarten through Grade 6.",
                        'available_grades': 'Kindergarten through Grade 6'
                    }
                else:
                    return {
                        'is_valid': True,
                        'grade': grade_num,
                        'message': f"Grade {grade_num} is available."
                    }
        
        return {'is_valid': True, 'message': 'No specific grade mentioned.'}
    
    def _extract_available_grades(self, data: List[Dict]) -> List[int]:
        """Extract available grade numbers from database responses"""
        import re
        
        available_grades = set()
        
        for item in data:
            text = (item.get('keywords', '') + ' ' + item.get('response', '')).lower()
            
            # Look for grade patterns
            grade_patterns = [
                r'grade\s*(\d+)',
                r'kindergarten',
                r'k-(\d+)',
                r'grades?\s*(\d+)\s*through\s*(\d+)',
                r'grades?\s*(\d+)\s*to\s*(\d+)',
            ]
            
            for pattern in grade_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    if pattern == r'kindergarten':
                        available_grades.add(0)  # Kindergarten = Grade 0
                    elif pattern in [r'k-(\d+)']:
                        # K-6 format
                        k_num = int(match.group(1))
                        available_grades.update(range(0, k_num + 1))
                    elif pattern in [r'grades?\s*(\d+)\s*through\s*(\d+)', r'grades?\s*(\d+)\s*to\s*(\d+)']:
                        # Grade range format
                        start_grade = int(match.group(1))
                        end_grade = int(match.group(2))
                        available_grades.update(range(start_grade, end_grade + 1))
                    else:
                        # Single grade
                        grade_num = int(match.group(1))
                        available_grades.add(grade_num)
        
        return sorted(list(available_grades))
    
    def _validate_search_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """Validate search results to ensure they match query intent"""
        
        if not results:
            return results
        
        # Calculate confidence scores for each result
        validated_results = []
        for result in results:
            confidence = self._calculate_result_confidence(query, result)
            if confidence > 0.3:  # Minimum confidence threshold
                validated_results.append(result)
        
        # If no results pass validation, return original results (fallback)
        if not validated_results:
            logger.warning(f"No results passed validation for query: {query}")
            return results[:3]  # Return top 3 original results as fallback
        
        return validated_results
    
    def _calculate_result_confidence(self, query: str, result: Dict) -> float:
        """Calculate confidence score for search results"""
        
        query_words = set(query.lower().split())
        keywords = result.get('keywords', '').lower()
        response = result.get('response', '').lower()
        
        # Combine keywords and response for matching
        result_text = f"{keywords} {response}"
        result_words = set(result_text.split())
        
        # Calculate word overlap
        overlap = len(query_words.intersection(result_words))
        total_words = len(query_words.union(result_words))
        
        if total_words == 0:
            return 0.0
        
        # Base confidence from word overlap
        base_confidence = overlap / total_words
        
        # Boost confidence for exact keyword matches
        keyword_matches = sum(1 for word in query_words if word in keywords)
        if keyword_matches > 0:
            base_confidence += keyword_matches * 0.1
        
        # Boost confidence for response content matches
        response_matches = sum(1 for word in query_words if word in response)
        if response_matches > 0:
            base_confidence += response_matches * 0.05
        
        return min(base_confidence, 1.0)  # Cap at 1.0
    
    def _format_grade_range(self, grades: List[int]) -> str:
        """Format grade range in a user-friendly way"""
        if not grades:
            return "No grade information available"
        
        # Convert 0 to Kindergarten
        if 0 in grades:
            grades = [g for g in grades if g != 0]
            if grades:
                return f"Kindergarten through Grade {max(grades)}"
            else:
                return "Kindergarten"
        
        if len(grades) == 1:
            return f"Grade {grades[0]}"
        else:
            return f"Grade {min(grades)} through Grade {max(grades)}"
    
    def _translate_query_for_search(self, query: str) -> str:
        """Translate Tagalog queries to English for better database matching"""
        import re
        query_lower = query.lower().strip()
        
        # Check if query is already in English to avoid unnecessary translation
        # Simple heuristic: if query contains common English words, don't translate
        english_indicators = ['what', 'where', 'when', 'why', 'how', 'who', 'which', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'can', 'could', 'should', 'may', 'might', 'activities', 'held', 'school', 'teacher', 'student', 'principal', 'admin', 'staff']
        
        # If query contains English indicators, don't translate
        if any(indicator in query_lower for indicator in english_indicators):
            translated_query = query_lower
        else:
            # Try basic translation for non-English queries
            try:
                from deep_translator import GoogleTranslator
                translated_query = GoogleTranslator(source='auto', target='en').translate(query_lower)
            except:
                translated_query = query_lower
        
        # Clean up common words that don't help with matching
        # Include Aklanon particles: 'du' (the), 'it' (this), 'hay' (is)
        # BUT PRESERVE GRADE NUMBERS (1, 2, 3, etc.)
        words_to_remove = ['ang', 'ng', 'sa', 'para', 'in', 'who', 'what', 'where', 'when', 'why', 'how', 'kayo', 'kayO', 'du', 'it', 'hay', 'ba', 'may']
        translated_words = translated_query.split()
        cleaned_words = []
        for word in translated_words:
            # Preserve grade numbers (1, 2, 3, etc.) and grade-related words
            if word.isdigit() or word in ['grade', 'teacher', 'adviser', 'advisor', 'guro', 'titser', 'maestra', 'maestro']:
                cleaned_words.append(word)
            elif word not in words_to_remove:
                cleaned_words.append(word)
        translated_query = ' '.join(cleaned_words)
        
        # Handle specific Tagalog question patterns
        if 'learning support aide' in translated_query.lower():
            translated_query = 'learning support aide'
        elif 'support aide' in translated_query.lower():
            translated_query = 'support aide'
        elif 'teacher' in translated_query.lower() and 'grade' in translated_query.lower():
            # Extract grade number and create proper query
            import re
            grade_match = re.search(r'grade\s+(\d+)', translated_query.lower())
            if grade_match:
                grade_num = grade_match.group(1)
                translated_query = f'grade {grade_num} teacher'
        elif 'principal' in translated_query.lower():
            translated_query = 'principal'
        elif 'cr' in translated_query.lower() or 'banyo' in translated_query.lower():
            translated_query = 'comfort room'
        
        # Special handling for "may prinsipal" queries
        if 'have principal' in translated_query or 'principal' in translated_query:
            # For principal queries, just search for "principal"
            translated_query = 'principal'
        
        # Handle "sino ang principal" queries specifically
        if 'sino' in query_lower and 'principal' in query_lower:
            translated_query = 'principal'
        
        # 🚨 FIX: Special handling for office hours queries
        if 'office hours' in translated_query or 'opisyal hours' in translated_query:
            # For office hours queries, search for "office hours"
            translated_query = 'office hours'
            
        # 🚨 ENHANCED: Special handling for grade teacher queries
        # Pattern 1: teacher/adviser before grade
        grade_teacher_pattern = re.search(r'(teacher|adviser|advisor|guro|titser|maestra|maestro).*?(grade|grado|baitang)\s*(\d+)', query_lower)
        # Pattern 2: grade before teacher/adviser  
        if not grade_teacher_pattern:
            grade_teacher_pattern = re.search(r'(grade|grado|baitang)\s*(\d+).*?(teacher|adviser|advisor|guro|titser|maestra|maestro)', query_lower)
        # Pattern 3: "may teacher ba ang grade X" - Tagalog question pattern
        if not grade_teacher_pattern:
            grade_teacher_pattern = re.search(r'may\s+(teacher|adviser|advisor|guro|titser|maestra|maestro)\s+ba\s+ang\s+(grade|grado|baitang)\s*(\d+)', query_lower)
            
        if grade_teacher_pattern:
            grade_num = None
            # For Pattern 3: "may teacher ba ang grade X" - grade is in group 3
            # Check which pattern matched to determine correct group
            # Pattern 1: teacher before grade - grade is in group 3
            # Pattern 2: grade before teacher - grade is in group 2  
            # Pattern 3: "may teacher ba ang grade X" - grade is in group 3
            if grade_teacher_pattern.group(1).lower() in ['grade', 'grado', 'baitang']:
                # Pattern 2: grade before teacher - grade is in group 2
                grade_num = grade_teacher_pattern.group(2)
            else:
                # Pattern 1 or 3: teacher before grade or Tagalog pattern - grade is in group 3
                grade_num = grade_teacher_pattern.group(3)
                
            if grade_num:
                # For grade teacher queries, create a standardized search pattern
                translated_query = f"grade {grade_num} adviser"
                # logger.info(f"🔧 GRADE TEACHER QUERY: '{query_lower}' -> '{translated_query}'")
        
        # Log the translation for debugging
        if translated_query != query_lower:
            # logger.info(f"🔧 TYPO FIX: '{query_lower}' -> '{translated_query}'")
            return translated_query
        
        return query_lower
    
    def _extract_important_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query using database-driven approach"""
        try:
            # Get all keywords from database
            result = self.supabase.table("chatbot_prompts") \
                .select("keywords") \
                .execute()
            
            if not result.data:
                return []
            
            # Build keyword database
            all_keywords = []
            for item in result.data:
                if item.get('keywords'):
                    all_keywords.extend(item['keywords'].split(', '))
            
            # Extract important keywords from query
            important_keywords = []
            query_words = query.split()
            
            for word in query_words:
                # Skip only very common Tagalog particles and English stopwords
                if word in ['ang', 'ng', 'sa', 'para', 'in', 'kayo', 'kayO', 'du', 'it', 'hay', 'ba', 'may', 'sino', 'ano', 'nasaan', 'saan']:
                    continue
                
                # Check if word matches any database keyword (exact or partial)
                best_match = None
                best_score = 0
                
                for keyword in all_keywords:
                    keyword_lower = keyword.lower().strip()
                    
                    # Exact match gets highest priority
                    if word == keyword_lower:
                        best_match = keyword_lower
                        best_score = 1.0
                        break
                    # Partial match gets lower priority
                    elif word in keyword_lower or keyword_lower in word:
                        # Calculate similarity score
                        from difflib import SequenceMatcher
                        score = SequenceMatcher(None, word, keyword_lower).ratio()
                        if score > best_score and score > 0.6:  # Only accept good matches
                            best_match = keyword_lower
                            best_score = score
                
                if best_match:
                    # Found a match, add the best English equivalent
                    english_keyword = self._get_english_equivalent(best_match)
                    if english_keyword and english_keyword not in important_keywords:
                        important_keywords.append(english_keyword)
            
            return important_keywords
            
        except Exception as e:
            logger.warning(f"Keyword extraction failed: {e}")
            return []
    
    def _get_english_equivalent(self, keyword: str) -> str:
        """Get English equivalent of a keyword"""
        # Common Tagalog to English mappings
        mappings = {
            'cr': 'comfort room',
            'banyo': 'comfort room',
            'palikuran': 'comfort room',
            'guro': 'teacher',
            'titser': 'teacher',
            'maestra': 'teacher',
            'maestro': 'teacher',
            'adviser': 'adviser',
            'advisor': 'adviser',
            'prinsipal': 'principal',
            'principal': 'principal',
            'paaralan': 'school',
            'eskwela': 'school',
            'klase': 'class',
            'grade': 'grade',
            'baitang': 'grade',
            'oras': 'hours',
            'time': 'hours',
            'library': 'library',
            'aklatan': 'library',
            'computer': 'computer',
            'lab': 'laboratory',
            'laboratory': 'laboratory',
            'guidance': 'guidance',
            'counselor': 'counselor',
            'support aide': 'support aide',
            'learning support aide': 'learning support aide',
            'aide': 'aide'
        }
        
        # Check for exact matches first
        if keyword in mappings:
            return mappings[keyword]
        
        # Check for partial matches
        for tagalog, english in mappings.items():
            if tagalog in keyword or keyword in tagalog:
                return english
        
        # If no mapping found, return the keyword as-is (might already be English)
        return keyword
        
        
        # 🎯 DYNAMIC TYPO FIX: Use fuzzy matching for typos
        # This will be handled in the search logic, not here
        
        # Clean up common words that don't help with matching
        # Include Aklanon particles: 'du' (the), 'it' (this), 'hay' (is)
        words_to_remove = ['ang', 'ng', 'sa', 'para', 'in', 'who', 'what', 'where', 'when', 'why', 'how', 'kayo', 'kayO', 'du', 'it', 'hay', 'ba', 'may']
        translated_words = translated_query.split()
        cleaned_words = [word for word in translated_words if word not in words_to_remove]
        translated_query = ' '.join(cleaned_words)
        
        # Handle specific Tagalog question patterns
        if 'learning support aide' in translated_query.lower():
            translated_query = 'learning support aide'
        elif 'support aide' in translated_query.lower():
            translated_query = 'support aide'
        elif 'teacher' in translated_query.lower() and 'grade' in translated_query.lower():
            # Extract grade number and create proper query
            import re
            grade_match = re.search(r'grade\s+(\d+)', translated_query.lower())
            if grade_match:
                grade_num = grade_match.group(1)
                translated_query = f'grade {grade_num} teacher'
        elif 'principal' in translated_query.lower():
            translated_query = 'principal'
        elif 'cr' in translated_query.lower() or 'banyo' in translated_query.lower():
            translated_query = 'comfort room'
        
        # Special handling for "may prinsipal" queries
        if 'have principal' in translated_query or 'principal' in translated_query:
            # For principal queries, just search for "principal"
            translated_query = 'principal'
        
        # Handle "sino ang principal" queries specifically
        if 'sino' in query_lower and 'principal' in query_lower:
            translated_query = 'principal'
        
        # 🚨 FIX: Special handling for office hours queries
        if 'office hours' in translated_query or 'opisyal hours' in translated_query:
            # For office hours queries, search for "office hours"
            translated_query = 'office hours'
            
        # 🚨 ENHANCED: Special handling for grade teacher queries
        # Pattern 1: teacher/adviser before grade
        grade_teacher_pattern = re.search(r'(teacher|adviser|advisor|guro|titser|maestra|maestro).*?(grade|grado|baitang)\s*(\d+)', query_lower)
        # Pattern 2: grade before teacher/adviser  
        if not grade_teacher_pattern:
            grade_teacher_pattern = re.search(r'(grade|grado|baitang)\s*(\d+).*?(teacher|adviser|advisor|guro|titser|maestra|maestro)', query_lower)
        # Pattern 3: "may teacher ba ang grade X" - Tagalog question pattern
        if not grade_teacher_pattern:
            grade_teacher_pattern = re.search(r'may\s+(teacher|adviser|advisor|guro|titser|maestra|maestro)\s+ba\s+ang\s+(grade|grado|baitang)\s*(\d+)', query_lower)
            
        if grade_teacher_pattern:
            grade_num = None
            # For Pattern 3: "may teacher ba ang grade X" - grade is in group 3
            # Check which pattern matched to determine correct group
            # Pattern 1: teacher before grade - grade is in group 3
            # Pattern 2: grade before teacher - grade is in group 2  
            # Pattern 3: "may teacher ba ang grade X" - grade is in group 3
            if grade_teacher_pattern.group(1).lower() in ['grade', 'grado', 'baitang']:
                # Pattern 2: grade before teacher - grade is in group 2
                grade_num = grade_teacher_pattern.group(2)
            else:
                # Pattern 1 or 3: teacher before grade or Tagalog pattern - grade is in group 3
                grade_num = grade_teacher_pattern.group(3)
                
            if grade_num:
                # For grade teacher queries, create a standardized search pattern
                translated_query = f"grade {grade_num} adviser"
                # logger.info(f"🔧 GRADE TEACHER QUERY: '{query_lower}' -> '{translated_query}'")
        
        # Log the translation for debugging
        if translated_query != query_lower:
            # logger.info(f"🔧 TYPO FIX: '{query_lower}' -> '{translated_query}'")
            return translated_query
        
        return query_lower
    
    def _get_dynamic_translation(self, query: str) -> str:
        """Get dynamic translation using existing database keywords - no setup required"""
        try:
            # Use existing chatbot_prompts keywords for translation - no additional database setup needed
            return self._get_keyword_based_translation(query)
            
        except Exception as e:
            logger.warning(f"Dynamic translation error: {e}")
            return self._get_fallback_translation(query)
    
    def _get_keyword_based_translation(self, query: str) -> str:
        """Get translation using existing keywords from chatbot_prompts table - no setup required"""
        try:
            # Get keywords from the existing database to find matches
            result = self.supabase.table("chatbot_prompts") \
                .select("keywords") \
                .execute()
            
            if result.data:
                all_keywords = []
                for item in result.data:
                    if item.get('keywords'):
                        all_keywords.extend(item['keywords'].split(', '))
                
                # Find the best matching keyword from the database
                best_match = self._find_best_keyword_match(query, all_keywords)
                if best_match:
                    # logger.info(f"🔧 KEYWORD TRANSLATION: '{query}' -> '{best_match}' (from existing database keywords)")
                    return best_match
            
            # If no keyword match, use intelligent pattern-based translation
            return self._get_intelligent_translation(query)
            
        except Exception as e:
            logger.warning(f"Keyword-based translation error: {e}")
            return self._get_intelligent_translation(query)
    
    def _find_best_keyword_match(self, query: str, keywords: List[str]) -> str:
        """Find the best matching keyword from database using fuzzy matching"""
        from difflib import SequenceMatcher
        
        best_match = None
        best_score = 0
        
        for keyword in keywords:
            # Check for direct word matches
            query_words = query.split()
            keyword_words = keyword.lower().split()
            
            # Calculate similarity score
            similarity = SequenceMatcher(None, query.lower(), keyword.lower()).ratio()
            
            # Check for word overlap
            word_overlap = len(set(query_words) & set(keyword_words))
            
            # Combined score
            combined_score = similarity * 0.7 + (word_overlap / max(len(query_words), len(keyword_words))) * 0.3
            
            if combined_score > best_score and combined_score > 0.3:  # Minimum threshold
                best_score = combined_score
                best_match = keyword
        
        return best_match
    
    async def _quick_exact_search(self, query: str) -> List[Dict[str, Any]]:
        """Quick exact search to check if we can skip WordNet expansion"""
        try:
            # Query is already translated by search_prompts
            translated_query = query
            
            # Search for exact phrase matches first
            clean_query = re.sub(r'[^\w\s]', ' ', translated_query.lower())
            words = [w for w in clean_query.split() if len(w) > 2]
            
            if not words:
                return []
            
            # Try exact phrase search first
            exact_phrase = ' '.join(words)
            try:
                result = self.supabase.table("chatbot_prompts") \
                    .select("*") \
                    .text_search("search_tsv", exact_phrase) \
                    .execute()
                
                if result.data and len(result.data) > 0:
                    return list(result.data[:3])  # Return top 3 exact matches
            except Exception:
                pass
            
            # Try individual word search
            results = []
            seen_ids = set()
            
            for word in list(words[:3]):  # Only check first 3 words for performance
                try:
                    res = self.supabase.table("chatbot_prompts") \
                        .select("*") \
                        .text_search("search_tsv", word) \
                        .execute()
                    
                    for item in res.data:
                        if item['id'] not in seen_ids:
                            results.append(item)
                            seen_ids.add(item['id'])
                            
                    if len(results) >= 10:  # Get more results for better scoring
                        break
                except Exception:
                    continue
            
            # Score and rank the results to get the most relevant ones
            if results:
                scored = []
                for result in results:
                    score = self._calculate_score(result, query)
                    scored.append((score, result))
                
                # Sort by score and return top results
                scored.sort(reverse=True, key=lambda x: x[0])
                return list([result for score, result in scored if score > 0][:5])
            
            return list(results[:5])  # Return top 5 results
            
        except Exception as e:
            logger.warning(f"Quick exact search failed: {e}")
            return []
    
    def _expand_query_with_synonyms(self, query: str, conversation_history: List[Dict] = None) -> List[str]:
        """Use NLTK WordNet for synonym expansion"""
        try:
            import nltk
            from nltk.corpus import wordnet
            
            variations = [query.lower()]
            words = query.lower().split()
            
            # Get synonyms for each word
            for word in words:
                if len(word) > 2:  # Skip very short words
                    synonyms = set()
                    for syn in wordnet.synsets(word):
                        for lemma in syn.lemmas():
                            synonym = lemma.name().replace('_', ' ')
                            if synonym != word and len(synonym) > 2:
                                synonyms.add(synonym)
                    
                    # Add variations with synonyms (limit to top 1 for performance)
                    if synonyms:
                        synonym = list(synonyms)[0]  # Take the first synonym
                        variation = query.lower().replace(word, synonym)
                        variations.append(variation)
            
            # Remove duplicates
            unique_variations = list(set(variations))
            
            return unique_variations
            
        except Exception as e:
            logger.warning(f"NLTK WordNet synonym expansion failed: {e}")
            return [query.lower()]
    
    def _expand_with_nlu_entities(self, query: str, nlu_result) -> List[str]:
        """Expand query using NLU entity information with NLTK"""
        try:
            import nltk
            from nltk.corpus import wordnet
            
            variations = [query.lower()]
            
            if not nlu_result or not nlu_result.entities:
                return variations
            
            # Use entity types to find domain-specific synonyms
            for entity in nlu_result.entities:
                entity_value = entity.value.lower()
                entity_type = entity.type.lower()
                
                # Get synonyms for entity value
                synonyms = set()
                for syn in wordnet.synsets(entity_value):
                    for lemma in syn.lemmas():
                        synonym = lemma.name().replace('_', ' ')
                        if synonym != entity_value and len(synonym) > 2:
                            synonyms.add(synonym)
                
                # Add variations with synonyms
                if synonyms:
                    synonym = list(synonyms)[0]  # Take the first synonym
                    variation = query.lower().replace(entity_value, synonym)
                    variations.append(variation)
            
            return list(set(variations))
            
        except Exception as e:
            logger.warning(f"NLTK NLU entity expansion failed: {e}")
            return [query.lower()]
    
    def _learn_question_patterns_from_database(self, query: str, keywords: List[str]) -> Dict[str, str]:
        """Learn question patterns from database keywords - no hardcoding"""
        patterns = {}
        
        try:
            # 🚨 SIMPLIFIED: Only learn very basic patterns to avoid over-translation
            # Just handle the most common question words without being too aggressive
            
            # Only learn if we have a clear match and the pattern is simple
            if 'ano' in query and any('what' in kw.lower() for kw in keywords):
                patterns['ano ang'] = 'what is'  # Only replace the full pattern
                
        except Exception as e:
            logger.warning(f"Question pattern learning failed: {e}")
        
        return patterns
    
    def _find_semantic_match(self, word: str, keywords: List[str]) -> str:
        """Find semantic match using database content - no hardcoding"""
        try:
            from difflib import SequenceMatcher
            
            best_match = None
            best_score = 0
            
            # 🚨 FIX: Only match individual words, not entire phrases
            # Extract individual words from all keywords
            all_words = []
            for keyword in keywords:
                all_words.extend(keyword.lower().split())
            
            # Remove duplicates and short words
            unique_words = list(set([w for w in all_words if len(w) > 2]))
            
            # Look for semantic matches in individual words only
            for kw_word in unique_words:
                if len(kw_word) > 2 and len(word) > 2:
                    similarity = SequenceMatcher(None, word.lower(), kw_word).ratio()
                    if similarity > best_score and similarity > 0.7:
                        best_score = similarity
                        best_match = kw_word  # Return just the word, not the entire phrase
            
            return best_match
            
        except Exception as e:
            logger.warning(f"Semantic matching failed: {e}")
            return None
    
    def _get_intelligent_translation(self, query: str) -> str:
        """Use intelligent pattern-based translation - no setup required"""
        try:
            # logger.info(f"🧠 INTELLIGENT TRANSLATION: Analyzing '{query}' for patterns")
            
            # Use intelligent pattern recognition based on common school terms
            # This learns from the query structure without requiring hardcoded dictionaries
            
            # Analyze query structure and extract meaningful terms
            query_lower = query.lower()
            translated = query_lower
            
            # 🚨 DYNAMIC: Learn question patterns from database content
            # No hardcoded patterns - learn from existing database keywords
            try:
                # Get existing keywords to learn question patterns
                result = self.supabase.table("chatbot_prompts") \
                    .select("keywords") \
                    .execute()
                
                if result.data:
                    all_keywords = []
                    for item in result.data:
                        if item.get('keywords'):
                            all_keywords.extend(item['keywords'].split(', '))
                    
                    # Look for question patterns in the database keywords
                    question_patterns = self._learn_question_patterns_from_database(query_lower, all_keywords)
                    if question_patterns:
                        for pattern, replacement in question_patterns.items():
                            translated = translated.replace(pattern, replacement)
                            # logger.info(f"🔧 LEARNED PATTERN: '{pattern}' -> '{replacement}' (from database)")
                            
            except Exception as e:
                logger.warning(f"Question pattern learning failed: {e}")
                # Continue without pattern replacement
            
            # 🚨 DYNAMIC: Learn translations from existing database keywords
            # This avoids hardcoding by using the existing database content
            try:
                # Get existing keywords to learn from
                result = self.supabase.table("chatbot_prompts") \
                    .select("keywords") \
                    .execute()
                
                if result.data:
                    # Extract all keywords and find potential matches
                    all_keywords = []
                    for item in result.data:
                        if item.get('keywords'):
                            all_keywords.extend(item['keywords'].split(', '))
                    
                    # 🚨 SIMPLIFIED: Just clean up particles and let database search handle the rest
                    # The database search is already robust enough to handle mixed languages
                    # logger.info(f"🔧 SIMPLIFIED TRANSLATION: Using particle cleanup only")
                    # Don't try to translate individual words - let the database search handle it
                    
            except Exception as e:
                logger.warning(f"Dynamic content translation failed: {e}")
                # Continue with the query as-is if dynamic translation fails
            
            # Clean up common particles that don't help with English matching
            particles = ['ang', 'ng', 'sa', 'na', 'para', 'in', 'the', 'a', 'an']
            words = translated.split()
            cleaned_words = [word for word in words if word not in particles and len(word) > 1]
            
            result = ' '.join(cleaned_words)
            # logger.info(f"🧠 INTELLIGENT TRANSLATION: '{query}' -> '{result}'")
            return result
            
        except Exception as e:
            logger.warning(f"Intelligent translation failed: {e}")
            return self._get_fallback_translation(query)
    
    def _expand_synonyms(self, query: str) -> str:
        """Dynamically expand synonyms using database content"""
        try:
            # Get all keywords from database to find synonyms
            result = self.supabase.table("chatbot_prompts") \
                .select("keywords") \
                .execute()
            
            if result.data:
                all_keywords = []
                for item in result.data:
                    if item.get('keywords'):
                        all_keywords.extend(item['keywords'].split(', '))
                
                # Find synonyms for words in the query
                expanded_terms = []
                query_words = query.split()
                
                for word in query_words:
                    expanded_terms.append(word)
                    
                    # Find synonyms from database keywords
                    for keyword in all_keywords:
                        if word in keyword.lower() and keyword.lower() != word:
                            # This keyword contains our word - might be a synonym
                            expanded_terms.append(keyword.lower())
                
                # Return expanded query
                return ' '.join(expanded_terms)
            
        except Exception as e:
            logger.warning(f"Synonym expansion error: {e}")
        
        return query
    
    def _get_fallback_translation(self, query: str) -> str:
        """Fallback translation using basic pattern matching"""
        # Basic fallback - just clean up common particles
        particles = ['ang', 'ng', 'sa', 'na', 'para', 'in']
        words = query.split()
        cleaned_words = [word for word in words if word not in particles and len(word) > 1]
        return ' '.join(cleaned_words)
    
    def _enhance_query_with_context(self, query: str, conversation_history: List[Dict] = None) -> str:
        """Enhance query with conversation context to understand references"""
        if not conversation_history:
            return query
        
        # 🚨 CRITICAL FIX: Don't use context for grade-specific queries
        # This prevents mixing up grades from previous conversations
        query_lower = query.lower()
        
        # If current query contains a specific grade, don't use context
        # This prevents "Grade 4" context from affecting "Grade 6" queries
        if re.search(r'grade\s*\d+', query_lower):
            return query
        
        # Look at the MOST RECENT user message for context (not all recent messages)
        # This ensures we use the latest topic, not accumulate all topics
        recent_user_messages = []
        for msg in conversation_history:
            if isinstance(msg, str):
                # Convert string messages to proper format
                recent_user_messages.append({"role": "user", "content": msg})
            elif isinstance(msg, dict) and msg.get("role") == "user":
                recent_user_messages.append(msg)
        
        if not recent_user_messages:
            return query
        
        # Get the most recent user message (excluding the current query)
        # We want the previous message, not the current one
        most_recent_message = recent_user_messages[-2] if len(recent_user_messages) >= 2 else None
        if not most_recent_message:
            return query
            
        content = most_recent_message.get("content", "").lower()
        
        # 🚨 CRITICAL FIX: Don't use context if previous message had a different grade
        # This prevents cross-contamination between grade-specific queries
        prev_grade_match = re.search(r'grade\s*(\d+)', content)
        if prev_grade_match:
            # Previous message had a grade, don't use context to avoid confusion
            return query
        
        # Extract context from the most recent message only
        context_words = []
        
        # Look for teacher/adviser references in the most recent message
        if any(word in content for word in ['adviser', 'advisor', 'teacher', 'guro']):
            context_words.append('adviser')
        
        # Look for staff role references in the most recent message
        staff_roles = ['support aide', 'learning support aide', 'aide', 'principal', 'staff', 'coordinator', 'counselor', 'guidance']
        for role in staff_roles:
            if role in content:
                context_words.append(role)
        
        # Look for specific names mentioned in the most recent message
        name_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', content)
        if name_match:
            name = name_match.group(1)
            if len(name.split()) <= 3:  # Reasonable name length
                context_words.append(name.lower())
        
        # Enhance the query with context from the most recent message
        if context_words:
            enhanced_query = f"{query} {' '.join(context_words)}"
            return enhanced_query
        
        return query
    
    async def search_prompts_three_tier(self, query: str, limit: int = 20, intent: str = None, 
                                      conversation_history: List[Dict] = None,
                                      nlu_result = None) -> List[Dict[str, Any]]:
        """Search using three-tier search strategy"""
        try:
            if not self.use_three_tier or not self.three_tier_search:
                logger.warning("Three-tier search not available, falling back to traditional search")
                return await self.search_prompts(query, limit, intent, True, conversation_history, nlu_result)
            
            logger.info(f"🔍 Using three-tier search for: '{query}'")
            
            # Use three-tier search for single best result
            if limit == 1:
                result = await self.three_tier_search.search(query, limit)
                if result:
                    return [result]
                else:
                    return []
            
            # Use three-tier search for multiple results
            results = await self.three_tier_search.search_multiple(query, limit)
            
            # Convert to expected format
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result.get('id'),
                    'keywords': result.get('keywords', ''),
                    'response': result.get('response', ''),
                    'score': result.get('score', 0),
                    'match_type': result.get('match_type', 'unknown'),
                    'tier': result.get('tier', 0)
                })
            
            logger.info(f"✅ Three-tier search returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Three-tier search failed: {e}")
            # Fallback to traditional search
            return await self.search_prompts(query, limit, intent, True, conversation_history, nlu_result)

    async def search_prompts(self, query: str, limit: int = 20, intent: str = None, 
                        use_semantic: bool = True, conversation_history: List[Dict] = None,
                        nlu_result = None) -> List[Dict[str, Any]]:
        """Smart scoring with NLU-driven synonym expansion"""
        try:
            # 1. Translate query for better database matching
            translated_query = self._translate_query_for_search(query)
            
            # DEBUG: Check for None returns
            logger.info(f"Search debug - translated_query type: {type(translated_query)}, value: {translated_query}")
            if translated_query is None:
                logger.warning("⚠️ translated_query returned None - fixing...")
                translated_query = query
            
            # 2. Enhance query with conversation context
            enhanced_query = self._enhance_query_with_context(translated_query, conversation_history)
            
            # DEBUG: Check for None returns
            logger.info(f"Search debug - enhanced_query type: {type(enhanced_query)}, value: {enhanced_query}")
            if enhanced_query is None:
                logger.warning("⚠️ enhanced_query returned None - fixing...")
                enhanced_query = translated_query
            
            # 2. Check if original query finds exact matches first (performance optimization)
            exact_results = await self._quick_exact_search(enhanced_query)
            
            # DEBUG: Check for None returns
            logger.info(f"Search debug - exact_results type: {type(exact_results)}, value: {exact_results}")
            if exact_results is None:
                logger.warning("⚠️ exact_results returned None - fixing...")
                exact_results = []
            
            if exact_results and len(exact_results) > 0:
                # Check if results contain relevant content for drill queries
                has_relevant_content = any(
                    any(term in str(result.get('keywords', '')).lower() or term in str(result.get('response', '')).lower() 
                        for term in ['drill', 'fire', 'earthquake', 'emergency'])
                    for result in exact_results
                )
                
                query_has_drill_terms = any(term in enhanced_query.lower() for term in ['drill', 'fire', 'earthquake', 'emergency'])
                
                # If query is about drills but results don't contain drill content, continue to full search
                if query_has_drill_terms and not has_relevant_content:
                    logger.info(f"🔍 Found {len(exact_results)} exact matches but no drill content, continuing to full search")
                    
                    # SIMPLIFIED: Direct drill search instead of complex full search
                    try:
                        drill_results = self.supabase.table("chatbot_prompts") \
                            .select("*") \
                            .ilike("keywords", "%drill%") \
                            .execute()
                        
                        if drill_results.data:
                            logger.info(f"Direct drill search found {len(drill_results.data)} results")
                            return drill_results.data[:limit]
                    except Exception as e:
                        logger.warning(f"Direct drill search failed: {e}")
                    
                    # Fallback: return empty list instead of complex search
                    return []
                else:
                    # Found exact matches, skip expensive WordNet expansion
                    logger.info(f"🔍 Found {len(exact_results)} exact matches, skipping WordNet expansion")
                    
                    # Score the exact results and return them
                    scored = []
                    for result in exact_results:
                        score = self._calculate_score(result, enhanced_query)
                        
                        # DEBUG: Check for None scores
                        logger.info(f"Search debug - score type: {type(score)}, value: {score}")
                        if score is None:
                            logger.warning("⚠️ score returned None - fixing...")
                            score = 0.0
                        
                        # Boost based on NLU confidence
                        if nlu_result and nlu_result.confidence > 0.7:
                            score += int(nlu_result.confidence * 20)
                        
                        scored.append((score, result))
                    
                    scored.sort(reverse=True, key=lambda x: x[0])
                    return list([result for score, result in scored if score > 0][:limit])
            else:
                # No exact matches, skip expansion for now to avoid errors
                logger.info(f"Search debug - Skipping expansion, using original query: {enhanced_query}")
                query_variations = [enhanced_query]
                
                # Skip all expansions to avoid errors
                all_variations = [enhanced_query]
                
                # 5. Search with all variations
                results = []
                seen_ids = set()
                
                logger.info(f"Search debug - all_variations: {all_variations}")
                logger.info(f"Search debug - all_variations type: {type(all_variations)}")
                
                # SAFE len() check
                try:
                    variations_length = len(all_variations) if all_variations is not None else 0
                    logger.info(f"Search debug - all_variations length: {variations_length}")
                except Exception as e:
                    logger.error(f"Search debug - ERROR getting length: {e}")
                    logger.error(f"Search debug - all_variations value: {all_variations}")
                    all_variations = [enhanced_query]  # Fallback
                
                # DEBUG: Check each step for None values
                if all_variations is None:
                    logger.error("⚠️ all_variations is None!")
                    all_variations = [enhanced_query]
                
                for variation in all_variations:
                    # DEBUG: Check for None variations
                    logger.info(f"Search debug - variation type: {type(variation)}, value: {variation}")
                    if variation is None:
                        logger.warning("⚠️ variation is None - skipping...")
                        continue
                    
                    clean = re.sub(r'[^\w\s]', ' ', variation.lower())
                    words = [w for w in clean.split() if len(w) > 2]
                    
                    if not words:
                        continue
                
                    # Track failed words for fallback search
                failed_words = []
                
                for word in words:
                        try:
                            # Use text_search on search_tsv column
                            res = self.supabase.table("chatbot_prompts") \
                                .select("*") \
                                .text_search("search_tsv", word) \
                                .execute()
                            
                            for item in res.data:
                                if item['id'] not in seen_ids:
                                    results.append(item)
                                    seen_ids.add(item['id'])
                        except Exception as e:
                            logger.warning(f"Search failed for '{word}': {e}")
                            failed_words.append(word)
                
                # SIMPLIFIED: Direct drill search for drill-related queries
                query_has_drill_terms = any(term in query.lower() for term in ['drill', 'fire', 'earthquake', 'emergency'])
                has_drill_content = any('drill' in str(result.get('keywords', '')).lower() or 'drill' in str(result.get('response', '')).lower() for result in results)
                
                if query_has_drill_terms and not has_drill_content:
                    try:
                        # Direct search for drill-related content
                        res = self.supabase.table("chatbot_prompts") \
                            .select("*") \
                            .ilike("keywords", "%drill%") \
                            .execute()
                        
                        for item in res.data:
                            if item['id'] not in seen_ids:
                                results.append(item)
                                seen_ids.add(item['id'])
                                
                        logger.info(f"Direct drill search found {len(res.data)} results")
                    except Exception as e:
                        logger.warning(f"Direct drill search failed: {e}")
                
                # 6. Score results (boost if NLU intent matches)
                scored = []
                for result in results:
                    score = self._calculate_score(result, enhanced_query)
                    
                    # Boost based on NLU confidence
                    if nlu_result and nlu_result.confidence > 0.7:
                        score += int(nlu_result.confidence * 20)
                    
                    scored.append((score, result))
                
                scored.sort(reverse=True, key=lambda x: x[0])
                results = [result for score, result in scored if score > 0][:limit]
                
                # Validate results to ensure they match query intent
                validated_results = self._validate_search_results(query, results)
                return validated_results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    async def _search_prompts_traditional(self, query: str, limit: int = 20, intent: str = None) -> List[Dict[str, Any]]:
        """Traditional keyword-based search with fuzzy matching"""
        try:
            all_results = []
            
            # Translate query for better matching
            logger.info(f"Search debug - Starting translation for: {query}")
            translated_query = self._translate_query_for_search(query)
            logger.info(f"Search debug - Translation result: {translated_query}")
            logger.info(f"Search debug - Translation type: {type(translated_query)}")
            if translated_query is None:
                logger.warning("Search debug - Translation returned None, using original query")
                translated_query = query
            
            # Clean query for PostgreSQL full-text search
            clean_query = self._clean_query_for_tsquery(translated_query)
            
            # Strategy 1: Full-text search with cleaned query
            if clean_query:
                try:
                    result = self.supabase.table("chatbot_prompts") \
                        .select("keywords, response, search_tsv") \
                        .text_search("search_tsv", clean_query) \
                        .execute()
                    
                    if result.data:
                        all_results.extend(result.data)
                        # logger.info(f"🔍 Found {len(result.data)} formatted search matches")
                except Exception as e:
                    logger.warning(f"Full-text search failed: {e}")
            
            # Strategy 1.5: Dynamic synonym expansion for better matching
            if any(word in query.lower() for word in ['cr', 'comfort', 'banyo', 'toilet', 'restroom']):
                try:
                    # Use dynamic synonym expansion instead of hardcoded patterns
                    expanded_query = self._expand_synonyms(query.lower())
                    if expanded_query != query.lower():
                        # logger.info(f"🔍 SYNONYM EXPANSION: '{query}' -> '{expanded_query}'")
                        # Search with expanded query
                        expanded_result = self.supabase.table("chatbot_prompts") \
                            .select("keywords, response, search_tsv") \
                            .text_search("search_tsv", expanded_query) \
                            .execute()
                        
                        if expanded_result.data:
                            all_results.extend(expanded_result.data)
                            # logger.info(f"🔍 EXPANDED SEARCH: Found {len(expanded_result.data)} additional results")
                except Exception as e:
                    logger.warning(f"Synonym expansion failed: {e}")
                    # Fallback: Try with even more aggressive cleaning
                    try:
                        # Remove all punctuation and special characters
                        ultra_clean = re.sub(r'[^a-zA-Z0-9\s]', '', translated_query)
                        ultra_clean_words = [word for word in ultra_clean.split() if len(word) > 2]
                        if ultra_clean_words:
                            ultra_clean_query = ' & '.join(ultra_clean_words)
                            result = self.supabase.table("chatbot_prompts") \
                                .select("keywords, response, search_tsv") \
                                .text_search("search_tsv", ultra_clean_query) \
                                .execute()
                            
                            if result.data:
                                all_results.extend(result.data)
                                # logger.info(f"🔍 Found {len(result.data)} matches with ultra-clean query")
                    except Exception as e2:
                        logger.warning(f"Ultra-clean search also failed: {e2}")
            
            # Strategy 2: Individual word searches
            words = translated_query.split()
            for word in words:
                if len(word) > 2:  # Skip short words
                    # Clean the word for tsquery - remove all problematic characters
                    clean_word = re.sub(r'[^a-zA-Z0-9]', '', word)
                    if clean_word and len(clean_word) > 1:
                        try:
                            result = self.supabase.table("chatbot_prompts") \
                                .select("keywords, response, search_tsv") \
                                .text_search("search_tsv", clean_word) \
                                .execute()
                            
                            if result.data:
                                all_results.extend(result.data)
                                # logger.info(f"📝 Found {len(result.data)} matches for word '{clean_word}'")
                        except Exception as e:
                            logger.warning(f"Word search failed for '{clean_word}': {e}")
                            # Try even more aggressive cleaning
                            try:
                                ultra_clean_word = re.sub(r'[^a-zA-Z]', '', word)
                                if ultra_clean_word and len(ultra_clean_word) > 1:
                                    result = self.supabase.table("chatbot_prompts") \
                                        .select("keywords, response, search_tsv") \
                                        .text_search("search_tsv", ultra_clean_word) \
                                        .execute()
                                    
                                    if result.data:
                                        all_results.extend(result.data)
                                        # logger.info(f"📝 Found {len(result.data)} matches for ultra-clean word '{ultra_clean_word}'")
                            except Exception as e2:
                                logger.warning(f"Ultra-clean word search also failed for '{ultra_clean_word}': {e2}")
            
            # Strategy 3: Keyword-based search
            try:
                result = self.supabase.table("chatbot_prompts") \
                    .select("keywords, response, search_tsv") \
                    .text_search("search_tsv", translated_query) \
                    .execute()
                
                if result.data:
                    all_results.extend(result.data)
                    # logger.info(f"👨‍🏫 Found {len(result.data)} adviser matches")
            except Exception as e:
                logger.warning(f"Keyword search failed: {e}")
            
            # 🎯 Strategy 4: FUZZY SEARCH - Get ALL entries and let scoring handle it
            # This ensures we don't miss entries due to typos
            try:
                result = self.supabase.table("chatbot_prompts") \
                    .select("keywords, response, search_tsv") \
                    .execute()
                
                if result.data:
                    # Filter to only school-related entries to avoid noise
                    school_related = []
                    for entry in result.data:
                        keywords = (entry.get('keywords') or '').lower()
                        response = (entry.get('response') or '').lower()
                        
                        # Check if entry is school-related
                        school_terms = ['school', 'student', 'teacher', 'grade', 'class', 'activity', 'activities', 
                                       'event', 'program', 'curriculum', 'education', 'learning']
                        
                        if any(term in keywords or term in response for term in school_terms):
                            school_related.append(entry)
                    
                    all_results.extend(school_related)
                    # logger.info(f"🎯 Found {len(school_related)} school-related entries for fuzzy matching")
                    # Debug: Log school activities entries
                    # for entry in school_related[:3]:  # Log first 3 entries
                    #     logger.info(f"🎯 School entry: Keywords='{entry.get('keywords', '')[:50]}...' Response='{entry.get('response', '')[:50]}...'")
                    pass
            except Exception as e:
                logger.warning(f"Fuzzy search failed: {e}")
            
            # Remove duplicates and return
            unique_results = []
            seen = set()
            for result in all_results:
                key = (result.get('keywords', ''), result.get('response', ''))
                if key not in seen:
                    seen.add(key)
                    unique_results.append(result)
            
            # logger.info(f"📊 Total unique results found: {len(unique_results)}")
            return list(unique_results[:limit * 5])  # Return more results for better scoring
            
        except Exception as e:
            logger.warning(f"Database search failed: {e}")
            return []
    
    def _calculate_score(self, result: Dict, query: str) -> int:
        """Use improved, reliable scoring system"""
        return self._improved_scorer.calculate_score(result, query)
