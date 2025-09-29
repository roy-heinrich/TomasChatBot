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
    
    def _translate_query_for_search(self, query: str) -> str:
        """Translate Tagalog query terms to English for database search"""
        # Tagalog to English mapping for common school terms
        tagalog_to_english = {
            # Grade levels
            'ikatlong': 'three', 'ikatatlong': 'three', 'ikatlo': 'three',
            'ikalimang': 'five', 'ikalima': 'five',
            'unang': 'one', 'una': 'one',
            'ikalawang': 'two', 'ikalawa': 'two',
            'ikaapat': 'four', 'ikapat': 'four',
            'ikaanim': 'six', 'ika-anim': 'six',
            'baitang': 'grade',
            
            # Staff roles
            'guro': 'teacher', 'maestro': 'teacher', 'maestra': 'teacher',
            'adviser': 'adviser', 'advisor': 'adviser',
            'principal': 'principal', 'punong guro': 'principal',
            'direktor': 'director',
            
            # Common terms
            'sino': 'who', 'ano': 'what', 'saan': 'where',
            'kailan': 'when', 'bakit': 'why', 'paano': 'how',
            'para sa': 'for', 'ng': 'of', 'sa': 'in'
        }
        
        # Number to word translation for grade searches
        number_to_word = {
            '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six',
            '7': 'seven', '8': 'eight', '9': 'nine', '10': 'ten'
        }
        
        # Question words to remove
        question_words = ['what', 'is', 'are', 'who', 'where', 'when', 'why', 'how', 'which', 'whose']
        
        # Possessive forms to clean
        possessive_patterns = ["'s", "'", "s'"]
        
        # Convert to lowercase for matching
        query_lower = query.lower()
        
        # Clean possessive forms first
        for pattern in possessive_patterns:
            query_lower = query_lower.replace(pattern, '')
        
        # Split query into words and translate each
        words = query_lower.split()
        translated_parts = []
        
        for word in words:
            # Clean word (remove punctuation)
            clean_word = word.strip('.,!?')
            
            # Skip question words
            if clean_word in question_words:
                continue
                
            # Check for number-to-word translation first (for grade searches)
            if clean_word in number_to_word:
                translated_parts.append(number_to_word[clean_word])
            # Check for Tagalog translation
            elif clean_word in tagalog_to_english:
                translated_parts.append(tagalog_to_english[clean_word])
            else:
                translated_parts.append(clean_word)
        
        # Join translated words
        translated_query = ' '.join(translated_parts)
        
        # Special handling for common patterns
        if 'guro para sa' in query_lower:
            # "guro para sa ikatlong baitang" -> "teacher for grade three"
            translated_query = translated_query.replace('guro para sa', 'teacher for')
            translated_query = translated_query.replace('baitang', 'grade')
        
        # Clean up common words that don't help with matching
        words_to_remove = ['ang', 'ng', 'sa', 'para', 'in', 'who', 'what', 'where', 'when', 'why', 'how']
        translated_words = translated_query.split()
        cleaned_words = [word for word in translated_words if word not in words_to_remove]
        translated_query = ' '.join(cleaned_words)
        
        # Log the translation for debugging
        if translated_query != query_lower:
            logger.info(f"🌐 Translated query: '{query}' -> '{translated_query}'")
        
        return translated_query
    
    def search_prompts(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search chatbot prompts using search_tsv column with improved strategy"""
        try:
            all_results = []
            
            # Special handling for grade searches - return only exact matches
            if any(word in query.lower() for word in ['grade', 'adviser', 'teacher']) and len(query.split()) >= 2:
                try:
                    # Translate the query first
                    translated_query = self._translate_query_for_search(query)
                    
                    # Try to find exact grade match first using translated query
                    result = self.supabase.table("chatbot_prompts") \
                        .select("keywords, response, search_tsv") \
                        .ilike("keywords", f"%{translated_query}%") \
                        .execute()
                    
                    if result.data:
                        # Filter for exact grade matches only
                        exact_grade_matches = []
                        for item in result.data:
                            keywords = item.get('keywords', '').lower()
                            # Check if this is an exact grade match
                            if any(grade_pattern in keywords for grade_pattern in [
                                'grade one', 'grade two', 'grade three', 'grade four', 'grade five', 'grade six'
                            ]):
                                exact_grade_matches.append(item)
                        
                        if exact_grade_matches:
                            logger.info(f"🎯 Found {len(exact_grade_matches)} exact grade matches")
                            return exact_grade_matches[:limit]
                        
                except Exception as e:
                    logger.warning(f"Exact grade search failed: {e}")
            
            # Continue with regular search strategies if no exact grade match found
            
            # Strategy 1: Try exact keyword match first (highest priority)
            try:
                result = self.supabase.table("chatbot_prompts") \
                    .select("keywords, response, search_tsv") \
                    .ilike("keywords", f"%{query}%") \
                    .execute()
                
                if result.data:
                    # For grade searches, prioritize exact matches
                    if any(word in query.lower() for word in ['grade', 'adviser', 'teacher']):
                        # Only add exact grade matches
                        exact_matches = []
                        for item in result.data:
                            keywords = item.get('keywords', '').lower()
                            if any(grade_word in keywords for grade_word in ['grade one', 'grade two', 'grade three', 'grade four', 'grade five', 'grade six']):
                                exact_matches.append(item)
                        
                        if exact_matches:
                            all_results.extend(exact_matches)
                            logger.info(f"🎯 Found {len(exact_matches)} exact grade matches")
                        else:
                            all_results.extend(result.data)
                            logger.info(f"🎯 Found {len(result.data)} exact keyword matches")
                    else:
                        all_results.extend(result.data)
                        logger.info(f"🎯 Found {len(result.data)} exact keyword matches")
            except Exception as e:
                logger.warning(f"Exact keyword search failed: {e}")
            
            # Strategy 1.1: Try searching in response field (for names and specific answers)
            try:
                result = self.supabase.table("chatbot_prompts") \
                    .select("keywords, response, search_tsv") \
                    .ilike("response", f"%{query}%") \
                    .execute()
                
                if result.data:
                    # Add results that aren't already in all_results
                    for item in result.data:
                        if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                            all_results.append(item)
                    logger.info(f"🎯 Found {len(result.data)} response field matches")
            except Exception as e:
                logger.warning(f"Response field search failed: {e}")
            
            # Strategy 1.1.1: Try partial name matching in response field (for "Jessica Go" vs "Ms. Jessica Z. Go")
            if len(query.split()) >= 2:  # Only for multi-word queries
                try:
                    # Split query into words (include words of 2+ characters for names like "Go")
                    query_words = [word.strip('.,!?') for word in query.split() if len(word) >= 2]
                    if len(query_words) >= 2:
                        # Search for results that contain the first word
                        first_word = query_words[0]
                        result = self.supabase.table("chatbot_prompts") \
                            .select("keywords, response, search_tsv") \
                            .ilike("response", f"%{first_word}%") \
                            .execute()
                        
                        if result.data:
                            # Filter to only include results with ALL words
                            filtered_results = []
                            for item in result.data:
                                response_text = item.get('response', '').lower()
                                if all(qword.lower() in response_text for qword in query_words):
                                    if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                        filtered_results.append(item)
                            
                            if filtered_results:
                                all_results.extend(filtered_results)
                                logger.info(f"🎯 Found {len(filtered_results)} partial name matches")
                                
                except Exception as e:
                    logger.warning(f"Partial name search failed: {e}")
            
            # Strategy 1.1.2: Try fuzzy matching for complex queries (like "ms jessica go advisory")
            if len(query.split()) >= 3:  # For complex queries
                try:
                    # Extract potential name parts and role parts
                    query_words = [word.strip('.,!?') for word in query.split() if len(word) >= 2]
                    
                    # Look for name patterns (2+ consecutive words that could be names)
                    name_candidates = []
                    for i in range(len(query_words) - 1):
                        if len(query_words[i]) >= 2 and len(query_words[i+1]) >= 2:
                            name_candidates.append(f"{query_words[i]} {query_words[i+1]}")
                    
                    # Search for each name candidate
                    for name_candidate in name_candidates:
                        # Try exact match first
                        result = self.supabase.table("chatbot_prompts") \
                            .select("keywords, response, search_tsv") \
                            .ilike("response", f"%{name_candidate}%") \
                            .execute()
                        
                        # If no exact match, try middle initial tolerant search
                        if not result.data and len(name_candidate.split()) == 2:
                            first_name, last_name = name_candidate.split()
                            
                            # Search for pattern: "first_name [middle_initial] last_name"
                            # This will match "jessica go" against "jessica z. go"
                            middle_initial_pattern = f"{first_name}%{last_name}"
                            
                            result = self.supabase.table("chatbot_prompts") \
                                .select("keywords, response, search_tsv") \
                                .ilike("response", f"%{middle_initial_pattern}%") \
                                .execute()
                        
                        if result.data:
                            # Add results that aren't already in all_results
                            new_results = []
                            for item in result.data:
                                if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                    all_results.append(item)
                                    new_results.append(item)
                            
                            if new_results:
                                logger.info(f"🎯 Found {len(new_results)} fuzzy name matches for '{name_candidate}'")
                                break  # Stop after first successful match
                                
                except Exception as e:
                    logger.warning(f"Fuzzy name search failed: {e}")
            
            # Strategy 1.2: Try fuzzy name matching (for partial names like "Jessica Go" vs "Ms. Jessica Z. Go")
            if any(word in query.lower() for word in ['jessica', 'go', 'ms', 'mrs', 'mr', 'dr']):
                try:
                    # Extract potential name parts (only meaningful words)
                    name_parts = [word.strip('.,!?') for word in query.split() if len(word) > 2 and word.lower() not in ['the', 'and', 'or', 'for', 'with', 'who', 'what', 'where', 'when', 'why', 'how']]
                    
                    # Only proceed if we have at least 2 meaningful parts (like "Jessica Go")
                    if len(name_parts) >= 2:
                        # Check if we already have accurate results
                        has_accurate_match = any(
                            all(part.lower() in item.get('response', '').lower() for part in name_parts)
                            for item in all_results
                        )
                        
                        # If no accurate match yet, try new search
                        if not has_accurate_match:
                            # Search for results that contain the first meaningful part
                            first_part = name_parts[0]
                            result = self.supabase.table("chatbot_prompts") \
                                .select("keywords, response, search_tsv") \
                                .ilike("response", f"%{first_part}%") \
                                .execute()
                            
                            if result.data:
                                # Filter results to only include those with ALL name parts
                                filtered_results = []
                                for item in result.data:
                                    response_text = item.get('response', '').lower()
                                    if all(part.lower() in response_text for part in name_parts):
                                        if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                            filtered_results.append(item)
                                
                                if filtered_results:
                                    all_results.extend(filtered_results)
                                    logger.info(f"🎯 Found {len(filtered_results)} accurate fuzzy name matches")
                            
                except Exception as e:
                    logger.warning(f"Fuzzy name search failed: {e}")
            
            # Strategy 1.5: Try translated query for Tagalog/English mismatch
            translated_query = self._translate_query_for_search(query)
            if translated_query and translated_query != query:
                try:
                    result = self.supabase.table("chatbot_prompts") \
                        .select("keywords, response, search_tsv") \
                        .ilike("keywords", f"%{translated_query}%") \
                        .execute()
                    
                    if result.data:
                        for item in result.data:
                            if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                all_results.append(item)
                        logger.info(f"🌐 Found {len(result.data)} translated query matches for '{translated_query}'")
                except Exception as e:
                    logger.warning(f"Translated query search failed: {e}")
            
            # Strategy 1.6: Try specific grade + teacher pattern matching
            if 'teacher' in translated_query and any(grade in translated_query for grade in ['three', '3', 'third']):
                try:
                    # Search for "Grade three" or "Grade 3" patterns
                    grade_patterns = ['Grade three', 'Grade 3', 'grade three', 'grade 3', 'three grade', '3rd grade']
                    for pattern in grade_patterns:
                        result = self.supabase.table("chatbot_prompts") \
                            .select("keywords, response, search_tsv") \
                            .ilike("keywords", f"%{pattern}%") \
                            .execute()
                        
                        if result.data:
                            for item in result.data:
                                if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                    all_results.append(item)
                            logger.info(f"🎯 Found {len(result.data)} grade pattern matches for '{pattern}'")
                            break  # Stop after first successful match
                except Exception as e:
                    logger.warning(f"Grade pattern search failed: {e}")
            
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
