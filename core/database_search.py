"""
Database Search Module - Fixed and Optimized
Handles all database search operations with proper result selection
"""
import logging
from typing import List, Dict, Optional, Any
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class DatabaseSearchEngine:
    """Optimized database search engine with proper result ranking"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
    
    def search_prompts(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search chatbot prompts using search_tsv column with improved strategy"""
        try:
            all_results = []
            
            # Strategy 1: Try exact keyword match first (highest priority)
            try:
                result = self.supabase.table("chatbot_prompts") \
                    .select("keywords, response, search_tsv") \
                    .ilike("keywords", f"%{query}%") \
                    .execute()
                
                if result.data:
                    all_results.extend(result.data)
                    logger.info(f"🎯 Found {len(result.data)} exact keyword matches")
            except Exception as e:
                logger.warning(f"Exact keyword search failed: {e}")
            
            # Strategy 2: Try formatted full-text search
            formatted_query = query.replace(' ', ' & ')
            try:
                result = self.supabase.table("chatbot_prompts") \
                    .select("keywords, response, search_tsv") \
                    .text_search('search_tsv', formatted_query) \
                    .execute()
                
                if result.data:
                    # Add results that aren't already in all_results
                    for item in result.data:
                        if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                            all_results.append(item)
                    logger.info(f"🔍 Found {len(result.data)} formatted search matches")
            except Exception as e:
                logger.warning(f"Formatted search failed: {e}")
            
            # Strategy 3: Try individual important words (skip common words)
            important_words = []
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'who', 'what', 'where', 'when', 'why', 'how'}
            
            words = query.split()
            for word in words:
                if len(word) > 2 and word.lower() not in common_words:
                    important_words.append(word)
            
            for word in important_words:
                try:
                    result = self.supabase.table("chatbot_prompts") \
                        .select("keywords, response, search_tsv") \
                        .text_search('search_tsv', word) \
                        .execute()
                    
                    if result.data:
                        # Add results that aren't already in all_results
                        for item in result.data:
                            if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                all_results.append(item)
                        logger.info(f"📝 Found {len(result.data)} matches for word '{word}'")
                except Exception as e:
                    logger.warning(f"Word search failed for '{word}': {e}")
            
            # Strategy 4: Try partial keyword matches for specific terms
            if 'adviser' in query.lower() or 'teacher' in query.lower():
                try:
                    result = self.supabase.table("chatbot_prompts") \
                        .select("keywords, response, search_tsv") \
                        .ilike("keywords", "%adviser%") \
                        .execute()
                    
                    if result.data:
                        for item in result.data:
                            if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                all_results.append(item)
                        logger.info(f"👨‍🏫 Found {len(result.data)} adviser matches")
                except Exception as e:
                    logger.warning(f"Adviser search failed: {e}")
            
            # Strategy 5: Extract core terms and handle numeric vs spelled-out numbers
            import re
            
            # Define number mapping first
            number_mapping = {
                '1': 'one', '2': 'two', '3': 'three', '4': 'four', 
                '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
            }
            
            # Extract core terms by removing question words and punctuation
            core_query = re.sub(r'^(who|what|where|when|why|how|sino|ano|saan|kailan|bakit|paano)\s+is\s+the\s+', '', query.lower())
            core_query = re.sub(r'\?$', '', core_query)
            core_query = core_query.strip()
            
            # Search for core terms
            if core_query and core_query != query.lower():
                try:
                    result = self.supabase.table("chatbot_prompts") \
                        .select("keywords, response, search_tsv") \
                        .ilike("keywords", f"%{core_query}%") \
                        .execute()
                    
                    if result.data:
                        for item in result.data:
                            if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                all_results.append(item)
                        logger.info(f"🎯 Found {len(result.data)} matches for core terms '{core_query}'")
                except Exception as e:
                    logger.warning(f"Core terms search failed for '{core_query}': {e}")
                
                # Also search for core terms with numbers converted to words
                alt_core_query = core_query
                for num, word in number_mapping.items():
                    if num in alt_core_query:
                        alt_core_query = alt_core_query.replace(num, word)
                
                if alt_core_query != core_query:
                    try:
                        result = self.supabase.table("chatbot_prompts") \
                            .select("keywords, response, search_tsv") \
                            .ilike("keywords", f"%{alt_core_query}%") \
                            .execute()
                        
                        if result.data:
                            for item in result.data:
                                logger.info(f"🎯 Checking result: '{item['keywords']}' -> '{item['response']}'")
                                if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                    all_results.append(item)
                                    logger.info(f"🎯 Added result: '{item['keywords']}' -> '{item['response']}'")
                                else:
                                    logger.info(f"🎯 Result already exists: '{item['keywords']}'")
                            logger.info(f"🎯 Found {len(result.data)} matches for converted core terms '{alt_core_query}'")
                    except Exception as e:
                        logger.warning(f"Converted core terms search failed for '{alt_core_query}': {e}")
                
                # Also search for the original query with numbers converted to words
                alt_query = query.lower()
                for num, word in number_mapping.items():
                    if num in alt_query:
                        alt_query = alt_query.replace(num, word)
                
                if alt_query != query.lower():
                    try:
                        result = self.supabase.table("chatbot_prompts") \
                            .select("keywords, response, search_tsv") \
                            .ilike("keywords", f"%{alt_query}%") \
                            .execute()
                        
                        if result.data:
                            for item in result.data:
                                if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                    all_results.append(item)
                            logger.info(f"🎯 Found {len(result.data)} matches for converted query '{alt_query}'")
                    except Exception as e:
                        logger.warning(f"Converted query search failed for '{alt_query}': {e}")
            
            # Handle numeric vs spelled-out numbers for both original and core query
            
            queries_to_process = [query, core_query] if core_query != query.lower() else [query]
            
            for current_query in queries_to_process:
                if not current_query:
                    continue
                    
                # If query contains a number, also search for the spelled-out version
                for num, word in number_mapping.items():
                    if num in current_query:
                        # Replace number with spelled-out word
                        alt_query = current_query.replace(num, word)
                        try:
                            result = self.supabase.table("chatbot_prompts") \
                                .select("keywords, response, search_tsv") \
                                .ilike("keywords", f"%{alt_query}%") \
                                .execute()
                            
                            if result.data:
                                for item in result.data:
                                    if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                        all_results.append(item)
                                logger.info(f"🔢 Found {len(result.data)} matches for spelled-out number '{alt_query}'")
                        except Exception as e:
                            logger.warning(f"Spelled-out number search failed for '{alt_query}': {e}")
                    
                    # Also try the reverse - if query has spelled-out word, search for number
                    if word in current_query.lower():
                        alt_query = current_query.lower().replace(word, num)
                        try:
                            result = self.supabase.table("chatbot_prompts") \
                                .select("keywords, response, search_tsv") \
                                .ilike("keywords", f"%{alt_query}%") \
                                .execute()
                            
                            if result.data:
                                for item in result.data:
                                    if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                        all_results.append(item)
                                logger.info(f"🔢 Found {len(result.data)} matches for numeric version '{alt_query}'")
                        except Exception as e:
                            logger.warning(f"Numeric search failed for '{alt_query}': {e}")
            
            # Remove duplicates and return
            unique_results = []
            seen_keywords = set()
            for result in all_results:
                if result['keywords'] not in seen_keywords:
                    unique_results.append(result)
                    seen_keywords.add(result['keywords'])
            
            logger.info(f"📊 Total unique results found: {len(unique_results)}")
            
            # Sort results by relevance before limiting
            # This ensures that the most relevant results are returned
            if unique_results:
                # Use the scoring algorithm to sort results
                scored_results = []
                for result in unique_results:
                    score = self._calculate_score(result, query)
                    scored_results.append((score, result))
                
                # Sort by score (highest first)
                scored_results.sort(key=lambda x: x[0], reverse=True)
                
                # Return the top results
                top_results = [result for score, result in scored_results[:limit]]
                logger.info(f"🏆 Returning top {len(top_results)} results sorted by relevance")
                return top_results
            
            return unique_results[:limit]
            
        except Exception as e:
            logger.warning(f"Database search failed: {e}")
            return []
    
    def _calculate_score(self, result: Dict, query: str) -> int:
        """Calculate score for a single result (used for sorting) - same logic as select_best_result"""
        import re
        
        score = 0
        query_lower = query.lower()
        keywords_lower = result['keywords'].lower()
        response_lower = result['response'].lower()
        
        # Extract important words from query
        important_query_words = [word for word in query_lower.split() 
                               if word not in ['who', 'what', 'where', 'when', 'why', 'how', 'is', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'sino', 'ano', 'saan', 'kailan', 'bakit', 'paano', 'ang', 'ng', 'sa', 'ay', 'ko', 'mo', 'niya', 'namin', 'ninyo', 'nila']]
        
        # 1. Exact keyword match (highest priority)
        if query_lower == keywords_lower:
            score += 200
        elif query_lower in keywords_lower:
            score += 150
        
        # 1.1. Semantic relevance boost - prioritize results that match the intent
        # If user asks "where can i find", prioritize results with "where is" or "location"
        if 'where' in query_lower and 'find' in query_lower:
            if 'where' in keywords_lower and ('is' in keywords_lower or 'location' in keywords_lower):
                score += 200  # Very high boost for semantic match
        elif 'how can i contact' in query_lower:
            if 'contact' in keywords_lower or 'reach' in keywords_lower:
                score += 200  # Very high boost for semantic match
        elif 'what is' in query_lower or 'what are' in query_lower:
            if 'what' in keywords_lower:
                score += 200  # Very high boost for semantic match
        
        # 1.5. Exact phrase matching for specific queries
        clean_query = re.sub(r'^(who|what|where|when|why|how|sino|ano|saan|kailan|bakit|paano)\s+is\s+the\s+', '', query_lower)
        clean_query = re.sub(r'\?$', '', clean_query)
        if clean_query == keywords_lower:
            score += 180
        elif clean_query in keywords_lower:
            score += 120
        
        # 1.6. Handle numeric to word conversion for better matching
        number_to_word = {
            '1': 'one', '2': 'two', '3': 'three', '4': 'four', 
            '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
        }
        
        alt_clean_query = clean_query
        for num, word in number_to_word.items():
            if num in alt_clean_query:
                alt_clean_query = alt_clean_query.replace(num, word)
        
        if alt_clean_query != clean_query:
            if alt_clean_query == keywords_lower:
                score += 2000  # Very high score for exact match with converted numbers
            elif alt_clean_query in keywords_lower:
                score += 1000  # High score for partial match with converted numbers
        
        # 1.7. Also check the reverse - if database has numbers, convert to words and match
        alt_keywords = keywords_lower
        for num, word in number_to_word.items():
            if num in alt_keywords:
                alt_keywords = alt_keywords.replace(num, word)
        
        if alt_keywords != keywords_lower:
            if clean_query == alt_keywords:
                score += 2000  # Very high score for exact match with converted database keywords
            elif clean_query in alt_keywords:
                score += 1000  # High score for partial match with converted database keywords
        
        # 2. Partial keyword match (very high priority)
        if any(word in keywords_lower for word in important_query_words):
            score += 100
        
        # 3. Adviser/teacher specific scoring
        if ('adviser' in query_lower or 'teacher' in query_lower) and ('adviser' in keywords_lower or 'teacher' in keywords_lower):
            score += 80
        
        # 4. Grade specific scoring
        if 'grade' in query_lower and 'grade' in keywords_lower:
            score += 60
        
        # 5. Word overlap scoring
        query_words = set(query_lower.split())
        keyword_words = set(keywords_lower.split())
        word_overlap = len(query_words.intersection(keyword_words))
        if word_overlap > 0:
            score += word_overlap * 20
        
        # 6. Response overlap scoring
        response_words = set(response_lower.split())
        response_overlap = len(query_words.intersection(response_words))
        if response_overlap > 0:
            score += response_overlap * 10
        
        # 7. Direct, concise answers get bonus
        if len(result['response']) < 100:
            score += 30
        
        # 8. Staff/adviser queries get bonus if not generic
        if any(word in query_lower for word in ['who', 'sino', 'adviser', 'teacher', 'principal']):
            if not any(phrase in response_lower for phrase in ['you must be looking', 'grade levels are offered']):
                score += 40
        
        # 9. Grade number matching
        grade_match = re.search(r'grade\s*(\d+)', query_lower)
        if grade_match:
            grade_num = grade_match.group(1)
            if grade_num in keywords_lower:
                score += 60
                if f"grade {grade_num}" in keywords_lower or f"grade{grade_num}" in keywords_lower:
                    score += 100
        
        # 10. Spelled-out grade matching
        grade_word_match = re.search(r'grade\s*(one|two|three|four|five|six|seven|eight|nine)', query_lower)
        if grade_word_match:
            grade_word = grade_word_match.group(1)
            if grade_word in keywords_lower:
                score += 60
                if f"grade {grade_word}" in keywords_lower:
                    score += 100
        
        # Penalties
        if any(phrase in response_lower for phrase in ['you must be looking', 'grade levels are offered']):
            score -= 50
        
        if len(result['response']) > 500:
            score -= 10
        
        return score
    
    def select_best_result(self, results: List[Dict], query: str) -> Optional[Dict[str, Any]]:
        """Select the best search result with improved scoring"""
        import re
        
        if not results:
            return None
        
        if len(results) == 1:
            return results[0]
        
        # Enhanced scoring system
        scored_results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Remove common words from query for better matching
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'who', 'what', 'where', 'when', 'why', 'how'}
        important_query_words = {word for word in query_words if word not in common_words}
        
        for result in results:
            score = 0
            keywords_lower = result['keywords'].lower()
            response_lower = result['response'].lower()
            
            # 1. Exact keyword match (highest priority)
            if query_lower == keywords_lower:
                score += 200
            elif query_lower in keywords_lower:
                score += 150
            
            # 1.1. Semantic relevance boost - prioritize results that match the intent
            # If user asks "where can i find", prioritize results with "where is" or "location"
            if 'where' in query_lower and 'find' in query_lower:
                if 'where' in keywords_lower and ('is' in keywords_lower or 'location' in keywords_lower):
                    score += 200  # Very high boost for semantic match
            elif 'how can i contact' in query_lower:
                if 'contact' in keywords_lower or 'reach' in keywords_lower:
                    score += 200  # Very high boost for semantic match
            elif 'what is' in query_lower or 'what are' in query_lower:
                if 'what' in keywords_lower:
                    score += 200  # Very high boost for semantic match
            
            # 1.5. Exact phrase matching for specific queries
            # Remove question words and punctuation for better matching
            clean_query = re.sub(r'^(who|what|where|when|why|how|sino|ano|saan|kailan|bakit|paano)\s+is\s+the\s+', '', query_lower)
            clean_query = re.sub(r'\?$', '', clean_query)
            if clean_query == keywords_lower:
                score += 180
            elif clean_query in keywords_lower:
                score += 120
            
            # 1.6. Handle numeric to word conversion for better matching
            # Convert numbers to words in clean_query and check for matches
            number_to_word = {
                '1': 'one', '2': 'two', '3': 'three', '4': 'four', 
                '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
            }
            
            # Create alternative queries with numbers converted to words
            alt_clean_query = clean_query
            for num, word in number_to_word.items():
                if num in alt_clean_query:
                    alt_clean_query = alt_clean_query.replace(num, word)
            
            # Check if the alternative query matches
            if alt_clean_query != clean_query:
                if alt_clean_query == keywords_lower:
                    score += 2000  # Very high score for exact match with converted numbers
                elif alt_clean_query in keywords_lower:
                    score += 1000  # High score for partial match with converted numbers
            
            # 1.7. Also check the reverse - if database has numbers, convert to words and match
            # This handles cases where database has "Grade 6" but query has "Grade six"
            alt_keywords = keywords_lower
            for num, word in number_to_word.items():
                if num in alt_keywords:
                    alt_keywords = alt_keywords.replace(num, word)
            
            if alt_keywords != keywords_lower:
                if clean_query == alt_keywords:
                    score += 2000  # Very high score for exact match with converted database keywords
                elif clean_query in alt_keywords:
                    score += 1000  # High score for partial match with converted database keywords
            
            # 2. Partial keyword match (very high priority)
            if any(word in keywords_lower for word in important_query_words):
                score += 100
            
            # 3. Exact phrase matching for specific terms
            if 'adviser' in query_lower and 'adviser' in keywords_lower:
                score += 80
            if 'teacher' in query_lower and 'teacher' in keywords_lower:
                score += 80
            if 'grade' in query_lower and 'grade' in keywords_lower:
                score += 60
            
            # 4. Word overlap scoring (only for important words)
            keyword_words = set(keywords_lower.split())
            word_overlap = len(important_query_words & keyword_words)
            score += word_overlap * 20
            
            # 5. Response content relevance
            response_words = set(response_lower.split())
            response_overlap = len(important_query_words & response_words)
            score += response_overlap * 10
            
            # 6. Penalize generic responses heavily
            generic_phrases = [
                "you must be looking", "i'm happy to help", "let me help",
                "visit the school office", "contact the school office",
                "grade levels are offered", "grading system", "sections are there"
            ]
            if any(phrase in response_lower for phrase in generic_phrases):
                score -= 50
            
            # 7. Boost for direct, specific answers
            if len(result['response']) < 100 and not any(generic in response_lower for generic in ["visit", "contact", "office"]):
                score += 30
            elif len(result['response']) > 500:
                score -= 10
            
            # 8. Special boost for staff/adviser queries
            if any(word in query_lower for word in ["who", "sino", "adviser", "teacher", "principal"]):
                if not any(generic in response_lower for generic in ["visit", "contact", "office", "grade levels", "grading system"]):
                    score += 40
            
            # 9. Boost for exact grade matches (both numeric and spelled-out)
            grade_match = re.search(r'grade\s+(\d+)', query_lower)
            if grade_match:
                grade_num = grade_match.group(1)
                # Map numbers to words
                number_to_word = {
                    '1': 'one', '2': 'two', '3': 'three', '4': 'four', 
                    '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
                }
                grade_word = number_to_word.get(grade_num, '')
                
                if grade_num in keywords_lower:
                    score += 60
                    # Extra boost for exact grade number match
                    if f"grade {grade_num}" in keywords_lower or f"grade{grade_num}" in keywords_lower:
                        score += 100
                
                # Also check for spelled-out version
                if grade_word and grade_word in keywords_lower:
                    score += 60
                    if f"grade {grade_word}" in keywords_lower:
                        score += 100
            
            scored_results.append((score, result))
        
        # Sort by score and return the best
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Log top 3 results for debugging
        logger.info(f"🔍 Top results for '{query}':")
        for i, (score, result) in enumerate(scored_results[:3]):
            logger.info(f"   {i+1}. Score: {score} - {result['keywords']}")
        
        return scored_results[0][1] if scored_results else None
