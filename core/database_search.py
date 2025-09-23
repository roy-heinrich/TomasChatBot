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
    
    async def search_prompts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search chatbot prompts using search_tsv column"""
        try:
            # Format query for PostgreSQL full-text search
            # Replace spaces with & for AND search, or use OR search
            formatted_query = query.replace(' ', ' & ')
            
            # Try the formatted query first
            try:
                result = self.supabase.table("chatbot_prompts") \
                    .select("keywords, response, search_tsv") \
                    .text_search('search_tsv', formatted_query) \
                    .execute()
                
                if result.data:
                    return result.data[:limit]
            except Exception as e:
                logger.warning(f"Formatted search failed: {e}")
            
            # Fallback: try individual words
            words = query.split()
            for word in words:
                if len(word) > 2:  # Skip very short words
                    try:
                        result = self.supabase.table("chatbot_prompts") \
                            .select("keywords, response, search_tsv") \
                            .text_search('search_tsv', word) \
                            .execute()
                        
                        if result.data:
                            return result.data[:limit]
                    except Exception as e:
                        logger.warning(f"Word search failed for '{word}': {e}")
            
            # Final fallback: use ilike search
            result = self.supabase.table("chatbot_prompts") \
                .select("keywords, response, search_tsv") \
                .ilike("keywords", f"%{query}%") \
                .execute()
            
            data = result.data if result.data else []
            return data[:limit]
            
        except Exception as e:
            logger.warning(f"Database search failed: {e}")
            return []
    
    def select_best_result(self, results: List[Dict], query: str) -> Optional[Dict[str, Any]]:
        """Select the best search result with improved scoring"""
        if not results:
            return None
        
        if len(results) == 1:
            return results[0]
        
        # Enhanced scoring system
        scored_results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for result in results:
            score = 0
            keywords_lower = result['keywords'].lower()
            response_lower = result['response'].lower()
            
            # 1. Exact keyword match (highest priority)
            if query_lower == keywords_lower:
                score += 100
            elif query_lower in keywords_lower:
                score += 80
            
            # 2. Word overlap scoring
            keyword_words = set(keywords_lower.split())
            word_overlap = len(query_words & keyword_words)
            score += word_overlap * 15
            
            # 3. Response content relevance
            response_words = set(response_lower.split())
            response_overlap = len(query_words & response_words)
            score += response_overlap * 5
            
            # 4. Penalize generic responses
            generic_phrases = [
                "you must be looking", "i'm happy to help", "let me help",
                "visit the school office", "contact the school office"
            ]
            if any(phrase in response_lower for phrase in generic_phrases):
                score -= 20
            
            # 5. Prefer concise, specific responses
            if len(result['response']) < 200:
                score += 10
            elif len(result['response']) > 500:
                score -= 5
            
            # 6. Boost for direct answers
            if any(word in query_lower for word in ["who", "sino", "what", "ano", "where", "saan"]):
                if not any(generic in response_lower for generic in ["visit", "contact", "office"]):
                    score += 15
            
            scored_results.append((score, result))
        
        # Sort by score and return the best
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Log scoring for debugging
        logger.info(f"🔍 Search scoring for '{query}':")
        for i, (score, result) in enumerate(scored_results[:3]):
            logger.info(f"   {i+1}. Score: {score} - {result['keywords'][:50]}...")
        
        return scored_results[0][1] if scored_results else None
