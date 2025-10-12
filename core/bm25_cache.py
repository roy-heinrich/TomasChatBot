"""
BM25 Ranking Cache for Three-Tier Search Strategy
Implements BM25 algorithm from scratch using standard Python libraries.
No external BM25 package required - this is a self-contained implementation.
"""
import logging
import math
import json
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
import re

logger = logging.getLogger(__name__)

class BM25Cache:
    """
    BM25 ranking system with caching for performance.
    
    This is a custom implementation of the BM25 algorithm using only standard Python libraries.
    No external BM25 packages are required - all calculations are done from scratch.
    """
    
    def __init__(self, supabase):
        self.supabase = supabase
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache
        self.last_cache_update = 0
        
        # BM25 parameters
        self.k1 = 1.2  # Term frequency saturation parameter
        self.b = 0.75  # Length normalization parameter
        
        # Document statistics (cached)
        self.doc_freqs = {}  # Document frequency for each term
        self.doc_lengths = {}  # Length of each document
        self.avg_doc_length = 0
        self.total_docs = 0
        
    async def _load_document_stats(self):
        """Load and cache document statistics for BM25 calculation"""
        try:
            # Get all documents from database
            result = self.supabase.table("chatbot_prompts") \
                .select("id, keywords, response") \
                .execute()
            
            if not result.data:
                logger.warning("No documents found for BM25 stats")
                return
            
            # Reset stats
            self.doc_freqs = defaultdict(int)
            self.doc_lengths = {}
            self.total_docs = len(result.data)
            
            # Process each document
            for doc in result.data:
                doc_id = doc['id']
                # Combine keywords and response for full text
                text = f"{doc.get('keywords', '')} {doc.get('response', '')}"
                
                # Tokenize and count terms
                terms = self._tokenize(text)
                term_counts = Counter(terms)
                
                # Store document length
                self.doc_lengths[doc_id] = len(terms)
                
                # Count document frequencies
                for term in set(terms):
                    self.doc_freqs[term] += 1
            
            # Calculate average document length
            if self.doc_lengths:
                self.avg_doc_length = sum(self.doc_lengths.values()) / len(self.doc_lengths)
            
            # logger.info(f"✅ BM25 stats loaded: {self.total_docs} docs, avg length: {self.avg_doc_length:.1f}")
            
        except Exception as e:
            logger.error(f"Failed to load BM25 document stats: {e}")
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for BM25 processing"""
        if not text:
            return []
        
        # Convert to lowercase and extract words
        text = text.lower()
        # Remove punctuation and split on whitespace
        words = re.findall(r'\b\w+\b', text)
        # Filter out very short words
        return [word for word in words if len(word) > 2]
    
    def _calculate_bm25_score(self, query_terms: List[str], doc_id: int, doc_text: str) -> float:
        """Calculate BM25 score for a document"""
        if not self.doc_freqs or not self.doc_lengths:
            return 0.0
        
        doc_terms = self._tokenize(doc_text)
        term_counts = Counter(doc_terms)
        doc_length = self.doc_lengths.get(doc_id, len(doc_terms))
        
        score = 0.0
        
        for term in query_terms:
            if term not in self.doc_freqs:
                continue
            
            # Term frequency in document
            tf = term_counts.get(term, 0)
            if tf == 0:
                continue
            
            # Document frequency
            df = self.doc_freqs[term]
            
            # Inverse document frequency
            idf = math.log((self.total_docs - df + 0.5) / (df + 0.5))
            
            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
            
            score += idf * (numerator / denominator)
        
        return score
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search using BM25 ranking"""
        try:
            # Load document stats if needed
            if not self.doc_freqs or not self.doc_lengths:
                await self._load_document_stats()
            
            if not self.doc_freqs:
                logger.warning("No document stats available for BM25 search")
                return []
            
            # Tokenize query
            query_terms = self._tokenize(query)
            if not query_terms:
                return []
            
            # Get all documents
            result = self.supabase.table("chatbot_prompts") \
                .select("id, keywords, response") \
                .execute()
            
            if not result.data:
                return []
            
            # Calculate BM25 scores for all documents
            scored_docs = []
            for doc in result.data:
                doc_id = doc['id']
                doc_text = f"{doc.get('keywords', '')} {doc.get('response', '')}"
                
                score = self._calculate_bm25_score(query_terms, doc_id, doc_text)
                
                if score > 0:
                    scored_docs.append({
                        'id': doc_id,
                        'keywords': doc.get('keywords', ''),
                        'response': doc.get('response', ''),
                        'score': score
                    })
            
            # Sort by score (descending) and return top_k
            scored_docs.sort(key=lambda x: x['score'], reverse=True)
            
            # logger.info(f"🔍 BM25 search: {len(scored_docs)} results, top score: {scored_docs[0]['score']:.2f}" if scored_docs else "No BM25 results")
            
            return scored_docs[:top_k]
            
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []
