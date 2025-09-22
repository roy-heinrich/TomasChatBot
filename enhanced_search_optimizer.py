"""
Enhanced Search Optimizer for TomasChatBot
Improves accuracy and performance while maintaining Supabase integration
"""

import asyncio
import logging
import time
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import hashlib
import json

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Enhanced search result with relevance scoring"""
    content: str
    relevance_score: float
    match_type: str  # "exact", "semantic", "keyword", "fuzzy"
    source: str  # "supabase", "summarized_text"
    keywords: str = ""
    confidence: float = 0.0

@dataclass
class QueryAnalysis:
    """Analysis of user query for optimized search"""
    intent: str
    entities: List[str]
    keywords: List[str]
    search_strategy: str
    priority_terms: List[str]
    confidence: float

class SearchStrategy(Enum):
    """Search strategy types"""
    EXACT_MATCH = "exact_match"
    SEMANTIC_SEARCH = "semantic_search"
    KEYWORD_SEARCH = "keyword_search"
    FUZZY_SEARCH = "fuzzy_search"
    HYBRID_SEARCH = "hybrid_search"

class EnhancedSearchOptimizer:
    """
    Enhanced search optimizer that improves accuracy and performance
    while maintaining full Supabase and summarized_text integration
    """
    
    def __init__(self):
        self.search_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.performance_metrics = {
            "search_times": [],
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Enhanced keyword patterns for better matching
        self.intent_patterns = {
            "enrollment": [
                "enroll", "enrollment", "register", "admission", "application",
                "requirements", "documents", "deadline", "process", "procedure"
            ],
            "school_info": [
                "school", "about", "information", "grades", "facilities", "programs",
                "curriculum", "academic", "education", "learning"
            ],
            "location": [
                "where", "location", "address", "directions", "map", "find",
                "fatima", "new washington", "aklan", "located"
            ],
            "staff": [
                "teacher", "principal", "head", "staff", "faculty", "guidance",
                "nurse", "secretary", "director", "admin", "guro", "titser"
            ],
            "contact": [
                "contact", "phone", "email", "number", "call", "reach",
                "tawag", "kontak", "numero"
            ],
            "schedule": [
                "schedule", "time", "hours", "when", "start", "end", "class",
                "oras", "panahon", "klase"
            ]
        }
        
        # Performance optimization settings
        self.max_search_time = 15.0  # seconds
        self.cache_size_limit = 1000
        self.parallel_search_limit = 3
        
    def _get_cache_key(self, query: str, search_type: str = "general") -> str:
        """Generate cache key for query"""
        normalized_query = re.sub(r'[^\w\s]', '', query.lower().strip())
        return hashlib.md5(f"{normalized_query}_{search_type}".encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        return time.time() - cache_entry.get("timestamp", 0) < self.cache_ttl
    
    async def analyze_query(self, query: str) -> QueryAnalysis:
        """Analyze query to determine optimal search strategy"""
        start_time = time.time()
        
        query_lower = query.lower()
        entities = []
        keywords = []
        intent = "general"
        confidence = 0.0
        
        # Extract entities using simple patterns
        entity_patterns = {
            "person_name": r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
            "grade_level": r'\b(?:grade|level)\s+\d+\b',
            "age": r'\b\d+\s*(?:years?\s*old|yrs?)\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        }
        
        for entity_type, pattern in entity_patterns.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend([(entity_type, match) for match in matches])
        
        # Determine intent and extract keywords
        intent_scores = {}
        for intent_name, patterns in self.intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            if score > 0:
                intent_scores[intent_name] = score
                keywords.extend([p for p in patterns if p in query_lower])
        
        if intent_scores:
            intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[intent] / len(self.intent_patterns[intent])
        
        # Determine search strategy
        if confidence > 0.7:
            search_strategy = SearchStrategy.EXACT_MATCH.value
        elif confidence > 0.4:
            search_strategy = SearchStrategy.KEYWORD_SEARCH.value
        else:
            search_strategy = SearchStrategy.HYBRID_SEARCH.value
        
        # Extract priority terms (most important words)
        priority_terms = []
        if keywords:
            priority_terms = keywords[:3]  # Top 3 keywords
        else:
            # Fallback: extract meaningful words
            words = re.findall(r'\b\w{3,}\b', query_lower)
            stop_words = {"the", "and", "or", "but", "for", "with", "what", "where", "when", "how", "who"}
            priority_terms = [w for w in words if w not in stop_words][:3]
        
        analysis_time = time.time() - start_time
        logger.info(f"🔍 Query analysis completed in {analysis_time:.3f}s: intent={intent}, confidence={confidence:.2f}")
        
        return QueryAnalysis(
            intent=intent,
            entities=entities,
            keywords=keywords,
            search_strategy=search_strategy,
            priority_terms=priority_terms,
            confidence=confidence
        )
    
    async def optimized_supabase_search(self, query: str, supabase_client, search_analysis: QueryAnalysis) -> List[SearchResult]:
        """Optimized Supabase search with enhanced accuracy"""
        start_time = time.time()
        results = []
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(query, "supabase")
            if cache_key in self.search_cache and self._is_cache_valid(self.search_cache[cache_key]):
                self.performance_metrics["cache_hits"] += 1
                logger.info("✅ Cache hit for Supabase search")
                return self.search_cache[cache_key]["results"]
            
            self.performance_metrics["cache_misses"] += 1
            
            # Strategy 1: Exact match for high-confidence queries
            if search_analysis.search_strategy == SearchStrategy.EXACT_MATCH.value:
                results = await self._exact_match_search(query, supabase_client, search_analysis)
            
            # Strategy 2: Keyword search for medium-confidence queries
            elif search_analysis.search_strategy == SearchStrategy.KEYWORD_SEARCH.value:
                results = await self._keyword_search(query, supabase_client, search_analysis)
            
            # Strategy 3: Hybrid search for low-confidence queries
            else:
                results = await self._hybrid_search(query, supabase_client, search_analysis)
            
            # Cache results
            if len(self.search_cache) < self.cache_size_limit:
                self.search_cache[cache_key] = {
                    "results": results,
                    "timestamp": time.time()
                }
            
            search_time = time.time() - start_time
            self.performance_metrics["search_times"].append(search_time)
            logger.info(f"🔍 Supabase search completed in {search_time:.3f}s with {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Optimized Supabase search failed: {e}")
            return []
    
    async def _exact_match_search(self, query: str, supabase_client, analysis: QueryAnalysis) -> List[SearchResult]:
        """High-precision exact match search"""
        results = []
        
        try:
            # Try exact keyword matches first
            for term in analysis.priority_terms:
                try:
                    response = supabase_client.table("chatbot_prompts") \
                        .select("keywords, response") \
                        .ilike("keywords", f"%{term}%") \
                        .limit(5) \
                        .execute()
                    
                    if response.data:
                        for item in response.data:
                            result = SearchResult(
                                content=f"Q: {item['keywords']}\nA: {item['response']}",
                                relevance_score=0.95,  # High score for exact matches
                                match_type="exact",
                                source="supabase",
                                keywords=item['keywords'],
                                confidence=0.9
                            )
                            results.append(result)
                            
                except Exception as e:
                    logger.warning(f"Exact match search failed for term '{term}': {e}")
            
            # Remove duplicates and sort by relevance
            results = self._deduplicate_and_rank(results)
            return results[:3]  # Return top 3 results
            
        except Exception as e:
            logger.error(f"❌ Exact match search failed: {e}")
            return []
    
    async def _keyword_search(self, query: str, supabase_client, analysis: QueryAnalysis) -> List[SearchResult]:
        """Medium-precision keyword search"""
        results = []
        
        try:
            # Search in keywords field
            for term in analysis.priority_terms:
                try:
                    response = supabase_client.table("chatbot_prompts") \
                        .select("keywords, response") \
                        .ilike("keywords", f"%{term}%") \
                        .limit(3) \
                        .execute()
                    
                    if response.data:
                        for item in response.data:
                            # Calculate relevance score based on term frequency
                            relevance = self._calculate_relevance(item['keywords'], analysis.priority_terms)
                            
                            result = SearchResult(
                                content=f"Q: {item['keywords']}\nA: {item['response']}",
                                relevance_score=relevance,
                                match_type="keyword",
                                source="supabase",
                                keywords=item['keywords'],
                                confidence=0.7
                            )
                            results.append(result)
                            
                except Exception as e:
                    logger.warning(f"Keyword search failed for term '{term}': {e}")
            
            # Also search in response field for broader coverage
            for term in analysis.priority_terms[:2]:  # Limit to top 2 terms
                try:
                    response = supabase_client.table("chatbot_prompts") \
                        .select("keywords, response") \
                        .ilike("response", f"%{term}%") \
                        .limit(2) \
                        .execute()
                    
                    if response.data:
                        for item in response.data:
                            relevance = self._calculate_relevance(item['response'], analysis.priority_terms)
                            
                            result = SearchResult(
                                content=f"Q: {item['keywords']}\nA: {item['response']}",
                                relevance_score=relevance * 0.8,  # Lower score for response field matches
                                match_type="keyword",
                                source="supabase",
                                keywords=item['keywords'],
                                confidence=0.6
                            )
                            results.append(result)
                            
                except Exception as e:
                    logger.warning(f"Response field search failed for term '{term}': {e}")
            
            results = self._deduplicate_and_rank(results)
            return results[:5]  # Return top 5 results
            
        except Exception as e:
            logger.error(f"❌ Keyword search failed: {e}")
            return []
    
    async def _hybrid_search(self, query: str, supabase_client, analysis: QueryAnalysis) -> List[SearchResult]:
        """Low-precision hybrid search with multiple strategies"""
        results = []
        
        try:
            # Combine multiple search strategies
            search_tasks = []
            
            # Task 1: Keyword search
            search_tasks.append(self._keyword_search(query, supabase_client, analysis))
            
            # Task 2: Fuzzy search for individual words
            if analysis.priority_terms:
                search_tasks.append(self._fuzzy_word_search(analysis.priority_terms, supabase_client))
            
            # Task 3: Intent-specific search
            if analysis.intent != "general":
                search_tasks.append(self._intent_specific_search(analysis.intent, supabase_client))
            
            # Execute searches in parallel
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine and deduplicate results
            for result_list in search_results:
                if isinstance(result_list, list):
                    results.extend(result_list)
            
            results = self._deduplicate_and_rank(results)
            return results[:7]  # Return top 7 results for hybrid search
            
        except Exception as e:
            logger.error(f"❌ Hybrid search failed: {e}")
            return []
    
    async def _fuzzy_word_search(self, terms: List[str], supabase_client) -> List[SearchResult]:
        """Fuzzy search for individual words"""
        results = []
        
        for term in terms:
            if len(term) > 3:  # Only search for meaningful words
                try:
                    response = supabase_client.table("chatbot_prompts") \
                        .select("keywords, response") \
                        .ilike("keywords", f"%{term}%") \
                        .limit(2) \
                        .execute()
                    
                    if response.data:
                        for item in response.data:
                            result = SearchResult(
                                content=f"Q: {item['keywords']}\nA: {item['response']}",
                                relevance_score=0.5,  # Lower score for fuzzy matches
                                match_type="fuzzy",
                                source="supabase",
                                keywords=item['keywords'],
                                confidence=0.4
                            )
                            results.append(result)
                            
                except Exception as e:
                    logger.warning(f"Fuzzy search failed for term '{term}': {e}")
        
        return results
    
    async def _intent_specific_search(self, intent: str, supabase_client) -> List[SearchResult]:
        """Search based on detected intent"""
        results = []
        
        # Map intents to specific search terms
        intent_terms = {
            "enrollment": ["enrollment", "enroll", "admission", "requirements"],
            "school_info": ["school", "about", "information", "grades"],
            "location": ["location", "address", "where", "fatima"],
            "staff": ["teacher", "principal", "staff", "faculty"],
            "contact": ["contact", "phone", "email", "number"],
            "schedule": ["schedule", "time", "hours", "when"]
        }
        
        terms = intent_terms.get(intent, [])
        for term in terms:
            try:
                response = supabase_client.table("chatbot_prompts") \
                    .select("keywords, response") \
                    .ilike("keywords", f"%{term}%") \
                    .limit(2) \
                    .execute()
                
                if response.data:
                    for item in response.data:
                        result = SearchResult(
                            content=f"Q: {item['keywords']}\nA: {item['response']}",
                            relevance_score=0.7,  # Medium score for intent-based matches
                            match_type="semantic",
                            source="supabase",
                            keywords=item['keywords'],
                            confidence=0.6
                        )
                        results.append(result)
                        
            except Exception as e:
                logger.warning(f"Intent-specific search failed for term '{term}': {e}")
        
        return results
    
    def _calculate_relevance(self, text: str, priority_terms: List[str]) -> float:
        """Calculate relevance score based on term frequency"""
        text_lower = text.lower()
        matches = sum(1 for term in priority_terms if term.lower() in text_lower)
        return min(matches / len(priority_terms), 1.0) if priority_terms else 0.0
    
    def _deduplicate_and_rank(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicates and rank by relevance"""
        # Remove duplicates based on content
        seen = set()
        unique_results = []
        for result in results:
            content_hash = hashlib.md5(result.content.encode()).hexdigest()
            if content_hash not in seen:
                seen.add(content_hash)
                unique_results.append(result)
        
        # Sort by relevance score (descending)
        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)
        return unique_results
    
    async def optimized_summarized_text_search(self, query: str, summarized_text: str, search_analysis: QueryAnalysis) -> List[SearchResult]:
        """Optimized search in summarized text with enhanced accuracy"""
        if not summarized_text:
            return []
        
        start_time = time.time()
        results = []
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(query, "summarized_text")
            if cache_key in self.search_cache and self._is_cache_valid(self.search_cache[cache_key]):
                self.performance_metrics["cache_hits"] += 1
                logger.info("✅ Cache hit for summarized text search")
                return self.search_cache[cache_key]["results"]
            
            self.performance_metrics["cache_misses"] += 1
            
            # Split text into sections for better matching
            sections = self._split_text_into_sections(summarized_text)
            
            # Search each section
            for section in sections:
                relevance = self._calculate_section_relevance(section, search_analysis.priority_terms)
                
                if relevance > 0.3:  # Only include relevant sections
                    result = SearchResult(
                        content=section,
                        relevance_score=relevance,
                        match_type="semantic",
                        source="summarized_text",
                        confidence=0.8
                    )
                    results.append(result)
            
            # Sort by relevance and limit results
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            results = results[:3]  # Return top 3 sections
            
            # Cache results
            if len(self.search_cache) < self.cache_size_limit:
                self.search_cache[cache_key] = {
                    "results": results,
                    "timestamp": time.time()
                }
            
            search_time = time.time() - start_time
            logger.info(f"🔍 Summarized text search completed in {search_time:.3f}s with {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Optimized summarized text search failed: {e}")
            return []
    
    def _split_text_into_sections(self, text: str) -> List[str]:
        """Split text into meaningful sections"""
        # Split by common section markers
        section_markers = ["\n\n", "##", "###", "**", "*"]
        
        sections = [text]  # Start with full text
        
        for marker in section_markers:
            new_sections = []
            for section in sections:
                if marker in section:
                    new_sections.extend(section.split(marker))
                else:
                    new_sections.append(section)
            sections = new_sections
        
        # Filter out very short sections
        sections = [s.strip() for s in sections if len(s.strip()) > 50]
        
        return sections
    
    def _calculate_section_relevance(self, section: str, priority_terms: List[str]) -> float:
        """Calculate relevance of a text section"""
        if not priority_terms:
            return 0.0
        
        section_lower = section.lower()
        matches = sum(1 for term in priority_terms if term.lower() in section_lower)
        
        # Bonus for multiple matches
        if matches > 1:
            return min(matches / len(priority_terms) * 1.2, 1.0)
        
        return matches / len(priority_terms)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        avg_search_time = sum(self.performance_metrics["search_times"]) / len(self.performance_metrics["search_times"]) if self.performance_metrics["search_times"] else 0
        
        return {
            "average_search_time": avg_search_time,
            "cache_hit_rate": self.performance_metrics["cache_hits"] / (self.performance_metrics["cache_hits"] + self.performance_metrics["cache_misses"]) if (self.performance_metrics["cache_hits"] + self.performance_metrics["cache_misses"]) > 0 else 0,
            "total_searches": len(self.performance_metrics["search_times"]),
            "cache_size": len(self.search_cache)
        }
    
    def clear_cache(self):
        """Clear search cache"""
        self.search_cache.clear()
        logger.info("🧹 Search cache cleared")
