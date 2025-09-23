"""
Keyword Matching Module - Fixed
Handles keyword matching with specific, non-broad patterns
"""
import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

class KeywordMatcher:
    """Fixed keyword matcher with specific patterns to avoid false matches"""
    
    def __init__(self):
        self.keyword_responses = self._initialize_keyword_responses()
    
    def _initialize_keyword_responses(self) -> Dict:
        """Initialize keyword responses with FIXED, specific patterns"""
        return {
            # Staff Information - SPECIFIC patterns only
            ("meliza", "delgado"): {
                "en": "Mrs. Meliza A. Delgado is our Head Teacher at Tomas SM. Bautista Elementary School.",
                "tl": "Si Mrs. Meliza A. Delgado ang aming Head Teacher sa Tomas SM. Bautista Elementary School.",
                "default": "Si Meliza A. Delgado ang Head Teacher ng Tomas SM. Bautista Elementary School."
            },
            ("head", "teacher"): {
                "en": "Mrs. Meliza A. Delgado is our Head Teacher.",
                "tl": "Si Mrs. Meliza A. Delgado ang aming Head Teacher.",
                "default": "Si Meliza A. Delgado ang Head Teacher."
            },
            
            # School Information - SPECIFIC patterns only
            ("address", "location", "where", "saan"): {
                "en": "Tomas SM. Bautista Elementary School is located in Fatima, New Washington, Aklan.",
                "tl": "Ang Tomas SM. Bautista Elementary School ay matatagpuan sa Fatima, New Washington, Aklan.",
                "default": "Ang lokasyon ng paaralan ay matatagpuan sa Fatima, New Washington, Aklan."
            },
            
            # Financial Information - SPECIFIC patterns only
            ("tuition", "fee", "payment"): {
                "en": "For tuition and fee information, please contact our school office.",
                "tl": "Para sa impormasyon tungkol sa tuition at bayad, pakiusap lang makipag-ugnayan sa school office.",
                "default": "Para sa impormasyon tungkol sa bayad, pakiusap lang makipag-ugnayan sa school office."
            },
            ("school", "fees"): {
                "en": "For school fees and tuition information, please contact our school office.",
                "tl": "Para sa impormasyon tungkol sa school fees at tuition, pakiusap lang makipag-ugnayan sa school office.",
                "default": "Para sa impormasyon tungkol sa school fees, pakiusap lang makipag-ugnayan sa school office."
            },
            
            # Enrollment Information - SPECIFIC patterns only
            ("enrollment", "admission", "register"): {
                "en": "For enrollment information, please contact our school office.",
                "tl": "Para sa impormasyon tungkol sa enrollment, pakiusap lang makipag-ugnayan sa school office.",
                "default": "Para sa impormasyon tungkol sa enrollment, pakiusap lang makipag-ugnayan sa school office."
            },
            
            # Greetings - SPECIFIC patterns only
            ("hello",): {
                "en": "Hello! I'm TOMAS, the digital assistant for Tomas SM. Bautista Elementary School. How can I help you?",
                "tl": "Kumusta! Ako si TOMAS, ang digital assistant ng Tomas SM. Bautista Elementary School. Paano ko kayo matutulungan?",
                "default": "Kumusta! Ako si TOMAS. Paano ko kayo matutulungan?"
            },
            ("hi",): {
                "en": "Hi! I'm TOMAS, the digital assistant for Tomas SM. Bautista Elementary School. How can I help you?",
                "tl": "Kumusta! Ako si TOMAS, ang digital assistant ng Tomas SM. Bautista Elementary School. Paano ko kayo matutulungan?",
                "default": "Kumusta! Ako si TOMAS. Paano ko kayo matutulungan?"
            },
            ("kumusta",): {
                "en": "Hello! I'm TOMAS, the digital assistant for Tomas SM. Bautista Elementary School. How can I help you?",
                "tl": "Kumusta! Ako si TOMAS, ang digital assistant ng Tomas SM. Bautista Elementary School. Paano ko kayo matutulungan?",
                "default": "Kumusta! Ako si TOMAS. Paano ko kayo matutulungan?"
            }
        }
    
    def find_match(self, query: str, lang: str) -> Optional[str]:
        """Find keyword match with FIXED logic to avoid false positives"""
        query_lower = query.lower()
        
        best_match = None
        max_matches = 0
        
        for keywords, response in self.keyword_responses.items():
            # FIXED: Require ALL keywords to be present for a match
            matches = 0
            for keyword in keywords:
                if keyword in query_lower:
                    matches += 1
            
            # Only match if ALL keywords in the pattern are found
            if matches == len(keywords) and matches > max_matches:
                max_matches = matches
                best_match = response
                logger.info(f"🎯 Keyword match found: {keywords} -> {matches}/{len(keywords)} matches")
        
        if best_match and max_matches > 0:
            logger.info(f"🎯 Keyword match found ({max_matches} matches)")
            
            # Return language-specific response
            if isinstance(best_match, dict):
                if lang == "tl":
                    return best_match.get("tl", best_match.get("default", ""))
                elif lang == "akl":
                    return best_match.get("tl", best_match.get("default", ""))  # Use Tagalog for Aklanon
                else:
                    return best_match.get("en", best_match.get("default", ""))
            else:
                return best_match
        
        return None
