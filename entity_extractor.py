"""
Advanced Entity Extraction System for TOMAS Chatbot
==================================================

This module provides sophisticated NLP-based entity extraction capabilities
to identify and extract meaningful information from user queries including:
- Person names (parents, children, staff)
- Grade levels and academic terms
- Subjects and curriculum topics  
- Dates and time expressions
- School-specific terminology
- Contact information
"""

import os
import nltk

# Point NLTK to the local nltk_data folder first, then Render path for deployment
local_nltk_path = os.path.join(os.path.dirname(__file__), "nltk_data")
render_nltk_path = "/opt/render/nltk_data"

# Add local path first (for development), then Render path (for deployment)
nltk.data.path.insert(0, local_nltk_path)
nltk.data.path.append(render_nltk_path)

import re
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import calendar
from functools import lru_cache

# Initialize NLTK immediately like in the earlier working builds
NLTK_AVAILABLE = False
NLTK_INITIALIZED = False

# Initialize NLTK functions as None - will be set during initialization
word_tokenize = None
sent_tokenize = None
pos_tag = None
ne_chunk = None
Tree = None

def _initialize_nltk():
    """Initialize NLTK safely with error handling"""
    global NLTK_AVAILABLE, NLTK_INITIALIZED
    global word_tokenize, sent_tokenize, pos_tag, ne_chunk, Tree
    
    if NLTK_INITIALIZED:
        return NLTK_AVAILABLE
    
    try:
        import nltk
        from nltk.tokenize import word_tokenize as _word_tokenize, sent_tokenize as _sent_tokenize
        from nltk.corpus import stopwords
        from nltk.tag import pos_tag as _pos_tag
        from nltk.chunk import ne_chunk as _ne_chunk
        from nltk.tree import Tree as _Tree
        
        # Set global variables
        word_tokenize = _word_tokenize
        sent_tokenize = _sent_tokenize
        pos_tag = _pos_tag
        ne_chunk = _ne_chunk
        Tree = _Tree
        
        NLTK_AVAILABLE = True
        NLTK_INITIALIZED = True
        print("✅ NLTK initialized successfully for entity extraction")
        return True
        
    except ImportError:
        NLTK_AVAILABLE = False
        NLTK_INITIALIZED = True
        print("NLTK not available for entity extraction")
        return False
    except Exception as e:
        NLTK_AVAILABLE = False
        NLTK_INITIALIZED = True
        print(f"NLTK initialization failed: {e}")
        return False

# Multilingual NLP engine removed - using rule-based entity extraction only
MULTILINGUAL_NLP_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class ExtractedEntity:
    """Represents an entity extracted from user input"""
    entity_type: str  # person_name, grade_level, subject, date, etc.
    value: str        # The actual extracted value
    confidence: float # Confidence score 0.0-1.0
    start_pos: int = 0
    end_pos: int = 0
    context: str = ""  # Surrounding context for disambiguation

class LightweightEntityExtractor:
    """
    Fast, lightweight entity extraction using regex patterns and caching
    """
    
    def __init__(self):
        # Pre-compiled regex patterns for performance
        self.patterns = {
            'PERSON': re.compile(r'(?:Mr|Mrs|Ms|Dr|Prof)\.?\s+([A-Z][a-z]+)', re.I),
            'LOCATION': re.compile(r'\b(?:in|at|from|to|visit|located)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.I),
            'ORG': re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Corp|Inc|University|School|Elementary)', re.I),
            'NAME_INTRO': re.compile(r'\b(?:my name is|i am|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', re.I),
            'GRADE': re.compile(r'\b(?:grade|g\.)\s*(\d+)\b', re.I),
            'SUBJECT': re.compile(r'\b(?:math|science|english|filipino|art|music|pe|physical education)\b', re.I),
            'SCHOOL_NAME': re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Elementary|School|University|College)\b', re.I),
            'CITY': re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:City|Town|Province|State)\b', re.I)
        }
        
        # Blacklist to filter out common false positives
        self.blacklist = {'Contact', 'Talk', 'Meet', 'The', 'I', 'You', 'We', 'They', 'This', 'That', 'Here', 'There'}
        
        # School-specific terms
        self.school_terms = {
            'principal', 'teacher', 'student', 'school', 'classroom', 'library', 'cafeteria', 
            'gymnasium', 'office', 'adviser', 'counselor', 'nurse', 'janitor', 'security'
        }
    
    @lru_cache(maxsize=500)
    def extract(self, text: str) -> List[Tuple[str, str]]:
        """
        Extract entities using lightweight regex patterns with caching
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of (entity_value, entity_type) tuples
        """
        entities = []
        
        for entity_type, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                entity = match.group(1).strip() if match.groups() else match.group(0).strip()
                
                # Filter out blacklisted entities
                if entity not in self.blacklist and len(entity) > 1:
                    # Additional validation for school context
                    if self._is_valid_entity(entity, entity_type, text):
                        entities.append((entity, entity_type))
        
        return entities
    
    def _is_valid_entity(self, entity: str, entity_type: str, context: str) -> bool:
        """Validate entity based on context and type"""
        context_lower = context.lower()
        entity_lower = entity.lower()
        
        # Skip very short entities
        if len(entity) < 2:
            return False
        
        # Skip common words that aren't entities
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        if entity_lower in common_words:
            return False
        
        # Type-specific validation
        if entity_type == 'PERSON':
            # Must be capitalized and not a common word
            return entity[0].isupper() and entity_lower not in common_words
        
        elif entity_type == 'LOCATION':
            # Must be capitalized and not a preposition
            prepositions = {'in', 'at', 'from', 'to', 'on', 'by', 'with', 'for'}
            return entity[0].isupper() and entity_lower not in prepositions
        
        elif entity_type == 'ORG':
            # Must contain organization indicators
            org_indicators = {'school', 'university', 'college', 'corp', 'inc', 'ltd', 'company'}
            return any(indicator in entity_lower for indicator in org_indicators)
        
        elif entity_type == 'SUBJECT':
            # Must be a known academic subject
            subjects = {'math', 'mathematics', 'science', 'english', 'filipino', 'art', 'music', 'pe', 'physical education'}
            return entity_lower in subjects
        
        elif entity_type == 'SCHOOL_NAME':
            # Must be capitalized and contain school indicators
            school_indicators = {'elementary', 'school', 'university', 'college', 'academy'}
            return entity[0].isupper() and any(indicator in entity_lower for indicator in school_indicators)
        
        elif entity_type == 'CITY':
            # Must be capitalized and contain location indicators
            location_indicators = {'city', 'town', 'province', 'state', 'municipality'}
            return entity[0].isupper() and any(indicator in entity_lower for indicator in location_indicators)
        
        elif entity_type == 'GRADE':
            # Must be a valid grade number
            try:
                grade_num = int(entity)
                return 1 <= grade_num <= 12
            except ValueError:
                return False
        
        return True


class AdvancedEntityExtractor:
    """
    Advanced entity extraction using NLP techniques and domain-specific patterns
    """
    
    def __init__(self):
        # Initialize lightweight extractor for fast processing
        self.lightweight_extractor = LightweightEntityExtractor()
        self.grade_patterns = self._build_grade_patterns()
        self.subject_patterns = self._build_subject_patterns()
        self.name_patterns = self._build_name_patterns()
        self.date_patterns = self._build_date_patterns()
        self.contact_patterns = self._build_contact_patterns()
        self.school_terms = self._build_school_terminology()
        
        # Smart NLTK configuration
        self.nltk_loaded = False
        self._nltk_cache = {}
        self._cache_timeout = 300  # 5 minutes
        self._performance_stats = {
            'total_queries': 0,
            'nltk_queries': 0,
            'cache_hits': 0,
            'avg_time_ms': 0
        }
        
        # Pre-compile regex patterns for performance
        self._name_patterns = [
            r'\b(?:my name is|i am|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            r'\b(?:dr\.|mr\.|mrs\.|ms\.|professor|prof\.)\s+([A-Z][a-z]+)\b',
            r'\b(?:meet with|talk to|contact)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        ]
        self._compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self._name_patterns]
        
        # Entity detection triggers
        self._nltk_triggers = [
            r'\b(?:my name is|i am)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b',
            r'\b(?:dr\.|mr\.|mrs\.|ms\.|professor|prof\.)\s+[A-Z][a-z]+\b',
            r'\b(?:visit|go to|located in)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b',
            r'\b(?:corporation|company|organization|school|university)\b'
        ]
        self._compiled_triggers = [re.compile(pattern, re.IGNORECASE) for pattern in self._nltk_triggers]
        
    def extract_entities(self, text: str, intent_context: str = None) -> List[ExtractedEntity]:
        """
        Extract all entities from the given text using lightweight regex first, then advanced patterns
        
        Args:
            text: Input text to analyze
            intent_context: The detected intent to help with disambiguation
            
        Returns:
            List of extracted entities with confidence scores
        """
        start_time = time.perf_counter()
        entities = []
        text_lower = text.lower()
        
        # 1. Fast lightweight extraction first
        lightweight_entities = self.lightweight_extractor.extract(text)
        for entity_value, entity_type in lightweight_entities:
            entities.append(ExtractedEntity(
                entity_type=entity_type.lower(),
                value=entity_value,
                confidence=0.8,  # High confidence for regex matches
                start_pos=text.find(entity_value),
                end_pos=text.find(entity_value) + len(entity_value),
                context=text[max(0, text.find(entity_value)-10):text.find(entity_value)+len(entity_value)+10]
            ))
        
        # 2. Advanced pattern matching for domain-specific entities
        entities.extend(self._extract_person_names(text, text_lower, intent_context))
        entities.extend(self._extract_grade_levels(text, text_lower))
        entities.extend(self._extract_subjects(text, text_lower))
        entities.extend(self._extract_dates(text, text_lower))
        entities.extend(self._extract_contact_info(text, text_lower))
        entities.extend(self._extract_school_terms(text, text_lower))
        entities.extend(self._extract_ages(text, text_lower))
        entities.extend(self._extract_staff_roles(text, text_lower))
        
        # 3. Smart NLTK extraction with conditional usage (only if lightweight didn't find enough)
        if len(entities) < 2 and self._should_use_nltk(text, entities):
            nltk_entities = self._extract_entities_with_nltk_cached(text)
            entities.extend(nltk_entities)
        
        # Update performance stats
        self._performance_stats['total_queries'] += 1
        
        # Extract entity relationships
        relationship_entities = self._extract_entity_relationships(text, entities)
        entities.extend(relationship_entities)
        
        # Context-aware entity extraction
        context_entities = self._extract_context_entities(text, entities, intent_context)
        entities.extend(context_entities)
        
        # Sort by confidence and remove overlaps
        entities = self._resolve_entity_conflicts(entities)
        
        # Detect relationships between entities
        entities = self._detect_entity_relationships(entities, text)
        
        logger.info(f"🔍 Rule-based extracted {len(entities)} entities from: '{text[:50]}...'")
        for entity in entities:
            logger.info(f"   📍 {entity.entity_type}: '{entity.value}' (confidence: {entity.confidence:.2f})")
        
        return entities
    
    def _should_use_nltk(self, text: str, existing_entities: List[ExtractedEntity]) -> bool:
        """Determine if NLTK extraction should be used"""
        
        # Skip NLTK if text is very short
        words = text.split()
        if len(words) < 5:
            return False
        
        # Skip NLTK if we already have good entities
        if len(existing_entities) >= 3:
            return False
        
        # Skip NLTK if no potential entities detected
        if not self._has_potential_entities(text):
            return False
        
        # Use NLTK for complex queries with potential entities
        return len(words) > 10 or any(trigger.search(text) for trigger in self._compiled_triggers)
    
    def _has_potential_entities(self, text: str) -> bool:
        """Check if text has potential entities without using NLTK"""
        
        # Check for capitalized words (potential proper nouns)
        words = text.split()
        capitalized_words = [word for word in words if word[0].isupper() and len(word) > 2]
        
        if len(capitalized_words) < 2:
            return False
        
        # Check for name patterns
        for pattern in self._compiled_patterns:
            if pattern.search(text):
                return True
        
        # Check for location indicators
        location_indicators = ['in', 'at', 'from', 'to', 'visit', 'go', 'located']
        if any(indicator in text.lower() for indicator in location_indicators):
            return True
        
        # Check for organization indicators
        org_indicators = ['corporation', 'company', 'organization', 'school', 'university', 'inc', 'ltd']
        if any(indicator in text.lower() for indicator in org_indicators):
            return True
        
        return True
    
    def _extract_entities_with_nltk_cached(self, text: str) -> List[ExtractedEntity]:
        """Cached NLTK entity extraction with lazy loading"""
        
        # Check in-memory cache first
        cache_key = text.lower().strip()
        if cache_key in self._nltk_cache:
            cached_result, timestamp = self._nltk_cache[cache_key]
            if time.time() - timestamp < self._cache_timeout:
                self._performance_stats['cache_hits'] += 1
                return cached_result
        
        # Lazy load NLTK if not already loaded
        if not self.nltk_loaded:
            self._load_nltk()
        
        # Extract with NLTK
        entities = self._extract_entities_with_nltk(text)
        
        # Cache result
        self._nltk_cache[cache_key] = (entities, time.time())
        self._performance_stats['nltk_queries'] += 1
        
        return entities
    
    def _load_nltk(self):
        """Lazy load NLTK models only when needed"""
        try:
            import nltk
            from nltk import word_tokenize, pos_tag, ne_chunk, Tree
            
            # Download required NLTK data if not present
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)
            
            try:
                nltk.data.find('taggers/averaged_perceptron_tagger')
            except LookupError:
                nltk.download('averaged_perceptron_tagger', quiet=True)
            
            try:
                nltk.data.find('chunkers/maxent_ne_chunker')
            except LookupError:
                nltk.download('maxent_ne_chunker', quiet=True)
            
            self.nltk_loaded = True
            logger.info("✅ NLTK models loaded successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load NLTK: {e}")
            self.nltk_loaded = False
    
    def _extract_entities_with_nltk(self, text: str) -> List[ExtractedEntity]:
        """Enhanced entity extraction using NLTK"""
        entities = []

        try:
            import nltk
            from nltk import word_tokenize, pos_tag, ne_chunk, Tree
            
            # Tokenize and tag the text
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            
            # Extract named entities using NLTK
            tree = ne_chunk(pos_tags)
            
            for subtree in tree:
                if isinstance(subtree, Tree):
                    entity_text = ' '.join([token for token, pos in subtree.leaves()])
                    entity_label = subtree.label()
                    
                    # Map NLTK entity types to our types
                    if entity_label == 'PERSON':
                        entities.append(ExtractedEntity(
                            entity_type='person_name',
                            value=entity_text,
                            confidence=0.8,
                            start_pos=text.find(entity_text),
                            end_pos=text.find(entity_text) + len(entity_text)
                        ))
                    elif entity_label in ['GPE', 'LOCATION']:
                        entities.append(ExtractedEntity(
                            entity_type='location',
                            value=entity_text,
                            confidence=0.7,
                            start_pos=text.find(entity_text),
                            end_pos=text.find(entity_text) + len(entity_text)
                        ))
                    elif entity_label == 'ORGANIZATION':
                        entities.append(ExtractedEntity(
                            entity_type='organization',
                            value=entity_text,
                            confidence=0.7,
                            start_pos=text.find(entity_text),
                            end_pos=text.find(entity_text) + len(entity_text)
                        ))

            # Extract proper nouns using POS tagging
            for token, pos in pos_tags:
                if pos == 'NNP' and len(token) > 2:  # Proper noun, at least 3 characters
                    if token.istitle() and self._is_valid_name(token):
                        entities.append(ExtractedEntity(
                            entity_type='person_name',
                            value=token,
                            confidence=0.6,
                            start_pos=text.find(token),
                            end_pos=text.find(token) + len(token)
                        ))

            logger.info(f"🔍 NLTK extracted {len(entities)} entities")

        except Exception as e:
            logger.warning(f"NLTK entity extraction failed: {e}")

        return entities
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        stats = self._performance_stats.copy()
        if stats['total_queries'] > 0:
            stats['nltk_usage_rate'] = stats['nltk_queries'] / stats['total_queries']
            stats['cache_hit_rate'] = stats['cache_hits'] / stats['total_queries']
        else:
            stats['nltk_usage_rate'] = 0
            stats['cache_hit_rate'] = 0
        
        stats['cache_size'] = len(self._nltk_cache)
        stats['nltk_loaded'] = self.nltk_loaded
        
        return stats
    
    def clear_cache(self):
        """Clear all caches"""
        self._nltk_cache.clear()
        print("🗑️ NLTK cache cleared")
    
    def force_nltk(self, text: str) -> List[ExtractedEntity]:
        """Force NLTK extraction for testing"""
        entities = []
        if self._should_use_nltk(text, entities):
            nltk_entities = self._extract_entities_with_nltk_cached(text)
            entities.extend(nltk_entities)
        return entities
    
    def skip_nltk(self, text: str) -> List[ExtractedEntity]:
        """Skip NLTK extraction for testing"""
        # Temporarily disable NLTK
        original_loaded = self.nltk_loaded
        self.nltk_loaded = False
        
        # Extract without NLTK
        entities = self.extract_entities(text)
        
        # Restore original state
        self.nltk_loaded = original_loaded
        
        return entities
    
    async def extract_entities_async(self, text: str, intent_context: str = None) -> List[ExtractedEntity]:
        """
        Async version of extract_entities for better performance with NLP models
        """
        entities = []
        
        # Use rule-based extraction for domain-specific entities
        text_lower = text.lower()
        
        # Extract different entity types using pattern matching
        entities.extend(self._extract_person_names(text, text_lower, intent_context))
        entities.extend(self._extract_grade_levels(text, text_lower))
        entities.extend(self._extract_subjects(text, text_lower))
        entities.extend(self._extract_dates(text, text_lower))
        entities.extend(self._extract_contact_info(text, text_lower))
        entities.extend(self._extract_school_terms(text, text_lower))
        entities.extend(self._extract_ages(text, text_lower))
        entities.extend(self._extract_staff_roles(text, text_lower))
        
        # Sort by confidence and remove overlaps
        entities = self._resolve_entity_conflicts(entities)
        
        logger.info(f"🔍 Total extracted {len(entities)} entities from: '{text[:50]}...'")
        for entity in entities:
            logger.info(f"   📍 {entity.entity_type}: '{entity.value}' (confidence: {entity.confidence:.2f})")
        
        return entities
    
    def _build_grade_patterns(self) -> Dict[str, List[str]]:
        """Build patterns for grade level detection"""
        return {
            "numeric": [
                r"grade\s*(\d+)", r"(\d+)(?:st|nd|rd|th)?\s*grade",
                r"level\s*(\d+)", r"year\s*(\d+)"
            ],
            "written": [
                r"(kindergarten|kinder|prep)", r"(first|second|third|fourth|fifth|sixth)\s*grade",
                r"grade\s*(one|two|three|four|five|six|seven|eight|nine|ten)"
            ],
            "filipino": [
                r"(unang|ikalawang|ikatlong|ikatatlong|ikaapat|ikalimang|ikaanim)\s*baitang",
                r"baitang\s*(isa|dalawa|tatlo|apat|lima|anim)",
                r"(unang|ikalawang|ikatlong|ikatatlong|ikaapat|ikalimang|ikaanim)\s*grade",
                r"grade\s*(isa|dalawa|tatlo|apat|lima|anim)",
                r"para\s+sa\s+(ikatlong|ikatatlong|ikalimang|unang|ikalawang|ikaapat|ikaanim)\s+baitang"
            ]
        }
    
    def _build_subject_patterns(self) -> List[str]:
        """Build patterns for subject/curriculum detection"""
        return [
            # Core subjects
            "mathematics", "math", "matematika", "science", "agham", "english", "ingles",
            "filipino", "reading", "writing", "social studies", "araling panlipunan",
            "physical education", "pe", "music", "art", "computer", "technology",
            
            # Elementary specific
            "mother tongue", "mother tongue based multilingual education", "mtb-mle",
            "values education", "edukasyong pagpapakatao", "health", "nutrition",
            
            # Skills and activities
            "spelling", "composition", "grammar", "arithmetic", "geometry",
            "science experiments", "sports", "drawing", "singing"
        ]
    
    def _build_name_patterns(self) -> List[str]:
        """Build patterns for name extraction"""
        return [
            # English patterns - handle both uppercase and lowercase names
            r"my name is ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+and|\s*,|\s*$|\s+who|\s+but)",
            r"i['\s]*m ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+and|\s*,|\s*$|\s+who|\s+but)",
            r"i am ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+and|\s*,|\s*$|\s+who|\s+but)",
            r"hi[,\s]*i['\s]*m ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+and|\s*,|\s*$|\s+who|\s+but)",
            r"hi[,\s]+i am ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+and|\s*,|\s*$|\s+who|\s+but)",
            r"hello[,\s]*i['\s]*m ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+and|\s*,|\s*$|\s+who|\s+but)",
            r"hello[,\s]+i am ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+and|\s*,|\s*$|\s+who|\s+but)",
            r"call me ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+and|\s*,|\s*$)",
            r"this is ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+and|\s*,|\s*$)",
            
            # Child/family patterns - handle both uppercase and lowercase names
            r"my (?:son|daughter|child) (?:is\s+)?([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+who|\s+and|\s*,|\s*$)",
            r"(?:son|daughter|child) named ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+who|\s+and|\s*,|\s*$)",
            r"her name is ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+and|\s*,|\s*$)",
            r"his name is ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+and|\s*,|\s*$)",
            r"daughter ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+who|\s+and|\s*,|\s*$)",
            
            # Filipino patterns - handle both uppercase and lowercase names
            r"ako si ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+at|\s*,|\s*$)",
            r"anak ko si ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+at|\s*,|\s*$)",
            r"pangalan (?:niya|niya) ay ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+at|\s*,|\s*$)",
            
            # Aklanon patterns - handle both uppercase and lowercase names
            r"ngaean ko si ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+at|\s*,|\s*$)",
            r"ngaean ko ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+at|\s*,|\s*$)",
            r"ngaean si ([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+at|\s*,|\s*$)"
        ]
    
    def _build_date_patterns(self) -> List[str]:
        """Build patterns for date/time extraction"""
        return [
            # Enrollment dates
            r"(\d{1,2}\/\d{1,2}\/\d{4})", r"(\d{1,2}-\d{1,2}-\d{4})",
            r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})",
            r"(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)",
            
            # Filipino months
            r"(enero|pebrero|marso|abril|mayo|hunyo|hulyo|agosto|setyembre|oktubre|nobyembre|disyembre)\s+(\d{1,2})",
            
            # Relative dates
            r"(next week|next month|tomorrow|today|yesterday)",
            r"(sa susunod na linggo|bukas|ngayon|kahapon)"
        ]
    
    def _build_contact_patterns(self) -> List[str]:
        """Build patterns for contact information"""
        return [
            # Phone numbers
            r"(\+63\d{10})", r"(09\d{9})", r"(\d{3}-\d{3}-\d{4})",
            r"(\d{4}-\d{3}-\d{4})", r"(\(\d{3}\)\s*\d{3}-\d{4})",
            
            # Email addresses
            r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
        ]
    
    def _build_school_terminology(self) -> List[str]:
        """Build school-specific terminology patterns"""
        return [
            # School facilities
            "library", "cafeteria", "gym", "gymnasium", "playground", "computer lab",
            "science lab", "clinic", "principal's office", "teacher's lounge",
            
            # School activities  
            "enrollment", "registration", "orientation", "graduation", "field trip",
            "parent-teacher conference", "school fair", "sports day",
            
            # Academic terms
            "semester", "quarter", "grading period", "report card", "transcript",
            "curriculum", "lesson plan", "homework", "assignment", "project"
        ]
    
    def _extract_person_names(self, text: str, text_lower: str, intent_context: str = None) -> List[ExtractedEntity]:
        """Extract person names with context awareness and intent-based filtering"""
        entities = []
        
        # 🚨 CRITICAL FIX: Skip name extraction for location/facilities inquiries
        # These intents often contain question words that shouldn't be names
        if intent_context in ['location_inquiry', 'facilities_inquiry']:
            # Check if this looks like a question (contains question words)
            question_indicators = ['diin', 'saan', 'where', 'what', 'how', 'when', 'why', 'which']
            if any(indicator in text_lower for indicator in question_indicators):
                logger.info(f"🔍 Skipping name extraction for {intent_context} with question indicators")
                return entities
        
        for pattern in self.name_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                
                # Clean the name (remove common prefixes)
                name = self._clean_extracted_name(name)
                
                # Validate name (exclude common false positives)
                if self._is_valid_name(name):
                    # Determine name type based on context
                    name_type = self._classify_name_type(text_lower, name.lower())
                    
                    entity = ExtractedEntity(
                        entity_type=name_type,
                        value=name.title(),
                        confidence=self._calculate_name_confidence(name, text_lower),
                        start_pos=match.start(1),
                        end_pos=match.end(1),
                        context=text[max(0, match.start()-20):match.end()+20]
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_grade_levels(self, text: str, text_lower: str) -> List[ExtractedEntity]:
        """Extract grade level information"""
        entities = []
        
        # Numeric grades
        for pattern in self.grade_patterns["numeric"]:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                grade_num = match.group(1)
                if grade_num.isdigit() and 1 <= int(grade_num) <= 12:
                    entity = ExtractedEntity(
                        entity_type="grade_level",
                        value=f"Grade {grade_num}",
                        confidence=0.9,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=text[max(0, match.start()-15):match.end()+15]
                    )
                    entities.append(entity)
        
        # Written grades (kindergarten, first grade, etc.)
        for pattern in self.grade_patterns["written"]:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                grade_text = match.group(1)
                normalized_grade = self._normalize_grade_level(grade_text)
                if normalized_grade:
                    entity = ExtractedEntity(
                        entity_type="grade_level",
                        value=normalized_grade,
                        confidence=0.85,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=text[max(0, match.start()-15):match.end()+15]
                    )
                    entities.append(entity)
        
        # Filipino grades (ikalimang baitang, etc.)
        for pattern in self.grade_patterns["filipino"]:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                grade_text = match.group(1)
                normalized_grade = self._normalize_filipino_grade(grade_text)
                if normalized_grade:
                    entity = ExtractedEntity(
                        entity_type="grade_level",
                        value=normalized_grade,
                        confidence=0.9,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=text[max(0, match.start()-15):match.end()+15]
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_subjects(self, text: str, text_lower: str) -> List[ExtractedEntity]:
        """Extract academic subjects using word boundary matching with validation"""
        entities = []
        
        for subject in self.subject_patterns:
            # Use word boundary matching to avoid false positives
            import re
            pattern = r'\b' + re.escape(subject) + r'\b'
            matches = re.finditer(pattern, text_lower)
            
            for match in matches:
                start_pos = match.start()
                
                # Skip false positives for "pe" - only match if it's standalone or part of "physical education"
                if subject == "pe":
                    # Check if it's part of "person" - if so, skip this match
                    if start_pos + 2 < len(text_lower) and text_lower[start_pos:start_pos+6] == "person":
                        continue  # Skip this match as it's "person" not "PE"
                
                # Additional validation to prevent false positives
                if self._validate_subject_extraction(subject, text, start_pos, match.end()):
                    entity = ExtractedEntity(
                        entity_type="academic_subject",
                        value=subject.title(),
                        confidence=0.8,
                        start_pos=start_pos,
                        end_pos=match.end(),
                        context=text[max(0, start_pos-15):match.end()+15]
                    )
                    entities.append(entity)
        
        return entities
    
    def _validate_subject_extraction(self, subject: str, text: str, start_pos: int, end_pos: int) -> bool:
        """Validate that subject extraction makes sense in context"""
        
        # Get surrounding context
        context_start = max(0, start_pos - 10)
        context_end = min(len(text), end_pos + 10)
        context = text[context_start:context_end].lower()
        
        # Known problematic patterns
        problematic_patterns = {
            'art': [
                # Prevent "art" from being extracted from "start"
                r'start', r'starts', r'starting',
                # Prevent from other common words
                r'part', r'parts', r'party', r'parties',
                r'smart', r'chart', r'dart', r'heart'
            ],
            'math': [
                # Prevent from common words
                r'match', r'matches', r'matching',
                r'path', r'paths', r'paths'
            ],
            'science': [
                # Prevent from common words
                r'since', r'conscience'
            ],
            'pe': [
                # Prevent from person-related words
                r'person', r'people', r'personal'
            ]
        }
        
        if subject in problematic_patterns:
            for pattern in problematic_patterns[subject]:
                if re.search(pattern, context):
                    return False
        
        # Additional context validation
        # If subject appears in a time-related context, be more careful
        time_contexts = ['time', 'when', 'start', 'end', 'begin', 'finish']
        if any(time_word in context for time_word in time_contexts):
            # For academic subjects, require class/subject context
            class_contexts = ['class', 'subject', 'course', 'lesson', 'period']
            if not any(class_word in context for class_word in class_contexts):
                return False
        
        return True
    
    def _extract_dates(self, text: str, text_lower: str) -> List[ExtractedEntity]:
        """Extract date and time information"""
        entities = []
        
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                date_text = match.group(0)
                parsed_date = self._parse_date(date_text)
                
                if parsed_date:
                    entity = ExtractedEntity(
                        entity_type="date",
                        value=parsed_date,
                        confidence=0.85,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=text[max(0, match.start()-15):match.end()+15]
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_contact_info(self, text: str, text_lower: str) -> List[ExtractedEntity]:
        """Extract contact information"""
        entities = []
        
        for pattern in self.contact_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                contact_value = match.group(1)
                contact_type = "phone_number" if any(c.isdigit() for c in contact_value) else "email"
                
                entity = ExtractedEntity(
                    entity_type=contact_type,
                    value=contact_value,
                    confidence=0.95,
                    start_pos=match.start(1),
                    end_pos=match.end(1),
                    context=text[max(0, match.start()-10):match.end()+10]
                )
                entities.append(entity)
        
        return entities
    
    def _extract_school_terms(self, text: str, text_lower: str) -> List[ExtractedEntity]:
        """Extract school-specific terminology"""
        entities = []
        
        for term in self.school_terms:
            if term in text_lower:
                start_pos = text_lower.find(term)
                entity = ExtractedEntity(
                    entity_type="school_term",
                    value=term.title(),
                    confidence=0.7,
                    start_pos=start_pos,
                    end_pos=start_pos + len(term),
                    context=text[max(0, start_pos-15):start_pos+len(term)+15]
                )
                entities.append(entity)
        
        return entities
    
    def _extract_ages(self, text: str, text_lower: str) -> List[ExtractedEntity]:
        """Extract age information"""
        entities = []
        
        age_patterns = [
            r"(\d+)\s*years?\s*old", r"age\s*(\d+)", r"(\d+)\s*(?:y/o|yo)",
            r"(\d+)\s*taon", r"edad\s*(\d+)"
        ]
        
        for pattern in age_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                age = match.group(1)
                if age.isdigit() and 3 <= int(age) <= 18:  # Reasonable age range for students
                    entity = ExtractedEntity(
                        entity_type="age",
                        value=f"{age} years old",
                        confidence=0.9,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=text[max(0, match.start()-15):match.end()+15]
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_staff_roles(self, text: str, text_lower: str) -> List[ExtractedEntity]:
        """Extract staff roles and administrative positions"""
        entities = []
        
        # Staff role patterns with English and Filipino terms
        staff_role_patterns = {
            "principal": {
                "patterns": [
                    r"(?:school\s+)?(?:head|principal|director)",
                    r"(?:head\s+)?(?:principal|headmaster|headmistress)",
                    r"(?:school\s+)?(?:administrator|administration)",
                    r"punong\s+(?:guro|teacher|ng\s+paaralan)(?:\s|$)",
                    r"(?:head\s+)?(?:ng\s+paaralan|sa\s+paaralan)",
                    r"(?:principal|direktor|administrador)",
                    r"in\s+charge(?:\s+of)?",
                    r"(?:who\s+)?(?:runs|manages)\s+(?:the\s+)?school"
                ],
                "confidence": 0.95
            },
            "teacher": {
                "patterns": [
                    r"(?:class\s+)?(?:teacher|instructor|educator)",
                    r"(?:guro|maestro|maestra)(?!\s+(?:ng\s+paaralan|sa\s+paaralan|ng\s+eskwela))",
                    r"(?:grade\s+\d+\s+)?teacher",
                    r"(?:subject\s+)?teacher",
                    r"sino\s+ang\s+(?:guro|teacher)",
                    r"(?:adviser|advisor)",
                    r"(?:homeroom\s+)?teacher",
                    r"guro\s+(?:para\s+sa|ng|sa)\s+(?:ikatlong|ikalimang|unang|ikalawang|ikaapat|ikaanim)\s+baitang"
                ],
                "confidence": 0.90
            },
            "guidance": {
                "patterns": [
                    r"(?:guidance\s+)?(?:counselor|counsellor)",
                    r"guidance\s+(?:office|teacher)",
                    r"school\s+psychologist"
                ],
                "confidence": 0.85
            },
            "nurse": {
                "patterns": [
                    r"(?:school\s+)?nurse",
                    r"clinic\s+(?:staff|nurse)",
                    r"health\s+(?:officer|personnel)"
                ],
                "confidence": 0.85
            },
            "secretary": {
                "patterns": [
                    r"(?:school\s+)?(?:secretary|clerk)",
                    r"(?:administrative\s+)?(?:assistant|staff)",
                    r"office\s+(?:staff|personnel)"
                ],
                "confidence": 0.80
            }
        }
        
        for role_type, role_info in staff_role_patterns.items():
            for pattern in role_info["patterns"]:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    entity = ExtractedEntity(
                        entity_type="staff_role",
                        value=role_type,
                        confidence=role_info["confidence"],
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=text[max(0, match.start()-10):match.end()+10]
                    )
                    entities.append(entity)
        
        return entities
    
    def _clean_extracted_name(self, name: str) -> str:
        """Clean extracted name by removing common prefixes and suffixes"""
        # Remove common Filipino/Aklanon prefixes
        prefixes_to_remove = ["si ", "ang ", "ng ", "sa ", "kay ", "ni "]
        
        name_lower = name.lower().strip()
        for prefix in prefixes_to_remove:
            if name_lower.startswith(prefix):
                name = name[len(prefix):].strip()
                break
        
        # Remove common suffixes
        suffixes_to_remove = [" ang", " nga", " na", " si"]
        for suffix in suffixes_to_remove:
            if name_lower.endswith(suffix):
                name = name[:-len(suffix)].strip()
                break
        
        return name.strip()
    
    def _is_valid_name(self, name: str) -> bool:
        """Validate if extracted text is likely a real name"""
        if not name or len(name) < 2:
            return False
        
        # 🚨 CRITICAL FIX: Expanded list of false positives to prevent common words being extracted as names
        false_positives = [
            # Common English words
            "super", "excited", "back", "again", "really", "very", "quite",
            "the", "and", "or", "but", "for", "with", "from", "about",
            "good", "great", "nice", "fine", "okay", "yes", "no",
            "interested", "in", "who", "what", "when", "where", "how",
            # Tagalog question words
            "sino", "ano", "saan", "kailan", "bakit", "paano",
            "this", "that", "these", "those", "all", "some", "many",
            # Common emotions and states
            "sad", "happy", "angry", "tired", "sick", "well", "fine", "ok",
            "excited", "nervous", "worried", "scared", "afraid", "confused",
            # Common question words and verbs
            "are", "is", "was", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "will", "would", "could", "should", "can", "may",
            "must", "shall", "might", "want", "need", "like", "love", "hate",
            # Common school-related words that shouldn't be names
            "school", "teacher", "student", "class", "grade", "principal", "head",
            "staff", "office", "library", "cafeteria", "gym", "playground",
            "enrollment", "admission", "registration", "application", "form",
            # Building and location names that shouldn't be person names
            "building", "administration", "administrasyon", "compound", "campus",
            "facility", "room", "hall", "center", "center", "area", "zone",
            "entrance", "exit", "door", "floor", "level", "ground", "first", "second",
            # Common Filipino/Aklanon words
            "ako", "si", "ang", "ng", "sa", "ko", "mo", "niya", "namin", "ninyo", "nila",
            "kumusta", "kamusta", "salamat", "magandang", "maayong", "paaralan", "eskwelahan",
            "baitang", "klase", "guro", "maestro", "direktor", "administrador",
            # Common articles and prepositions
            "a", "an", "the", "of", "to", "in", "on", "at", "by", "for", "with",
            "up", "down", "out", "off", "over", "under", "through", "during",
            # Common adjectives
            "big", "small", "old", "new", "young", "old", "hot", "cold", "warm", "cool",
            "fast", "slow", "high", "low", "long", "short", "wide", "narrow",
            "clean", "dirty", "safe", "dangerous", "easy", "hard", "simple", "complex",
            # Common nouns that aren't names
            "time", "day", "night", "morning", "afternoon", "evening", "week", "month", "year",
            "house", "home", "car", "bus", "train", "plane", "book", "paper", "pen", "pencil",
            "food", "water", "money", "work", "job", "family", "friend", "child", "parent",
            # 🚨 NEW: Common abbreviations and contractions that shouldn't be names
            "tho", "though", "btw", "lol", "omg", "wtf", "jk", "tbh", "imo", "fyi",
            "etc", "vs", "aka", "asap", "rsvp", "p.s", "p.s.", "n/a", "tba", "tbd"
        ]
        
        
        # Check for name-like characteristics
        words = name.split()
        for word in words:
            if word.lower() in false_positives:
                return False
            # Names should be mostly alphabetic
            if not word.replace("'", "").replace("-", "").isalpha():
                return False
            # 🚨 FIX: Names should be at least 2 characters long
            if len(word) < 2:
                return False
            # 🚨 FIX: Names shouldn't be all lowercase common words
            if word.islower() and word in false_positives:
                return False
        
        # 🚨 FIX: Check for building/location names that shouldn't be person names
        building_indicators = ["building", "administration", "administrasyon", "compound", "campus", "facility", "room", "hall", "center", "area", "zone"]
        if any(indicator in name.lower() for indicator in building_indicators):
            return False
        
        # 🚨 FIX: Additional validation - names should have at least one character that's not a common word
        # This prevents single common words from being extracted as names
        if len(words) == 1 and words[0].lower() in false_positives:
            return False
        
        # 🚨 NEW: Smart validation for multi-word names
        # If any word in the name is a common abbreviation or contraction, reject the whole name
        for word in words:
            if word.lower() in ["tho", "though", "btw", "lol", "omg", "wtf", "jk", "tbh", "imo", "fyi"]:
                return False
        
        return True
    
    def _classify_name_type(self, text_lower: str, name_lower: str) -> str:
        """Classify the type of name based on context"""
        
        # Check for child/family context
        child_indicators = ["son", "daughter", "child", "kid", "anak"]
        if any(indicator in text_lower for indicator in child_indicators):
            return "child_name"
        
        # Check for staff context
        staff_indicators = ["teacher", "principal", "staff", "guro", "maestro"]
        if any(indicator in text_lower for indicator in staff_indicators):
            return "staff_name"
        
        # Default to person name
        return "person_name"
    
    def _calculate_name_confidence(self, name: str, text_lower: str) -> float:
        """Calculate confidence score for name extraction"""
        confidence = 0.8  # Base confidence
        
        # Boost confidence for proper introductions
        if "my name is" in text_lower or "ako si" in text_lower:
            confidence += 0.15
        
        # Boost for family context
        if any(word in text_lower for word in ["son", "daughter", "child", "anak"]):
            confidence += 0.1
        
        # Reduce confidence for very short names
        if len(name) <= 3:
            confidence -= 0.2
        
        return min(confidence, 0.95)
    
    def _normalize_grade_level(self, grade_text: str) -> Optional[str]:
        """Normalize grade level text to standard format"""
        grade_mapping = {
            "kindergarten": "Kindergarten", "kinder": "Kindergarten", "prep": "Kindergarten",
            "first": "Grade 1", "second": "Grade 2", "third": "Grade 3",
            "fourth": "Grade 4", "fifth": "Grade 5", "sixth": "Grade 6",
            "one": "Grade 1", "two": "Grade 2", "three": "Grade 3",
            "four": "Grade 4", "five": "Grade 5", "six": "Grade 6"
        }
        
        return grade_mapping.get(grade_text.lower())
    
    def _normalize_filipino_grade(self, grade_text: str) -> Optional[str]:
        """Normalize Filipino grade level text to standard format"""
        filipino_grade_mapping = {
            # Ordinal forms
            "unang": "Grade 1", "ikalawang": "Grade 2", "ikatlong": "Grade 3", "ikatatlong": "Grade 3",
            "ikaapat": "Grade 4", "ikalimang": "Grade 5", "ikaanim": "Grade 6",
            # Cardinal forms
            "isa": "Grade 1", "dalawa": "Grade 2", "tatlo": "Grade 3",
            "apat": "Grade 4", "lima": "Grade 5", "anim": "Grade 6",
            # Alternative forms
            "una": "Grade 1", "pangalawa": "Grade 2", "pangatlo": "Grade 3", "pang-apat": "Grade 4",
            "panglima": "Grade 5", "panganim": "Grade 6",
            # Additional variations
            "ikatlong": "Grade 3", "ikatatlong": "Grade 3"
        }
        
        return filipino_grade_mapping.get(grade_text.lower())
    
    def _parse_date(self, date_text: str) -> Optional[str]:
        """Parse and normalize date text"""
        # This is a simplified implementation
        # In production, you'd use more sophisticated date parsing
        
        # Handle relative dates
        relative_dates = {
            "today": datetime.now().strftime("%Y-%m-%d"),
            "tomorrow": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "yesterday": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "ngayon": datetime.now().strftime("%Y-%m-%d"),
            "bukas": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        }
        
        if date_text in relative_dates:
            return relative_dates[date_text]
        
        # Return original text for now (could be enhanced with dateutil)
        return date_text
    
    def _resolve_entity_conflicts(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Resolve overlapping entities by keeping highest confidence"""
        if not entities:
            return entities
        
        # Sort by start position
        entities.sort(key=lambda e: e.start_pos)
        
        resolved = []
        for entity in entities:
            # Check for overlaps with already resolved entities
            overlaps = False
            for resolved_entity in resolved:
                if (entity.start_pos < resolved_entity.end_pos and 
                    entity.end_pos > resolved_entity.start_pos):
                    # Overlap detected - keep the one with higher confidence
                    if entity.confidence > resolved_entity.confidence:
                        resolved.remove(resolved_entity)
                        resolved.append(entity)
                    overlaps = True
                    break
            
            if not overlaps:
                resolved.append(entity)
        
        return sorted(resolved, key=lambda e: e.confidence, reverse=True)
    
    def _extract_entity_relationships(self, text: str, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Extract relationships between entities"""
        relationship_entities = []
        
        try:
            # Look for relationship patterns
            relationship_patterns = [
                # Parent-child relationships
                (r'(\w+)\s+(child|anak|son|daughter)', 'PARENT_CHILD'),
                (r'(my|my child|anak ko|my son|my daughter)\s+(\w+)', 'PARENT_CHILD'),
                
                # Teacher-student relationships
                (r'(\w+)\s+(teacher|guro|instructor)', 'TEACHER_STUDENT'),
                (r'(teacher|guro|instructor)\s+(\w+)', 'TEACHER_STUDENT'),
                
                # Grade-subject relationships
                (r'(grade|level)\s+(\d+)\s+(math|science|english|filipino)', 'GRADE_SUBJECT'),
                (r'(\d+)\s+(math|science|english|filipino)', 'GRADE_SUBJECT'),
                
                # Time-activity relationships
                (r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(morning|afternoon|evening)', 'TIME_ACTIVITY'),
                (r'(\d+):(\d+)\s+(am|pm)', 'TIME_ACTIVITY'),
                
                # Location-activity relationships
                (r'(library|gym|cafeteria|office|classroom)\s+(visit|go|meet)', 'LOCATION_ACTIVITY'),
                (r'(visit|go|meet)\s+(library|gym|cafeteria|office|classroom)', 'LOCATION_ACTIVITY')
            ]
            
            for pattern, relationship_type in relationship_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    relationship_entities.append(ExtractedEntity(
                        entity_type=relationship_type,
                        value=match.group(),
                        confidence=0.8,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=match.group()
                    ))
            
            logger.info(f"🔗 Extracted {len(relationship_entities)} relationship entities")
            return relationship_entities
            
        except Exception as e:
            logger.error(f"Relationship extraction failed: {e}")
            return []
    
    def _extract_context_entities(self, text: str, entities: List[ExtractedEntity], 
                                 intent_context: str = None) -> List[ExtractedEntity]:
        """Extract entities based on context and intent"""
        context_entities = []
        
        try:
            # Context-aware extraction based on intent
            if intent_context:
                if 'enrollment' in intent_context.lower():
                    # Look for enrollment-related entities
                    enrollment_patterns = [
                        (r'(application|form|document|requirement)', 'ENROLLMENT_ITEM'),
                        (r'(deadline|due date|cutoff)', 'ENROLLMENT_DEADLINE'),
                        (r'(fee|payment|cost|tuition)', 'ENROLLMENT_FEE')
                    ]
                    
                    for pattern, entity_type in enrollment_patterns:
                        matches = re.finditer(pattern, text, re.IGNORECASE)
                        for match in matches:
                            context_entities.append(ExtractedEntity(
                                entity_type=entity_type,
                                value=match.group(),
                                confidence=0.9,
                                start_pos=match.start(),
                                end_pos=match.end(),
                                context=match.group()
                            ))
                
                elif 'schedule' in intent_context.lower():
                    # Look for schedule-related entities
                    schedule_patterns = [
                        (r'(class|period|session|meeting)', 'SCHEDULE_ITEM'),
                        (r'(start|end|begin|finish)', 'SCHEDULE_TIME'),
                        (r'(room|location|place)', 'SCHEDULE_LOCATION')
                    ]
                    
                    for pattern, entity_type in schedule_patterns:
                        matches = re.finditer(pattern, text, re.IGNORECASE)
                        for match in matches:
                            context_entities.append(ExtractedEntity(
                                entity_type=entity_type,
                                value=match.group(),
                                confidence=0.9,
                                start_pos=match.start(),
                                end_pos=match.end(),
                                context=match.group()
                            ))
            
            logger.info(f"🎯 Extracted {len(context_entities)} context entities")
            return context_entities
            
        except Exception as e:
            logger.error(f"Context entity extraction failed: {e}")
            return []
    
    def _detect_entity_relationships(self, entities: List[ExtractedEntity], text: str) -> List[ExtractedEntity]:
        """Detect relationships between entities"""
        try:
            relationship_count = 0
            
            # Add relationship metadata to entities
            for i, entity1 in enumerate(entities):
                for j, entity2 in enumerate(entities[i+1:], i+1):
                    # Check if entities are related
                    relationship = self._analyze_entity_relationship(entity1, entity2, text)
                    if relationship:
                        # Add relationship information to entities
                        if not hasattr(entity1, 'relationships'):
                            entity1.relationships = []
                        if not hasattr(entity2, 'relationships'):
                            entity2.relationships = []
                        
                        entity1.relationships.append({
                            'entity': entity2,
                            'relationship': relationship,
                            'confidence': relationship.get('confidence', 0.5)
                        })
                        entity2.relationships.append({
                            'entity': entity1,
                            'relationship': relationship,
                            'confidence': relationship.get('confidence', 0.5)
                        })
                        
                        relationship_count += 1
                        logger.info(f"🔗 Detected relationship: {relationship['type']} between {entity1.value} and {entity2.value} (confidence: {relationship.get('confidence', 0.5):.2f})")
            
            # Also try to detect relationships using pattern matching
            self._detect_additional_relationships(entities, text)
            
            logger.info(f"🔗 Detected {relationship_count} relationships between {len(entities)} entities")
            return entities
            
        except Exception as e:
            logger.error(f"Entity relationship detection failed: {e}")
            return entities
    
    def _detect_additional_relationships(self, entities: List[ExtractedEntity], text: str) -> None:
        """Detect additional relationships using pattern matching"""
        try:
            text_lower = text.lower()
            additional_relationships = 0
            
            # Look for specific patterns that might indicate relationships
            for i, entity1 in enumerate(entities):
                for j, entity2 in enumerate(entities):
                    if i >= j:  # Avoid duplicates
                        continue
                    
                    # Check if entities are close in text
                    distance = abs(entity1.start_pos - entity2.start_pos)
                    if distance > 150:  # Skip if too far apart
                        continue
                    
                    # Get context between entities
                    start_pos = min(entity1.start_pos, entity2.start_pos)
                    end_pos = max(entity1.end_pos, entity2.end_pos)
                    context = text[start_pos:end_pos].lower()
                    
                    # Check for specific relationship patterns
                    relationship = self._detect_specific_relationships(entity1, entity2, context, text)
                    if relationship:
                        # Add relationship if not already exists
                        if not hasattr(entity1, 'relationships'):
                            entity1.relationships = []
                        if not hasattr(entity2, 'relationships'):
                            entity2.relationships = []
                        
                        # Check if relationship already exists
                        existing = any(rel['entity'] == entity2 for rel in entity1.relationships)
                        if not existing:
                            entity1.relationships.append({
                                'entity': entity2,
                                'relationship': relationship,
                                'confidence': relationship.get('confidence', 0.5)
                            })
                            entity2.relationships.append({
                                'entity': entity1,
                                'relationship': relationship,
                                'confidence': relationship.get('confidence', 0.5)
                            })
                            
                            additional_relationships += 1
                            logger.info(f"🔗 Additional relationship detected: {relationship['type']} between {entity1.value} and {entity2.value} (confidence: {relationship.get('confidence', 0.5):.2f})")
            
            if additional_relationships > 0:
                logger.info(f"🔗 Detected {additional_relationships} additional relationships through pattern matching")
            
        except Exception as e:
            logger.error(f"Additional relationship detection failed: {e}")
    
    def _analyze_entity_relationship(self, entity1: ExtractedEntity, entity2: ExtractedEntity, text: str) -> Optional[Dict]:
        """Enhanced entity relationship analysis with improved algorithms"""
        try:
            # Check proximity in text - more lenient threshold
            distance = abs(entity1.start_pos - entity2.start_pos)
            if distance > 200:  # Increased threshold for better detection
                return None
            
            # Get context between entities
            start_pos = min(entity1.start_pos, entity2.start_pos)
            end_pos = max(entity1.end_pos, entity2.end_pos)
            context = text[start_pos:end_pos].lower()
            
            # Enhanced relationship patterns with context analysis
            relationship_patterns = [
                # Parent-child relationships
                (['PERSON', 'GRADE'], 'PARENT_CHILD', 0.95),
                (['PERSON', 'PERSON'], 'PARENT_CHILD', 0.85),
                (['PERSON', 'SUBJECT'], 'PARENT_CHILD', 0.75),
                (['person_name', 'grade_level'], 'PARENT_CHILD', 0.95),
                (['person_name', 'academic_subject'], 'PARENT_CHILD', 0.85),
                
                # Teacher-student relationships
                (['PERSON', 'SUBJECT'], 'TEACHER_STUDENT', 0.9),
                (['PERSON', 'GRADE'], 'TEACHER_STUDENT', 0.85),
                (['PERSON', 'ACTIVITY'], 'TEACHER_STUDENT', 0.8),
                (['person_name', 'academic_subject'], 'TEACHER_STUDENT', 0.9),
                (['person_name', 'grade_level'], 'TEACHER_STUDENT', 0.85),
                (['staff_role', 'academic_subject'], 'TEACHER_STUDENT', 0.9),
                (['staff_role', 'grade_level'], 'TEACHER_STUDENT', 0.85),
                
                # Grade-subject relationships
                (['GRADE', 'SUBJECT'], 'GRADE_SUBJECT', 0.95),
                (['GRADE', 'ACTIVITY'], 'GRADE_ACTIVITY', 0.9),
                (['GRADE', 'PERSON'], 'GRADE_STUDENT', 0.85),
                (['grade_level', 'academic_subject'], 'GRADE_SUBJECT', 0.95),
                (['grade_level', 'person_name'], 'GRADE_STUDENT', 0.85),
                
                # Time-activity relationships
                (['TIME', 'ACTIVITY'], 'TIME_ACTIVITY', 0.95),
                (['TIME', 'LOCATION'], 'TIME_LOCATION', 0.9),
                (['TIME', 'PERSON'], 'TIME_PERSON', 0.8),
                (['TIME_ACTIVITY', 'grade_level'], 'TIME_ACTIVITY', 0.95),
                (['TIME_ACTIVITY', 'academic_subject'], 'TIME_ACTIVITY', 0.9),
                
                # Location-activity relationships
                (['LOCATION', 'ACTIVITY'], 'LOCATION_ACTIVITY', 0.95),
                (['LOCATION', 'TIME'], 'LOCATION_TIME', 0.9),
                (['LOCATION', 'PERSON'], 'LOCATION_PERSON', 0.8),
                (['school_term', 'grade_level'], 'LOCATION_ACTIVITY', 0.9),
                (['school_term', 'TIME_ACTIVITY'], 'LOCATION_TIME', 0.9),
                
                # Staff-activity relationships
                (['PERSON', 'ACTIVITY'], 'STAFF_ACTIVITY', 0.9),
                (['PERSON', 'TIME'], 'STAFF_TIME', 0.85),
                (['PERSON', 'LOCATION'], 'STAFF_LOCATION', 0.8),
                (['staff_role', 'TIME_ACTIVITY'], 'STAFF_ACTIVITY', 0.9),
                (['person_name', 'TIME_ACTIVITY'], 'STAFF_ACTIVITY', 0.85)
            ]
            
            # Check for matching patterns
            for entity_types, relationship_type, base_confidence in relationship_patterns:
                if (entity1.entity_type in entity_types and entity2.entity_type in entity_types):
                    # Calculate enhanced confidence based on context
                    confidence = self._calculate_relationship_confidence(
                        entity1, entity2, context, relationship_type, base_confidence
                    )
                    
                    if confidence > 0.5:  # Lowered threshold for better detection
                        return {
                            'type': relationship_type,
                            'description': f"{entity1.value} - {entity2.value} ({relationship_type})",
                            'confidence': confidence,
                            'context': context,
                            'distance': distance
                        }
            
            # Additional pattern matching for specific test cases
            return self._detect_specific_relationships(entity1, entity2, context, text)
            
        except Exception as e:
            logger.error(f"Enhanced entity relationship analysis failed: {e}")
            return None
    
    def _detect_specific_relationships(self, entity1: ExtractedEntity, entity2: ExtractedEntity, 
                                      context: str, text: str) -> Optional[Dict]:
        """Detect specific relationship patterns for test cases"""
        try:
            # Pattern matching for specific test cases
            text_lower = text.lower()
            
            # Parent-child patterns
            if any(word in text_lower for word in ['my child', 'my son', 'my daughter', 'child', 'student']):
                if (entity1.entity_type in ['PERSON', 'person_name'] and 
                    entity2.entity_type in ['GRADE', 'SUBJECT', 'PERSON', 'grade_level', 'academic_subject']):
                    return {
                        'type': 'PARENT_CHILD',
                        'description': f"{entity1.value} - {entity2.value} (PARENT_CHILD)",
                        'confidence': 0.9,
                        'context': context,
                        'distance': abs(entity1.start_pos - entity2.start_pos)
                    }
            
            # Teacher-student patterns
            if any(word in text_lower for word in ['teaches', 'teacher', 'instructor']):
                if (entity1.entity_type in ['PERSON', 'person_name', 'staff_role'] and 
                    entity2.entity_type in ['SUBJECT', 'GRADE', 'ACTIVITY', 'academic_subject', 'grade_level']):
                    return {
                        'type': 'TEACHER_STUDENT',
                        'description': f"{entity1.value} - {entity2.value} (TEACHER_STUDENT)",
                        'confidence': 0.9,
                        'context': context,
                        'distance': abs(entity1.start_pos - entity2.start_pos)
                    }
            
            # Grade-subject patterns
            if any(word in text_lower for word in ['grade', 'level', 'class']):
                if (entity1.entity_type in ['GRADE', 'grade_level'] and 
                    entity2.entity_type in ['SUBJECT', 'ACTIVITY', 'academic_subject']):
                    return {
                        'type': 'GRADE_SUBJECT',
                        'description': f"{entity1.value} - {entity2.value} (GRADE_SUBJECT)",
                        'confidence': 0.9,
                        'context': context,
                        'distance': abs(entity1.start_pos - entity2.start_pos)
                    }
            
            # Time-activity patterns
            if any(word in text_lower for word in ['morning', 'afternoon', 'evening', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday']):
                if (entity1.entity_type in ['TIME', 'TIME_ACTIVITY'] and 
                    entity2.entity_type in ['ACTIVITY', 'LOCATION', 'grade_level', 'academic_subject']):
                    return {
                        'type': 'TIME_ACTIVITY',
                        'description': f"{entity1.value} - {entity2.value} (TIME_ACTIVITY)",
                        'confidence': 0.9,
                        'context': context,
                        'distance': abs(entity1.start_pos - entity2.start_pos)
                    }
            
            # Location-activity patterns
            if any(word in text_lower for word in ['library', 'gym', 'cafeteria', 'office', 'classroom']):
                if (entity1.entity_type in ['LOCATION', 'school_term'] and 
                    entity2.entity_type in ['ACTIVITY', 'TIME', 'TIME_ACTIVITY', 'grade_level']):
                    return {
                        'type': 'LOCATION_ACTIVITY',
                        'description': f"{entity1.value} - {entity2.value} (LOCATION_ACTIVITY)",
                        'confidence': 0.9,
                        'context': context,
                        'distance': abs(entity1.start_pos - entity2.start_pos)
                    }
            
            # Staff-activity patterns
            if any(word in text_lower for word in ['principal', 'director', 'meet', 'meeting', 'will']):
                if (entity1.entity_type in ['PERSON', 'person_name', 'staff_role'] and 
                    entity2.entity_type in ['ACTIVITY', 'TIME', 'LOCATION', 'TIME_ACTIVITY']):
                    return {
                        'type': 'STAFF_ACTIVITY',
                        'description': f"{entity1.value} - {entity2.value} (STAFF_ACTIVITY)",
                        'confidence': 0.9,
                        'context': context,
                        'distance': abs(entity1.start_pos - entity2.start_pos)
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Specific relationship detection failed: {e}")
            return None

    def _calculate_relationship_confidence(self, entity1: ExtractedEntity, entity2: ExtractedEntity, 
                                         context: str, relationship_type: str, base_confidence: float) -> float:
        """Calculate enhanced confidence for entity relationships"""
        try:
            confidence = base_confidence
            
            # Boost confidence based on context keywords
            context_boosters = {
                'PARENT_CHILD': ['my', 'child', 'son', 'daughter', 'student', 'is', 'in', 'needs', 'help'],
                'TEACHER_STUDENT': ['teaches', 'teaching', 'instructor', 'teacher', 'class', 'subject'],
                'GRADE_SUBJECT': ['grade', 'level', 'class', 'for', 'in', 'studying', 'students'],
                'TIME_ACTIVITY': ['morning', 'afternoon', 'evening', 'at', 'on', 'when', 'open'],
                'LOCATION_ACTIVITY': ['in', 'at', 'visit', 'go', 'meet', 'open', 'library', 'gym'],
                'STAFF_ACTIVITY': ['meets', 'meeting', 'will', 'principal', 'director', 'parents']
            }
            
            if relationship_type in context_boosters:
                boosters = context_boosters[relationship_type]
                matches = sum(1 for booster in boosters if booster in context)
                confidence += matches * 0.15  # Increased boost for each matching keyword
            
            # Boost confidence for closer entities
            distance = abs(entity1.start_pos - entity2.start_pos)
            if distance < 30:
                confidence += 0.2
            elif distance < 60:
                confidence += 0.15
            elif distance < 100:
                confidence += 0.1
            
            # Boost confidence for higher entity confidence
            avg_entity_confidence = (entity1.confidence + entity2.confidence) / 2
            confidence += avg_entity_confidence * 0.2  # Increased boost
            
            # Additional context-based boosts
            if any(word in context for word in ['is', 'in', 'for', 'with', 'on', 'at']):
                confidence += 0.1
            
            return min(confidence, 0.98)  # Cap at 98%
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return base_confidence

# 🚨 CRITICAL FIX: Initialize NLTK immediately when module is imported
# This ensures NLTK is ready before any entity extraction happens
_initialize_nltk()