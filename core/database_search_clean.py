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
        # Define score weights (all reasonable values)
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
            'staff': ['who', 'sino', 'teacher', 'adviser', 'principal', 'staff', 'guro'],
            'schedule': ['hours', 'schedule', 'time', 'when', 'start', 'end'],
            'location': ['where', 'saan', 'location', 'find'],
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
        
        # 1. Exact match (highest priority)
        if clean_query == keywords_lower or query_lower == keywords_lower:
            score += self.weights['exact_match']
        
        # 2. Keyword containment
        if clean_query in keywords_lower or query_lower in keywords_lower:
            score += self.weights['keyword_match']
        
        # 3. Word overlap scoring
        query_words = self._get_important_words(clean_query)
        keyword_words = set(keywords_lower.split())
        response_words = set(response_lower.split())
        
        keyword_overlap = len(query_words & keyword_words)
        response_overlap = len(query_words & response_words)
        
        score += keyword_overlap * self.weights['word_overlap']
        score += response_overlap * self.weights['response_match']
        
        # 4. Length bonus (concise answers preferred)
        if len(result.get('response', '')) < 150:
            score += self.weights['length_bonus']
        
        # 5. Semantic similarity (simple fuzzy match)
        similarity = SequenceMatcher(None, clean_query, keywords_lower).ratio()
        score += int(similarity * self.weights['semantic_similarity'])
        
        # 6. Intent matching
        query_intent = self._detect_intent(query_lower)
        content_intent = self._detect_intent(keywords_lower + ' ' + response_lower)
        
        if query_intent and query_intent == content_intent:
            score += self.weights['intent_match']
        
        # 7. Grade-specific matching
        score += self._score_grade_match(query_lower, keywords_lower, response_lower)
        
        # 7.5. Kindergarten fuzzy matching
        if 'kinder' in query_lower and 'kindergarten' in keywords_lower:
            score += 20  # Boost for kinder -> kindergarten match
        elif 'kindergarten' in query_lower and 'kinder' in keywords_lower:
            score += 20  # Boost for kindergarten -> kinder match
        
        # 8. Penalties
        score -= self._calculate_penalties(result)
        
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
    """Clean database search engine with reliable scoring"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self._improved_scorer = ImprovedScorer()
    
    def _clean_query_for_tsquery(self, query: str) -> str:
        """Clean query for PostgreSQL tsquery syntax to avoid syntax errors"""
        # Remove problematic characters that cause tsquery syntax errors
        cleaned = query.strip()
        
        # Remove punctuation that causes issues
        cleaned = re.sub(r'[!@#$%^&*()_+=\[\]{}|;:"<>?/~`]', '', cleaned)
        
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
                    .or_("keywords.ilike.%grade level%,keywords.ilike.%grade%,keywords.ilike.%kindergarten%") \
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
        query_lower = query.lower()
        translated_query = query_lower
        
        # Common Tagalog to English translations
        translations = {
            'sino': 'who',
            'ano': 'what', 
            'saan': 'where',
            'kailan': 'when',
            'bakit': 'why',
            'paano': 'how',
            'guro': 'teacher',
            'adviser': 'adviser',
            'prinsipal': 'principal',
            'baitang': 'grade',
            'klase': 'class',
            'paaralan': 'school',
            'oras': 'time',
            'schedule': 'schedule'
        }
        
        # Apply translations
        for tagalog, english in translations.items():
            translated_query = translated_query.replace(tagalog, english)
        
        # Handle specific patterns
        if 'guro para sa' in query_lower:
            # "guro para sa ikatlong baitang" -> "teacher for grade three"
            translated_query = translated_query.replace('guro para sa', 'teacher for')
            translated_query = translated_query.replace('baitang', 'grade')
        
        # Clean up common words that don't help with matching
        words_to_remove = ['ang', 'ng', 'sa', 'para', 'in', 'who', 'what', 'where', 'when', 'why', 'how', 'kayo', 'kayO']
        translated_words = translated_query.split()
        cleaned_words = [word for word in translated_words if word not in words_to_remove]
        translated_query = ' '.join(cleaned_words)
        
        # Special handling for "may prinsipal" queries
        if 'have principal' in translated_query or 'principal' in translated_query:
            # For principal queries, just search for "principal"
            translated_query = 'principal'
        
        # Log the translation for debugging
        if translated_query != query_lower:
            return translated_query
        
        return query_lower
    
    async def search_prompts(self, query: str, limit: int = 20, intent: str = None, use_semantic: bool = True) -> List[Dict[str, Any]]:
        """Search chatbot prompts with reliable scoring"""
        
        # 🎯 CRITICAL: Check grade level validation FIRST before any database search
        grade_validation = self._validate_grade_level(query)
        if not grade_validation['is_valid']:
            # Return a special result for invalid grades - NO DATABASE SEARCH
            logger.info(f"🚫 Grade validation failed: {grade_validation['message']}")
            return [{
                'keywords': f"Grade {grade_validation['grade']} not available",
                'response': grade_validation['message'],
                'search_tsv': f"grade {grade_validation['grade']} not available",
                'is_grade_validation': True
            }]
        
        # Get candidates using traditional keyword search
        candidates = await self._search_prompts_traditional(query, limit * 2, intent)
        
        if not candidates:
            return []
        
        # Apply scoring and sorting to ensure best results are first
        scored_results = []
        for result in candidates:
            score = self._calculate_score(result, query)
            scored_results.append((score, result))
        
        # Sort by score (highest first)
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Return the top results
        top_results = [result for score, result in scored_results[:limit]]
        
        return top_results
    
    async def _search_prompts_traditional(self, query: str, limit: int = 20, intent: str = None) -> List[Dict[str, Any]]:
        """Traditional keyword-based search"""
        try:
            all_results = []
            
            # Translate query for better matching
            translated_query = self._translate_query_for_search(query)
            
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
                        logger.info(f"🔍 Found {len(result.data)} formatted search matches")
                except Exception as e:
                    logger.warning(f"Full-text search failed: {e}")
            
            # Strategy 2: Individual word searches
            words = translated_query.split()
            for word in words:
                if len(word) > 2:  # Skip short words
                    try:
                        result = self.supabase.table("chatbot_prompts") \
                            .select("keywords, response, search_tsv") \
                            .text_search("search_tsv", word) \
                            .execute()
                        
                        if result.data:
                            all_results.extend(result.data)
                            logger.info(f"📝 Found {len(result.data)} matches for word '{word}'")
                    except Exception as e:
                        logger.warning(f"Word search failed for '{word}': {e}")
            
            # Strategy 3: Keyword-based search
            try:
                result = self.supabase.table("chatbot_prompts") \
                    .select("keywords, response, search_tsv") \
                    .ilike("keywords", f"%{translated_query}%") \
                    .execute()
                
                if result.data:
                    all_results.extend(result.data)
                    logger.info(f"👨‍🏫 Found {len(result.data)} adviser matches")
            except Exception as e:
                logger.warning(f"Keyword search failed: {e}")
            
            # Remove duplicates and return
            unique_results = []
            seen = set()
            for result in all_results:
                key = (result.get('keywords', ''), result.get('response', ''))
                if key not in seen:
                    seen.add(key)
                    unique_results.append(result)
            
            logger.info(f"📊 Total unique results found: {len(unique_results)}")
            return unique_results[:limit]
            
        except Exception as e:
            logger.warning(f"Database search failed: {e}")
            return []
    
    def _calculate_score(self, result: Dict, query: str) -> int:
        """Use improved, reliable scoring system"""
        return self._improved_scorer.calculate_score(result, query)
