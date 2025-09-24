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

# Point NLTK to the folder where Render installed the data
nltk_data_path = "/opt/render/nltk_data"
os.environ["NLTK_DATA"] = nltk_data_path
nltk.data.path.append(nltk_data_path)

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import calendar

# NLTK will be imported lazily to avoid deployment issues
NLTK_AVAILABLE = False
NLTK_INITIALIZED = False

def _initialize_nltk():
    """Initialize NLTK safely with error handling"""
    global NLTK_AVAILABLE, NLTK_INITIALIZED
    
    if NLTK_INITIALIZED:
        return NLTK_AVAILABLE
    
    try:
        import nltk
        from nltk.tokenize import word_tokenize, sent_tokenize
        from nltk.corpus import stopwords
        from nltk.tag import pos_tag
        from nltk.chunk import ne_chunk
        from nltk.tree import Tree
        
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

# Import the new multilingual NLP engine
try:
    from multilingual_nlp import multilingual_nlp
    MULTILINGUAL_NLP_AVAILABLE = True
except ImportError:
    MULTILINGUAL_NLP_AVAILABLE = False
    print("⚠️ Multilingual NLP engine not available - using fallback entity extraction")

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

class AdvancedEntityExtractor:
    """
    Advanced entity extraction using NLP techniques and domain-specific patterns
    """
    
    def __init__(self):
        self.grade_patterns = self._build_grade_patterns()
        self.subject_patterns = self._build_subject_patterns()
        self.name_patterns = self._build_name_patterns()
        self.date_patterns = self._build_date_patterns()
        self.contact_patterns = self._build_contact_patterns()
        self.school_terms = self._build_school_terminology()
        
    def extract_entities(self, text: str, intent_context: str = None) -> List[ExtractedEntity]:
        """
        Extract all entities from the given text using rule-based patterns
        (Use extract_entities_async for semantic NLP extraction)
        
        Args:
            text: Input text to analyze
            intent_context: The detected intent to help with disambiguation
            
        Returns:
            List of extracted entities with confidence scores
        """
        entities = []
        text_lower = text.lower()
        
        # Extract different entity types using pattern matching
        entities.extend(self._extract_person_names(text, text_lower))
        entities.extend(self._extract_grade_levels(text, text_lower))
        entities.extend(self._extract_subjects(text, text_lower))
        entities.extend(self._extract_dates(text, text_lower))
        entities.extend(self._extract_contact_info(text, text_lower))
        entities.extend(self._extract_school_terms(text, text_lower))
        entities.extend(self._extract_ages(text, text_lower))
        entities.extend(self._extract_staff_roles(text, text_lower))
        
        # Enhanced extraction using NLTK
        nltk_entities = self._extract_entities_with_nltk(text)
        entities.extend(nltk_entities)
        
        # Sort by confidence and remove overlaps
        entities = self._resolve_entity_conflicts(entities)
        
        logger.info(f"🔍 Rule-based extracted {len(entities)} entities from: '{text[:50]}...'")
        for entity in entities:
            logger.info(f"   📍 {entity.entity_type}: '{entity.value}' (confidence: {entity.confidence:.2f})")
        
        return entities
    
    def _extract_entities_with_nltk(self, text: str) -> List[ExtractedEntity]:
        """Enhanced entity extraction using NLTK"""
        entities = []
        
        if not NLTK_AVAILABLE:
            return entities
        
        try:
            # Tokenize and tag the text
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            
            # Named Entity Recognition
            try:
                # Try to use NLTK's named entity chunker
                chunked = ne_chunk(pos_tags)
                
                for chunk in chunked:
                    if isinstance(chunk, Tree):
                        entity_type = chunk.label()
                        entity_text = ' '.join([token for token, pos in chunk.leaves()])
                        
                        # Map NLTK entity types to our types
                        if entity_type == 'PERSON':
                            entities.append(ExtractedEntity(
                                entity_type='person_name',
                                value=entity_text,
                                confidence=0.8,
                                start_pos=text.find(entity_text),
                                end_pos=text.find(entity_text) + len(entity_text)
                            ))
                        elif entity_type in ['GPE', 'LOCATION']:
                            entities.append(ExtractedEntity(
                                entity_type='location',
                                value=entity_text,
                                confidence=0.7,
                                start_pos=text.find(entity_text),
                                end_pos=text.find(entity_text) + len(entity_text)
                            ))
                        elif entity_type == 'ORGANIZATION':
                            entities.append(ExtractedEntity(
                                entity_type='organization',
                                value=entity_text,
                                confidence=0.7,
                                start_pos=text.find(entity_text),
                                end_pos=text.find(entity_text) + len(entity_text)
                            ))
            except Exception as e:
                logger.warning(f"NLTK NER failed: {e}")
            
            # Extract proper nouns using POS tagging
            proper_nouns = []
            for token, pos in pos_tags:
                if pos == 'NNP' and len(token) > 1:  # Proper noun
                    proper_nouns.append(token)
            
            # Check if proper nouns are likely person names
            for noun in proper_nouns:
                if noun.istitle() and len(noun) > 2:
                    # Simple heuristic: capitalized words that could be names
                    entities.append(ExtractedEntity(
                        entity_type='person_name',
                        value=noun,
                        confidence=0.6,
                        start_pos=text.find(noun),
                        end_pos=text.find(noun) + len(noun)
                    ))
            
            logger.info(f"🔍 NLTK extracted {len(entities)} entities")
            
        except Exception as e:
            logger.warning(f"NLTK entity extraction failed: {e}")
        
        return entities
    
    async def extract_entities_async(self, text: str, intent_context: str = None) -> List[ExtractedEntity]:
        """
        Async version of extract_entities for better performance with NLP models
        """
        entities = []
        
        # First, try semantic multilingual entity extraction if available
        if MULTILINGUAL_NLP_AVAILABLE:
            try:
                # Detect language first for better extraction
                lang_result = await multilingual_nlp.detect_language_semantic(text)
                language = lang_result.language
                
                # Extract entities using multilingual NER
                semantic_entities = await multilingual_nlp.extract_entities_multilingual(text, language)
                
                # Convert to our format
                for entity in semantic_entities:
                    entities.append(ExtractedEntity(
                        entity_type=entity.label.lower(),
                        value=entity.normalized_form or entity.text,
                        confidence=entity.confidence,
                        start_pos=entity.start,
                        end_pos=entity.end,
                        context=f"Language: {language}, Method: semantic"
                    ))
                
                logger.info(f"🔍 Semantic extraction found {len(entities)} entities")
                
            except Exception as e:
                logger.warning(f"⚠️ Semantic entity extraction failed: {e}, falling back to rule-based")
        
        # Add rule-based extraction for domain-specific entities
        text_lower = text.lower()
        
        # Extract different entity types using pattern matching
        entities.extend(self._extract_person_names(text, text_lower))
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
                r"(unang|ikalawang|ikatlong|ikaapat|ikalimang|ikaanim)\s*baitang",
                r"baitang\s*(isa|dalawa|tatlo|apat|lima|anim)"
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
    
    def _extract_person_names(self, text: str, text_lower: str) -> List[ExtractedEntity]:
        """Extract person names with context awareness"""
        entities = []
        
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
        
        return entities
    
    def _extract_subjects(self, text: str, text_lower: str) -> List[ExtractedEntity]:
        """Extract academic subjects"""
        entities = []
        
        for subject in self.subject_patterns:
            if subject in text_lower:
                start_pos = text_lower.find(subject)
                entity = ExtractedEntity(
                    entity_type="academic_subject",
                    value=subject.title(),
                    confidence=0.8,
                    start_pos=start_pos,
                    end_pos=start_pos + len(subject),
                    context=text[max(0, start_pos-15):start_pos+len(subject)+15]
                )
                entities.append(entity)
        
        return entities
    
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
                    r"(?:punong\s+)?(?:guro|teacher)",
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
                    r"(?:guro|maestro|maestra)",
                    r"(?:grade\s+\d+\s+)?teacher",
                    r"(?:subject\s+)?teacher"
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
        
        # Exclude common false positives
        false_positives = [
            "super", "excited", "back", "again", "really", "very", "quite",
            "the", "and", "or", "but", "for", "with", "from", "about",
            "good", "great", "nice", "fine", "okay", "yes", "no",
            "interested", "in", "who", "what", "when", "where", "how",
            "this", "that", "these", "those", "all", "some", "many"
        ]
        
        # Check for name-like characteristics
        words = name.split()
        for word in words:
            if word.lower() in false_positives:
                return False
            # Names should be mostly alphabetic
            if not word.replace("'", "").replace("-", "").isalpha():
                return False
            # Names should be valid (we'll capitalize them later)
            # Don't require capital letters since we handle both cases
        
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