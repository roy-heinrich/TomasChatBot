"""
Embedding Re-ranker Module
Provides semantic search capabilities by re-ranking database search results
using local embeddings and cosine similarity.
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio
import time

logger = logging.getLogger(__name__)

@dataclass
class RerankResult:
    """Result of re-ranking with semantic similarity"""
    result: Dict[str, Any]
    similarity_score: float
    original_rank: int
    final_rank: int

class EmbeddingReranker:
    """
    Local embedding-based re-ranker for semantic search
    
    Uses sentence-transformers model to generate embeddings locally
    and re-rank database search results by semantic similarity.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.initialized = False
        self.initialization_time = None
        
    async def _ensure_initialized(self):
        """Lazy initialization of the embedding model"""
        if not self.initialized:
            await self._initialize_model()
    
    async def _initialize_model(self):
        """Initialize the sentence transformer model"""
        try:
            logger.info(f"🔄 Loading embedding model: {self.model_name}")
            start_time = time.time()
            
            # Import sentence-transformers
            from sentence_transformers import SentenceTransformer
            
            # Load model with optimized settings
            self.model = SentenceTransformer(
                self.model_name,
                device='cpu',  # Use CPU for compatibility
                cache_folder='./models'  # Cache models locally
            )
            
            self.initialization_time = time.time() - start_time
            self.initialized = True
            
            logger.info(f"✅ Embedding model loaded in {self.initialization_time:.2f}s")
            
        except ImportError:
            logger.error("❌ sentence-transformers not installed. Install with: pip install sentence-transformers")
            self.model = None
            self.initialized = False
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            self.model = None
            self.initialized = False
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            # Normalize vectors
            a_norm = a / np.linalg.norm(a)
            b_norm = b / np.linalg.norm(b)
            
            # Calculate cosine similarity
            similarity = np.dot(a_norm, b_norm)
            return float(similarity)
        except Exception as e:
            logger.warning(f"⚠️ Cosine similarity calculation failed: {e}")
            return 0.0
    
    async def generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for a single text"""
        await self._ensure_initialized()
        
        if not self.model:
            logger.warning("⚠️ Embedding model not available")
            return None
        
        try:
            # Clean and prepare text
            clean_text = self._clean_text_for_embedding(text)
            
            # Generate embedding
            embedding = self.model.encode(clean_text, convert_to_numpy=True)
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            return None
    
    def _clean_text_for_embedding(self, text: str) -> str:
        """Clean text for better embedding quality"""
        if not text:
            return ""
        
        # Basic cleaning
        clean_text = text.strip().lower()
        
        # Remove excessive whitespace
        import re
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        # Remove special characters that might confuse the model
        clean_text = re.sub(r'[^\w\s]', ' ', clean_text)
        
        return clean_text.strip()
    
    async def rerank_results(self, 
                           query: str, 
                           candidates: List[Dict[str, Any]], 
                           max_candidates: int = 10) -> List[RerankResult]:
        """
        Re-rank database search results using semantic similarity
        
        Args:
            query: User's search query
            candidates: List of database search results
            max_candidates: Maximum number of candidates to process
            
        Returns:
            List of RerankResult objects sorted by semantic similarity
        """
        if not candidates:
            return []
        
        # Limit candidates for performance
        candidates = candidates[:max_candidates]
        
        await self._ensure_initialized()
        
        if not self.model:
            logger.warning("⚠️ Embedding model not available, returning original order")
            return [
                RerankResult(
                    result=candidate,
                    similarity_score=0.0,
                    original_rank=i,
                    final_rank=i
                )
                for i, candidate in enumerate(candidates)
            ]
        
        try:
            logger.info(f"🔄 Re-ranking {len(candidates)} candidates for query: '{query[:50]}...'")
            
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            if query_embedding is None:
                logger.warning("⚠️ Failed to generate query embedding")
                return self._fallback_rerank(candidates)
            
            # Generate embeddings for all candidates
            candidate_embeddings = []
            valid_candidates = []
            
            for candidate in candidates:
                # Combine keywords and response for better semantic matching
                candidate_text = self._prepare_candidate_text(candidate)
                embedding = await self.generate_embedding(candidate_text)
                
                if embedding is not None:
                    candidate_embeddings.append(embedding)
                    valid_candidates.append(candidate)
                else:
                    logger.warning(f"⚠️ Failed to generate embedding for candidate: {candidate.get('keywords', 'Unknown')}")
            
            if not candidate_embeddings:
                logger.warning("⚠️ No valid embeddings generated")
                return self._fallback_rerank(candidates)
            
            # Calculate similarities
            similarities = []
            for i, candidate_embedding in enumerate(candidate_embeddings):
                similarity = self._cosine_similarity(query_embedding, candidate_embedding)
                
                # 🎯 FIX: Boost grade-level information for grade-related queries
                candidate = valid_candidates[i]
                query_lower = query.lower()
                keywords_lower = candidate.get('keywords', '').lower()
                response_lower = candidate.get('response', '').lower()
                
                if 'grade' in query_lower and ('grade level' in keywords_lower or 'grade level' in response_lower):
                    similarity += 0.1  # Boost grade level information
                    logger.info(f"🎯 Boosted grade level info: {candidate.get('keywords', '')[:30]}... (+0.1)")
                
                # 🎯 FIX: Boost comprehensive database entries for Tagalog queries
                if any(tagalog_word in query_lower for tagalog_word in ['may', 'ba', 'ang', 'sa', 'tomas']):
                    # Boost entries with more detailed responses
                    response_length = len(candidate.get('response', ''))
                    if response_length > 100:  # Longer, more detailed responses
                        similarity += 0.05  # Small boost for comprehensive entries
                        logger.info(f"🎯 Boosted comprehensive entry for Tagalog: {candidate.get('keywords', '')[:30]}... (+0.05)")
                    
                    # Boost entries with "what" or "how" questions (more comprehensive)
                    if any(word in keywords_lower for word in ['what', 'how', 'does', 'are']):
                        similarity += 0.03  # Small boost for question-based entries
                        logger.info(f"🎯 Boosted question-based entry for Tagalog: {candidate.get('keywords', '')[:30]}... (+0.03)")
                
                similarities.append(similarity)
            
            # Create rerank results
            rerank_results = []
            for i, (candidate, similarity) in enumerate(zip(valid_candidates, similarities)):
                rerank_results.append(RerankResult(
                    result=candidate,
                    similarity_score=similarity,
                    original_rank=i,
                    final_rank=0  # Will be set after sorting
                ))
            
            # Sort by similarity (highest first)
            rerank_results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            # Update final ranks
            for i, result in enumerate(rerank_results):
                result.final_rank = i
            
            logger.info(f"✅ Re-ranked {len(rerank_results)} results")
            
            # Log top results for debugging
            for i, result in enumerate(rerank_results[:3]):
                keywords = result.result.get('keywords', 'Unknown')[:50]
                logger.info(f"🏆 Rank {i+1}: {keywords}... (similarity: {result.similarity_score:.3f})")
            
            return rerank_results
            
        except Exception as e:
            logger.error(f"❌ Re-ranking failed: {e}")
            return self._fallback_rerank(candidates)
    
    def _prepare_candidate_text(self, candidate: Dict[str, Any]) -> str:
        """Prepare candidate text for embedding by combining relevant fields"""
        # Combine keywords and response for better semantic matching
        keywords = candidate.get('keywords', '')
        response = candidate.get('response', '')
        
        # Use keywords as primary, response as secondary
        if keywords:
            return f"{keywords} {response[:200]}"  # Limit response length
        else:
            return response[:300]  # Fallback to response only
    
    def _fallback_rerank(self, candidates: List[Dict[str, Any]]) -> List[RerankResult]:
        """Fallback when embedding fails - return original order"""
        return [
            RerankResult(
                result=candidate,
                similarity_score=0.0,
                original_rank=i,
                final_rank=i
            )
            for i, candidate in enumerate(candidates)
        ]
    
    async def get_best_match(self, 
                           query: str, 
                           candidates: List[Dict[str, Any]], 
                           similarity_threshold: float = 0.3) -> Optional[Dict[str, Any]]:
        """
        Get the best semantic match from candidates
        
        Args:
            query: User's search query
            candidates: List of database search results
            similarity_threshold: Minimum similarity score to consider a match
            
        Returns:
            Best matching result or None if no good match found
        """
        rerank_results = await self.rerank_results(query, candidates)
        
        if not rerank_results:
            return None
        
        best_result = rerank_results[0]
        
        if best_result.similarity_score >= similarity_threshold:
            logger.info(f"🎯 Best semantic match found (similarity: {best_result.similarity_score:.3f})")
            return best_result.result
        else:
            logger.info(f"⚠️ No good semantic match found (best similarity: {best_result.similarity_score:.3f})")
            return None
    
    def is_available(self) -> bool:
        """Check if the embedding model is available"""
        return self.initialized and self.model is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model"""
        return {
            "model_name": self.model_name,
            "initialized": self.initialized,
            "initialization_time": self.initialization_time,
            "available": self.is_available()
        }

# Global instance for easy access
_reranker_instance = None

async def get_reranker() -> EmbeddingReranker:
    """Get the global reranker instance (singleton pattern)"""
    global _reranker_instance
    
    if _reranker_instance is None:
        _reranker_instance = EmbeddingReranker()
        # Initialize the model immediately
        await _reranker_instance._initialize_model()
    
    return _reranker_instance
