
"""
PgVector Semantic Search for Render Free Tier
Uses sentence-transformers + pgvector for optimal performance
"""
import logging
import numpy as np
from typing import List, Dict, Optional, Any
from supabase import create_client, Client
import gc
import os

logger = logging.getLogger(__name__)

class PgVectorSemanticSearch:
    """Semantic search using pgvector for optimal performance"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.model = None
        self.model_loaded = False
        
        # Check if pgvector is available
        self.pgvector_available = self._check_pgvector()
        
        logger.info(f"✅ PgVector semantic search initialized (pgvector: {self.pgvector_available})")
    
    def _check_pgvector(self) -> bool:
        """Check if pgvector extension is available"""
        try:
            # Try to create a test vector
            result = self.supabase.rpc('check_pgvector').execute()
            return True
        except Exception as e:
            logger.warning(f"⚠️ PgVector not available: {e}")
            return False
    
    def _load_model_if_needed(self):
        """Load model only when needed to save memory"""
        if not self.model_loaded:
            try:
                from sentence_transformers import SentenceTransformer
                
                # Use the smallest, most efficient model
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                self.model_loaded = True
                
                logger.info("🧠 Semantic model loaded (lazy loading)")
                
                # Force garbage collection to free memory
                gc.collect()
                
            except Exception as e:
                logger.error(f"❌ Failed to load semantic model: {e}")
                self.model = None
                self.model_loaded = False
    
    def _unload_model(self):
        """Unload model to free memory when not needed"""
        if self.model_loaded:
            self.model = None
            self.model_loaded = False
            gc.collect()
            logger.info("🧹 Semantic model unloaded to free memory")
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding with memory optimization"""
        try:
            self._load_model_if_needed()
            
            if not self.model:
                logger.warning("⚠️ Semantic model not available")
                return None
            
            # Generate embedding
            embedding = self.model.encode([text], convert_to_tensor=False)
            
            # Unload model immediately to free memory
            self._unload_model()
            
            return embedding[0].tolist()
            
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            self._unload_model()
            return None
    
    async def pgvector_search(self, query: str, limit: int = 20, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Perform semantic search using pgvector (if available)"""
        if not self.pgvector_available:
            logger.warning("⚠️ PgVector not available, falling back to Python similarity")
            return await self._python_similarity_search(query, limit, threshold)
        
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            if not query_embedding:
                logger.warning("⚠️ Could not generate query embedding")
                return []
            
            # Use pgvector for similarity search
            result = self.supabase.rpc(
                'semantic_search',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': threshold,
                    'match_count': limit
                }
            ).execute()
            
            if result.data:
                logger.info(f"🔍 PgVector search found {len(result.data)} results")
                return result.data
            else:
                logger.info("No results found with pgvector")
                return []
                
        except Exception as e:
            logger.error(f"❌ PgVector search failed: {e}")
            # Fallback to Python similarity
            return await self._python_similarity_search(query, limit, threshold)
    
    async def _python_similarity_search(self, query: str, limit: int, threshold: float) -> List[Dict[str, Any]]:
        """Fallback Python similarity search"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            if not query_embedding:
                return []
            
            # Get records with embeddings
            result = self.supabase.table("chatbot_prompts") \
                .select("id, keywords, response, embedding") \
                .not_.is_("embedding", "null") \
                .execute()
            
            if not result.data:
                return []
            
            # Calculate similarities
            similarities = []
            for record in result.data:
                if record.get('embedding'):
                    try:
                        record_embedding = record['embedding']
                        if isinstance(record_embedding, str):
                            record_embedding = eval(record_embedding)
                        
                        # Calculate cosine similarity
                        similarity = self._cosine_similarity(query_embedding, record_embedding)
                        
                        if similarity >= threshold:
                            similarities.append({
                                'id': record['id'],
                                'keywords': record['keywords'],
                                'response': record['response'],
                                'similarity': similarity
                            })
                    except Exception as e:
                        logger.warning(f"Error processing record {record['id']}: {e}")
                        continue
            
            # Sort by similarity
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            logger.info(f"🔍 Python similarity search found {len(similarities)} results")
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"❌ Python similarity search failed: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    async def hybrid_search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Hybrid search combining pgvector semantic and traditional methods"""
        try:
            # 1. PgVector semantic search
            semantic_results = await self.pgvector_search(query, limit * 2, threshold=0.6)
            
            # 2. Traditional search
            from core.database_search import DatabaseSearchEngine
            traditional_engine = DatabaseSearchEngine(
                self.supabase._url, 
                self.supabase._key
            )
            traditional_results = traditional_engine.search_prompts(query, limit * 2)
            
            # 3. Combine results
            result_map = {}
            
            # Add semantic results
            for result in semantic_results:
                key = result.get('keywords', '')
                if key not in result_map:
                    result_map[key] = {
                        'data': result,
                        'semantic_score': result.get('similarity', 0.0),
                        'traditional_score': 0.0,
                        'hybrid_score': 0.0
                    }
            
            # Add traditional results
            for i, result in enumerate(traditional_results):
                key = result.get('keywords', '')
                if key in result_map:
                    result_map[key]['traditional_score'] = 1.0 - (i / max(len(traditional_results), 1))
                else:
                    result_map[key] = {
                        'data': result,
                        'semantic_score': 0.0,
                        'traditional_score': 1.0 - (i / max(len(traditional_results), 1)),
                        'hybrid_score': 0.0
                    }
            
            # Calculate hybrid scores
            for key, result_info in result_map.items():
                result_info['hybrid_score'] = (
                    result_info['semantic_score'] * 0.6 +  # Higher weight for semantic
                    result_info['traditional_score'] * 0.4
                )
            
            # Sort by hybrid score
            sorted_results = sorted(
                result_map.values(), 
                key=lambda x: x['hybrid_score'], 
                reverse=True
            )
            
            # Return final results
            final_results = []
            for result_info in sorted_results:
                result_data = result_info['data'].copy()
                final_results.append(result_data)
            
            search_type = "PgVector" if self.pgvector_available else "Python"
            logger.info(f"🔀 Hybrid search ({search_type}): {len(semantic_results)} semantic + {len(traditional_results)} traditional = {len(final_results)} unique results")
            return final_results[:limit]
            
        except Exception as e:
            logger.error(f"❌ Hybrid search failed: {e}")
            # Fallback to traditional search
            from core.database_search import DatabaseSearchEngine
            traditional_engine = DatabaseSearchEngine(
                self.supabase._url, 
                self.supabase._key
            )
            return traditional_engine.search_prompts(query, limit)
