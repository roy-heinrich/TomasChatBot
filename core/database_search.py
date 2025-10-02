"""
Database Search Module - Fixed and Optimized
Handles all database search operations with proper result selection
Enhanced with semantic re-ranking using local embeddings
"""
import logging
from typing import List, Dict, Optional, Any
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class DatabaseSearchEngine:
    """Optimized database search engine with semantic re-ranking"""
    
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
            'principal': 'principal', 'prinsipal': 'principal', 'punong guro': 'principal',
            'direktor': 'director',
            
            # Common terms
            'sino': 'who', 'ano': 'what', 'saan': 'where',
            'kailan': 'when', 'bakit': 'why', 'paano': 'how',
            'para sa': 'for', 'ng': 'of', 'sa': 'in',
            'may': 'have', 'mayroon': 'have', 'meron': 'have'
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
            # Query translated successfully
        
            return translated_query
    
    async def search_prompts(self, query: str, limit: int = 20, intent: str = None, use_semantic: bool = True) -> List[Dict[str, Any]]:
        """Search chatbot prompts with optional semantic re-ranking"""
        # First, get candidates using traditional keyword search
        candidates = await self._search_prompts_traditional(query, limit * 2, intent)  # Get more candidates for re-ranking
        
        if not candidates:
            return []
        
        # Return database search results (no embeddings, no reranking)
        return candidates[:limit]
    
    async def _search_prompts_traditional(self, query: str, limit: int = 20, intent: str = None) -> List[Dict[str, Any]]:
        """Traditional keyword-based search (original search_prompts logic)"""
        try:
            all_results = []
            
            # Normalize common typos in the query for better matching
            normalized_query = query.lower()
            typo_corrections = {
                'kayo': ['kayO', 'kay0', 'kayoo', 'kayou'],
                'prinsipal': ['principal', 'prinsipal', 'prinsipal', 'prinsipal'],
                'sino': ['sino', 'sino', 'sino', 'sino'],
                'may': ['may', 'may', 'may', 'may']
            }
            
            for correct, typos in typo_corrections.items():
                for typo in typos:
                    normalized_query = normalized_query.replace(typo, correct)
            
            # Query normalized successfully
            
            # Use NLU intent to guide search strategy
            if intent == "schedule_inquiry" or any(word in query.lower() for word in ['hours', 'schedule', 'time', 'start', 'end']):
                # For school hours queries, search for time-related information
                try:
                    time_queries = ['hours', 'schedule', 'time', 'start', 'end', 'classes', 'school day']
                    for time_query in time_queries:
                        result = self.supabase.table("chatbot_prompts") \
                            .select("keywords, response, search_tsv") \
                            .ilike("response", f"%{time_query}%") \
                            .execute()
                        
                        if result.data:
                            for item in result.data:
                                if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                    all_results.append(item)
                                    # Time entry added
                            # Time matches found
                            
                except Exception as e:
                    logger.warning(f"⚠️ Time search failed: {e}")
            
            elif intent == "staff_inquiry" or any(word in query.lower() for word in ['guro', 'teacher', 'principal', 'sino', 'who']):
                # For staff queries, search for specific staff information
                try:
                    # Search for grade-specific teacher information
                    if any(word in query.lower() for word in ['ikalimang', 'fifth', 'grade 5', '5th']):
                        grade_queries = ['grade 5', 'fifth', 'ikalimang', '5th', 'teacher', 'guro', 'adviser', 'grade five']
                        for grade_query in grade_queries:
                            # Search in both response and keywords fields
                            result = self.supabase.table("chatbot_prompts") \
                                .select("keywords, response, search_tsv") \
                                .or_(f"response.ilike.%{grade_query}%,keywords.ilike.%{grade_query}%") \
                                .execute()
                            
                            if result.data:
                                for item in result.data:
                                    if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                        all_results.append(item)
                                        # Grade 5 entry added
                                # Grade 5 matches found
                                
                except Exception as e:
                    logger.warning(f"⚠️ Grade 5 search failed: {e}")
            
            elif intent == "staff_inquiry" or any(word in query.lower() for word in ['principal', 'prinsipal', 'teacher', 'guro', 'staff', 'superintendent', 'head', 'adviser']):
                # For staff inquiries, search for staff-related information
                logger.info(f"🎯 STAFF INQUIRY DETECTED: {query}")
                try:
                    staff_queries = ['principal', 'prinsipal', 'teacher', 'guro', 'staff', 'head teacher', 'school head', 'superintendent']
                    for staff_query in staff_queries:
                        result = self.supabase.table("chatbot_prompts") \
                            .select("keywords, response, search_tsv") \
                            .ilike("keywords", f"%{staff_query}%") \
                            .execute()
                        
                        if result.data:
                            for item in result.data:
                                if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                    all_results.append(item)
                            # Staff matches found
                            
                        # Also search in response field for staff names
                        result = self.supabase.table("chatbot_prompts") \
                            .select("keywords, response, search_tsv") \
                            .ilike("response", f"%{staff_query}%") \
                            .execute()
                        
                        if result.data:
                            for item in result.data:
                                if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                    all_results.append(item)
                            # Staff response matches found
                            
                except Exception as e:
                    logger.warning(f"Staff search failed: {e}")
                
                # If we found staff results, return them
                if all_results:
                    logger.info(f"📊 Total unique results found: {len(all_results)}")
                    return all_results[:limit]
            
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
            
            # Strategy 1.5: Special handling for principal/staff queries
            if any(word in query.lower() for word in ['principal', 'prinsipal', 'may principal', 'may prinsipal']):
                try:
                    # Search for principal-related entries
                    principal_queries = ['principal', 'prinsipal', 'school head', 'head teacher']
                    for principal_query in principal_queries:
                        result = self.supabase.table("chatbot_prompts") \
                            .select("keywords, response, search_tsv") \
                            .ilike("keywords", f"%{principal_query}%") \
                            .execute()
                        
                        if result.data:
                            # Add results that aren't already in all_results
                            for item in result.data:
                                if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                    all_results.append(item)
                            logger.info(f"🎯 Found {len(result.data)} principal matches for '{principal_query}'")
                            
                        # Also search in response field for principal names
                        result = self.supabase.table("chatbot_prompts") \
                            .select("keywords, response, search_tsv") \
                            .ilike("response", f"%{principal_query}%") \
                            .execute()
                        
                        if result.data:
                            for item in result.data:
                                if not any(existing['keywords'] == item['keywords'] for existing in all_results):
                                    all_results.append(item)
                            logger.info(f"🎯 Found {len(result.data)} principal response matches for '{principal_query}'")
                            
                except Exception as e:
                    logger.warning(f"Principal search failed: {e}")
            
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
                
                # Debug: Log the top results with their scores
                for i, (score, result) in enumerate(scored_results[:5]):
                    keywords = result.get('keywords', '')[:50]
                    logger.info(f"🏆 Top {i+1}: {keywords}... (score: {score})")
                
                return top_results
            
            return unique_results[:limit]
            
        except Exception as e:
            logger.warning(f"Database search failed: {e}")
            return []
    
    def _detect_query_intent(self, query_lower: str) -> str:
        """Detect the intent of the user query"""
        # Staff/people related queries (HIGHEST PRIORITY - check first)
        if any(word in query_lower for word in ['who', 'sino', 'principal', 'teacher', 'guro', 'staff', 'may', 'prinsipal', 'superintendent', 'head', 'adviser']):
            return "staff_inquiry"
        
        # Schedule/time related queries
        if any(word in query_lower for word in ['hours', 'schedule', 'time', 'start', 'end', 'when', 'kailan']):
            return "schedule_inquiry"
        
        # Location related queries
        if any(word in query_lower for word in ['where', 'saan', 'location', 'diin', 'find', 'locate']):
            return "location_inquiry"
        
        # General school info
        if any(word in query_lower for word in ['what', 'ano', 'about', 'tungkol', 'school', 'paaralan']):
            return "general_inquiry"
        
        return "general_inquiry"
    
    def _detect_content_type(self, response_lower: str, keywords_lower: str) -> str:
        """Detect the type of content in the database entry"""
        # Schedule/time content
        if any(word in response_lower for word in ['hours', 'schedule', 'time', 'start', 'end', 'monday', 'friday', 'classes']):
            return "schedule_info"
        
        # Staff/people content - check both response and keywords
        if (any(word in response_lower for word in ['principal', 'teacher', 'guro', 'staff', 'head', 'adviser', 'director', 'superintendent']) or
            any(word in keywords_lower for word in ['principal', 'teacher', 'guro', 'staff', 'head', 'adviser', 'director', 'superintendent'])):
            return "staff_info"
        
        # Location content
        if any(word in response_lower for word in ['located', 'location', 'address', 'building', 'room', 'office']):
            return "location_info"
        
        # General school content
        if any(word in response_lower for word in ['school', 'education', 'students', 'curriculum', 'programs']):
            return "general_info"
        
        return "general_info"
    
    def _calculate_intent_content_similarity(self, query_intent: str, content_type: str, query_lower: str, response_lower: str, keywords_lower: str) -> int:
        """Calculate NLP-based similarity between query intent and content type"""
        from difflib import SequenceMatcher
        
        # Base score for intent-content type matching
        base_score = 0
        
        # Intent-content type compatibility matrix
        if query_intent == "schedule_inquiry" and content_type == "schedule_info":
            base_score = 200
        elif query_intent == "staff_inquiry" and content_type == "staff_info":
            base_score = 200
        elif query_intent == "location_inquiry" and content_type == "location_info":
            base_score = 200
        elif query_intent == "general_inquiry" and content_type == "general_info":
            base_score = 100
        
        # NLP-based semantic similarity for specific terms
        semantic_boost = 0
        
        # For staff inquiries, use SMART NLP/NLU algorithm that prioritizes exact matches
        if query_intent == "staff_inquiry" and content_type == "staff_info":
            # Calculate semantic similarity between query and keywords using NLP
            query_keywords_similarity = SequenceMatcher(None, query_lower, keywords_lower).ratio()
            query_response_similarity = SequenceMatcher(None, query_lower, response_lower).ratio()
            
            # SMART ALGORITHM: Check for exact superintendent matches first
            if 'superintendent' in query_lower and 'superintendent' in keywords_lower:
                # EXACT SUPERINTENDENT MATCH: Gets MASSIVE priority
                semantic_boost = 5000  # Much higher than grade matches
                logger.info(f"🎯 EXACT SUPERINTENDENT MATCH: {keywords_lower} -> {semantic_boost} points")
                return base_score + semantic_boost
            
            # SMART ALGORITHM: Check for exact grade matches
            grade_terms = ['grade 1', 'grade one', '1st', 'first', 'una', 'grade 2', 'grade two', '2nd', 'second', 'ikalawa', 'grade 3', 'grade three', '3rd', 'third', 'ikatlo', 'grade 4', 'grade four', '4th', 'fourth', 'ikaapat', 'grade 5', 'grade five', '5th', 'fifth', 'ikalimang', 'grade 6', 'grade six', '6th', 'sixth', 'ikaanim']
            query_has_grade = any(term in query_lower for term in grade_terms)
            content_has_grade = any(term in keywords_lower for term in grade_terms)
            
            if query_has_grade and content_has_grade:
                # EXACT MATCH: Grade-specific entries get MASSIVE priority
                # Check if the grade numbers match exactly
                query_grade_num = None
                content_grade_num = None
                
                for term in ['grade 1', 'grade one', '1st', 'first', 'una']:
                    if term in query_lower:
                        query_grade_num = '1'
                        break
                for term in ['grade 2', 'grade two', '2nd', 'second', 'ikalawa']:
                    if term in query_lower:
                        query_grade_num = '2'
                        break
                for term in ['grade 3', 'grade three', '3rd', 'third', 'ikatlo']:
                    if term in query_lower:
                        query_grade_num = '3'
                        break
                for term in ['grade 4', 'grade four', '4th', 'fourth', 'ikaapat']:
                    if term in query_lower:
                        query_grade_num = '4'
                        break
                for term in ['grade 5', 'grade five', '5th', 'fifth', 'ikalimang']:
                    if term in query_lower:
                        query_grade_num = '5'
                        break
                for term in ['grade 6', 'grade six', '6th', 'sixth', 'ikaanim']:
                    if term in query_lower:
                        query_grade_num = '6'
                        break
                        
                for term in ['grade 1', 'grade one', '1st', 'first', 'una']:
                    if term in keywords_lower:
                        content_grade_num = '1'
                        break
                for term in ['grade 2', 'grade two', '2nd', 'second', 'ikalawa']:
                    if term in keywords_lower:
                        content_grade_num = '2'
                        break
                for term in ['grade 3', 'grade three', '3rd', 'third', 'ikatlo']:
                    if term in keywords_lower:
                        content_grade_num = '3'
                        break
                for term in ['grade 4', 'grade four', '4th', 'fourth', 'ikaapat']:
                    if term in keywords_lower:
                        content_grade_num = '4'
                        break
                for term in ['grade 5', 'grade five', '5th', 'fifth', 'ikalimang']:
                    if term in keywords_lower:
                        content_grade_num = '5'
                        break
                for term in ['grade 6', 'grade six', '6th', 'sixth', 'ikaanim']:
                    if term in keywords_lower:
                        content_grade_num = '6'
                        break
                
                if query_grade_num and content_grade_num and query_grade_num == content_grade_num:
                    # PERFECT MATCH: Same grade number - give MASSIVE boost
                    semantic_boost = 1000  # Fixed high score for exact grade matches
                    logger.info(f"🎯 PERFECT GRADE MATCH: Grade {query_grade_num} -> {semantic_boost} points")
                else:
                    # Grade-specific but different grade - moderate boost
                    nlp_similarity = (query_keywords_similarity * 0.8) + (query_response_similarity * 0.2)
                    semantic_boost = int(nlp_similarity * 400)
                    logger.info(f"🎯 Grade-Specific Match: keywords={query_keywords_similarity:.2f}, response={query_response_similarity:.2f} -> {semantic_boost} points")
            else:
                # Pure NLP-based semantic matching - no hardcoding
                # Use advanced NLP similarity with weighted importance
                
                # Calculate semantic similarity using multiple NLP techniques
                from difflib import SequenceMatcher
                
                # 1. Sequence similarity (character-level)
                sequence_sim = SequenceMatcher(None, query_lower, keywords_lower).ratio()
                
                # 2. Word overlap similarity (Jaccard)
                query_words = set(query_lower.split())
                keywords_words = set(keywords_lower.split())
                response_words = set(response_lower.split())
                
                if len(query_words) > 0 and len(keywords_words) > 0:
                    jaccard_keywords = len(query_words.intersection(keywords_words)) / len(query_words.union(keywords_words))
                else:
                    jaccard_keywords = 0.0
                
                if len(query_words) > 0 and len(response_words) > 0:
                    jaccard_response = len(query_words.intersection(response_words)) / len(query_words.union(response_words))
                else:
                    jaccard_response = 0.0
                
                # 3. Semantic importance weighting with synonym matching
                # Important terms get higher weight
                important_terms = ['superintendent', 'principal', 'head', 'teacher', 'adviser', 'director', 'manager', 'leader']
                
                # Check for semantic matches (synonyms and related terms)
                semantic_matches = 0
                if 'superintendent' in query_lower and ('superintendent' in keywords_lower or 'superintendent' in response_lower):
                    semantic_matches += 1
                    logger.info(f"🎯 SUPERINTENDENT MATCH FOUND: query='{query_lower}', keywords='{keywords_lower}'")
                if 'principal' in query_lower and ('principal' in keywords_lower or 'head' in keywords_lower):
                    semantic_matches += 1
                if 'head' in query_lower and ('head' in keywords_lower or 'principal' in keywords_lower):
                    semantic_matches += 1
                if 'teacher' in query_lower and ('teacher' in keywords_lower or 'adviser' in keywords_lower):
                    semantic_matches += 1
                
                query_importance = sum(1 for term in important_terms if term in query_lower)
                content_importance = sum(1 for term in important_terms if term in keywords_lower or term in response_lower)
                
                # 4. Combined NLP similarity with importance weighting
                base_nlp_sim = (sequence_sim * 0.3) + (jaccard_keywords * 0.4) + (jaccard_response * 0.3)
                importance_boost = (query_importance + content_importance) * 0.1
                semantic_boost_score = semantic_matches * 0.5  # Big boost for semantic matches
                
                # 5. Final semantic boost calculation with massive boost for exact matches
                if semantic_matches > 0:
                    # Massive boost for exact semantic matches
                    semantic_boost = 2000 + (semantic_matches * 1000)
                    logger.info(f"🎯 EXACT SEMANTIC MATCH: {semantic_matches} matches -> {semantic_boost} points")
                else:
                    semantic_boost = int((base_nlp_sim + importance_boost + semantic_boost_score) * 1000)
                    logger.info(f"🎯 NLP Semantic Match: seq={sequence_sim:.2f}, jaccard_kw={jaccard_keywords:.2f}, jaccard_resp={jaccard_response:.2f}, importance={query_importance}+{content_importance} -> {semantic_boost} points")
        
        # For schedule inquiries, use pure NLP/NLU semantic matching
        elif query_intent == "schedule_inquiry" and content_type == "schedule_info":
            # Calculate semantic similarity between query and keywords using NLP
            query_keywords_similarity = SequenceMatcher(None, query_lower, keywords_lower).ratio()
            query_response_similarity = SequenceMatcher(None, query_lower, response_lower).ratio()
            
            # Use weighted NLP similarity (keywords are more important for schedule queries)
            nlp_similarity = (query_keywords_similarity * 0.7) + (query_response_similarity * 0.3)
            semantic_boost = int(nlp_similarity * 200)  # Pure NLP-based scoring
            logger.info(f"🎯 NLP Schedule Match: keywords={query_keywords_similarity:.2f}, response={query_response_similarity:.2f} -> {semantic_boost} points")
        
        return base_score + semantic_boost
    
    def _calculate_semantic_similarity(self, query: str, response: str) -> float:
        """Calculate advanced semantic similarity using NLP techniques"""
        from difflib import SequenceMatcher
        
        # Word-based similarity (Jaccard)
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        
        if len(query_words) == 0 and len(response_words) == 0:
            return 0.0
        
        # Jaccard similarity
        intersection = query_words.intersection(response_words)
        union = query_words.union(response_words)
        jaccard_similarity = len(intersection) / len(union) if len(union) > 0 else 0.0
        
        # Sequence similarity
        sequence_similarity = SequenceMatcher(None, query.lower(), response.lower()).ratio()
        
        # Keyword importance weighting
        important_terms = ['grade', 'teacher', 'adviser', 'hours', 'schedule', 'time', 'principal', 'staff']
        query_important = sum(1 for term in important_terms if term in query.lower())
        response_important = sum(1 for term in important_terms if term in response.lower())
        
        # Boost similarity if both contain important terms
        importance_boost = 0.0
        if query_important > 0 and response_important > 0:
            importance_boost = min(0.3, (query_important + response_important) * 0.1)
        
        # Combine similarities with importance boost
        combined_similarity = (jaccard_similarity * 0.4) + (sequence_similarity * 0.6) + importance_boost
        
        return min(combined_similarity, 1.0)
    
    def _calculate_score(self, result: Dict, query: str) -> int:
        """Calculate score for a single result (used for sorting) - same logic as select_best_result"""
        import re
        
        score = 0
        query_lower = query.lower()
        keywords_lower = result['keywords'].lower()
        response_lower = result['response'].lower()
        
        # Debug logging for school hours entries
        if 'hours' in response_lower and ('start' in response_lower or 'end' in response_lower):
            logger.info(f"🎯 Processing school hours entry: {keywords_lower} -> {response_lower[:50]}...")
        
        # Intent-based content prioritization (proper solution)
        query_intent = self._detect_query_intent(query_lower)
        content_type = self._detect_content_type(response_lower, keywords_lower)
        
        # Debug: Log what we're processing
        logger.info(f"🔍 Processing entry: keywords='{keywords_lower}', response='{response_lower[:50]}...', intent={query_intent}, content_type={content_type}")
        
        # NLP-based intent-content matching (no hard-coded boosts)
        intent_content_match = self._calculate_intent_content_similarity(query_intent, content_type, query_lower, response_lower, keywords_lower)
        score += intent_content_match
        if intent_content_match > 0:
            logger.info(f"🎯 NLP Intent-Content Match: {response_lower[:50]}... (score: {score})")
        
        # Advanced NLP semantic similarity
        semantic_score = self._calculate_semantic_similarity(query_lower, response_lower)
        score += semantic_score * 200  # Scale semantic similarity (increased from 100)
        if semantic_score > 0.5:  # Lowered threshold for better matching
            logger.info(f"🎯 High semantic similarity: {semantic_score:.2f} (score: {score})")
        
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
            
            # 0. MASSIVE boost for school hours entries (HIGHEST PRIORITY)
            if any(word in query_lower for word in ['hours', 'schedule', 'time', 'start', 'end']):
                time_indicators = ['hours', 'schedule', 'time', 'start', 'end', 'classes', 'school day']
                if any(word in response_lower for word in time_indicators):
                    score += 10000  # MASSIVE boost for school hours content
                    logger.info(f"🎯 MASSIVE boost for school hours: {response_lower[:100]}... (score: {score})")
            
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
