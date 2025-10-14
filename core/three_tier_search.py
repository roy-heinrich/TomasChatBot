"""
Three-Tier Search Strategy Implementation
Combines FTS + BM25 + Smart Fuzzy for comprehensive search results
"""
import logging
from typing import List, Dict, Any, Optional
from core.bm25_cache import BM25Cache
from core.context_aware_fuzzy import ContextAwareFuzzy

logger = logging.getLogger(__name__)

class ThreeTierSearch:
    """Three-tier search strategy with intelligent fallback"""
    
    def __init__(self, supabase):
        self.supabase = supabase
        self.bm25 = BM25Cache(supabase)
        self.fuzzy = ContextAwareFuzzy(supabase)
        
        # Search configuration
        self.fts_config = 'english'
        self.bm25_high_confidence_threshold = 5.0
        self.bm25_low_confidence_threshold = 3.0
        self.fuzzy_threshold = 85.0
    
    async def search(self, query: str, limit: int = 1) -> Optional[Dict[str, Any]]:
        """Three-tier search with intelligent fallback"""
        
        if not query or not query.strip():
            return None
        
        # logger.info(f"🔍 Three-tier search for: '{query}'")
        
        # TIER 1: PostgreSQL FTS exact phrase match
        fts_result = await self._tier1_fts_search(query)
        if fts_result:
            # logger.info("✅ TIER 1: FTS exact match found")
            return fts_result
        
        # TIER 2: BM25 ranking
        bm25_result = await self._tier2_bm25_search(query)
        if bm25_result:
            score = bm25_result.get('score', 0)
            if score > self.bm25_high_confidence_threshold:
                # logger.info(f"✅ TIER 2: BM25 high confidence match (score: {score:.2f})")
                return bm25_result
            elif score > self.bm25_low_confidence_threshold:
                # logger.info(f"⚠️ TIER 2: BM25 medium confidence match (score: {score:.2f})")
                # Continue to Tier 3 for better match, but keep this as fallback
                tier3_result = await self._tier3_fuzzy_search(query)
                if tier3_result:
                    # logger.info("✅ TIER 3: Fuzzy match found, using over BM25")
                    return tier3_result
                else:
                    # logger.info("⚠️ No better fuzzy match, using BM25 result")
                    return bm25_result
        
        # TIER 3: Smart fuzzy (only if BM25 is uncertain or no results)
        if not bm25_result or bm25_result.get('score', 0) < self.bm25_low_confidence_threshold:
            # logger.info("⚠️ TIER 3: Using smart fuzzy fallback")
            fuzzy_result = await self._tier3_fuzzy_search(query)
            if fuzzy_result:
                # logger.info("✅ TIER 3: Fuzzy match found")
                return fuzzy_result
        
        # Final fallback: return BM25 result even if low confidence
        if bm25_result:
            score = bm25_result.get('score', 0)
            # logger.info(f"⚠️ Final fallback: Low confidence BM25 result (score: {score:.2f})")
            return bm25_result
        
        # logger.info("❌ No results found in any tier")
        return None
    
    async def _tier1_fts_search(self, query: str) -> Optional[Dict[str, Any]]:
        """Tier 1: PostgreSQL Full-Text Search with simple word matching"""
        try:
            # Clean query for FTS to avoid syntax errors
            clean_query = self._clean_fts_query(query)
            if not clean_query:
                return None
            
            # Try simple word search (same as existing database search)
            result = self.supabase.table('chatbot_prompts').select('*').text_search(
                'search_tsv',
                clean_query
            ).execute()
            
            if result.data:
                # Calculate scores for all results and pick the best one
                best_result = None
                best_score = 0
                
                for doc in result.data:
                    relevance_score = self._calculate_fts_relevance_score(query, doc)
                    if relevance_score > best_score:
                        best_score = relevance_score
                        best_result = doc
                
                if best_result:
                    return {
                        'id': best_result.get('id'),
                        'keywords': best_result.get('keywords', ''),
                        'response': best_result.get('response', ''),
                        'score': best_score,  # Dynamic relevance score
                        'match_type': 'fts',
                        'tier': 1
                    }
            
            return None
            
        except Exception as e:
            logger.warning(f"Tier 1 FTS search failed: {e}")
            return None
    
    def _clean_fts_query(self, query: str) -> str:
        """Clean query for FTS to avoid syntax errors - same as existing database search"""
        if not query:
            return ""
        
        import re
        
        # Remove problematic characters that cause tsquery syntax errors
        cleaned = query.strip()
        
        # Remove ALL punctuation and special characters that cause tsquery issues
        cleaned = re.sub(r'[!@#$%^&*()_+=\[\]{}|;:"<>?/~`\\]', '', cleaned)
        
        # Remove exclamation marks and other problematic characters
        cleaned = re.sub(r'[!?]', '', cleaned)
        
        # Remove escaped characters and backslashes
        cleaned = re.sub(r'\\', '', cleaned)
        
        # Remove single characters and very short words, but preserve numbers
        words = cleaned.split()
        valid_words = [word for word in words if len(word) > 1 or word.isdigit()]
        
        if not valid_words:
            return ""
            
        # Join with & for tsquery syntax (same as existing database search)
        return ' & '.join(valid_words)
    
    async def _tier2_bm25_search(self, query: str) -> Optional[Dict[str, Any]]:
        """Tier 2: BM25 ranking for semantic similarity"""
        try:
            results = await self.bm25.search(query, top_k=1)
            if results:
                result = results[0]
                return {
                    'id': result.get('id'),
                    'keywords': result.get('keywords', ''),
                    'response': result.get('response', ''),
                    'score': result.get('score', 0),
                    'match_type': 'bm25',
                    'tier': 2
                }
            return None
            
        except Exception as e:
            logger.warning(f"Tier 2 BM25 search failed: {e}")
            return None
    
    async def _tier3_fuzzy_search(self, query: str) -> Optional[Dict[str, Any]]:
        """Tier 3: Context-aware fuzzy matching"""
        try:
            result = await self.fuzzy.search(query, threshold=self.fuzzy_threshold)
            if result:
                return {
                    'id': result.get('id'),
                    'keywords': result.get('keywords', ''),
                    'response': result.get('response', ''),
                    'score': result.get('score', 0),
                    'match_type': 'fuzzy',
                    'tier': 3
                }
            return None
            
        except Exception as e:
            logger.warning(f"Tier 3 fuzzy search failed: {e}")
            return None
    
    async def search_multiple(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search and return multiple results from all tiers"""
        try:
            all_results = []
            
            # Get results from all tiers
            fts_results = await self._get_fts_results(query, limit)
            bm25_results = await self._get_bm25_results(query, limit)
            fuzzy_results = await self._get_fuzzy_results(query, limit)
            
            # Combine and deduplicate results
            seen_ids = set()
            
            # Add FTS results first (highest priority)
            for result in fts_results:
                if result['id'] not in seen_ids:
                    all_results.append(result)
                    seen_ids.add(result['id'])
            
            # Add BM25 results
            for result in bm25_results:
                if result['id'] not in seen_ids:
                    all_results.append(result)
                    seen_ids.add(result['id'])
            
            # Add fuzzy results
            for result in fuzzy_results:
                if result['id'] not in seen_ids:
                    all_results.append(result)
                    seen_ids.add(result['id'])
            
            # Sort by score (descending)
            all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            return all_results[:limit]
            
        except Exception as e:
            logger.error(f"Multiple search failed: {e}")
            return []
    
    async def _get_fts_results(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Get FTS results for multiple search"""
        try:
            # Clean query for FTS
            clean_query = self._clean_fts_query(query)
            if not clean_query:
                return []
            
            result = self.supabase.table('chatbot_prompts').select('*').text_search(
                'search_tsv',
                clean_query
            ).execute()
            
            results = []
            for i, doc in enumerate(result.data):  # Process all results first
                # Calculate relevance-based score instead of fixed score
                relevance_score = self._calculate_fts_relevance_score(query, doc)
                results.append({
                    'id': doc.get('id'),
                    'keywords': doc.get('keywords', ''),
                    'response': doc.get('response', ''),
                    'score': relevance_score,  # Dynamic relevance score
                    'match_type': 'fts',
                    'tier': 1
                })
            
            # Sort by score (highest first) and return top results
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.warning(f"FTS multiple search failed: {e}")
            # Return empty list instead of crashing
            return []
    
    def _calculate_fts_relevance_score(self, query: str, doc: Dict[str, Any]) -> float:
        """Calculate relevance-based score for FTS results"""
        try:
            import re
            from difflib import SequenceMatcher
            
            query_lower = query.lower()
            keywords = doc.get('keywords', '').lower()
            response = doc.get('response', '').lower()
            
            # Calculate keyword match score
            keyword_words = keywords.split()
            query_words = query_lower.split()
            
            keyword_matches = 0
            for q_word in query_words:
                for k_word in keyword_words:
                    if q_word in k_word or k_word in q_word:
                        keyword_matches += 1
                        break
            
            keyword_score = (keyword_matches / len(query_words)) * 50 if query_words else 0
            
            # Calculate response relevance score
            response_score = 0
            if response:
                # Check for exact phrase matches
                if query_lower in response:
                    response_score += 30
                
                # Check for word overlap
                response_words = response.split()
                response_matches = 0
                for q_word in query_words:
                    for r_word in response_words:
                        if q_word in r_word or r_word in q_word:
                            response_matches += 1
                            break
                
                response_score += (response_matches / len(query_words)) * 20 if query_words else 0
            
            # Base score for FTS match
            base_score = 60
            
            # Total score (max 100)
            total_score = min(base_score + keyword_score + response_score, 100)
            
            return total_score
            
        except Exception as e:
            logger.warning(f"FTS relevance calculation failed: {e}")
            return 60.0  # Default score
    
    async def _get_bm25_results(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Get BM25 results for multiple search"""
        try:
            results = await self.bm25.search(query, top_k=limit)
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result.get('id'),
                    'keywords': result.get('keywords', ''),
                    'response': result.get('response', ''),
                    'score': result.get('score', 0),
                    'match_type': 'bm25',
                    'tier': 2
                })
            return formatted_results
            
        except Exception as e:
            logger.warning(f"BM25 multiple search failed: {e}")
            return []
    
    async def _get_fuzzy_results(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Get fuzzy results for multiple search"""
        try:
            # Get all documents and calculate fuzzy scores
            result = self.supabase.table("chatbot_prompts") \
                .select("id, keywords, response") \
                .execute()
            
            if not result.data:
                return []
            
            scored_results = []
            for doc in result.data:
                doc_text = f"{doc.get('keywords', '')} {doc.get('response', '')}"
                score = self.fuzzy._calculate_fuzzy_score(query, doc_text)
                
                if score >= self.fuzzy_threshold:
                    scored_results.append({
                        'id': doc['id'],
                        'keywords': doc.get('keywords', ''),
                        'response': doc.get('response', ''),
                        'score': score,
                        'match_type': 'fuzzy',
                        'tier': 3
                    })
            
            # Sort by score and return top results
            scored_results.sort(key=lambda x: x['score'], reverse=True)
            return scored_results[:limit]
            
        except Exception as e:
            logger.warning(f"Fuzzy multiple search failed: {e}")
            return []
