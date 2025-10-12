"""
Context-Aware Fuzzy Matching for Three-Tier Search Strategy
Implements intelligent fuzzy matching with context awareness
"""
import logging
import re
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
import asyncio

logger = logging.getLogger(__name__)

class ContextAwareFuzzy:
    """Context-aware fuzzy matching with semantic understanding"""
    
    def __init__(self, supabase):
        self.supabase = supabase
        
        # Context-aware synonyms and related terms
        self.semantic_groups = {
            'school_info': ['school', 'elementary', 'tomas', 'bautista', 'institution', 'academy'],
            'staff': ['teacher', 'staff', 'faculty', 'instructor', 'educator', 'principal', 'admin'],
            'activities': ['activity', 'event', 'program', 'celebration', 'festival', 'competition'],
            'schedule': ['schedule', 'time', 'hours', 'period', 'session', 'class'],
            'enrollment': ['enrollment', 'admission', 'registration', 'application', 'enroll'],
            'contact': ['contact', 'phone', 'email', 'address', 'location', 'office'],
            'grades': ['grade', 'level', 'year', 'class', 'baitang', 'grado'],
            'subjects': ['subject', 'course', 'lesson', 'curriculum', 'academic'],
            'facilities': ['facility', 'building', 'room', 'library', 'cafeteria', 'gym'],
            'nutrition': ['nutrition', 'food', 'meal', 'diet', 'healthy', 'eating'],
            'scouts': ['scout', 'boy scout', 'girl scout', 'scouting', 'character'],
            'language': ['language', 'filipino', 'tagalog', 'english', 'buwan ng wika']
        }
        
        # Common misspellings and variations
        self.common_variations = {
            'teacher': ['titser', 'guro', 'maestra', 'maestro', 'instructor'],
            'principal': ['prinsipal', 'head', 'director', 'admin'],
            'school': ['skul', 'eskuwela', 'paaralan', 'institution'],
            'activities': ['aktibidad', 'event', 'program', 'activity'],
            'schedule': ['iskedyul', 'orario', 'timetable', 'time'],
            'enrollment': ['enrolment', 'registration', 'admission'],
            'nutrition': ['nutrisyon', 'food', 'meal', 'diet'],
            'scouts': ['eskaut', 'boy scout', 'girl scout'],
            'language': ['wika', 'lengguwahe', 'salita']
        }
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better fuzzy matching"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation for matching
        text = re.sub(r'[^\w\s]', ' ', text)
        
        return text.strip()
    
    def _expand_query_terms(self, query: str) -> List[str]:
        """Expand query with synonyms and variations"""
        normalized_query = self._normalize_text(query)
        terms = normalized_query.split()
        expanded_terms = set(terms)
        
        # Add semantic group matches
        for term in terms:
            for group_name, group_terms in self.semantic_groups.items():
                if term in group_terms:
                    expanded_terms.update(group_terms)
        
        # Add common variations
        for term in terms:
            if term in self.common_variations:
                expanded_terms.update(self.common_variations[term])
        
        return list(expanded_terms)
    
    def _calculate_fuzzy_score(self, query: str, text: str) -> float:
        """Calculate fuzzy matching score between query and text"""
        if not query or not text:
            return 0.0
        
        # Normalize both texts
        query_norm = self._normalize_text(query)
        text_norm = self._normalize_text(text)
        
        # Direct similarity
        direct_similarity = SequenceMatcher(None, query_norm, text_norm).ratio()
        
        # Word-level similarity
        query_words = set(query_norm.split())
        text_words = set(text_norm.split())
        
        if not query_words:
            return 0.0
        
        # Calculate word overlap
        common_words = query_words.intersection(text_words)
        word_overlap = len(common_words) / len(query_words)
        
        # Calculate semantic similarity using expanded terms
        expanded_query_terms = self._expand_query_terms(query)
        expanded_text_terms = self._expand_query_terms(text)
        
        expanded_common = set(expanded_query_terms).intersection(set(expanded_text_terms))
        semantic_similarity = len(expanded_common) / len(expanded_query_terms) if expanded_query_terms else 0
        
        # Combined score (weighted average)
        combined_score = (
            direct_similarity * 0.3 +
            word_overlap * 0.4 +
            semantic_similarity * 0.3
        )
        
        return combined_score * 100  # Convert to percentage
    
    async def search(self, query: str, threshold: float = 85.0) -> Optional[Dict[str, Any]]:
        """Search using context-aware fuzzy matching"""
        try:
            # Get all documents
            result = self.supabase.table("chatbot_prompts") \
                .select("id, keywords, response") \
                .execute()
            
            if not result.data:
                return None
            
            best_match = None
            best_score = 0.0
            
            # Calculate fuzzy scores for all documents
            for doc in result.data:
                doc_text = f"{doc.get('keywords', '')} {doc.get('response', '')}"
                
                # Calculate score for keywords
                keywords_score = self._calculate_fuzzy_score(query, doc.get('keywords', ''))
                
                # Calculate score for response
                response_score = self._calculate_fuzzy_score(query, doc.get('response', ''))
                
                # Use the higher of the two scores
                doc_score = max(keywords_score, response_score)
                
                if doc_score > best_score and doc_score >= threshold:
                    best_score = doc_score
                    best_match = {
                        'id': doc['id'],
                        'keywords': doc.get('keywords', ''),
                        'response': doc.get('response', ''),
                        'score': doc_score,
                        'match_type': 'fuzzy'
                    }
            
            if best_match:
                # logger.info(f"🔍 Fuzzy match found: {best_score:.1f}% similarity")
                return best_match
            else:
                # logger.info(f"🔍 No fuzzy match above {threshold}% threshold")
                return None
                
        except Exception as e:
            logger.error(f"Context-aware fuzzy search failed: {e}")
            return None
