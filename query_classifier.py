"""
Query Classification System for Structured Responses
==================================================

This module classifies queries to determine if they require structured responses
and identifies the appropriate response type and template to use.
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from structured_response import ResponseType

@dataclass
class QueryClassification:
    """Result of query classification."""
    needs_structured_response: bool
    response_type: Optional[ResponseType]
    confidence: float
    keywords: List[str]
    suggested_template: Optional[str]
    complexity_level: str  # simple, moderate, complex

class QueryClassifier:
    """Classifies queries to determine if they need structured responses."""
    
    def __init__(self):
        # ELEMENTARY SCHOOL CONTEXT ONLY - reject university queries
        self.university_patterns = [
            r"university", r"college", r"unibersidad", r"unibersity", r"degree", r"bachelor",
            r"master", r"graduate", r"undergraduate", r"transfer.*university", r"university.*transfer",
            r"thesis", r"dissertation", r"research.*program", r"academic.*research", 
            r"faculty.*directory", r"university.*faculty", r"graduate.*school",
            r"dormitory", r"residence.*hall", r"campus.*housing", r"tuition.*university",
            r"university.*tuition", r"college.*admission", r"university.*admission",
            r"higher.*education", r"tertiary.*education", r"post.*secondary"
        ]
        
        self.procedural_patterns = {
            # Elementary enrollment procedures ONLY (K-6)
            "enrollment": [
                r"how (do|to|can) (i|we) (enroll|register|apply)",
                r"how to (enroll|register|apply)",
                r"(enrollment|registration|application) (process|procedure|steps)",
                r"paano (mag-?enroll|mag-?register|mag-?apply)",
                r"(pag-?enroll|pag-?register|registration) process",
                r"ano ang (process|hakbang|steps) (sa|para sa|ng) (enrollment|registration)",
                r"enrollment requirements",
                r"admission process",
                r"admission requirements",
                r"(enroll|register).*requirements",
                r"apply.*school",
                r"kindergarten.*enroll",
                r"grade.*enroll",
                r"elementary.*enroll",
                r"(want|need) to enroll",
                r"enroll.*child",
                r"enroll.*kindergarten",
                r"what.*need.*do.*enroll",
                r"what.*do.*enroll",
                r"enroll.*my (child|son|daughter|kid)",
                r"(i|we) want.*enroll",
                r"what.*process.*enroll",
                r"what.*steps.*enroll"
            ],
            
            # Elementary school transfer procedures (between schools)
            "transfer": [
                r"transfer (process|procedure|requirements)",
                r"how (do|to|can) (i|we) transfer",
                r"how to transfer",
                r"transferee requirements",
                r"paano (mag-?transfer|ako mag-?transfer)",
                r"transfer.*school",
                r"change.*school",
                r"transfer.*elementary",
                r"elementary.*transfer"
            ],
            
            # Elementary graduation/completion certificates
            "graduation": [
                r"graduation (process|requirements|procedures)",
                r"completion (certificate|requirements)",
                r"graduation certificate",
                r"elementary.*graduation",
                r"completion.*elementary"
            ],
            
            # Elementary school document requests
            "documents": [
                r"(transcript|certificate|report card) (request|application)",
                r"how to (get|obtain|request) (transcript|certificate|report card)",
                r"document requirements",
                r"paano kumuha ng (transcript|certificate|report card)",
                r"school records",
                r"student records"
            ],
            
            # Elementary school financial information
            "financial": [
                r"(tuition|payment|fees) (process|procedure|information)",
                r"school fees",
                r"how to pay",
                r"payment (methods|options|procedures)",
                r"school expenses",
                r"financial assistance"
            ]
        }
        
        self.informational_patterns = {
            # Elementary school programs (K-6 grades)
            "programs": [
                r"what (programs|classes|grades) (are )?available",
                r"list of (programs|classes|grade levels)",
                r"ano ang mga (grade|programa|klase)",
                r"available (programs|classes|grades)",
                r"academic programs",
                r"kindergarten.*program",
                r"grade.*program"
            ],
            
            # Elementary admission requirements
            "requirements": [
                r"what are the (admission|enrollment|entry)? requirements",
                r"(admission|enrollment|entry) requirements",
                r"ano ang (requirements|kailangan)",
                r"mga (requirements|kailangan)",
                r"required documents",
                r"requirements.*admission",
                r"admission.*requirements",
                r"what.*requirements",
                r"kindergarten.*requirements",
                r"grade.*requirements"
            ],
            
            # Elementary school office information
            "offices": [
                r"(office|room|classroom) (location|hours|contact)",
                r"where is (the )?(principal|teacher|office)",
                r"office hours",
                r"contact (information|details)",
                r"school.*contact",
                r"contact.*school",
                r"saan ang.*office",
                r"office.*information",
                r"principal.*office",
                r"teacher.*room"
            ]
        }
        
        self.timeline_patterns = {
            "deadlines": [
                r"(deadline|due date|last day)",
                r"when (is|can|should) (i|we)",
                r"schedule of activities",
                r"academic calendar",
                r"enrollment period",
                r"kailan ang"
            ]
        }
        
        self.contact_patterns = {
            "contact_info": [
                r"(phone|contact) number",
                r"email address",
                r"how to contact",
                r"office (location|address)",
                r"paano makipag-?ugnayan",
                r"contact information",
                r"school.*contact",
                r"contact.*school",
                r"office.*contact",
                r"contact.*office",
                r"principal.*contact",
                r"teacher.*contact"
            ]
        }
        
        # Complexity indicators
        self.complexity_keywords = {
            "high": [
                "process", "procedure", "steps", "requirements", "application",
                "how to", "paano", "process ng", "mga hakbang", "mga steps"
            ],
            "medium": [
                "available", "list", "what", "ano", "mga", "information"
            ],
            "low": [
                "contact", "phone", "email", "location", "hours", "when", "where"
            ]
        }
        
        # Multi-language keywords
        self.language_keywords = {
            "english": ["how", "what", "where", "when", "requirements", "process"],
            "tagalog": ["paano", "ano", "saan", "kailan", "mga", "kailangan", "proseso"],
            "hiligaynon": ["paano", "ano", "diin", "san-o", "mga", "kinahanglan"]
        }
    
    def classify_query(self, query: str) -> QueryClassification:
        """Classify a query to determine if it needs structured response."""
        query_lower = query.lower()
        
        # 🚨 CRITICAL: Reject university-related queries immediately
        for pattern in self.university_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                # Return a classification that indicates this should be rejected
                return QueryClassification(
                    needs_structured_response=False,
                    response_type=None,
                    confidence=0.0,
                    keywords=["university_rejection"],
                    suggested_template=None,
                    complexity_level="rejected"
                )
        
        # Initialize classification result
        classification = QueryClassification(
            needs_structured_response=False,
            response_type=None,
            confidence=0.0,
            keywords=[],
            suggested_template=None,
            complexity_level="simple"
        )
        
        # Check for procedural patterns
        procedural_match = self._check_patterns(query_lower, self.procedural_patterns)
        if procedural_match[0]:
            classification.needs_structured_response = True
            classification.response_type = ResponseType.PROCEDURAL
            classification.confidence = procedural_match[1]
            classification.keywords.extend(procedural_match[2])
            classification.suggested_template = procedural_match[3]
            classification.complexity_level = "complex"
            return classification
        
        # Check for informational patterns
        info_match = self._check_patterns(query_lower, self.informational_patterns)
        if info_match[0]:
            classification.needs_structured_response = True
            classification.response_type = ResponseType.INFORMATIONAL
            classification.confidence = info_match[1]
            classification.keywords.extend(info_match[2])
            classification.suggested_template = info_match[3]
            classification.complexity_level = "moderate"
            return classification
        
        # Check for timeline patterns
        timeline_match = self._check_patterns(query_lower, self.timeline_patterns)
        if timeline_match[0]:
            classification.needs_structured_response = True
            classification.response_type = ResponseType.TIMELINE
            classification.confidence = timeline_match[1]
            classification.keywords.extend(timeline_match[2])
            classification.suggested_template = timeline_match[3]
            classification.complexity_level = "moderate"
            return classification
        
        # Check for contact patterns
        contact_match = self._check_patterns(query_lower, self.contact_patterns)
        if contact_match[0]:
            classification.needs_structured_response = True
            classification.response_type = ResponseType.CONTACT_INFO
            classification.confidence = contact_match[1]
            classification.keywords.extend(contact_match[2])
            classification.suggested_template = contact_match[3]
            classification.complexity_level = "simple"
            return classification
        
        # Check complexity based on keywords
        complexity_score = self._calculate_complexity(query_lower)
        if complexity_score > 0.6:
            classification.needs_structured_response = True
            classification.response_type = ResponseType.INFORMATIONAL
            classification.confidence = complexity_score
            classification.complexity_level = "moderate"
        
        return classification
    
    def _check_patterns(self, query: str, pattern_dict: Dict[str, List[str]]) -> Tuple[bool, float, List[str], Optional[str]]:
        """Check query against pattern dictionary."""
        best_match = False
        best_confidence = 0.0
        matched_keywords = []
        best_template = None
        
        for template_name, patterns in pattern_dict.items():
            match_count = 0
            total_patterns = len(patterns)
            
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    match_count += 1
                    # Extract keywords from the pattern
                    matched_keywords.extend(self._extract_keywords_from_pattern(pattern, query))
            
            if match_count > 0:
                confidence = match_count / total_patterns
                if confidence > best_confidence:
                    best_match = True
                    best_confidence = confidence
                    best_template = template_name
        
        return best_match, best_confidence, matched_keywords, best_template
    
    def _extract_keywords_from_pattern(self, pattern: str, query: str) -> List[str]:
        """Extract relevant keywords from matched pattern."""
        # Simple keyword extraction - could be enhanced
        keywords = []
        
        # Extract words from pattern (remove regex symbols)
        pattern_words = re.findall(r'\w+', pattern)
        query_words = query.lower().split()
        
        for word in pattern_words:
            if word in query_words and len(word) > 2:
                keywords.append(word)
        
        return keywords
    
    def _calculate_complexity(self, query: str) -> float:
        """Calculate complexity score based on keywords."""
        complexity_score = 0.0
        word_count = len(query.split())
        
        # Check for complexity keywords
        for level, keywords in self.complexity_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    if level == "high":
                        complexity_score += 0.3
                    elif level == "medium":
                        complexity_score += 0.2
                    elif level == "low":
                        complexity_score += 0.1
        
        # Adjust based on query length
        if word_count > 8:
            complexity_score += 0.2
        elif word_count > 5:
            complexity_score += 0.1
        
        return min(complexity_score, 1.0)
    
    def detect_language(self, query: str) -> str:
        """Detect the primary language of the query."""
        query_lower = query.lower()
        
        scores = {}
        for lang, keywords in self.language_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            scores[lang] = score
        
        if scores:
            best_lang = max(scores, key=scores.get)
            if scores[best_lang] > 0:
                return best_lang
        
        return "english"  # Default
    
    def get_suggested_structure(self, classification: QueryClassification) -> Dict:
        """Get suggested structure based on classification."""
        if not classification.needs_structured_response:
            return {"structure_type": "simple"}
        
        structures = {
            ResponseType.PROCEDURAL: {
                "structure_type": "step_by_step",
                "sections": ["overview", "requirements", "steps", "contacts", "notes"],
                "include_timeline": True,
                "include_requirements": True
            },
            ResponseType.INFORMATIONAL: {
                "structure_type": "multi_section",
                "sections": ["overview", "details", "requirements", "contacts"],
                "include_timeline": False,
                "include_requirements": True
            },
            ResponseType.TIMELINE: {
                "structure_type": "timeline",
                "sections": ["overview", "schedule", "deadlines", "contacts"],
                "include_timeline": True,
                "include_requirements": False
            },
            ResponseType.CONTACT_INFO: {
                "structure_type": "contact_focused",
                "sections": ["contacts", "hours", "location"],
                "include_timeline": False,
                "include_requirements": False
            }
        }
        
        return structures.get(classification.response_type, {"structure_type": "simple"})