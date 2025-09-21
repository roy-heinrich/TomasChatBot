"""
Advanced Multilingual NLP Engine for the TOMAS Chatbot
Supports English, Tagalog, and Aklanon with semantic understanding
"""

import logging
import json
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
import os

logger = logging.getLogger(__name__)

try:
    from transformers import AutoTokenizer, AutoModel, pipeline
    from sentence_transformers import SentenceTransformer, util
    import torch
    import numpy as np
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available. Install with: pip install transformers sentence-transformers torch")

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Install with: pip install spacy")

try:
    from langdetect import detect, detect_langs
    from langdetect.lang_detect_exception import LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError as e:
    LANGDETECT_AVAILABLE = False
    logger.warning(f"langdetect not available: {e}. Install with: pip install langdetect")
    # Create dummy classes for type hints
    class LangDetectException(Exception):
        pass

@dataclass
class LanguageDetectionResult:
    """Enhanced language detection result with confidence and analysis"""
    language: str
    confidence: float
    scores: Dict[str, float]
    method: str  # "semantic", "statistical", "rule_based", "hybrid"
    features: Dict[str, Any]

@dataclass
class SemanticIntent:
    """Semantic intent classification result"""
    intent: str
    confidence: float
    similarity_score: float
    matched_example: str
    method: str

@dataclass
class MultilingualEntity:
    """Multilingual entity extraction result"""
    text: str
    label: str
    start: int
    end: int
    confidence: float
    language: str
    normalized_form: str = None

class MultilingualNLPEngine:
    """
    Advanced NLP engine that uses semantic embeddings and multilingual models
    instead of hardcoded patterns for better language understanding
    """
    
    def __init__(self):
        self.sentence_model = None
        self.nlp_models = {}
        self.intent_embeddings = {}
        self.example_intents = {}
        self.language_models = {}
        self.initialized = False
        
        # Don't initialize models here - do it lazily when needed
    
    async def _ensure_initialized(self):
        """Ensure models are initialized before use"""
        if not self.initialized:
            await self._initialize_models()
            self.initialized = True
    
    async def _initialize_models(self):
        """Initialize NLP models asynchronously"""
        try:
            if TRANSFORMERS_AVAILABLE:
                logger.info("🚀 Initializing multilingual sentence transformer...")
                # Use multilingual model that supports many languages including Tagalog
                self.sentence_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
                
                # Initialize intent classification examples
                await self._initialize_intent_examples()
                
                logger.info("✅ Sentence transformer initialized successfully")
            
            if SPACY_AVAILABLE:
                # Try to load multilingual spaCy model
                try:
                    self.nlp_models['en'] = spacy.load('en_core_web_sm')
                except OSError:
                    logger.warning("English spaCy model not found. Install with: python -m spacy download en_core_web_sm")
                
                # For now, use English model for Tagalog/Aklanon as well
                # In production, you'd want specific models or train custom ones
                
        except Exception as e:
            logger.error(f"❌ Error initializing NLP models: {e}")
    
    async def _initialize_intent_examples(self):
        """Initialize intent classification examples with embeddings"""
        
        # Define example utterances for each intent across languages
        intent_examples = {
            "greeting_simple": [
                "hello", "hi", "hey", "good morning", "good afternoon",
                "kumusta", "kamusta", "maayong aga", "maayong hapon", 
                "magandang umaga", "magandang hapon"
            ],
            "greeting_with_name": [
                "hello my name is john", "hi i am mary", "good morning i'm peter",
                "kumusta ako si juan", "magandang umaga ako si maria",
                "maayong aga ako si pedro"
            ],
            "name_introduction": [
                "my name is", "i am", "i'm called", "call me",
                "ako si", "ako ay", "tawagan mo ako",
                "ngalan ko", "pangalan ko ay"
            ],
            "enrollment_inquiry": [
                "i want to enroll", "how to enroll", "enrollment process", 
                "register my child", "admission requirements",
                "gusto mag-enroll", "paano mag-enroll", "pag-enroll",
                "rehistro sang bata", "paano mag-register"
            ],
            "location_inquiry": [
                "where is the school", "school location", "school address",
                "how to get to school", "directions to school",
                "saan ang paaralan", "lokasyon ng school", "address ng school",
                "diin ang paaralan", "lokasyon sang eskwelahan"
            ],
            "staff_inquiry": [
                "who is the principal", "who is the teacher", "school staff",
                "head teacher", "school head", "administrator",
                "sino ang principal", "sino ang guro", "school head",
                "sin-o ang principal", "sin-o nga guro"
            ],
            "contact_info": [
                "contact number", "phone number", "email address",
                "how to contact", "contact information",
                "numero", "contact number ninyo", "phone ninyo",
                "numero ninyo", "contact nga numero"
            ],
            "school_info": [
                "tell me about the school", "school information", "about your school",
                "school programs", "what programs", "curriculum",
                "sabihin tungkol sa school", "impormasyon ng school",
                "ano nga programa", "mga programa sang school"
            ],
            "appreciation": [
                "thank you", "thanks", "salamat", "maraming salamat",
                "appreciate it", "thank you so much",
                "salamat gid", "damo nga salamat"
            ]
        }
        
        # Create embeddings for all examples
        if self.sentence_model:
            for intent, examples in intent_examples.items():
                embeddings = self.sentence_model.encode(examples)
                self.intent_embeddings[intent] = embeddings
                self.example_intents[intent] = examples
                
            logger.info(f"📚 Created embeddings for {len(intent_examples)} intents")
    
    async def detect_language_semantic(self, text: str) -> LanguageDetectionResult:
        """
        Semantic language detection using multilingual models
        instead of hardcoded patterns
        """
        
        # Ensure models are initialized
        await self._ensure_initialized()
        
        features = {}
        scores = {"en": 0.0, "tl": 0.0, "akl": 0.0}
        
        # Method 1: Statistical language detection
        statistical_result = await self._statistical_language_detection(text)
        scores.update(statistical_result["scores"])
        features["statistical"] = statistical_result
        
        # Method 2: Semantic similarity to known language patterns
        if self.sentence_model:
            semantic_result = await self._semantic_language_detection(text)
            # Combine with statistical scores
            for lang in scores:
                scores[lang] = (scores[lang] + semantic_result["scores"].get(lang, 0.0)) / 2
            features["semantic"] = semantic_result
        
        # Method 3: Linguistic feature analysis
        linguistic_result = await self._linguistic_feature_analysis(text)
        features["linguistic"] = linguistic_result
        
        # Apply linguistic boosters
        for lang, boost in linguistic_result.items():
            if lang in scores:
                scores[lang] += boost * 0.3  # 30% weight for linguistic features
        
        # Normalize scores
        total = sum(scores.values())
        if total > 0:
            scores = {lang: score/total for lang, score in scores.items()}
        
        # Determine best language
        best_lang = max(scores, key=scores.get)
        confidence = scores[best_lang]
        
        # Handle Aklanon as variant of Tagalog for now (can be improved with more data)
        if best_lang == "akl" or (best_lang == "tl" and self._has_aklanon_markers(text)):
            final_lang = "akl"
        else:
            final_lang = best_lang
        
        return LanguageDetectionResult(
            language=final_lang,
            confidence=confidence,
            scores=scores,
            method="hybrid",
            features=features
        )
    
    async def _statistical_language_detection(self, text: str) -> Dict:
        """Use statistical methods for language detection"""
        scores = {"en": 0.0, "tl": 0.0, "akl": 0.0}
        
        if LANGDETECT_AVAILABLE:
            try:
                # Use langdetect for statistical analysis
                detected_langs = detect_langs(text)
                
                for lang_result in detected_langs:
                    lang_code = lang_result.lang
                    prob = lang_result.prob
                    
                    # Map language codes
                    if lang_code == "en":
                        scores["en"] += prob
                    elif lang_code in ["tl", "fil"]:  # Filipino/Tagalog
                        scores["tl"] += prob
                    else:
                        # Unknown language, might be Aklanon
                        scores["akl"] += prob * 0.3
                        
            except (LangDetectException, Exception) as e:
                # Text too short, unclear, or other error
                logger.debug(f"Statistical language detection failed: {e}")
                scores = {"en": 0.33, "tl": 0.33, "akl": 0.33}
        else:
            # Fallback when langdetect is not available
            scores = {"en": 0.33, "tl": 0.33, "akl": 0.33}
        
        return {"scores": scores, "method": "statistical"}
    
    async def _semantic_language_detection(self, text: str) -> Dict:
        """Use semantic similarity to detect language"""
        scores = {"en": 0.0, "tl": 0.0, "akl": 0.0}
        
        if not self.sentence_model:
            return {"scores": scores, "method": "semantic", "details": "model_not_available"}
        
        # Language prototype sentences
        language_prototypes = {
            "en": [
                "Hello, how are you today?",
                "Where is the school located?", 
                "I want to enroll my child",
                "Thank you for your help",
                "What time does school start?"
            ],
            "tl": [
                "Kumusta ka ngayon?",
                "Saan ang lokasyon ng paaralan?",
                "Gusto kong mag-enroll ng anak ko", 
                "Salamat sa inyong tulong",
                "Anong oras nagsisimula ang klase?"
            ],
            "akl": [
                "Kamusta ka subong?",
                "Diin ang lokasyon sang paaralan?",
                "Gusto ko mag-enroll sang akon bata",
                "Salamat sa inyo nga bulig",
                "Ano nga oras magsugod ang klase?"
            ]
        }
        
        try:
            # Encode input text
            text_embedding = self.sentence_model.encode([text])
            
            # Compare with language prototypes
            for lang, prototypes in language_prototypes.items():
                prototype_embeddings = self.sentence_model.encode(prototypes)
                similarities = util.cos_sim(text_embedding, prototype_embeddings)
                # Take maximum similarity as language score
                scores[lang] = float(torch.max(similarities).item())
                
        except Exception as e:
            logger.warning(f"Semantic language detection failed: {e}")
        
        return {"scores": scores, "method": "semantic"}
    
    async def _linguistic_feature_analysis(self, text: str) -> Dict[str, float]:
        """Analyze linguistic features to boost language detection"""
        features = {}
        text_lower = text.lower()
        
        # English linguistic features
        english_features = 0.0
        if re.search(r'\b(the|and|or|but|with|for|at|by|from)\b', text_lower):
            english_features += 0.3
        if re.search(r'\b(school|teacher|student|class|grade)\b', text_lower):
            english_features += 0.2
        if re.search(r'\b(where|what|when|who|how)\b', text_lower):
            english_features += 0.2
        
        # Tagalog linguistic features  
        tagalog_features = 0.0
        if re.search(r'\b(ng|sa|ang|si|ni|kay)\b', text_lower):
            tagalog_features += 0.4
        if re.search(r'\b(po|opo|naman|din|rin)\b', text_lower):
            tagalog_features += 0.3
        if re.search(r'\b(ako|ikaw|siya|kami|tayo|kayo|sila)\b', text_lower):
            tagalog_features += 0.2
        
        # Aklanon linguistic features
        aklanon_features = 0.0
        if re.search(r'\b(sang|nga|gid|ro|it)\b', text_lower):
            aklanon_features += 0.4
        if re.search(r'\b(sin-o|diin|siin|ngaa)\b', text_lower):
            aklanon_features += 0.3
        if re.search(r'\b(ako|imo|iya|aton|inyo|ila)\b', text_lower):
            aklanon_features += 0.2
        
        features["en"] = english_features
        features["tl"] = tagalog_features  
        features["akl"] = aklanon_features
        
        return features
    
    def _has_aklanon_markers(self, text: str) -> bool:
        """Check for distinctive Aklanon markers"""
        text_lower = text.lower()
        aklanon_markers = [
            "gid", "sang", "nga", "sin-o", "diin", "siin", 
            "wara", "mayo", "ro", "it", "eon"
        ]
        return any(marker in text_lower for marker in aklanon_markers)
    
    async def classify_intent_semantic(self, text: str, language: str = None) -> SemanticIntent:
        """
        Classify intent using semantic similarity instead of keyword matching
        """
        
        # Ensure models are initialized
        await self._ensure_initialized()
        
        if not self.sentence_model or not self.intent_embeddings:
            # Fallback to simple classification
            return SemanticIntent(
                intent="unknown",
                confidence=0.1,
                similarity_score=0.0,
                matched_example="",
                method="fallback"
            )
        
        try:
            # Encode input text
            text_embedding = self.sentence_model.encode([text])
            
            best_intent = "unknown"
            best_similarity = 0.0
            best_example = ""
            
            # Compare with all intent embeddings
            for intent, embeddings in self.intent_embeddings.items():
                similarities = util.cos_sim(text_embedding, embeddings)
                max_similarity = float(torch.max(similarities).item())
                
                if max_similarity > best_similarity:
                    best_similarity = max_similarity
                    best_intent = intent
                    # Find which example had the best match
                    best_idx = torch.argmax(similarities).item()
                    best_example = self.example_intents[intent][best_idx]
            
            # Convert similarity to confidence (adjust threshold as needed)
            confidence = best_similarity if best_similarity > 0.3 else 0.1
            
            return SemanticIntent(
                intent=best_intent,
                confidence=confidence,
                similarity_score=best_similarity,
                matched_example=best_example,
                method="semantic_similarity"
            )
            
        except Exception as e:
            logger.error(f"❌ Semantic intent classification failed: {e}")
            return SemanticIntent(
                intent="unknown",
                confidence=0.1,
                similarity_score=0.0,
                matched_example="",
                method="error"
            )
    
    async def extract_entities_multilingual(self, text: str, language: str) -> List[MultilingualEntity]:
        """
        Extract entities using multilingual NER instead of hardcoded patterns
        """
        
        # Ensure models are initialized
        await self._ensure_initialized()
        
        entities = []
        
        # Use spaCy NER if available
        if language in self.nlp_models:
            nlp = self.nlp_models[language]
            doc = nlp(text)
            
            for ent in doc.ents:
                entities.append(MultilingualEntity(
                    text=ent.text,
                    label=ent.label_,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.8,  # spaCy doesn't provide confidence scores by default
                    language=language
                ))
        
        # Add custom multilingual entity extraction
        entities.extend(await self._extract_custom_entities(text, language))
        
        return entities
    
    async def _extract_custom_entities(self, text: str, language: str) -> List[MultilingualEntity]:
        """Extract custom entities relevant to school chatbot"""
        entities = []
        
        # Name extraction patterns (multilingual)
        name_patterns = {
            "en": [
                r"my name is (\w+)",
                r"i am (\w+)",
                r"call me (\w+)",
                r"i'm (\w+)"
            ],
            "tl": [
                r"ako si (\w+)",
                r"ako ay (\w+)", 
                r"pangalan ko ay (\w+)",
                r"tawagan mo ako (\w+)"
            ],
            "akl": [
                r"ako si (\w+)",
                r"ngalan ko (\w+)",
                r"tawagon mo ako (\w+)"
            ]
        }
        
        patterns = name_patterns.get(language, name_patterns["en"])
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append(MultilingualEntity(
                    text=match.group(1),
                    label="PERSON",
                    start=match.start(1),
                    end=match.end(1),
                    confidence=0.9,
                    language=language,
                    normalized_form=match.group(1).title()
                ))
        
        return entities
    
    async def translate_contextual(self, text: str, source_lang: str, target_lang: str, context: str = None) -> str:
        """
        Context-aware translation using transformer models
        """
        
        if not TRANSFORMERS_AVAILABLE:
            # Fallback to simple translation
            from deep_translator import GoogleTranslator
            return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        
        try:
            # For now, use a simple approach. In production, you'd use specialized translation models
            # or fine-tuned models for the school domain
            
            if source_lang == target_lang:
                return text
            
            # Create context-aware prompt for better translation
            if context:
                enhanced_text = f"Context: {context}\nTranslate: {text}"
            else:
                enhanced_text = text
            
            # Use Google Translator as fallback but could be enhanced with transformer models
            from deep_translator import GoogleTranslator
            return GoogleTranslator(source=source_lang, target=target_lang).translate(enhanced_text)
            
        except Exception as e:
            logger.error(f"❌ Contextual translation failed: {e}")
            return text

# Global instance
multilingual_nlp = MultilingualNLPEngine()