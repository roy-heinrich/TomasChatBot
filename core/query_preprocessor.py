#!/usr/bin/env python3
"""
Query Pre-processing Cache
Optimizes query processing while respecting grade-specific isolation
"""
import asyncio
import hashlib
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class PreprocessedQuery:
    """Preprocessed query result"""
    original_query: str
    processed_query: str
    detected_language: str
    detected_intent: str
    extracted_grade: Optional[str]
    query_type: str  # 'grade_specific', 'general', 'emergency'
    confidence: float
    timestamp: float
    cache_key: str

class QueryPreprocessor:
    """Smart query pre-processing with grade-aware caching"""
    
    def __init__(self):
        self.preprocessing_cache: Dict[str, PreprocessedQuery] = {}
        self.cache_ttl = 1800  # 30 minutes
        self.max_cache_size = 1000
        self.grade_patterns = {
            r'grade\s*(\d+)': 'grade_specific',
            r'grado\s*(\d+)': 'grade_specific',
            r'baitang\s*(\d+)': 'grade_specific',
            r'(\d+)\s*grade': 'grade_specific',
            r'(\d+)\s*grado': 'grade_specific'
        }
        
        # Emergency patterns (highest priority)
        self.emergency_patterns = [
            r'emergency', r'heart attack', r'bleeding', r'fire', r'accident',
            r'911', r'help', r'urgent', r'critical', r'danger'
        ]
        
        # General query patterns
        self.general_patterns = [
            r'school hours', r'principal', r'enrollment', r'fees',
            r'location', r'contact', r'address', r'phone'
        ]
    
    def _create_cache_key(self, query: str, include_grade: bool = True) -> str:
        """Create cache key with grade isolation"""
        # Normalize query
        normalized = query.lower().strip()
        
        # Extract grade if present
        grade = None
        if include_grade:
            for pattern in self.grade_patterns.keys():
                match = re.search(pattern, normalized)
                if match:
                    grade = match.group(1)
                    break
        
        # Create hash
        if grade:
            # Include grade in cache key for grade-specific queries
            key_data = f"{normalized}:grade:{grade}"
        else:
            # General queries don't include grade
            key_data = f"{normalized}:general"
        
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _extract_grade(self, query: str) -> Optional[str]:
        """Extract grade from query"""
        query_lower = query.lower()
        
        for pattern in self.grade_patterns.keys():
            match = re.search(pattern, query_lower)
            if match:
                return match.group(1)
        
        return None
    
    def _classify_query_type(self, query: str, grade: Optional[str]) -> str:
        """Classify query type with grade awareness"""
        query_lower = query.lower()
        
        # Check for emergency first (highest priority)
        for pattern in self.emergency_patterns:
            if re.search(pattern, query_lower):
                return 'emergency'
        
        # Check for grade-specific queries
        if grade:
            return 'grade_specific'
        
        # Check for general queries
        for pattern in self.general_patterns:
            if re.search(pattern, query_lower):
                return 'general'
        
        return 'general'
    
    def _detect_language(self, query: str) -> str:
        """Simple language detection for preprocessing"""
        query_lower = query.lower()
        
        # Aklanon patterns
        aklanon_indicators = ['du', 'it', 'hay', 'akon', 'nga', 'unga', 'makaron', 'imaw']
        if any(indicator in query_lower for indicator in aklanon_indicators):
            return 'akl'
        
        # Tagalog patterns
        tagalog_indicators = ['ang', 'ng', 'sa', 'ay', 'si', 'mga', 'namin', 'natin', 'po', 'naman']
        if any(indicator in query_lower for indicator in tagalog_indicators):
            return 'tl'
        
        # Default to English
        return 'en'
    
    def _detect_intent(self, query: str, query_type: str) -> str:
        """Simple intent detection for preprocessing"""
        query_lower = query.lower()
        
        if query_type == 'emergency':
            return 'emergency'
        
        # Staff inquiries
        if any(word in query_lower for word in ['who', 'teacher', 'adviser', 'principal', 'sino']):
            return 'staff_inquiry'
        
        # Schedule inquiries
        if any(word in query_lower for word in ['hours', 'time', 'schedule', 'oras']):
            return 'schedule_inquiry'
        
        # Enrollment inquiries
        if any(word in query_lower for word in ['enroll', 'admission', 'apply', 'register']):
            return 'enrollment_inquiry'
        
        # Financial inquiries
        if any(word in query_lower for word in ['fee', 'payment', 'cost', 'price']):
            return 'financial_inquiry'
        
        return 'general_inquiry'
    
    async def preprocess_query(self, query: str) -> PreprocessedQuery:
        """Preprocess query with smart caching"""
        # Check cache first
        cache_key = self._create_cache_key(query)
        
        if cache_key in self.preprocessing_cache:
            cached_result = self.preprocessing_cache[cache_key]
            
            # Check if cache is still valid
            if time.time() - cached_result.timestamp < self.cache_ttl:
                logger.info(f"💾 Preprocessing cache HIT for: {query[:50]}...")
                return cached_result
            else:
                # Remove expired cache
                del self.preprocessing_cache[cache_key]
        
        logger.info(f"🔄 Preprocessing cache MISS for: {query[:50]}...")
        
        # Extract grade
        grade = self._extract_grade(query)
        
        # Classify query type
        query_type = self._classify_query_type(query, grade)
        
        # Detect language
        detected_language = self._detect_language(query)
        
        # Detect intent
        detected_intent = self._detect_intent(query, query_type)
        
        # Create processed query (cleaned version)
        processed_query = self._clean_query(query)
        
        # Calculate confidence
        confidence = self._calculate_confidence(query, grade, query_type)
        
        # Create result
        result = PreprocessedQuery(
            original_query=query,
            processed_query=processed_query,
            detected_language=detected_language,
            detected_intent=detected_intent,
            extracted_grade=grade,
            query_type=query_type,
            confidence=confidence,
            timestamp=time.time(),
            cache_key=cache_key
        )
        
        # Store in cache
        self._store_in_cache(cache_key, result)
        
        return result
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize query"""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', query.strip())
        
        # Remove common filler words
        filler_words = ['please', 'can you', 'could you', 'would you', 'po', 'naman']
        words = cleaned.split()
        filtered_words = [word for word in words if word.lower() not in filler_words]
        
        return ' '.join(filtered_words)
    
    def _calculate_confidence(self, query: str, grade: Optional[str], query_type: str) -> float:
        """Calculate confidence score for preprocessing"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for grade-specific queries
        if query_type == 'grade_specific' and grade:
            confidence += 0.3
        
        # Boost confidence for emergency queries
        if query_type == 'emergency':
            confidence += 0.4
        
        # Boost confidence for clear patterns
        if len(query.split()) >= 3:  # Longer queries are usually clearer
            confidence += 0.1
        
        # Boost confidence for specific keywords
        specific_keywords = ['teacher', 'adviser', 'principal', 'hours', 'enroll']
        if any(keyword in query.lower() for keyword in specific_keywords):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _store_in_cache(self, cache_key: str, result: PreprocessedQuery):
        """Store result in cache with size management"""
        # Check cache size
        if len(self.preprocessing_cache) >= self.max_cache_size:
            # Remove oldest entries
            oldest_key = min(
                self.preprocessing_cache.keys(),
                key=lambda k: self.preprocessing_cache[k].timestamp
            )
            del self.preprocessing_cache[oldest_key]
            logger.info("🧹 Preprocessing cache cleanup: removed oldest entry")
        
        # Store new result
        self.preprocessing_cache[cache_key] = result
        logger.info(f"💾 Stored preprocessing result: {result.query_type} (grade: {result.extracted_grade})")
    
    def invalidate_grade_cache(self, grade: str):
        """Invalidate cache entries for specific grade (respects grade isolation)"""
        keys_to_remove = []
        
        for cache_key, result in self.preprocessing_cache.items():
            if result.extracted_grade == grade:
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self.preprocessing_cache[key]
        
        if keys_to_remove:
            logger.info(f"🗑️ Invalidated {len(keys_to_remove)} preprocessing cache entries for Grade {grade}")
    
    def invalidate_all_cache(self):
        """Invalidate all preprocessing cache"""
        count = len(self.preprocessing_cache)
        self.preprocessing_cache.clear()
        logger.info(f"🗑️ Invalidated all {count} preprocessing cache entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get preprocessing cache statistics"""
        total_entries = len(self.preprocessing_cache)
        
        # Count by query type
        type_counts = {}
        grade_counts = {}
        
        for result in self.preprocessing_cache.values():
            # Count by type
            type_counts[result.query_type] = type_counts.get(result.query_type, 0) + 1
            
            # Count by grade
            if result.extracted_grade:
                grade_counts[result.extracted_grade] = grade_counts.get(result.extracted_grade, 0) + 1
        
        return {
            'total_entries': total_entries,
            'cache_size_limit': self.max_cache_size,
            'cache_utilization': (total_entries / self.max_cache_size) * 100,
            'query_types': type_counts,
            'grade_distribution': grade_counts,
            'cache_ttl': self.cache_ttl
        }
    
    def cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        current_time = time.time()
        expired_keys = []
        
        for cache_key, result in self.preprocessing_cache.items():
            if current_time - result.timestamp > self.cache_ttl:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self.preprocessing_cache[key]
        
        if expired_keys:
            logger.info(f"🧹 Cleaned up {len(expired_keys)} expired preprocessing cache entries")

# Global preprocessor instance
query_preprocessor = QueryPreprocessor()

# Convenience functions
async def preprocess_query(query: str) -> PreprocessedQuery:
    """Preprocess a query with caching"""
    return await query_preprocessor.preprocess_query(query)

def invalidate_grade_preprocessing_cache(grade: str):
    """Invalidate preprocessing cache for specific grade"""
    query_preprocessor.invalidate_grade_cache(grade)

def get_preprocessing_cache_stats() -> Dict[str, Any]:
    """Get preprocessing cache statistics"""
    return query_preprocessor.get_cache_stats()
