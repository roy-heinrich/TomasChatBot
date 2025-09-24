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

# Lightweight NLP alternatives - defer imports to avoid wordnet issues
NLTK_AVAILABLE = False
TEXTBLOB_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Install with: pip install scikit-learn")

try:
    from gensim.models import Word2Vec
    from gensim.similarities import WmdSimilarity
    GENSIM_AVAILABLE = True
except (ImportError, Exception) as e:
    GENSIM_AVAILABLE = False
    logger.warning(f"Gensim not available: {e}. Using fallback methods.")


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
        # Lightweight NLP components
        self.tfidf_vectorizer = None
        self.word2vec_model = None
        self.stemmer = None
        self.stop_words = set()
        
        # Legacy heavy components (disabled)
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
        """Initialize lightweight NLP models asynchronously"""
        try:
            # Initialize NLTK components with safe imports
            global NLTK_AVAILABLE, TEXTBLOB_AVAILABLE
            try:
                logger.info("🚀 Initializing NLTK components...")
                import nltk
                from nltk.tokenize import word_tokenize, sent_tokenize
                from nltk.corpus import stopwords
                from nltk.stem import PorterStemmer
                
                # Set up NLTK data path to use local nltk_data folder
                nltk_data_dir = os.path.join(os.getcwd(), 'nltk_data')
                if os.path.exists(nltk_data_dir):
                    nltk.data.path.append(nltk_data_dir)
                    logger.info(f"✅ Using local NLTK data from: {nltk_data_dir}")
                else:
                    logger.warning("⚠️ Local nltk_data folder not found, using default paths")
                
                # Verify essential NLTK resources are available
                try:
                    nltk.data.find('tokenizers/punkt')
                    logger.info("✅ Punkt tokenizer available")
                except LookupError:
                    logger.warning("⚠️ Punkt tokenizer not found")
                
                try:
                    nltk.data.find('corpora/stopwords')
                    logger.info("✅ Stopwords available")
                except LookupError:
                    logger.warning("⚠️ Stopwords not found")
                
                try:
                    nltk.data.find('corpora/wordnet')
                    logger.info("✅ WordNet available")
                except LookupError:
                    logger.warning("⚠️ WordNet not found")
                
                # Initialize NLTK components
                self.stemmer = PorterStemmer()
                try:
                    self.stop_words = set(stopwords.words('english'))
                    logger.info(f"✅ Loaded {len(self.stop_words)} English stopwords")
                except Exception as e:
                    logger.warning(f"⚠️ Could not load stopwords: {e}")
                    self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
                
                NLTK_AVAILABLE = True
                logger.info("✅ NLTK components initialized successfully")
            except Exception as e:
                logger.warning(f"NLTK initialization failed: {e}")
                NLTK_AVAILABLE = False
                # Set fallback values
                self.stemmer = None
                self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
            
            # Initialize TextBlob with safe imports
            try:
                logger.info("🚀 Initializing TextBlob...")
                from textblob import TextBlob
                TEXTBLOB_AVAILABLE = True
                logger.info("✅ TextBlob initialized successfully")
            except Exception as e:
                logger.warning(f"TextBlob initialization failed: {e}")
                TEXTBLOB_AVAILABLE = False
            
            # Initialize scikit-learn TF-IDF vectorizer
            if SKLEARN_AVAILABLE:
                logger.info("🚀 Initializing TF-IDF vectorizer...")
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=1000,
                    stop_words='english',
                    ngram_range=(1, 2),
                    lowercase=True
                )
                logger.info("✅ TF-IDF vectorizer initialized successfully")
                
                # Initialize intent classification examples
                await self._initialize_intent_examples()
                
            # Legacy heavy model initialization (disabled for deployment)
            # if TRANSFORMERS_AVAILABLE:
            #     logger.info("🚀 Initializing multilingual sentence transformer...")
            #     self.sentence_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
            #     logger.info("✅ Sentence transformer initialized successfully")
            
            # if SPACY_AVAILABLE:
            #     try:
            #         self.nlp_models['en'] = spacy.load('en_core_web_sm')
            #     except OSError:
            #         logger.warning("English spaCy model not found. Install with: python -m spacy download en_core_web_sm")
                
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
        
        # Store examples for lightweight TF-IDF based classification
        self.example_intents = intent_examples
        logger.info(f"📚 Stored {len(intent_examples)} intent examples for TF-IDF classification")
        
        # Legacy heavy embedding creation (disabled for deployment)
        # if self.sentence_model:
        #     for intent, examples in intent_examples.items():
        #         embeddings = self.sentence_model.encode(examples)
        #         self.intent_embeddings[intent] = embeddings
        #         self.example_intents[intent] = examples
        #     logger.info(f"📚 Created embeddings for {len(intent_examples)} intents")
    
    async def detect_language_semantic(self, text: str) -> LanguageDetectionResult:
        """
        Semantic language detection using multilingual models
        instead of hardcoded patterns
        """
        
        # Ensure models are initialized
        await self._ensure_initialized()
        
        features = {}
        scores = {"en": 0.0, "tl": 0.0, "akl": 0.0}
        
        # Method 1: Statistical language detection (reduced weight)
        statistical_result = await self._statistical_language_detection(text)
        # 🎯 FIX: Reduce statistical weight since langdetect doesn't support Tagalog/Aklanon
        for lang in scores:
            scores[lang] += statistical_result["scores"].get(lang, 0.0) * 0.2  # Only 20% weight
        features["statistical"] = statistical_result
        
        # Method 2: Semantic similarity to known language patterns (using TF-IDF)
        if self.tfidf_vectorizer and SKLEARN_AVAILABLE:
            semantic_result = await self._semantic_language_detection(text)
            # Combine with statistical scores
            for lang in scores:
                scores[lang] += semantic_result["scores"].get(lang, 0.0) * 0.3  # 30% weight
            features["semantic"] = semantic_result
        
        # Method 3: Linguistic feature analysis (increased weight)
        linguistic_result = await self._linguistic_feature_analysis(text)
        features["linguistic"] = linguistic_result
        
        # 🎯 FIX: Apply linguistic boosters with higher weight
        for lang, boost in linguistic_result.items():
            if lang in scores:
                scores[lang] += boost * 0.8  # 80% weight for linguistic features
        
        # Normalize scores
        total = sum(scores.values())
        if total > 0:
            scores = {lang: score/total for lang, score in scores.items()}
        
        # Determine best language
        best_lang = max(scores, key=scores.get)
        confidence = scores[best_lang]
        
        # 🎯 FIX: Rule-based override for clear patterns (highest priority)
        text_lower = text.lower()
        
        # Strong English patterns (override everything)
        if re.search(r'\b(how do|how can|how to|what is|what are|where is|when is|who is)\b', text_lower):
            final_lang = "en"  # Force English for clear English question patterns
            confidence = 0.95  # High confidence for rule-based detection
        # 🎯 FIX: Strong English patterns for safety and emergency terms (highest priority)
        if re.search(r'\b(earthquake|fire|drill|emergency|safety|evacuation|disaster)\b', text_lower):
            final_lang = "en"  # Force English for safety terms
            confidence = 0.95  # High confidence for rule-based detection
        # 🎯 FIX: Common English words that should always be English
        elif re.search(r'\b(hello|hi|goodbye|bye|thank you|thanks|help|yes|no|ok|okay)\b', text_lower):
            final_lang = "en"  # Force English for common English words
            confidence = 0.95  # High confidence for rule-based detection
        # Strong Tagalog patterns (override everything)
        elif re.search(r'\b(ako si|pangalan ko|naaalala mo|ano ang|sino ang|kumusta|kamusta|anong|baitang|paaralan|bukas|para sa)\b', text_lower):
            final_lang = "tl"  # Force Tagalog for clear Tagalog patterns
            confidence = 0.95  # High confidence for rule-based detection
        # 🎯 FIX: Specific Tagalog greeting patterns
        elif re.search(r'\b(kumusta,?\s+ako\s+si|kamusta,?\s+ako\s+si)\b', text_lower):
            final_lang = "tl"  # Force Tagalog for "kumusta, ako si" patterns
            confidence = 0.95  # High confidence for rule-based detection
        # Strong Aklanon patterns (override everything)
        elif re.search(r'\b(maayong adlaw|maayong gabii|maayong buntag)\b', text_lower):
            final_lang = "akl"  # Force Aklanon for clear Aklanon patterns
            confidence = 0.95  # High confidence for rule-based detection
        # Fallback to hybrid detection
        elif best_lang == "akl" or (best_lang == "tl" and self._has_aklanon_markers(text)):
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
        """Use TF-IDF based similarity to detect language (lightweight alternative)"""
        scores = {"en": 0.0, "tl": 0.0, "akl": 0.0}
        
        if not self.tfidf_vectorizer or not SKLEARN_AVAILABLE:
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
            # Combine all prototypes for TF-IDF training
            all_texts = [text]
            all_labels = []
            
            for lang, prototypes in language_prototypes.items():
                all_texts.extend(prototypes)
                all_labels.extend([lang] * len(prototypes))
            
            # Fit TF-IDF on all texts
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)
            
            # Get text vector (first row)
            text_vector = tfidf_matrix[0:1]
            
            # Calculate similarities with each language's prototypes
            for i, lang in enumerate(language_prototypes.keys()):
                # Get indices for this language's prototypes
                start_idx = 1 + sum(len(language_prototypes[l]) for l in list(language_prototypes.keys())[:i])
                end_idx = start_idx + len(language_prototypes[lang])
                
                # Get prototype vectors for this language
                prototype_vectors = tfidf_matrix[start_idx:end_idx]
                
                # Calculate cosine similarities
                similarities = cosine_similarity(text_vector, prototype_vectors)
                
                # Take maximum similarity as language score
                scores[lang] = float(np.max(similarities))
                
        except Exception as e:
            logger.warning(f"TF-IDF language detection failed: {e}")
            return {"scores": scores, "method": "semantic", "details": f"error: {e}"}
        
        return {"scores": scores, "method": "semantic", "details": "success"}
    
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
        
        # 🎯 FIX: Strong English indicators for greetings and name introductions
        if re.search(r'\b(hi|hello|hey|good morning|good afternoon|good evening)\b', text_lower):
            english_features += 0.5  # Strong English indicator
        if re.search(r'\b(i am|i\'m|my name is|call me)\b', text_lower):
            english_features += 0.4  # Strong English indicator for name introductions
        # 🎯 FIX: Strong English indicators for common question patterns
        if re.search(r'\b(how do|how can|how to|what is|what are|where is|when is|who is)\b', text_lower):
            english_features += 0.6  # Very strong English indicator for question patterns
        if re.search(r'\b(teachers|parents|students|school|communicate|communication)\b', text_lower):
            english_features += 0.4  # Strong English indicator for school-related terms
        # 🎯 FIX: Add English indicators for safety and emergency terms
        if re.search(r'\b(earthquake|fire|drill|emergency|safety|evacuation|disaster)\b', text_lower):
            english_features += 0.5  # Strong English indicator for safety terms
        # 🎯 FIX: Add English indicators for common English words
        if re.search(r'\b(drills|procedures|policies|rules|guidelines|instructions)\b', text_lower):
            english_features += 0.4  # Strong English indicator for procedural terms
        
        # Tagalog linguistic features  
        tagalog_features = 0.0
        if re.search(r'\b(ng|sa|ang|si|ni|kay)\b', text_lower):
            tagalog_features += 0.4
        if re.search(r'\b(po|opo|naman|din|rin)\b', text_lower):
            tagalog_features += 0.3
        if re.search(r'\b(ako|ikaw|siya|kami|tayo|kayo|sila)\b', text_lower):
            tagalog_features += 0.2
        # 🎯 FIX: Strong Tagalog indicators for name patterns
        if re.search(r'\b(ako si|pangalan ko|naaalala mo|ano ang pangalan)\b', text_lower):
            tagalog_features += 0.8  # Very strong Tagalog indicator
        # Additional Tagalog patterns
        if re.search(r'\b(kumusta|kamusta|magandang|mabuti|salamat|po|opo)\b', text_lower):
            tagalog_features += 0.4  # Strong Tagalog indicator
        
        # Aklanon linguistic features
        aklanon_features = 0.0
        # 🎯 FIX: More specific Aklanon markers to avoid false positives
        if re.search(r'\b(sang|nga|gid|ro)\b', text_lower):
            aklanon_features += 0.4
        if re.search(r'\b(sin-o|diin|siin|ngaa)\b', text_lower):
            aklanon_features += 0.3
        # 🎯 FIX: Strong Aklanon greeting patterns
        if re.search(r'\b(maayong adlaw|maayong gabii|maayong buntag)\b', text_lower):
            aklanon_features += 0.6  # Very strong Aklanon indicator
        # 🎯 FIX: Remove "it" from Aklanon markers as it's too common in English
        # Only count "it" as Aklanon if it appears in specific Aklanon contexts
        if re.search(r'\b(ako|imo|iya|aton|inyo|ila)\b', text_lower):
            aklanon_features += 0.2
        
        # 🎯 FIX: Penalize Aklanon if strong English indicators are present
        if english_features > 0.3:
            aklanon_features *= 0.5  # Reduce Aklanon score when English indicators are strong
        
        features["en"] = english_features
        features["tl"] = tagalog_features  
        features["akl"] = aklanon_features
        
        return features
    
    def _has_aklanon_markers(self, text: str) -> bool:
        """Check for distinctive Aklanon markers"""
        text_lower = text.lower()
        # 🎯 FIX: More specific Aklanon markers, removed "it" as it's too common in English
        aklanon_markers = [
            "gid", "sang", "nga", "sin-o", "diin", "siin", 
            "wara", "mayo", "ro", "eon", "ngaa", "aton", "inyo"
        ]
        return any(marker in text_lower for marker in aklanon_markers)
    
    async def classify_intent_semantic(self, text: str, language: str = None) -> SemanticIntent:
        """
        Classify intent using semantic similarity instead of keyword matching
        """
        
        # Ensure models are initialized
        await self._ensure_initialized()
        
        if not self.tfidf_vectorizer or not self.example_intents or not SKLEARN_AVAILABLE:
            # Fallback to simple classification
            return SemanticIntent(
                intent="unknown",
                confidence=0.1,
                similarity_score=0.0,
                matched_example="",
                method="fallback"
            )
        
        try:
            # Prepare all examples for TF-IDF
            all_texts = [text]
            all_labels = []
            all_examples = []
            
            for intent, examples in self.example_intents.items():
                all_texts.extend(examples)
                all_labels.extend([intent] * len(examples))
                all_examples.extend(examples)
            
            # Fit TF-IDF on all texts
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)
            
            # Get text vector (first row)
            text_vector = tfidf_matrix[0:1]
            
            best_intent = "unknown"
            best_similarity = 0.0
            best_example = ""
            
            # Calculate similarities with each intent's examples
            current_idx = 1  # Start after the input text
            for intent, examples in self.example_intents.items():
                # Get vectors for this intent's examples
                intent_vectors = tfidf_matrix[current_idx:current_idx + len(examples)]
                
                # Calculate cosine similarities
                similarities = cosine_similarity(text_vector, intent_vectors)
                max_similarity = float(np.max(similarities))
                
                if max_similarity > best_similarity:
                    best_similarity = max_similarity
                    best_intent = intent
                    # Find which example had the best match
                    best_idx = np.argmax(similarities)
                    best_example = examples[best_idx]
                
                current_idx += len(examples)
            
            # Convert similarity to confidence (adjust threshold as needed)
            confidence = best_similarity if best_similarity > 0.3 else 0.1
            
            return SemanticIntent(
                intent=best_intent,
                confidence=confidence,
                similarity_score=best_similarity,
                matched_example=best_example,
                method="tfidf_similarity"
            )
            
        except Exception as e:
            logger.error(f"❌ TF-IDF intent classification failed: {e}")
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
        
        # Use NLTK for basic text processing if available
        if NLTK_AVAILABLE and self.stemmer:
            try:
                # Import NLTK functions locally to avoid import-time issues
                from nltk.tokenize import word_tokenize
                # Tokenize and get POS tags for basic entity extraction
                tokens = word_tokenize(text)
                
                # Simple named entity recognition using patterns
                for i, token in enumerate(tokens):
                    # Capitalized words might be names
                    if token[0].isupper() and len(token) > 1:
                        entities.append(MultilingualEntity(
                            text=token,
                            label="PERSON",
                            start=text.find(token),
                            end=text.find(token) + len(token),
                            confidence=0.6,  # Lower confidence for pattern-based extraction
                            language=language
                        ))
                
                logger.info(f"🔍 NLTK extracted {len(entities)} entities")
            except Exception as e:
                logger.warning(f"NLTK entity extraction failed: {e}")
        
        # Legacy spaCy NER (disabled for deployment)
        # if language in self.nlp_models:
        #     nlp = self.nlp_models[language]
        #     doc = nlp(text)
        #     for ent in doc.ents:
        #         entities.append(MultilingualEntity(
        #             text=ent.text,
        #             label=ent.label_,
        #             start=ent.start_char,
        #             end=ent.end_char,
        #             confidence=0.8,
        #             language=language
        #         ))
        
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
        
        # Use lightweight translation (transformers disabled for deployment)
        try:
            from deep_translator import GoogleTranslator
            return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        except Exception as e:
            logger.warning(f"Translation failed: {e}")
            return text  # Return original text if translation fails

# Global instance
multilingual_nlp = MultilingualNLPEngine()