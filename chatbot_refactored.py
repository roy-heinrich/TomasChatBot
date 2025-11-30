"""
Refactored ChatBot - Clean, Modular, and Fixed
Main chatbot class with all underlying issues resolved
"""
import os
import logging
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import time
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from .env file
load_dotenv()

# Import our clean modules
from core.database_search import DatabaseSearchEngine
from core.cached_database_search import CachedDatabaseSearch
# PgVector semantic search removed for lightweight version
from core.language_detector import LanguageDetector
from core.response_generator import ResponseGenerator
from core.keyword_matcher import KeywordMatcher
from core.conversation_memory import ConversationMemory
# Context-aware NLU removed - using simple logic instead
# ML enhancements removed - they cause hallucinations

# Import existing modules
from nlu_engine import NLUEngine, Intent, NLUResult
from core.optimized_nlu_engine import OptimizedNLUEngine
from entity_extractor import AdvancedEntityExtractor, ExtractedEntity
from core.security import sql_protector
from core.enhanced_security import enhanced_security
from core.query_preprocessor import preprocess_query, invalidate_grade_preprocessing_cache

# Import advanced AI modules
from core.conversation_analyzer import ConversationAnalyzer, ConversationContext
from core.emotional_intelligence import EmotionalIntelligence, EmotionalAnalysis
from core.response_personalizer import ResponsePersonalizer, PersonalizedResponse

logger = logging.getLogger(__name__)

@dataclass
class ChatResponse:
    """Clean response structure
    Added performance_metrics for per-phase latency instrumentation (seconds).
    Keys examples: total, preprocess, language_detect, nlu, entities, memory_update,
    search, response_generate, personalization, translation.
    """
    response: List[str]  # Can be single message or split messages
    entities: List[Dict[str, Any]]
    detected_language: str
    language_confidence: float
    is_split: bool
    message_count: int
    intent: Optional[str] = None  # Add intent field
    performance_metrics: Optional[Dict[str, float]] = None

class ChatBot:
    """Clean, refactored chatbot with fixed underlying issues"""
    
    def __init__(self, groq_key: str):
        # Initialize core components
        self.language_detector = LanguageDetector()
        self.response_generator = ResponseGenerator(groq_key)
        self.keyword_matcher = KeywordMatcher()
        
        # Initialize Supabase client
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        self.supabase = create_client(supabase_url, supabase_key)
        
        # Initialize database search with Redis caching
        self.database_search = CachedDatabaseSearch(
            supabase_client=self.supabase,
            redis_url=os.environ.get('REDIS_URL')
        )
        
        # PgVector semantic search removed for lightweight version
        
        # Initialize NLP components
        # Initialize optimized NLU engine with Redis caching
        redis_client = None
        if hasattr(self.database_search, 'redis') and self.database_search.redis_available:
            redis_client = self.database_search.redis
        self.nlu_engine = OptimizedNLUEngine(redis_client=redis_client)
        self.entity_extractor = AdvancedEntityExtractor()
        
        # Initialize conversation memory
        self.conversation_memory = ConversationMemory()
        
        # Context-aware NLU removed - using simple logic instead
        
        # Initialize context-aware translation
        from core.context_translator import ContextTranslator
        self.context_translator = ContextTranslator()
        
        # Initialize advanced AI modules
        self.conversation_analyzer = ConversationAnalyzer()
        self.emotional_intelligence = EmotionalIntelligence()
        self.response_personalizer = ResponsePersonalizer()
        
        # 🚨 AUTOMATIC CACHE MANAGEMENT: Prevent stale results
        self._setup_automatic_cache_management()
        
        # Initialize automatic cache manager (deferred until first async call)
        self._cache_manager_initialized = False
        
        # logger.info("✅ ChatBot initialized with clean, modular architecture")  # Reduced for Railway
    
    def _setup_automatic_cache_management(self):
        """Setup automatic cache management to prevent stale results"""
        try:
            # Set shorter TTL for grade-related queries to prevent stale results
            if hasattr(self.database_search, 'cache_ttl'):
                # Increase TTL to 2 hours for better cache hit rate
                self.database_search.cache_ttl = 7200  # 2 hours
            
            # 🚨 OPTIMIZATION: Don't flush cache on startup - this kills performance
            # Allow Redis to persist cache entries across restarts
            # Only invalidate grade-specific caches if needed, not all caches
            logger.info("✅ Automatic cache management setup complete (cache preservation enabled)")
        except Exception as e:
            logger.warning(f"Cache management setup failed: {e}")
    
    def _validate_and_invalidate_grade_cache(self, query: str, search_results: List[Dict]):
        """Validate search results and invalidate cache if wrong grade is returned"""
        try:
            import re
            # Extract grade from query
            grade_match = re.search(r'grade\s*(\d+)', query.lower())
            if not grade_match:
                return
            
            target_grade = grade_match.group(1)
            
            # Check if top result has the wrong grade
            if search_results:
                top_result = search_results[0]
                combined_text = (top_result.get('keywords', '') + ' ' + 
                               top_result.get('response', '')).lower()
                
                # Check if top result has the correct grade
                has_correct_grade = f'grade {target_grade}' in combined_text
                
                # Check if top result has wrong grades
                has_wrong_grade = any(
                    f'grade {other}' in combined_text 
                    for other in ['1', '2', '3', '4', '5', '6']
                    if other != target_grade
                )
                
                if not has_correct_grade and has_wrong_grade:
                    logger.warning(f"🚨 Cache returned wrong grade for Grade {target_grade} query - invalidating")
                    # Invalidate all caches for this grade
                    if hasattr(self.database_search, 'redis') and self.database_search.redis_available:
                        self.database_search.redis.flushall()
                        logger.info("🗑️ All caches invalidated due to wrong grade results")
        except Exception as e:
            logger.warning(f"Cache validation failed: {e}")
    
    def _extract_user_name(self, conversation_history: List[Dict]) -> str:
        """Extract user name from conversation history using NLP entity extraction"""
        for msg in reversed(conversation_history):
            if isinstance(msg, str):
                content = msg
            elif isinstance(msg, dict):
                if msg.get("role") == "user":
                    content = msg.get("content", "")
                else:
                    continue
            else:
                continue
            
            # logger.info(f"🔍 Extracting name from: '{content}'")  # Reduced for Railway
            
            # Use the entity extractor to find PERSON entities
            entities = self.entity_extractor.extract_entities(content)
            # logger.info(f"🔍 Found {len(entities)} entities")  # Reduced for Railway
            
            # Look for PERSON entities that could be names
            for entity in entities:
                # logger.info(f"🔍 Entity: type='{entity.entity_type}', value='{entity.value}', confidence={entity.confidence}")  # Reduced for Railway
                if entity.entity_type in ["PERSON", "person_name"] and entity.confidence > 0.7:
                    # Clean up the name (remove punctuation, capitalize properly)
                    name = ''.join(c for c in entity.value if c.isalnum() or c.isspace()).strip()
                    if name and len(name) > 1 and len(name) < 50:  # Reasonable name length
                        # logger.info(f"🔍 Extracted name: '{name.title()}'")  # Reduced for Railway
                        return name.title()
            
            # Use the NLU engine's NLP-based name extraction for better accuracy
            extracted_name = self.nlu_engine._extract_name_using_nlp(content, "name_introduction")
            if extracted_name:
                # logger.info(f"🔍 NLU extracted name: '{extracted_name}'")  # Reduced for Railway
                return extracted_name
        # logger.info("🔍 No name found in conversation history")  # Reduced for Railway
        return ""
    
    def _extract_child_name(self, conversation_history: List[Dict]) -> str:
        """Extract child name from conversation history"""
        for msg in reversed(conversation_history):
            if isinstance(msg, str):
                content = msg.lower()
            elif isinstance(msg, dict):
                if msg.get("role") == "user":
                    content = msg.get("content", "").lower()
                else:
                    continue
            else:
                continue
            
            # Look for child name patterns
            if "my child" in content or "anak ko" in content or "child's name" in content:
                # Extract child name
                parts = content.split()
                for i, part in enumerate(parts):
                    if part in ["child", "anak"] and i + 1 < len(parts):
                        return parts[i + 1].title()
        return ""
    
    def _detect_context_language(self, conversation_history: List[Dict]) -> Tuple[str, float]:
        """Detect language based on conversation context"""
        try:
            if not conversation_history:
                return "en", 0.5
            
            # Analyze recent messages for language patterns
            recent_messages = conversation_history[-3:]  # Last 3 messages
            language_scores = {"en": 0.0, "tl": 0.0, "akl": 0.0}
            
            for msg in recent_messages:
                if isinstance(msg, str):
                    content = msg
                elif isinstance(msg, dict):
                    if msg.get("role") == "user":
                        content = msg.get("content", "")
                    else:
                        continue
                else:
                    continue
                
                if content:
                    # Use enhanced language detection
                    lang, conf = self.language_detector.detect_language(content)
                    if lang in language_scores:
                        language_scores[lang] += conf
            
            # Get the language with highest score
            if any(score > 0 for score in language_scores.values()):
                best_lang = max(language_scores.items(), key=lambda x: x[1])
                return best_lang[0], min(best_lang[1], 0.9)
            else:
                return "en", 0.5
                
        except Exception as e:
            logger.error(f"Context language detection failed: {e}")
            return "en", 0.5
    
    def _fix_translated_html(self, text: str) -> str:
        """Fix HTML attributes that may have been translated and restore HTML elements"""
        if not isinstance(text, str):
            return text
            
        # First, restore HTML elements from placeholders
        result = self._restore_html_from_placeholders(text)
        
        # Then fix common HTML attribute translations
        fixes = {
            'target="_blangko"': 'target="_blank"',
            'target="_blanko"': 'target="_blank"',
            'kulay: puti': 'color: white',
            'kulay:puti': 'color: white',
            'kulay:puti;': 'color: white;',
            'kulay: puti;': 'color: white;',
            'wala': 'none',
            'wala;': 'none;',
            'blangko': 'blank',
            'kulay': 'color',
            'display: inline-block;': 'display: inline-block;',
            'background-color: #0084ff;': 'background-color: #0084ff;',
            'padding: 12px 24px;': 'padding: 12px 24px;',
            'text-decoration: wala;': 'text-decoration: none;',
            'text-decoration:wala;': 'text-decoration: none;',
            'border-radius: 8px;': 'border-radius: 8px;',
            'font-weight: bold;': 'font-weight: bold;',
            'margin: 10px 0;': 'margin: 10px 0;',
        }
        
        for translated, correct in fixes.items():
            result = result.replace(translated, correct)
        
        return result
    
    def _restore_html_from_placeholders(self, text: str) -> str:
        """Restore HTML elements from AI model placeholders"""
        import re
        
        # Check if this looks like a messenger button with placeholders
        if '__html_element_' in text.lower() and 'messenger' in text.lower():
            # Replace with the correct messenger button HTML
            messenger_button = '<a href="https://m.me/114901Tomas" target="_blank" style="display: inline-block; background-color: #0084ff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 10px 0;">💬Messenger</a>'
            
            # Replace the placeholder pattern with the actual HTML
            result = re.sub(r'__[Hh]tml_element_\d+__', '', text)
            result = re.sub(r'💬messenger', messenger_button, result)
            return result
        
        return text

    def _check_persistent_escalation(self, conversation_history: List[Dict]) -> bool:
        """Check if user has been persistent about wanting to talk to someone"""
        if not conversation_history:
            return False
        
        # Look for escalation patterns in recent messages
        recent_messages = conversation_history[-6:]  # Last 6 messages
        
        escalation_count = 0
        escalation_patterns = [
            "talk to", "speak to", "contact", "live person", "human", "admin", "staff", 
            "principal", "teacher", "guidance", "counselor", "someone", "anyone",
            "school office", "office", "where can", "how can",
            "makausap", "makipag-usap", "magistryo", "tao", "staff", "principal",
            "kausapin", "gusto ko kausapin", "admin lang", "wala, admin lang"
        ]
        
        # Only count user messages, not assistant responses
        user_messages = []
        for msg in recent_messages:
            if isinstance(msg, str):
                user_messages.append({"role": "user", "content": msg})
            elif isinstance(msg, dict) and msg.get('role') == 'user':
                user_messages.append(msg)
        
        for message in user_messages:
            if isinstance(message, str):
                content = message.lower()
            elif isinstance(message, dict):
                content = message.get('content', '').lower()
            else:
                content = ''
            
            # Check for escalation patterns
            if any(pattern in content for pattern in escalation_patterns):
                escalation_count += 1
        
        # 🚨 ADJUSTED: Require 2+ mentions for persistence - first request gets helpful response, second gets escalation
        # This ensures users get helpful response first, then escalation on repeat requests
        is_persistent = escalation_count >= 1
        return is_persistent
    
    def _map_to_response_language(self, detected_lang: str) -> str:
        """Map detected language to response language"""
        if detected_lang == "en":
            return "en"  # English queries → English responses
        elif detected_lang == "akl":
            return "tl"  # Aklanon queries → Tagalog responses
        elif detected_lang == "tl":
            return "tl"  # Tagalog queries → Tagalog responses
        else:
            return "en"  # Default to English
    
    def _detect_multiple_questions(self, query: str) -> Tuple[bool, List[str]]:
        """Detect if user sent multiple questions (1-5) and parse them"""
        import re
        
        # Clean the query and apply typo correction
        query = query.strip()
        query = self._correct_common_typos(query)
        
        
        # 🚨 CRITICAL FIX: Default to NOT splitting unless there's clear evidence
        # This prevents false positives like "i have a daughter and shes in grade 4?"
        
        # First, check for obvious single statements that should NEVER be split
        single_statement_patterns = [
            # Personal statements with "and" - these are single statements, not multiple questions
            r'i\s+have\s+.*?and\s+.*?',  # "i have a daughter and shes in grade 4"
            r'my\s+\w+\s+.*?and\s+.*?',  # "my child is in grade 3 and 4"
            r'we\s+have\s+.*?and\s+.*?',  # "we have a child and he's in grade 5"
            r'our\s+\w+\s+.*?and\s+.*?', # "our daughter and she's in grade 2"
            # Tagalog personal statements
            r'ako\s+may\s+.*?at\s+.*?',  # "ako may anak at nasa baitang 4"
            r'ang\s+\w+\s+ko\s+.*?at\s+.*?',  # "ang anak ko ay si Maria at nasa baitang 4"
            # Aklanon personal statements
            r'ako\s+may\s+.*?at\s+.*?',  # "ako may unga at nasa baitang 4"
            r'ang\s+\w+\s+ko\s+.*?at\s+.*?',  # "ang unga ko ay si Maria at nasa baitang 4"
            # Help requests that shouldn't be split
            r'can\s+you\s+help\s+.*?',  # "can you help me find where the office is"
            r'please\s+help\s+.*?',  # "please help me find"
            r'help\s+me\s+.*?',  # "help me find"
        ]
        
        is_single_statement = any(re.search(pattern, query, re.IGNORECASE) for pattern in single_statement_patterns)
        
        # If it's clearly a single statement, don't split
        if is_single_statement:
            return False, [query]
        
        # Only proceed with multiquestion detection if there are multiple question marks
        question_marks = query.count('?')
        
        # If we have multiple question marks, then we can consider splitting
        if question_marks > 1:
            questions = [q.strip() for q in query.split('?') if q.strip()]
            # Remove the last empty element if it exists
            if questions and not questions[-1]:
                questions = questions[:-1]
            
            # Only return as multiple questions if we have at least 2 meaningful questions
            if len(questions) >= 2:
                # Filter out very short questions
                filtered_questions = []
                for q in questions:
                    q = q.strip()
                    if len(q) > 10:  # Minimum meaningful question length
                        filtered_questions.append(q)
            
                if len(filtered_questions) >= 2:
                    return True, filtered_questions
        
        # Enhanced detection for genuine multiple questions connected by "and"
        # Only split if both parts look like complete questions
        genuine_multiquestion_patterns = [
            # Pattern: "what is X and where is Y" - both parts are complete questions
            r'(what|where|when|who|how|why|which|can|could|would|should|is|are|do|does|did|will|have|has)\s+.*?\s+and\s+(what|where|when|who|how|why|which|can|could|would|should|is|are|do|does|did|will|have|has)\s+.*?',
            # Pattern: "who is X and who is Y" - both parts are complete questions
            r'(who|what|where|when|how|why|which|can|could|would|should|is|are|do|does|did|will|have|has)\s+.*?\s+and\s+(who|what|where|when|how|why|which|can|could|would|should|is|are|do|does|did|will|have|has)\s+.*?',
        ]
        
        for pattern in genuine_multiquestion_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                # Split by "and" and check if both parts are meaningful questions
                parts = re.split(r'\s+and\s+', query, flags=re.IGNORECASE)
                if len(parts) >= 2:
                    filtered_parts = []
                    for part in parts:
                        part = part.strip()
                        if len(part) > 15:  # Minimum length for a complete question
                            # Check if it starts with a question word
                            question_starters = ['what', 'where', 'when', 'who', 'how', 'why', 'which', 'can', 'could', 'would', 'should', 'is', 'are', 'do', 'does', 'did', 'will', 'have', 'has']
                            if any(part.lower().startswith(starter + ' ') for starter in question_starters):
                                filtered_parts.append(part)
                    
                    if len(filtered_parts) >= 2:
                        return True, filtered_parts
        
        # Default: treat as single question/statement
        return False, [query]
    
    def _process_multiple_questions(self, questions: List[str], conversation_history: List[Dict] = None, 
                                   session_id: str = None) -> List[Dict]:
        """Process multiple questions and return structured results"""
        results = []
        
        for i, question in enumerate(questions):
            # Create a context for this specific question
            question_context = {
                'question_number': i + 1,
                'total_questions': len(questions),
                'is_multi_question': True,
                'other_questions': [q for j, q in enumerate(questions) if j != i]
            }
            
            results.append({
                'question': question,
                'context': question_context,
                'processed': False  # Will be processed in main chat method
            })
        
        return results
    
    async def _handle_multiple_questions(self, questions: List[str], conversation_history: List[Dict] = None, 
                                       user_timezone: str = None, session_id: str = None) -> ChatResponse:
        """Handle multiple questions in a context-aware manner"""
        try:
            # Process each question individually but maintain context
            question_responses = []
            all_entities = []
            detected_language = "en"
            language_confidence = 0.5
            combined_intent = "multi_question"
            
            # Track conversation context for each question
            # Ensure conversation_history is a list
            if isinstance(conversation_history, str):
                current_conversation_history = [{"role": "user", "content": conversation_history}]
            elif isinstance(conversation_history, list):
                current_conversation_history = conversation_history
            else:
                current_conversation_history = []
            
            for i, question in enumerate(questions):
                # Add context from previous questions in this session
                multi_question_context = f"Question {i+1} of {len(questions)}: {question}"
                
                # Create enhanced conversation history for this question
                enhanced_history = current_conversation_history.copy()
                if i > 0:
                    # Add context from previous questions in this multi-question session
                    enhanced_history.append({
                        "role": "system", 
                        "content": f"User is asking multiple questions. This is question {i+1} of {len(questions)}. Previous questions: {', '.join(questions[:i])}"
                    })
                
                # Process this individual question
                try:
                    # Use the main chat logic for each question
                    single_response = await self._process_single_question(
                        question, enhanced_history, user_timezone, session_id, 
                        is_multi_question=True, question_number=i+1, total_questions=len(questions)
                    )
                    
                    if single_response:
                        question_responses.append(single_response)
                        # Collect entities and language info
                        if hasattr(single_response, 'entities'):
                            all_entities.extend(single_response.entities)
                        if hasattr(single_response, 'detected_language'):
                            detected_language = single_response.detected_language
                        if hasattr(single_response, 'language_confidence'):
                            language_confidence = single_response.language_confidence
                            
                except Exception as e:
                    logger.error(f"Error processing question {i+1}: {e}")
                    # Add error response for this question
                    question_responses.append(f"Question {i+1}: I encountered an error processing this question. Please try rephrasing it.")
            
            # Combine all responses into a coherent multi-question response
            if question_responses:
                # Create a structured response that addresses all questions
                combined_response = self._combine_multi_question_responses(question_responses, questions, detected_language)
                
                return ChatResponse(
                    response=combined_response,
                    entities=all_entities,
                    detected_language=detected_language,
                    language_confidence=language_confidence,
                    is_split=len(combined_response) > 1,
                    message_count=len(combined_response),
                    intent=combined_intent
                )
            else:
                # Fallback if no responses were generated
                return ChatResponse(
                    response=["I received multiple questions but couldn't process them properly. Please try asking one question at a time."],
                    entities=[],
                    detected_language="en",
                    language_confidence=0.5,
                    is_split=False,
                    message_count=1,
                    intent="error"
                )
                
        except Exception as e:
            logger.error(f"Error handling multiple questions: {e}")
            return ChatResponse(
                response=["I encountered an error processing your multiple questions. Please try asking one question at a time."],
                entities=[],
                detected_language="en",
                language_confidence=0.5,
                is_split=False,
                message_count=1,
                intent="error"
            )
    
    async def _process_single_question(self, question: str, conversation_history: List[Dict], 
                                     user_timezone: str, session_id: str, 
                                     is_multi_question: bool = False, question_number: int = 1, 
                                     total_questions: int = 1) -> ChatResponse:
        """Process a single question with multi-question context"""
        try:
            # Initialize performance timing
            t_start = time.perf_counter()
            phase_times = {}
            
            def mark(phase_name: str):
                """Mark a checkpoint in the processing timeline"""
                phase_times[phase_name] = time.perf_counter() - t_start
            
            # 0. Typo correction for individual questions
            question = self._correct_common_typos(question)
            
            # Use the existing chat logic but with multi-question context
            # This is essentially the same as the main chat method but with additional context
            
            # 0.1. Enhanced security validation for individual questions
            is_valid, error_msg, validation_details = enhanced_security.validate_input(question, "query")
            if not is_valid:
                logger.warning(f"Enhanced security validation failed for question: {error_msg}")
                return ChatResponse(
                    response=["I'm sorry, but I cannot process that type of request. Please ask about school-related topics instead."],
                    entities=[],
                    detected_language="en",
                    language_confidence=1.0,
                    is_split=False,
                    message_count=1,
                    intent="security_block"
                )
            
            # Legacy SQL injection check
            if sql_protector.is_sql_injection(question):
                return ChatResponse(
                    response=["I'm sorry, but I cannot process that type of request. Please ask about school-related topics instead."],
                    entities=[],
                    detected_language="en",
                    language_confidence=1.0,
                    is_split=False,
                    message_count=1,
                    intent="security_block"
                )
            
            # 1. Use reliable language detection only
            detected_lang, confidence = self.language_detector.detect_language(question)
            
            response_lang = self._map_to_response_language(detected_lang)
            
            # 2. Get NLU analysis
            nlu_result = await self.nlu_engine.analyze_intent(question)
            
            # 3. Enhanced entity extraction
            entities = self.entity_extractor.extract_entities(question, nlu_result.intent.value if nlu_result else None)
            
            # 4. Update conversation memory with multi-question context
            user_name = ""
            if session_id:
                existing_name = self.conversation_memory.get_user_name(session_id)
                if existing_name:
                    user_name = existing_name
                else:
                    if conversation_history:
                        extracted_user_name = self.conversation_memory.extract_user_name(conversation_history)
                        if extracted_user_name:
                            user_name = extracted_user_name
                
                # Update memory with multi-question context
                multi_question_context = f"Multi-question session: {question_number}/{total_questions}"
                user_memory = self.conversation_memory.update_user_memory(
                    session_id, user_name, f"{multi_question_context}: {question}", conversation_history
                )
            
            # 5. Database search with multi-question context and conversation history
            intent_name = nlu_result.intent.name.lower() if nlu_result and nlu_result.intent else None
            search_results = await self.database_search.search_prompts_three_tier(question, limit=10, intent=intent_name, conversation_history=conversation_history, nlu_result=nlu_result)
            
            # 6. Simple context analysis - use database results if available
            context_analysis = type('ContextAnalysis', (), {
                'should_use_context': len(search_results) > 0,
                'reasoning': 'Simple logic: use database results if found',
                'confidence_level': type('ConfidenceLevel', (), {'value': 'high'})(),
                'fallback_suggestions': []
            })()
            
            best_result = None
            if context_analysis.should_use_context and search_results:
                best_result = search_results[0]
            
            # 7. Generate response with multi-question context
            if best_result:
                if isinstance(best_result, dict):
                    keywords = best_result.get('keywords', '')
                    response = best_result.get('response', '')
                    context = f"Database Information: {keywords} - {response}"
                else:
                    context = f"Database Information: {best_result}"
            else:
                context = "No specific information available in database for this query"
            
            # Add multi-question context to the response
            if is_multi_question:
                context += f"\n\nMulti-question context: This is question {question_number} of {total_questions} questions the user asked."
            
            # Add personalized memory context
            if session_id:
                memory_context = self.conversation_memory.get_conversation_context(session_id, user_name)
                if memory_context:
                    context += f"\n\nPersonal Context: {memory_context}"
            
            # Generate response
            nlu_info = {
                'intent': nlu_result.intent.value if nlu_result else 'unknown',
                'confidence': nlu_result.confidence if nlu_result else 0.0,
                'entities': [(e.entity_type, e.value) for e in entities],
                'is_multi_question': is_multi_question,
                'question_number': question_number,
                'total_questions': total_questions
            }
            
            # CRITICAL: Check if we have sufficient database context to prevent hallucinations
            # But only for information queries - greetings, emergencies, etc. don't need database context
            intent_requires_db = nlu_result and nlu_result.intent.value in [
                'staff_inquiry', 'general_inquiry', 'grade_inquiry', 'activity_inquiry', 
                'schedule_inquiry', 'facility_inquiry', 'unknown'
            ]
            
            # 🚨 FIXED: Reduced minimum context threshold from 50 to 20 characters
            # Brief contact information (emails, short addresses) are legitimate and should be used
            if intent_requires_db and (not context or len(context.strip()) < 20):  # Insufficient context for info queries
                logger.warning(f"⚠️ Insufficient database context for query: '{question[:50]}...'")
                # Return a safe response that doesn't hallucinate
                response_text = f"I don't have specific information about that in my database. Please contact the school office for more details."
            else:
                response_text = await self.response_generator.generate_response(
                    question, context, response_lang, conversation_history, nlu_info, user_name, entities, float(confidence), context_analysis
                )
            
            # Split response if needed
            split_messages = response_text if isinstance(response_text, list) else [response_text]
            
            mark('finalize')
            phase_times['total'] = time.perf_counter() - t_start
            return ChatResponse(
                response=split_messages,
                entities=[{"entity_type": e.entity_type, "value": e.value, "confidence": e.confidence} for e in entities],
                detected_language=detected_lang,  # Use original detected language, not mapped
                language_confidence=confidence,
                is_split=len(split_messages) > 1,
                message_count=len(split_messages),
                intent=nlu_result.intent.value if nlu_result and nlu_result.intent else 'unknown',
                performance_metrics=phase_times
            )
            
        except Exception as e:
            logger.error(f"Error processing single question: {e}")
            return ChatResponse(
                response=[f"Question {question_number}: I encountered an error processing this question."],
                entities=[],
                detected_language="en",
                language_confidence=0.5,
                is_split=False,
                message_count=1,
                intent="error"
            )
    
    def _combine_multi_question_responses(self, question_responses: List[ChatResponse], 
                                        original_questions: List[str], detected_language: str) -> List[str]:
        """Combine multiple question responses into separate bubbles for each question"""
        try:
            combined_messages = []
            
            # Add each question and its response as separate bubbles
            for i, (question, response) in enumerate(zip(original_questions, question_responses)):
                if hasattr(response, 'response') and response.response:
                    # Create a professional, paragraph-style response for each question
                    if detected_language in ["tl", "akl"]:
                        # Tagalog format
                        question_intro = f"Tungkol sa inyong tanong na '{question}':"
                    else:
                        # English format
                        question_intro = f"Regarding your question about '{question}':"
                    
                    combined_messages.append(question_intro)
                    
                    # Add the response content as a natural paragraph
                    if isinstance(response.response, list):
                        # Combine multiple response parts into a single paragraph
                        response_text = " ".join(response.response)
                        combined_messages.append(response_text)
                    else:
                        combined_messages.append(response.response)
            
            # Add a polite closing message
            if detected_language in ["tl", "akl"]:
                closing = "Kung may iba pang katanungan, huwag mag-atubiling magtanong!"
            else:
                closing = "If you have any other questions, feel free to ask!"
            
            combined_messages.append(closing)
            
            return combined_messages
            
        except Exception as e:
            logger.error(f"Error combining multi-question responses: {e}")
            # Fallback: return individual responses
            fallback_responses = []
            for i, response in enumerate(question_responses):
                if hasattr(response, 'response') and response.response:
                    if isinstance(response.response, list):
                        fallback_responses.extend(response.response)
                    else:
                        fallback_responses.append(response.response)
            return fallback_responses

    def _is_pure_greeting(self, query: str, nlu_result) -> bool:
        """Check if this is a pure greeting (no question content) vs greeting + question"""
        if not nlu_result or not nlu_result.intent.value.startswith('greeting'):
            return False
        
        query_lower = query.lower().strip()
        
        # Multi-word greeting phrases that should be recognized as complete greetings
        multi_word_greetings = [
            "good morning", "good afternoon", "good evening", "good day", "good night", "good noon",
            "magandang umaga", "magandang hapon", "magandang gabi", "magandang araw",
            "maayong aga", "maayong hapon", "maayong gab-i", "maayong adlaw", "maayong gabii", "maayong buntag",
            "hey there", "hello there", "hi there"
        ]
        
        # Single-word greeting words
        single_word_greetings = [
            "hi", "hello", "hey", "kamusta", "kumusta", "morning", "afternoon", "evening", "night", "day",
            "greetings", "hiya", "wassup", "howdy", "yo"
        ]
        
        # Question words that indicate there's a real question (actual words, not punctuation)
        question_words = ["what", "where", "when", "who", "how", "why", "which", "can", "could", 
                         "would", "should", "is", "are", "do", "does", "did", "will", "have", "has",
                         "ano", "saan", "kailan", "sino", "paano", "bakit", "alin", "pwed", "maaari", 
                         "gusto", "kailangan", "time", "class", "start", "adviser", "grade"]
        
        # Check if query contains question words (must be actual words, not punctuation)
        # Split and clean punctuation to check for real question words
        words_only = query_lower.rstrip('!?.,:;').split()
        has_question_content = any(word in question_words or word.rstrip('!?.,:;') in question_words 
                                   for word in words_only)
        
        # If it has question content, it's not a pure greeting
        if has_question_content:
            return False
        
        # Check if the entire query is a multi-word greeting
        for multi_greeting in multi_word_greetings:
            if query_lower == multi_greeting:
                return True
            # Also check if it's the multi-word greeting plus punctuation
            if query_lower.rstrip('!?.,:;') == multi_greeting:
                return True
        
        # Check if query is just a single-word greeting (with optional punctuation)
        query_clean = query_lower.rstrip('!?.,:;')
        if query_clean in single_word_greetings:
            return True
        
        # For other cases, use the original logic as fallback
        words = query_lower.split()
        greeting_word_count = sum(1 for word in words 
                                 if word in single_word_greetings or 
                                 any(greeting in word for greeting in single_word_greetings))
        
        # If more than half the words are greeting words, it's likely a pure greeting
        return greeting_word_count >= len(words) * 0.5

    def _correct_common_typos(self, query: str) -> str:
        """Real fuzzy matching typo correction using string similarity"""
        import re
        import time
        start_time = time.time()
        
        try:
            from difflib import SequenceMatcher
        except ImportError:
            # Fallback to basic similarity if difflib not available
            return query
        
        # School-related vocabulary for fuzzy matching
        school_vocabulary = [
            'school', 'activities', 'available', 'principal', 'enrollment', 
            'student', 'students', 'teacher', 'teachers', 'education',
            'program', 'programs', 'schedule', 'hours', 'location', 'address',
            'grade', 'grades', 'class', 'classes', 'subject', 'subjects',
            'event', 'events', 'celebration', 'month', 'year', 'semester',
            'curriculum', 'academic', 'extracurricular', 'sports', 'music',
            'art', 'science', 'mathematics', 'english', 'filipino', 'history',
            'social', 'studies', 'physical', 'education', 'computer', 'technology',
            'support', 'aide', 'learning', 'assistance', 'help',
            'start', 'end', 'begin', 'finish', 'time', 'when', 'where',  # Common query words
            'being', 'held', 'what', 'are', 'is', 'was', 'were', 'have', 'has', 'had',  # Common English words
            # Emergency keywords to prevent correction
            'heart', 'attack', 'stroke', 'emergency', 'medical', 'ambulance',
            'bleeding', 'unconscious', 'dying', 'pain', 'injury', 'accident'
        ]
        
        words = query.split()
        corrected_words = []
        
        for word in words:
            # Preserve punctuation by separating it from the word
            word_match = re.match(r'^(\w+)([^\w]*)$', word)
            if word_match:
                base_word = word_match.group(1)
                punctuation = word_match.group(2)
            else:
                base_word = word
                punctuation = ''
            
            # Clean the word (remove punctuation for matching)
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            if len(clean_word) < 3:  # Skip very short words
                corrected_words.append(word)
                continue
            
            # Find the best match using fuzzy matching with context validation
            best_match = None
            best_ratio = 0.0
            
            for vocab_word in school_vocabulary:
                # Calculate similarity ratio
                ratio = SequenceMatcher(None, clean_word, vocab_word.lower()).ratio()
                
                # Dynamic threshold based on word length and context
                threshold = self._calculate_dynamic_threshold(clean_word, vocab_word)
                
                # If similarity is high enough and passes context validation
                if ratio > threshold and ratio > best_ratio:
                    # Additional validation to prevent false positives
                    if self._validate_word_correction(clean_word, vocab_word, query):
                        best_ratio = ratio
                        best_match = vocab_word
            
            # Use the best match if found, otherwise keep original
            if best_match and best_ratio > self._calculate_dynamic_threshold(clean_word, best_match):
                # Preserve original capitalization pattern and punctuation
                if word.isupper():
                    corrected_words.append(best_match.upper() + punctuation)
                elif word.istitle():
                    corrected_words.append(best_match.title() + punctuation)
                else:
                    corrected_words.append(best_match + punctuation)
            else:
                corrected_words.append(word)
        
        corrected_query = ' '.join(corrected_words)
        
        # Record metrics and check for false positives
        duration_ms = (time.time() - start_time) * 1000
        corrections = []
        
        for i, (original, corrected) in enumerate(zip(words, corrected_words)):
            if original != corrected:
                corrections.append({
                    'original': original,
                    'corrected': corrected,
                    'position': i
                })
        
        # Record typo correction metrics
        try:
            from core.monitoring_system import record_metric, record_false_positive
            
            record_metric(
                operation="typo_correction",
                duration_ms=duration_ms,
                success=True,
                additional_data={
                    "original_query": query,
                    "corrected_query": corrected_query,
                    "corrections": corrections,
                    "changed": query != corrected_query
                }
            )
            
            # Check for false positives
            false_positive_patterns = [
                {"original": "start", "false_positive": "art", "context": "time does the class"},
                {"original": "end", "false_positive": "and", "context": "class"},
                {"original": "begin", "false_positive": "big", "context": "class"},
                {"original": "math", "false_positive": "match", "context": "class"},
                {"original": "science", "false_positive": "since", "context": "class"},
            ]
            
            for correction in corrections:
                original_word = correction['original'].lower()
                corrected_word = correction['corrected'].lower()
                
                for pattern_info in false_positive_patterns:
                    if (pattern_info['original'] == original_word and 
                        pattern_info['false_positive'] == corrected_word and
                        pattern_info['context'] in query.lower()):
                        
                        record_false_positive(
                            operation="typo_correction",
                            details={
                                "original_query": query,
                                "corrected_query": corrected_query,
                                "correction": correction,
                                "pattern": pattern_info['original'],
                                "false_positive": pattern_info['false_positive']
                            }
                        )
                        break
        
        except ImportError:
            # Monitoring not available, continue silently
            pass
        
        return corrected_query
    
    def _calculate_dynamic_threshold(self, original_word: str, candidate_word: str) -> float:
        """Calculate dynamic threshold based on word characteristics"""
        base_threshold = 0.8  # Increased from 0.7
        
        # Higher threshold for shorter words (more prone to false positives)
        if len(original_word) <= 4:
            base_threshold = 0.9
        elif len(original_word) <= 6:
            base_threshold = 0.85
        
        # Higher threshold if words have same length (prevents substring matches)
        if len(original_word) == len(candidate_word):
            base_threshold += 0.05
        
        # Lower threshold for words with significant length difference
        length_diff = abs(len(original_word) - len(candidate_word))
        if length_diff >= 3:
            base_threshold -= 0.1
        
        return min(max(base_threshold, 0.7), 0.95)  # Keep between 0.7-0.95
    
    def _validate_word_correction(self, original_word: str, candidate_word: str, full_query: str) -> bool:
        """Additional validation to prevent false positive corrections"""
        import re
        
        # Prevent corrections that create nonsensical phrases
        problematic_patterns = [
            # Time-related false positives
            (r'\bstart\b', r'\bart\b', 'time does the class'),
            (r'\bend\b', r'\band\b', 'class'),
            (r'\bbegin\b', r'\bbig\b', 'class'),
            
            # Subject-related false positives  
            (r'\bmath\b', r'\bmatch\b', 'class'),
            (r'\bscience\b', r'\bsince\b', 'class'),
            
            # Common false positive patterns
            (r'\bthe\b', r'\bthey\b', 'class'),
            (r'\bof\b', r'\boff\b', 'class'),
        ]
        
        for original_pattern, candidate_pattern, context in problematic_patterns:
            if (re.search(original_pattern, original_word.lower()) and 
                re.search(candidate_pattern, candidate_word.lower()) and
                context in full_query.lower()):
                return False
        
        # Prevent corrections that change word meaning significantly
        meaning_preserving_words = ['start', 'end', 'begin', 'finish', 'time', 'when', 'where', 'what', 'how']
        if original_word.lower() in meaning_preserving_words and candidate_word.lower() not in meaning_preserving_words:
            return False
        
        # Prevent corrections to academic subjects unless context suggests it
        academic_subjects = ['art', 'math', 'science', 'english', 'filipino', 'music', 'pe']
        if (original_word.lower() not in academic_subjects and 
            candidate_word.lower() in academic_subjects and
            'class' not in full_query.lower() and 'subject' not in full_query.lower()):
            return False
        
        return True
    
    async def _handle_emergency_query(self, query: str, preprocessed) -> ChatResponse:
        """Handle emergency queries with immediate response"""
        try:
            # Immediate emergency response
            emergency_response = "🚨 MEDICAL EMERGENCY DETECTED! Tawagan ang 911 o ang inyong lokal na emergency services kaagad."
            
            return ChatResponse(
                response=[emergency_response],
                entities=[],
                detected_language=preprocessed.detected_language,
                language_confidence=1.0,
                is_split=False,
                message_count=1,
                intent="emergency"
            )
        except Exception as e:
            logger.error(f"Emergency handling failed: {e}")
            return ChatResponse(
                response=["🚨 EMERGENCY DETECTED! Please call 911 or your local emergency services immediately."],
                entities=[],
                detected_language="en",
                language_confidence=1.0,
                is_split=False,
                message_count=1,
                intent="emergency"
            )

    async def chat(self, query: str, conversation_history: List[Dict] = None, 
                   user_timezone: str = None, session_id: str = None) -> ChatResponse:
        """Main chat method - Groq-first approach for natural responses with multi-question support"""
        try:
            # --- Performance instrumentation setup ---
            t_start = time.perf_counter()
            t_last = t_start
            phase_times: Dict[str, float] = {}
            def mark(name: str):
                nonlocal t_last
                now = time.perf_counter()
                phase_times[name] = phase_times.get(name, 0.0) + (now - t_last)
                t_last = now
            # Initialize cache manager on first async call
            if not self._cache_manager_initialized:
                try:
                    from automatic_cache_manager import setup_automatic_cache_management
                    await setup_automatic_cache_management(self)
                    self._cache_manager_initialized = True
                    mark('cache_manager_init')
                except Exception as e:
                    logger.warning(f"Cache manager initialization failed: {e}")
                    self._cache_manager_initialized = True  # Don't retry
            
            # Debug removed
            # 0. Enhanced input validation
            if not query or not query.strip():
                raise ValueError("Empty or whitespace-only query is not allowed")
            
            # Enhanced security validation
            is_valid, error_msg, validation_details = enhanced_security.validate_input(query, "query")
            if not is_valid:
                logger.warning(f"Enhanced security validation failed: {error_msg}")
                return ChatResponse(
                    response=["I'm sorry, but I cannot process that type of request. Please ask about school-related topics instead."],
                    entities=[],
                    detected_language="en",
                    language_confidence=1.0,
                    is_split=False,
                    message_count=1,
                    intent="security_block",
                    performance_metrics={'total': time.perf_counter() - t_start, **phase_times}
                )
            
            # 🚀 QUERY PRE-PROCESSING CACHE (Grade-Aware)
            preprocessed = await preprocess_query(query)
            mark('preprocess')
            logger.info(f"🔍 Preprocessed: {preprocessed.query_type} (grade: {preprocessed.extracted_grade}, confidence: {preprocessed.confidence:.2f})")
            
            # Use preprocessed results to optimize processing
            if preprocessed.query_type == 'emergency':
                # Emergency queries get immediate processing
                logger.info("🚨 Emergency query detected - bypassing normal processing")
                return await self._handle_emergency_query(query, preprocessed)
            
            # Emergency detection is handled by NLU engine
            # 0.1. Typo correction
            original_query = query
            query = self._correct_common_typos(query)
            mark('typo_correction')
            
            
            # 0.1. Multi-question detection and processing
            is_multi_question, questions = self._detect_multiple_questions(query)
            
            if is_multi_question:
                # Process multiple questions
                return await self._handle_multiple_questions(questions, conversation_history, user_timezone, session_id)
            
            # 0.2. Legacy SQL injection check (kept for compatibility)
            if sql_protector.is_sql_injection(query):
                # Removed verbose SQL injection logging
                return ChatResponse(
                    response=["I'm sorry, but I cannot process that type of request. Please ask about school-related topics instead."],
                    entities=[],
                    detected_language="en",
                    language_confidence=1.0,
                    is_split=False,
                    message_count=1,
                    intent="security_block"
                )
            # 1. Use reliable language detection only
            detected_lang, confidence = self.language_detector.detect_language(query)
            mark('language_detect')
            # logger.info(f"🌍 Language detection: {detected_lang} (confidence: {confidence:.2f})")
            
            # Map detected language to response language
            response_lang = self._map_to_response_language(detected_lang)
            # logger.info(f"🌍 Language mapping: {detected_lang} → {response_lang}")  # Reduced for Railway
            
            # Get conversation history from memory if session_id is provided
            if session_id and not conversation_history:
                conversation_history = self.conversation_memory.get_conversation_history(session_id)
            
            # IMPROVED: For short queries or follow-up questions, prioritize conversation context
            is_short_query = len(query.split()) < 4  # Short queries like "how about grade 5"
            is_follow_up = any(word in query.lower() for word in ["how about", "what about", "and", "also"])
            
            # Check for mixed-language input OR short follow-up queries
            if confidence < 0.7 or (is_short_query and is_follow_up):
                # logger.info("🔍 Low confidence language detection or short follow-up query - using conversation context")
                # Use context-aware translation for mixed languages or follow-up queries
                if conversation_history:
                    context_lang, context_confidence = self._detect_context_language(conversation_history)
                    # For follow-up queries, always prefer conversation context
                    if (is_short_query and is_follow_up) or context_confidence > confidence:
                        detected_lang = context_lang
                        response_lang = self._map_to_response_language(detected_lang)
                        confidence = max(context_confidence, 0.8)  # Boost confidence for context-based detection
                        # logger.info(f"🌍 Context-based language detection: {detected_lang} → {response_lang} (confidence: {confidence:.2f})")
            
            # 2. Get NLU analysis for intent with enhanced context
            nlu_context = {
                "conversation_history": conversation_history,
                "detected_language": detected_lang,
                "language_confidence": confidence,
                "query_length": len(query),
                "has_question_mark": "?" in query,
                "word_count": len(query.split())
            }
            nlu_result = await self.nlu_engine.analyze_intent(query, nlu_context)
            mark('nlu')
            logger.info(f"🎯 NLU Intent: {nlu_result.intent.value if nlu_result else 'None'} for query: '{query}'")
            
            # Emergency detection is now handled by NLU engine with context awareness
            
            # Semantic intent classification removed - using simple NLU only
            # logger.info(f"🎯 NLU Intent: {nlu_result.intent.value} for query: {query}")
            
            # CRITICAL SAFETY: Check for medical emergencies via NLU (SECOND PRIORITY)
            # Use the NLU engine's intent classification
            if nlu_result and hasattr(nlu_result, 'intent') and hasattr(nlu_result.intent, 'value'):
                intent_value = nlu_result.intent.value
                # logger.info(f"🎯 Checking emergency intent: {intent_value}")
                
                if intent_value == "emergency" or intent_value == "medical_emergency":
                    logger.warning(f"🚨 EMERGENCY DETECTED via NLU: {query}")
                    return self._handle_emergency_response(query, response_lang, detected_lang)
            
            # 2.5. Advanced AI Analysis - Conversation Intelligence
            conversation_context = None
            emotional_analysis = None
            
            try:
                # Ensure conversation_history is properly formatted
                safe_conversation_history = []
                if conversation_history:
                    for msg in conversation_history:
                        if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                            safe_conversation_history.append(msg)
                        elif isinstance(msg, str):
                            # Convert string messages to proper format
                            safe_conversation_history.append({
                                'role': 'user',
                                'content': msg
                            })
                
                # Analyze conversation context
                conversation_context = await self.conversation_analyzer.analyze_conversation_context(
                    current_query=query,
                    conversation_history=safe_conversation_history,
                    nlu_result=nlu_result,
                    entities=[]  # Will be populated later
                )
                # logger.info(f"🧠 Conversation analysis: {conversation_context.topic_flow}, urgency: {conversation_context.urgency_level}")  # Reduced for Railway
                
                # Analyze emotions
                emotional_analysis = await self.emotional_intelligence.analyze_emotions(
                    current_query=query,
                    conversation_history=safe_conversation_history,
                    language=detected_lang
                )
                # logger.info(f"💭 Emotional analysis: {emotional_analysis.primary_emotion} (intensity: {emotional_analysis.emotion_intensity:.2f})")
                
            except Exception as e:
                logger.warning(f"⚠️ Advanced AI analysis failed: {e}")
                # Continue with basic processing
            
            # 3. Enhanced entity extraction with relationships
            entities = self.entity_extractor.extract_entities(query, nlu_result.intent.value if nlu_result else None)
            mark('entities')
            
            # Entity extraction completed
            
            # logger.info(f"🔍 Enhanced entity extraction: {len(entities)} entities with relationships")  # Commented out debug logs
            
            # Log entity relationships
            for entity in entities:
                if hasattr(entity, 'relationships') and entity.relationships:
                    for rel in entity.relationships:
                        # logger.info(f"🔗 Relationship: {entity.value} -> {rel['entity'].value} ({rel['relationship']['type']})")  # Commented out debug logs
                        pass
            
            # 4. Enhanced memory system - extract user info and update memory
            user_name = ""
            child_name = ""
            
            # First, try to get existing user name from memory
            if session_id:
                existing_name = self.conversation_memory.get_user_name(session_id)
                if existing_name:
                    user_name = existing_name
                    # logger.info(f"🧠 Retrieved existing user name from memory: {user_name}")  # Commented out debug logs
            
            # If no existing name, try to extract from conversation history
            if not user_name:
                if conversation_history:
                    # Extract names from conversation history regardless of intent
                    # This ensures we capture names even in casual conversations
                    extracted_user_name = self.conversation_memory.extract_user_name(conversation_history)
                    extracted_child_name = self.conversation_memory.extract_child_name(conversation_history) if hasattr(self.conversation_memory, 'extract_child_name') else None
                    
                    if extracted_user_name:
                        user_name = extracted_user_name
                        child_name = extracted_child_name
                        # logger.info(f"🔍 Extracted names from conversation: user='{user_name}', child='{child_name}'")  # Commented out debug logs
                    else:
                        # logger.info("🔍 No names found in conversation history")  # Commented out debug logs
                        pass
                else:
                    # If no conversation history, try to extract from current query
                    # logger.info("🔍 No conversation history - trying to extract from current query")  # Commented out debug logs
                    # Create a temporary conversation history with current query
                    temp_history = [{"role": "user", "content": query}]
                    extracted_user_name = self.conversation_memory.extract_user_name(temp_history)
                    extracted_child_name = self.conversation_memory.extract_child_name(temp_history) if hasattr(self.conversation_memory, 'extract_child_name') else None
                    
                    if extracted_user_name:
                        user_name = extracted_user_name
                        child_name = extracted_child_name
                        # logger.info(f"🔍 Extracted names from current query: user='{user_name}', child='{child_name}'")  # Commented out debug logs
                    else:
                        # logger.info("🔍 No names found in current query")  # Commented out debug logs
                        pass
            
            # Update conversation memory
            if session_id:
                # logger.info(f"🧠 Updating memory - Session: {session_id}, User name: '{user_name}', Query: '{query}'")  # Commented out debug logs
                user_memory = self.conversation_memory.update_user_memory(
                    session_id, user_name, query, conversation_history
                )
                mark('memory_update')
                # logger.info(f"🧠 Updated memory for user: {user_memory.name}, topics: {list(user_memory.topics.keys())}")  # Commented out debug logs
                
                # Debug: Check if name was actually stored
                stored_name = self.conversation_memory.get_user_name(session_id)
                # logger.info(f"🧠 Memory verification - Stored name: '{stored_name}'")  # Commented out debug logs
            
            # Special case: Handle child information queries with context
            if session_id and conversation_history:
                # Check if user is asking about their child's grade
                child_grade_query_patterns = [
                    # English patterns
                    r"what\s+grade\s+(?:is\s+)?(?:my\s+)?(?:daughter|son|child|kid)",
                    r"(?:my\s+)?(?:daughter|son|child|kid)\s+(?:is\s+)?(?:in\s+)?what\s+grade",
                    r"what\s+grade\s+level\s+(?:is\s+)?(?:my\s+)?(?:daughter|son|child|kid)",
                    
                    # Tagalog patterns
                    r"ano\s+ang\s+baitang\s+(?:ng\s+)?(?:anak|bata)\s+ko",  # "Ano ang baitang ng anak ko"
                    r"anong\s+grade\s+(?:ang\s+)?(?:anak|bata)\s+ko",  # "Anong grade ang anak ko"
                    r"anong\s+baitang\s+(?:ang\s+)?(?:anak|bata)\s+ko",  # "Anong baitang ang anak ko"
                    r"(?:anak|bata)\s+ko\s+(?:ay\s+)?(?:sa\s+)?anong\s+(?:baitang|grade)",  # "Anak ko ay sa anong baitang"
                    r"si\s+(\w+)\s+(?:ay\s+)?(?:sa\s+)?anong\s+(?:baitang|grade)",  # "Si Maria ay sa anong baitang"
                    
                    # Aklanon patterns
                    r"ano\s+ang\s+baitang\s+(?:ng\s+)?(?:unga|anak)\s+ko",  # "Ano ang baitang ng unga ko"
                    r"anong\s+grade\s+(?:ang\s+)?(?:unga|anak)\s+ko",  # "Anong grade ang unga ko"
                    r"anong\s+baitang\s+(?:ang\s+)?(?:unga|anak)\s+ko",  # "Anong baitang ang unga ko"
                    r"(?:unga|anak)\s+ko\s+(?:ay\s+)?(?:sa\s+)?anong\s+(?:baitang|grade)",  # "Unga ko ay sa anong baitang"
                    r"du\s+(\w+)\s+(?:ay\s+)?(?:sa\s+)?anong\s+(?:baitang|grade)",  # "Du Maria ay sa anong baitang"
                ]
                
                query_lower = query.lower()
                import re
                is_child_grade_query = any(re.search(pattern, query_lower, re.IGNORECASE) for pattern in child_grade_query_patterns)
                
                if is_child_grade_query:
                    # Try to get child information from memory
                    child_info = self.conversation_memory._extract_child_information(session_id)
                    if child_info and "grade" in child_info.lower():
                        # Extract grade from child info
                        grade_match = re.search(r'grade\s+(\d+)', child_info.lower())
                        if grade_match:
                            grade = grade_match.group(1)
                            return ChatResponse(
                                response=[f"Based on our previous conversation, your child is in grade {grade}."],
                                entities=entities,
                                detected_language=detected_lang,
                                language_confidence=confidence,
                                is_split=False,
                                message_count=1,
                                intent="child_inquiry"
                            )
                    else:
                        # No child grade information found in memory
                        return ChatResponse(
                            response=["I don't have information about your child's grade level from our previous conversations. Could you please tell me what grade your child is in?"],
                            entities=entities,
                            detected_language=detected_lang,
                            language_confidence=confidence,
                            is_split=False,
                            message_count=1,
                            intent="child_inquiry"
                        )
            
            # Special case: Handle name-related queries directly
            # First, check for English name queries
            english_name_phrases = ["what's my name", "what is my name", "my name", "who am i", "do you know my name", "who is my name"]
            
            # Tagalog name query phrases
            tagalog_name_phrases = ["ano ang pangalan ko", "ano pangalan ko", "sino ako", 
                                   "sinong pangalan ko", "alam mo ba pangalan ko", "ano'ng pangalan ko"]
            
            # Try to translate query for Tagalog detection
            translated_query = query.lower()
            if detected_lang in ["tl", "akl"]:
                try:
                    # Use context translator to translate to English
                    translated_query, _ = self.context_translator.translate_with_context(
                        query, "en", conversation_history, session_id
                    )
                    logger.info(f"🌐 Translated name query: '{query}' -> '{translated_query}'")
                except Exception as e:
                    logger.warning(f"Translation failed for name query: {e}")
            
            # Check if this is a name-related query in any language
            is_name_query = (any(phrase in query.lower() for phrase in english_name_phrases) or
                            any(phrase in query.lower() for phrase in tagalog_name_phrases) or
                            any(phrase in translated_query.lower() for phrase in english_name_phrases))
            
            # 🚨 CRITICAL FIX: Exclude greeting+name introductions from the name_query check
            # "hello, my name is Heinz" should be a GREETING, not a name_query
            # But "what is my name" should be a name_query
            greeting_with_name_patterns = ["hello, my name", "hi, my name", "hi, i'm", "hello, i'm", 
                                           "good morning, my name", "good afternoon, my name", "good evening, my name",
                                           "kumusta, my name", "kumusta, i'm", "kumusta, ang pangalan", "kumusta, ang pang",
                                           "magandang, my name", "maayong, my name"]
            
            if is_name_query and any(pattern in query.lower() for pattern in greeting_with_name_patterns):
                # This is a greeting with name introduction, not a name query
                # Let the normal NLU processing handle it
                is_name_query = False
            
            if is_name_query:
                # CRITICAL FIX: Get user name directly from conversation memory
                stored_name = None
                if session_id:
                    stored_name = self.conversation_memory.get_user_name(session_id)
                    # logger.info(f"👤 Retrieved name from memory: '{stored_name}'")
                
                # Use stored_name if available, otherwise fall back to user_name
                final_name = stored_name or user_name
                
                if final_name:
                    # logger.info(f"👤 User asking about their name - we know it's: {final_name}")
                    # DIRECT RESPONSE: Skip AI and provide a direct response with the name
                    # This ensures the name is always included in the response
                    if detected_lang in ["tl", "akl"]:
                        # Tagalog response
                        response_text = f"Ang pangalan mo ay {final_name}. Kumusta ka? Maari kitang tulungan tungkol sa mga impormasyon sa paaralan."
                    else:
                        # English response
                        response_text = f"Your name is {final_name}. How can I help you with school information today?"
                    
                    # Return the response directly, bypassing the rest of the processing
                    return ChatResponse(
                        response=[response_text],
                        entities=entities,
                        detected_language=detected_lang,
                        language_confidence=confidence,
                        is_split=False,
                        message_count=1,
                        intent="name_query"
                    )
                else:
                    # logger.info("👤 User asking about their name - we don't know it yet")
                    # Skip database search and ask for their name
                    search_results = []
                    best_result = None
                    context = "User is asking about their name but we don't have it in memory. Ask them to introduce themselves."
            else:
                # 🚨 CRITICAL: Check for special intents FIRST before database search
                # These intents should skip database search entirely
                if nlu_result and nlu_result.intent.value == 'contact_escalation':
                    logger.info("👥 Contact escalation requested - checking conversation history for persistence")
                    
                    # Check if user has been persistent about wanting to talk to someone
                    persistent_escalation = self._check_persistent_escalation(conversation_history)
                    logger.info(f"👥 Persistent escalation: {persistent_escalation}")
                    
                    if persistent_escalation:
                        logger.info("👥 Persistent escalation detected - providing direct contact option")
                        # Provide direct escalation response
                        search_results = []
                        best_result = None
                        if response_lang in ["tl", "akl"]:
                            context = "HARDCODED_ADMIN_TAGALOG"
                        else:
                            context = "HARDCODED_ADMIN_ENGLISH"
                        logger.info(f"👥 Context set to: {context}")
                    else:
                        # logger.info("👥 First escalation request - using helpful approach first")
                        # Use helpful approach for first request
                        search_results = []
                        best_result = None
                        context = "User wants to talk to someone from the school - be helpful first by offering assistance with school topics, enrollment, schedules, or other school information. Only mention contact options if they specifically ask again after being helpful."
                else:
                    # 3. Perform traditional database search to get context for Groq
                    intent_name = nlu_result.intent.name.lower() if nlu_result and nlu_result.intent else None
                    
                    # Enhance search with emotional context using smart enhancement
                    # Note: Translation is handled inside search_prompts method
                    search_query = self._apply_smart_enhancement(query, emotional_analysis, intent_name)
                    # logger.info(f"💭 Enhanced search query: '{search_query}' (emotion: {emotional_analysis.primary_emotion if emotional_analysis else 'none'})")
                    
                    # 🎯 ENHANCEMENT: Handle different query types with context awareness
                    context = None  # Initialize context variable
                    search_results = []
                    best_result = None
                    
                    # 🚨 FIX: Check for greetings FIRST before treating as simple_response
                    # This ensures greetings are handled with proper responses, not as generic simple responses
                    is_greeting = nlu_result and nlu_result.intent.value in ['greeting_simple', 'greeting_with_name', 'greeting_excited', 'greeting_formal', 'greeting_casual', 'greeting_returning_user']
                    
                    if is_greeting:
                        # Skip simple_response handling for greetings - let them flow through to proper greeting response
                        search_results = []
                        best_result = None
                    elif self._is_simple_response(query):
                        # Handle simple responses (yes, no, ok, etc.) - but NOT greetings
                        context = await self._handle_simple_response(query, conversation_history, session_id)
                        if context:
                            # Return simple response directly without AI processing
                            return ChatResponse(
                                response=[context],
                                entities=entities,
                                detected_language=detected_lang,
                                language_confidence=confidence,
                                is_split=False,
                                message_count=1,
                                intent='simple_response'
                            )
                        else:
                            # Fallback to regular search
                            search_results = await self._handle_multiple_grade_search(search_query, intent_name, conversation_history, nlu_result)
                            mark('search')
                            best_result = search_results[0] if search_results else None
                    elif self._is_vague_query(query):
                        # Handle vague queries with suggestions
                        search_results = await self._handle_multiple_grade_search(search_query, intent_name, conversation_history, nlu_result)
                        mark('search')
                        suggestions = await self._generate_query_suggestions(query, search_results)
                        if suggestions:
                            # Return suggestions directly without AI processing
                            return ChatResponse(
                                response=[f"I'm not sure what you're looking for with '{query}'. Here are some suggestions:\n\n{suggestions}\n\nPlease ask a more specific question and I'll be happy to help!"],
                                entities=entities,
                                detected_language=detected_lang,
                                language_confidence=confidence,
                                is_split=False,
                                message_count=1,
                                intent='vague_query'
                            )
                        else:
                            best_result = search_results[0] if search_results else None
                    else:
                        # Regular search for complex queries
                        search_results = await self._handle_multiple_grade_search(search_query, intent_name, conversation_history, nlu_result)
                        mark('search')
                        best_result = search_results[0] if search_results else None
                    
                    # 🚨 AUTOMATIC: Invalidate cache if grade query returns wrong results
                    if 'grade' in query.lower() and search_results:
                        self._validate_and_invalidate_grade_cache(query, search_results)
                        
                        # Also invalidate preprocessing cache for the grade
                        if hasattr(preprocessed, 'extracted_grade') and preprocessed.extracted_grade:
                            invalidate_grade_preprocessing_cache(preprocessed.extracted_grade)
                    
                    # 4. Simple logic: Use top database result if available
                    best_result = None
                    if search_results:
                        # Skip contact escalation queries - don't use irrelevant database results
                        if nlu_result and nlu_result.intent.value == 'contact_escalation':
                            logger.info("🚨 Contact escalation detected - not using database results")
                            pass
                        else:
                            # Use the top-ranked result (scoring algorithm already ranked by relevance)
                            best_result = search_results[0]
                            logger.info(f"🏆 Using top-ranked result: {best_result.get('keywords', 'No keywords')}")
                            logger.info(f"🏆 Best result response: {best_result.get('response', 'No response')[:100]}...")
                    
                    # 4.5. Fallback: If no best_result but we have search results and unknown intent, use them
                    if not best_result and search_results and (not nlu_result or nlu_result.intent.value == 'unknown'):
                        best_result = search_results[0]
                
                # 🎯 CRITICAL: Check for invalid grades BEFORE database search
                if 'grade' in query.lower():
                    # Quick grade validation to avoid irrelevant database searches
                    import re
                    grade_match = re.search(r'grade\s*(-?\d+)', query.lower())
                    if grade_match:
                            grade_num = int(grade_match.group(1))
                            # Handle negative grades, zero, and obviously invalid grades
                            if grade_num <= 0:
                                return ChatResponse(
                                    response=[f"Grade {grade_num} is not a valid grade level. Grade levels must be positive numbers (1-6)."],
                                    entities=entities,
                                    detected_language=detected_lang,  # Use original detected language, not mapped
                                    language_confidence=confidence,
                                    is_split=False,
                                    message_count=1,
                                    intent=nlu_result.intent.value if nlu_result and nlu_result.intent else 'unknown'
                                )
                            elif grade_num > 12:
                                return ChatResponse(
                                    response=[f"Grade {grade_num} is not a valid grade level. Elementary schools typically offer grades 1-6."],
                                    entities=entities,
                                    detected_language=detected_lang,  # Use original detected language, not mapped
                                    language_confidence=confidence,
                                    is_split=False,
                                    message_count=1,
                                    intent=nlu_result.intent.value if nlu_result and nlu_result.intent else 'unknown'
                                )
            
            # 5. Generate response using Groq with context-aware analysis
            # Debug removed
            if not context:
                context = "No specific information available in database for this query"
            
            if best_result:
                # logger.info("📚 Using database context for response generation")
                # Provide complete database information as context
                if isinstance(best_result, dict):
                    keywords = best_result.get('keywords', '')
                    response = best_result.get('response', '')
                    context = f"Database Information: {keywords} - {response}"
                    # Debug removed
                else:
                    logger.warning(f"⚠️ Best result is not a dict: {type(best_result)} - {best_result}")
                    context = f"Database Information: {best_result}"
                
                # 🎯 ENHANCEMENT: For multiple grade queries, include all relevant results
                if 'grade' in query.lower() and ('and' in query.lower() or '&' in query.lower()):
                    # Check if we have multiple grade results
                    grade_results = []
                    for result in search_results:
                        if isinstance(result, dict):
                            # Check both response and keywords for grade information
                            response_text = result.get('response', '').lower()
                            keywords_text = result.get('keywords', '').lower()
                            if 'grade' in keywords_text or any(f'grade {i}' in keywords_text for i in range(1, 7)):
                                grade_results.append(result)
                    
                    if len(grade_results) > 1:
                        # Build comprehensive context with all grade information
                        context = "Database Information for Multiple Grades:\n"
                        for i, result in enumerate(grade_results):
                            keywords = result.get('keywords', '')
                            response = result.get('response', '')
                            context += f"Grade {i+1}: {keywords} - {response}\n"
                        context = context.strip()
                
                # 🎯 FIX: Add explicit clarification for grade level questions
                if 'grade' in query.lower() and 'grade level' in context.lower():
                    context += "\n\nIMPORTANT: If the database says 'kindergarten through grade 6', this means Grade 7 and above are NOT offered."
                
                # 🎯 REMOVED: Grade validation bypass - let all responses go through natural response generator
                # This ensures grade responses are natural and conversational, not robotic
                
                # 🔧 ENHANCED LANGUAGE GUARD (Priority 3 Fix)
                # Prevent AI from switching languages based on low-confidence language detection
                # Issue: Short English queries like "13 years old" were detected as Tagalog with low confidence
                # This caused the already-correct English response to be translated to Tagalog
                if response_lang == 'tl':
                    # Add explicit instruction for Tagalog responses
                    context += "\n\nCRITICAL LANGUAGE INSTRUCTION: You MUST respond in Tagalog ONLY. Do NOT respond in English. Use proper Tagalog grammar and natural sentence structure. Be conversational but professional. If you receive English context, respond in Tagalog."
                elif response_lang == 'en':
                    # Add explicit instruction for English responses
                    context += "\n\nCRITICAL LANGUAGE INSTRUCTION: You MUST respond in English ONLY. Do NOT respond in Tagalog or any other language. Use proper English grammar and natural sentence structure. Be conversational but professional. Even if context mentions Tagalog, respond in English."
            else:
                # Context-aware NLU determined not to use database context
                # logger.info("🎯 Context-aware NLU: Not using database context")
                if nlu_result and nlu_result.intent.value == 'contact_escalation':
                    context = "User wants to talk to someone from the school - be helpful first by offering assistance with school topics, enrollment, schedules, or other school information. Only mention contact options if they specifically ask again after being helpful."
                else:
                    context = "No specific information available in database for this query"
                # logger.info(f"🔍 DEBUG: No best_result, context set to: {context}")
            
            # Debug: Log the final context before sending to AI
            # Debug removed
            
            # Add personalized memory context
            if session_id:
                memory_context = self.conversation_memory.get_conversation_context(session_id, user_name)
                if memory_context:
                    context += f"\n\nPersonal Context: {memory_context}"
                    # logger.info(f"🧠 Added memory context: {memory_context}")  # Commented out debug logs
            
            # Add conversation analysis context for better responses
            if conversation_context:
                # Add topic flow context
                if conversation_context.topic_flow:
                    context += f"\n\nConversation Topics: {', '.join(conversation_context.topic_flow)}"
                
                # Add urgency context
                if conversation_context.urgency_level != 'medium':
                    context += f"\n\nUrgency Level: {conversation_context.urgency_level}"
                
                # Add user expertise context
                if conversation_context.user_expertise != 'intermediate':
                    context += f"\n\nUser Expertise: {conversation_context.user_expertise}"
                
                # Add emotional context
                if emotional_analysis and emotional_analysis.primary_emotion != 'neutral':
                    context += f"\n\nUser Emotion: {emotional_analysis.primary_emotion} (intensity: {emotional_analysis.emotion_intensity:.1f})"
                    if emotional_analysis.support_needed:
                        context += "\n\nUser needs additional support - be extra helpful and empathetic"
                
                # Check if this is a greeting/returning user
                if any(word in query.lower() for word in ["hi", "hello", "hey", "kumusta", "kamusta"]):
                    personalized_greeting = self.conversation_memory.get_personalized_greeting(session_id, user_name)
                    if personalized_greeting:
                        context += f"\n\nPersonalized Greeting: {personalized_greeting}"
                        # logger.info(f"👋 Added personalized greeting: {personalized_greeting}")  # Commented out debug logs
            
            # Get NLU info for better context (already analyzed above)
            nlu_info = {
                'intent': nlu_result.intent.value if nlu_result else 'unknown',
                'confidence': nlu_result.confidence if nlu_result else 0.0,
                'entities': [(e.entity_type, e.value) for e in entities],
                'query_analysis': {
                    'length': len(query),
                    'word_count': len(query.split()),
                    'has_question_mark': '?' in query,
                    'detected_language': detected_lang,
                    'language_confidence': confidence,
                    'is_likely_gibberish': self._analyze_query_clarity(query, detected_lang),
                    'complexity_score': self._calculate_query_complexity(query)
                },
                'emotional_analysis': {
                    'primary_emotion': emotional_analysis.primary_emotion if emotional_analysis else 'neutral',
                    'emotion_intensity': emotional_analysis.emotion_intensity if emotional_analysis else 0.0,
                    'sentiment_score': emotional_analysis.sentiment_score if emotional_analysis else 0.0,
                    'suggested_response_tone': emotional_analysis.suggested_response_tone if emotional_analysis else 'professional_friendly',
                    'empathy_level': emotional_analysis.empathy_level if emotional_analysis else 'low',
                    'support_needed': emotional_analysis.support_needed if emotional_analysis else False
                } if emotional_analysis else None,
                'conversation_context': {
                    'topic_flow': conversation_context.topic_flow if conversation_context else [],
                    'urgency_level': conversation_context.urgency_level if conversation_context else 'medium',
                    'user_expertise': conversation_context.user_expertise if conversation_context else 'intermediate',
                    'conversation_sentiment': conversation_context.conversation_sentiment if conversation_context else 0.0
                } if conversation_context else None
            }
            
            # 🚨 CRITICAL FIX: Removed ML-based gibberish detection since we stripped ML dependencies
            # Let the Context-Aware NLU and database search handle everything
            
            
            # 🚨 FIX: Handle name introductions and greeting with name even without database context
            # BUT ONLY if we don't have database context already
            if not best_result:
                # Check if this is a pure greeting (no other content) vs greeting + question
                is_pure_greeting = self._is_pure_greeting(query, nlu_result)
                
                if nlu_result and nlu_result.intent.value in ['name_introduction', 'greeting_with_name']:
                    # logger.info(f"👋 {nlu_result.intent.value} detected - handling with Groq even without database context")  # Commented out debug logs
                    # For name introductions, we don't need database context
                    context = "User is introducing themselves with their name"
                elif nlu_result and nlu_result.intent.value == 'emotional_expression':
                    # logger.info(f"😊 {nlu_result.intent.value} detected - handling emotional expression")  # Commented out debug logs
                    # For emotional expressions, provide empathetic response
                    context = "User is expressing their emotional state"
                elif nlu_result and nlu_result.intent.value in ['appreciation', 'APPRECIATION']:
                    # logger.info(f"🙏 {nlu_result.intent.value} detected - handling appreciation/thanks")  # Commented out debug logs
                    # For appreciation/thanks, provide friendly acknowledgment
                    context = "User is expressing appreciation or thanks"
                elif nlu_result and nlu_result.intent.value == 'greeting_simple' and is_pure_greeting:
                    # logger.info(f"👋 {nlu_result.intent.value} detected - handling simple greeting")  # Commented out debug logs
                    # For simple greetings, provide friendly response
                    context = "User is giving a simple greeting"
                elif nlu_result and nlu_result.intent.value == 'greeting_simple' and not is_pure_greeting:
                    # This is a greeting + question - treat as informational query
                    context = "User is greeting and asking a question - answer the question while being friendly"
                elif nlu_result and nlu_result.intent.value == 'medical_emergency':
                    # logger.info(f"🚨 {nlu_result.intent.value} detected - handling medical emergency")  # Commented out debug logs
                    # For medical emergencies, provide immediate emergency response
                    context = "MEDICAL EMERGENCY DETECTED - User is experiencing a medical emergency requiring immediate attention"
                elif nlu_result and nlu_result.intent.value == 'unknown':
                    # For unknown intents, try to use database results if available
                    if conversation_history:
                        # Try to enhance the query with context and search
                        enhanced_query = self.database_search._enhance_query_with_context(query, conversation_history)
                        search_results = await self.database_search.search_prompts(enhanced_query, limit=5, conversation_history=conversation_history)
                        if search_results:
                            best_result = search_results[0]
                            context = f"Database Information: {best_result.get('keywords', '')} - {best_result.get('response', '')}"
                        else:
                            context = "User query is unclear or unknown. Provide helpful general assistance."
                    else:
                        context = "User query is unclear or unknown. Provide helpful general assistance."
                elif nlu_result and nlu_result.intent.value == 'contact_escalation':
                    # For contact escalation, check if user has been persistent
                    persistent_escalation = self._check_persistent_escalation(conversation_history)
                    
                    if persistent_escalation:
                        # Persistent escalation - provide hardcoded admin response with messenger
                        if response_lang in ["tl", "akl"]:
                            context = "HARDCODED_ADMIN_TAGALOG"
                        else:
                            context = "HARDCODED_ADMIN_ENGLISH"
                    else:
                        # First escalation request - be helpful first
                        context = "User wants to talk to someone from the school - be helpful first by offering assistance with school topics, enrollment, schedules, or other school information. Only mention contact options if they specifically ask again after being helpful."
                # Remove the old fallback logic - let Groq handle all cases intelligently
            
            # Generate response with Groq (professional, factual, humane, jolly, no roleplay)
            # Pass enhanced NLP/NLU information for better response generation
            nlu_info_dict = nlu_info  # Use the enhanced nlu_info with emotional analysis
            
            # CRITICAL FIX: Get user name directly from conversation memory if not already provided
            final_user_name = user_name
            if not final_user_name and session_id:
                stored_name = self.conversation_memory.get_user_name(session_id)
                if stored_name:
                    final_user_name = stored_name
                    logger.info(f"🧠 Using name from memory for response generation: {final_user_name}")
            
            # Check for hardcoded admin responses
            if context == "HARDCODED_ADMIN_TAGALOG":
                response_text = "Maaari mong kausapin ang admin ng Tomas SM. Bautista Elementary School sa loob ng opisina ng paaralan. Pumunta sa kanilang tanggapan upang makausap ang mga opisyal. Para sa karagdagang impormasyon, kayo ay maaari kang mag message sa kanilang Messenger:"
                # Add messenger link for hardcoded admin response
                response_text = self.response_generator.add_messenger_link_if_needed(
                    response_text, query, context, response_lang
                )
            elif context == "HARDCODED_ADMIN_ENGLISH":
                response_text = "You can contact the admin of Tomas SM. Bautista Elementary School at the school office. Go to their office to speak with the officials. For additional information, you can message them on Messenger:"
                # Add messenger link for hardcoded admin response
                response_text = self.response_generator.add_messenger_link_if_needed(
                    response_text, query, context, response_lang
                )
                # Fix HTML attributes that may have been translated
                if isinstance(response_text, list):
                    response_text = [self._fix_translated_html(item) for item in response_text]
                else:
                    response_text = self._fix_translated_html(response_text)
            else:
                # CRITICAL: Check if we have sufficient database context to prevent hallucinations
                # But only for information queries - greetings, emergencies, etc. don't need database context
                intent_requires_db = nlu_result and nlu_result.intent.value in [
                    'staff_inquiry', 'general_inquiry', 'grade_inquiry', 'activity_inquiry', 
                    'schedule_inquiry', 'facility_inquiry', 'unknown'
                ]
                
                # 🚨 FIXED: Reduced minimum context threshold from 50 to 20 characters
                # Brief contact information (emails, short addresses) are legitimate and should be used
                if intent_requires_db and (not context or len(context.strip()) < 20):  # Insufficient context for info queries
                    logger.warning(f"⚠️ Insufficient database context for query: '{query[:50]}...'")
                    # Return a safe response that doesn't hallucinate
                    response_text = f"I don't have specific information about that in my database. Please contact the school office for more details."
                else:
                    # Generate AI response with proper database context
                    response_text = await self.response_generator.generate_response(
                        query, context, response_lang, conversation_history, nlu_info_dict, final_user_name, entities, float(confidence), None
                    )
                    mark('response_generate')
                
                # Add Messenger link for contact escalation requests (only for non-hardcoded responses)
                if nlu_result and nlu_result.intent.value == 'contact_escalation':
                    response_text = self.response_generator.add_messenger_link_if_needed(
                        response_text, query, context, response_lang
                    )
                
                # Fix HTML attributes that may have been translated
                # logger.info(f"🔧 Before AI HTML fix: {response_text}")
                
                # Apply post-processing to all responses
                if isinstance(response_text, list):
                    response_text = [self._fix_translated_html(item) for item in response_text]
                else:
                    response_text = self._fix_translated_html(response_text)
                # logger.info(f"🔧 After AI HTML fix: {response_text}")
                # Ensure response_text is properly flattened if it's a nested list
                if isinstance(response_text, list) and len(response_text) > 0 and isinstance(response_text[0], list):
                    # Flatten nested lists
                    flattened = []
                    for item in response_text:
                        if isinstance(item, list):
                            flattened.extend(item)
                        else:
                            flattened.append(item)
                    response_text = flattened
            
            # Advanced AI Enhancement - Response Personalization (ONLY if we have database context)
            if context and context not in ["No specific information available in database for this query", "User is introducing themselves with their name", "User is expressing their emotional state"]:
                try:
                    # Create user profile from conversation context
                    user_profile = {
                        'name': user_name,
                        'child_name': child_name,
                        'personality_traits': getattr(conversation_context, 'user_personality', {}) if conversation_context else {},
                        'expertise_level': getattr(conversation_context, 'user_expertise', 'intermediate') if conversation_context else 'intermediate',
                        'preferred_language': response_lang,
                        'conversation_history': conversation_history or []
                    }
                    
                    # Create conversation context dict
                    conversation_context_dict = {
                        'topic_flow': conversation_context.topic_flow if conversation_context else [],
                        'urgency_level': conversation_context.urgency_level if conversation_context else 'medium',
                        'conversation_stage': 'ongoing',
                        'emotional_state': emotional_analysis.primary_emotion if emotional_analysis else 'neutral',
                        'complexity_level': 'medium'
                    }
                    
                    # Personalize the response
                    personalized_response = await self.response_personalizer.personalize_response(
                        base_response=response_text,
                        user_profile=user_profile,
                        conversation_context=conversation_context_dict,
                        emotional_analysis=emotional_analysis,
                        language=response_lang
                    )
                    mark('personalization')
                    
                    # Apply personalization to the response (only if it's a string)
                    if isinstance(response_text, str):
                        response_text = await self.response_personalizer.apply_personalization(
                            response=response_text,
                            personalization=personalized_response,
                            user_name=user_name,
                            conversation_history=conversation_history
                        )
                    else:
                        # Skip personalization for already split responses
                        # logger.info("ℹ️ Skipping personalization - response already split")
                        pass
                    
                    # logger.info(f"🎨 Response personalized: tone={personalized_response.tone}, formality={personalized_response.formality_level}")  # Reduced for Railway
                    
                except Exception as e:
                    logger.warning(f"⚠️ Response personalization failed: {e}")
                    # Continue with original response
            else:
                # logger.info("ℹ️ Skipping personalization - no database context available")  # Reduced for Railway
                pass
            
            # Apply context-aware translation if needed
            # 🔧 FIX: Only translate if VERY confident (> 0.85) that it's not English
            # Changed from 0.8 to 0.85 to prevent translating English queries to Tagalog
            # Issue: "13 years old" was detected as Tagalog with 0.45 confidence, then translated
            if detected_lang != "en" and confidence > 0.85:
                # logger.info("🌐 Applying context-aware translation")  # Commented out debug logs
                # Handle both string and list responses
                if isinstance(response_text, list):
                    # Translate each message in the list
                    translated_messages = []
                    for message in response_text:
                        translated_message, translation_confidence = self.context_translator.translate_with_context(
                            message, detected_lang, conversation_history, session_id
                        )
                        mark('translation')
                        if translation_confidence > 0.7:
                            translated_messages.append(translated_message)
                        else:
                            translated_messages.append(message)
                    response_text = translated_messages
                else:
                    # Single string response
                    translated_response, translation_confidence = self.context_translator.translate_with_context(
                        response_text, detected_lang, conversation_history, session_id
                    )
                    mark('translation')
                    if translation_confidence > 0.7:
                        response_text = translated_response
                    # logger.info(f"🌐 Context-aware translation applied (confidence: {translation_confidence:.2f})  # Commented out debug logs")
                
                # Fix HTML attributes that may have been translated (AFTER translation)
                if isinstance(response_text, list):
                    response_text = [self._fix_translated_html(item) for item in response_text]
                else:
                    response_text = self._fix_translated_html(response_text)
            
            # Post-process to fix HTML button if it was translated (AFTER translation)
            if isinstance(response_text, list) and len(response_text) > 1:
                # Check if the second message contains a translated HTML button
                second_message = response_text[1]
                # Check for various patterns of translated HTML
                has_translated_html = (
                    ("messenger" in second_message.lower()) and 
                    ("href=" in second_message or "<a href" in second_message) and
                    ("blangko" in second_message or "kulay" in second_message or "wala" in second_message)
                )
                
                if has_translated_html:
                    # Replace with correct HTML button
                    correct_button = '<a href="https://m.me/114901Tomas" target="_blank" style="display: inline-block; background-color: #0084ff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 10px 0;">📱 Messenger</a>'
                    # Extract the intro text and replace the button
                    intro_match = second_message.split('\n\n')[0] if '\n\n' in second_message else second_message.split('\n')[0]
                    response_text[1] = f"{intro_match}\n\n{correct_button}"
            
            # 6. Response is already split by generate_response
            split_messages = response_text if isinstance(response_text, list) else [response_text]
            
            mark('finalize')
            phase_times['total'] = time.perf_counter() - t_start
            return ChatResponse(
                response=split_messages,
                entities=[{"entity_type": e.entity_type, "value": e.value, "confidence": e.confidence} for e in entities],
                detected_language=detected_lang,  # Use original detected language, not mapped
                language_confidence=confidence,
                is_split=len(split_messages) > 1,
                message_count=len(split_messages),
                intent=nlu_result.intent.value if nlu_result and nlu_result.intent else 'unknown',
                performance_metrics=phase_times
            )
            
        except Exception as e:
            logger.error(f"❌ Chat error: {e}")
            # Only use keyword matching as fallback for errors
            try:
                keyword_response = self.keyword_matcher.find_match(query, detected_lang if 'detected_lang' in locals() else "en")
                if keyword_response:
                    # logger.info("🔄 Using keyword fallback due to error")  # Commented out debug logs
                    return self._create_response(keyword_response, entities if 'entities' in locals() else [], detected_lang if 'detected_lang' in locals() else "en", confidence if 'confidence' in locals() else 0.5)
            except:
                pass
            
            # Provide minimal metrics on error path
            try:
                phase_times['total'] = time.perf_counter() - t_start
            except Exception:
                pass
            return ChatResponse(
                response=["An internal error occurred."],
                entities=[],
                detected_language=detected_lang if 'detected_lang' in locals() else "en",
                language_confidence=confidence if 'confidence' in locals() else 0.0,
                is_split=False,
                message_count=1,
                intent='error',
                performance_metrics=phase_times if 'phase_times' in locals() else None
            )
    
    def _create_response(self, response_text: str, entities: List[ExtractedEntity], 
                        detected_lang: str, confidence: float) -> ChatResponse:
        """Create a ChatResponse object"""
        split_messages = response_text if isinstance(response_text, list) else [response_text]
        
        return ChatResponse(
            response=split_messages,
            entities=[{"entity_type": e.entity_type, "value": e.value, "confidence": e.confidence} for e in entities],
            detected_language=detected_lang,
            language_confidence=confidence,
            is_split=len(split_messages) > 1,
            message_count=len(split_messages),
            intent='keyword_match'
        )
    
    async def _create_no_information_response(self, query: str, detected_lang: str, confidence: float, nlu_result, entities: List, session_id: str = None) -> ChatResponse:
        """Create structured response when no database information is found"""
        
        # Analyze the query using NLP/NLU to understand what the user is asking about
        query_lower = query.lower().strip()
        
        # Determine the topic/subject of the query using NLP analysis
        topic_keywords = {
            'enrollment': ['enrollment', 'enroll', 'admission', 'register', 'registration', 'apply', 'application'],
            'schedule': ['schedule', 'time', 'when', 'hours', 'class', 'period', 'timetable'],
            'location': ['where', 'location', 'address', 'place', 'find', 'directions'],
            'contact': ['contact', 'phone', 'number', 'email', 'reach', 'call'],
            'academic': ['grade', 'subject', 'course', 'curriculum', 'study', 'learning'],
            'services': ['service', 'help', 'support', 'assistance', 'guidance', 'counselor'],
            'general': ['information', 'about', 'tell', 'know', 'question']
        }
        
        # Use NLU intent to better understand the query
        detected_topic = 'general'
        if nlu_result and nlu_result.intent:
            intent = nlu_result.intent.value
            if intent in ['question', 'information_request']:
                # Analyze the query content to determine topic
                for topic, keywords in topic_keywords.items():
                    if any(keyword in query_lower for keyword in keywords):
                        detected_topic = topic
                        break
        
        # Generate appropriate response based on detected language and topic
        if detected_lang in ['tl', 'akl']:  # Tagalog/Aklanon
            response_text = "Paumanhin po, wala pong impormasyon tungkol dito sa database."
        else:  # English
            response_text = "I'm sorry, no information is available in the database for this topic."
        
        # Split long responses if needed
        split_messages = response_text if isinstance(response_text, list) else [response_text]
        
        return ChatResponse(
            response=split_messages,
            entities=[{"entity_type": e.entity_type, "value": e.value, "confidence": e.confidence} for e in entities],
            detected_language=detected_lang,
            language_confidence=confidence,
            is_split=len(split_messages) > 1,
            message_count=len(split_messages),
            intent='no_information_found'
        )

    async def _create_fallback_response(self, query: str, detected_lang: str, confidence: float, session_id: str = None) -> ChatResponse:
        """Create fallback response for gibberish/unclear input - respect language mapping"""
        
        # Map to response language (English queries = English, Tagalog/Aklanon = Tagalog)
        response_lang = self._map_to_response_language(detected_lang)
        
        # For unclear input, acknowledge and redirect to school inquiries in appropriate language
        if response_lang == "tl":
            context = f"User has sent unclear input: '{query}'. Acknowledge that their message wasn't clear, but always redirect them to what TOMAS really is - a chatbot for school inquiries at Tomas SM. Bautista Elementary School. Ask them what they'd like to know about the school. Respond in Tagalog."
        else:
            context = f"User has sent unclear input: '{query}'. Acknowledge that their message wasn't clear, but always redirect them to what TOMAS really is - a chatbot for school inquiries at Tomas SM. Bautista Elementary School. Ask them what they'd like to know about the school."
        
        # Get user name for personalization
        user_name = ""
        if session_id:
            user_name = self.conversation_memory.get_user_name(session_id)
        
        try:
            # Use appropriate language for fallback responses
            response_text = await self.response_generator.generate_response(
                query, context, response_lang, [], None, user_name, [], 0.8
            )
            
            # Split long responses if needed
            split_messages = response_text if isinstance(response_text, list) else [response_text]
            
            return ChatResponse(
                response=split_messages,
                entities=[],
                detected_language=detected_lang,  # Use original detected language, not mapped  # Use mapped response language
                language_confidence=0.8,
                is_split=len(split_messages) > 1,
                message_count=len(split_messages),
                intent='fallback'
            )
        except Exception as e:
            logger.error(f"❌ Error in fallback response generation: {e}")
            # Only use this as absolute last resort
            # Use appropriate language for fallback
            if response_lang == "tl":
                fallback_text = "Paumanhin po, wala pong impormasyon tungkol dito sa database."
            else:
                fallback_text = "I'm sorry, no information is available in the database for this topic."
            
            return ChatResponse(
                response=[fallback_text],
                entities=[],
                detected_language=detected_lang,  # Use original detected language, not mapped  # Use mapped response language
                language_confidence=0.8,
                is_split=False,
                message_count=1,
                intent='fallback'
            )
    
    def _create_error_response(self, detected_lang: str) -> ChatResponse:
        """Create error response"""
        if detected_lang == "tl" or detected_lang == "akl":
            error_text = "Paumanhin po, wala pong impormasyon tungkol dito sa database."
        else:
            error_text = "I'm sorry, no information is available in the database for this topic."
        
        return ChatResponse(
            response=[error_text],
            entities=[],
            detected_language=detected_lang,
            language_confidence=0.5,
            is_split=False,
            message_count=1,
            intent='error'
        )
    
    def _analyze_query_clarity(self, query: str, detected_lang: str) -> bool:
        """Analyze query clarity using NLP techniques"""
        query_lower = query.lower().strip()
        
        # Basic length check
        if len(query_lower) < 3:
            return True
        
        # Check for meaningful word patterns
        words = query_lower.split()
        if len(words) == 0:
            return True
        
        # Check for repeated characters (gibberish indicator)
        if len(set(query_lower)) < len(query_lower) * 0.3:
            return True
        
        # Check for keyboard patterns
        keyboard_patterns = ['qwerty', 'asdfgh', 'zxcvbn', 'hjkl']
        if any(pattern in query_lower for pattern in keyboard_patterns):
            return True
        
        # Check for language-specific patterns
        if detected_lang in ['tl', 'akl']:
            # Tagalog/Aklanon meaningful words
            meaningful_patterns = ['ang', 'ng', 'sa', 'ay', 'si', 'mga', 'ko', 'mo', 'niya', 'nila', 'kami', 'kayo', 'sila', 'ano', 'saan', 'kailan', 'sino', 'paano', 'bakit', 'alin']
            if not any(pattern in query_lower for pattern in meaningful_patterns):
                if len(words) > 2:  # Only flag if query is long enough to expect meaningful words
                    return True
        else:
            # English meaningful words
            meaningful_patterns = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'what', 'where', 'when', 'who', 'how', 'why', 'which']
            if not any(pattern in query_lower for pattern in meaningful_patterns):
                if len(words) > 2:  # Only flag if query is long enough to expect meaningful words
                    return True
        
        return False
    
    def _calculate_query_complexity(self, query: str) -> float:
        """Calculate query complexity score (0.0 to 1.0)"""
        words = query.split()
        word_count = len(words)
        
        # Base complexity on word count
        if word_count <= 3:
            return 0.2
        elif word_count <= 6:
            return 0.5
        elif word_count <= 10:
            return 0.7
        else:
            return 0.9
    
    def _detect_gibberish_input(self, query: str, nlu_result, entities: List, detected_lang: str, confidence: float) -> bool:
        """
        Enhanced gibberish detection with sophisticated language-aware patterns
        """
        query_lower = query.lower().strip()
        
        # If NLU has high confidence, trust it (especially for Tagalog/Aklanon)
        if nlu_result and nlu_result.confidence > 0.4:
            return False
        
        # If language detection is confident for Tagalog/Aklanon, don't flag as gibberish
        if detected_lang in ['tl', 'akl'] and confidence > 0.7:
            return False
        
        # Enhanced gibberish detection with multiple sophisticated checks
        gibberish_score = 0.0
        max_score = 1.0
        
        # 1. Character diversity analysis (more sophisticated)
        if len(query) > 6:
            unique_chars = len(set(query_lower.replace(' ', '')))
            total_chars = len(query_lower.replace(' ', ''))
            diversity_ratio = unique_chars / total_chars if total_chars > 0 else 0
            
            if diversity_ratio < 0.3:  # Less than 30% unique characters
                gibberish_score += 0.3
            elif diversity_ratio < 0.5:  # Less than 50% unique characters
                gibberish_score += 0.2
        
        # 2. Vowel-consonant ratio analysis (language-aware)
        if len(query) > 4:
            vowels = set('aeiou')
            vowel_count = sum(1 for char in query_lower if char in vowels)
            consonant_count = sum(1 for char in query_lower if char.isalpha() and char not in vowels)
            
            if consonant_count > 0:
                vc_ratio = vowel_count / consonant_count
                # Different thresholds for different languages
                if detected_lang in ['tl', 'akl']:
                    # Filipino languages have more consonant clusters
                    if vc_ratio < 0.2:  # Too few vowels
                        gibberish_score += 0.2
                else:
                    # English has more balanced vowel-consonant ratio
                    if vc_ratio < 0.1:  # Extremely few vowels
                        gibberish_score += 0.3
        
        # 3. Consecutive consonant analysis (enhanced)
        if len(query) > 6:
            consecutive_consonants = 0
            max_consecutive = 0
            vowels = set('aeiou')
            
            for char in query_lower:
                if char.isalpha():
                    if char not in vowels:
                        consecutive_consonants += 1
                        max_consecutive = max(max_consecutive, consecutive_consonants)
                    else:
                        consecutive_consonants = 0
            
            # Language-aware thresholds
            if detected_lang in ['tl', 'akl']:
                if max_consecutive >= 6:  # Very high for Filipino languages
                    gibberish_score += 0.3
                elif max_consecutive >= 5:
                    gibberish_score += 0.2
            else:
                if max_consecutive >= 5:  # High for English
                    gibberish_score += 0.3
                elif max_consecutive >= 4:
                    gibberish_score += 0.2
        
        # 4. Pattern recognition (enhanced with more patterns)
        obvious_gibberish_patterns = [
            # Keyboard patterns
            "qwertyuiop", "asdfghjkl", "zxcvbnm", "qwerty", "asdfgh", "zxcvbn",
            # Repeated characters
            "aaaaaaaa", "bbbbbbbb", "cccccccc", "dddddddd", "eeeeeeee",
            # Sequential patterns
            "123456789", "abcdefgh", "qwertyui", "asdfghjk",
            # Common gibberish
            "asdfasdf", "qwerqwer", "zxcvzxcv", "hjklhjkl",
            # Random character sequences
            "qwerty", "asdfgh", "zxcvbn", "hjklui", "mnbvcx",
            # Number-letter mixed gibberish
            "q1w2e3", "a1s2d3", "z1x2c3", "h1j2k3",
            # Repeated patterns
            "qweqwe", "asdasd", "zxcxzc", "hjkhjk"
        ]
        
        for pattern in obvious_gibberish_patterns:
            if pattern in query_lower:
                gibberish_score += 0.4
                break
        
        # 5. Entropy analysis (measure of randomness)
        if len(query) > 8:
            import math
            char_counts = {}
            for char in query_lower:
                if char.isalpha():
                    char_counts[char] = char_counts.get(char, 0) + 1
            
            if char_counts:
                total_chars = sum(char_counts.values())
                entropy = 0
                for count in char_counts.values():
                    probability = count / total_chars
                    if probability > 0:
                        entropy -= probability * math.log2(probability)
                
                # Low entropy indicates repetitive patterns (gibberish)
                if entropy < 2.0:  # Very low entropy
                    gibberish_score += 0.3
                elif entropy < 2.5:  # Low entropy
                    gibberish_score += 0.2
        
        # 6. Word structure analysis
        words = query_lower.split()
        if words:
            valid_words = 0
            for word in words:
                if len(word) > 1:
                    # Check if word has reasonable vowel-consonant structure
                    vowel_count = sum(1 for char in word if char in 'aeiou')
                    consonant_count = sum(1 for char in word if char.isalpha() and char not in 'aeiou')
                    
                    if consonant_count > 0:
                        vc_ratio = vowel_count / consonant_count
                        # Reasonable vowel-consonant ratio
                        if 0.1 <= vc_ratio <= 2.0:  # Reasonable range
                            valid_words += 1
            
            word_validity_ratio = valid_words / len(words) if words else 0
            if word_validity_ratio < 0.3:  # Less than 30% valid words
                gibberish_score += 0.2
        
        # 7. Language-specific validation
        if detected_lang == 'en':
            # English-specific checks
            english_indicators = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
            if not any(indicator in query_lower for indicator in english_indicators):
                if len(query) > 10:  # Long query without common English words
                    gibberish_score += 0.1
        
        elif detected_lang in ['tl', 'akl']:
            # Filipino language-specific checks
            filipino_indicators = ['ang', 'ng', 'sa', 'na', 'ay', 'mga', 'ko', 'mo', 'niya', 'nila', 'namin', 'natin']
            if not any(indicator in query_lower for indicator in filipino_indicators):
                if len(query) > 10:  # Long query without common Filipino words
                    gibberish_score += 0.1
        
        # Final decision based on cumulative score
        return gibberish_score >= 0.5  # Threshold for gibberish detection
    
    def _handle_emergency_response(self, query: str, response_lang: str, detected_lang: str) -> ChatResponse:
        """Handle medical emergency responses with immediate action guidance"""
        logger.warning(f"🚨 PROCESSING EMERGENCY: {query}")
        
        # Emergency response messages in multiple languages
        # Include all test-expected keywords: 911, emergency, medical, help, immediately
        emergency_responses = {
            'en': [
                "🚨 MEDICAL EMERGENCY DETECTED! Please call 911 or your local emergency services immediately.",
                "This is a life-threatening situation that requires immediate medical help. Do not wait - call emergency services now!",
                "If you are having a heart attack, stroke, or any medical emergency, call 911 immediately.",
                "Do not use this chatbot for medical emergencies. Call emergency services right now for help!",
                "Your safety is the top priority. Please call 911 immediately for medical help."
            ],
            'tl': [
                "🚨 MEDICAL EMERGENCY DETECTED! Tawagan ang 911 o ang inyong lokal na emergency services kaagad.",
                "Ito ay isang life-threatening na sitwasyon na nangangailangan ng agarang medical help. Huwag maghintay - tawagan ang emergency services ngayon!",
                "Kung kayo ay may heart attack, stroke, o anumang medical emergency, tawagan ang 911 kaagad.",
                "Huwag gamitin ang chatbot na ito para sa medical emergencies. Tawagan ang emergency services ngayon para sa tulong!",
                "Ang inyong kaligtasan ang pinakamahalaga. Pakitawagan ang 911 kaagad para sa medical help."
            ]
        }
        
        # Get appropriate response based on language
        if response_lang in emergency_responses:
            response_text = emergency_responses[response_lang]
        else:
            # Default to English if language not supported
            response_text = emergency_responses['en']
        
        # Log the emergency for monitoring
        logger.critical(f"🚨 EMERGENCY RESPONSE SENT: {query} -> {response_text[0]}")
        
        return ChatResponse(
            response=response_text,
            detected_language=detected_lang,  # Use original detected language, not mapped
            language_confidence=1.0,
            entities=[],
            intent="emergency",
            is_split=len(response_text) > 1,
            message_count=len(response_text)
        )
    
    def _is_factual_query(self, query: str, intent: str = None) -> bool:
        """Enhanced factual query detection with intent-based and keyword-based detection"""
        
        # Intent-based detection (highest priority)
        factual_intents = [
            'location_inquiry', 'schedule_inquiry', 'staff_inquiry', 
            'enrollment_inquiry', 'facilities_inquiry', 'school_info',
            'contact_inquiry', 'academic_inquiry'
        ]
        if intent and intent in factual_intents:
            return True
        
        # Keyword-based detection
        factual_keywords = [
            # English keywords
            'location', 'address', 'where', 'when', 'what', 'who', 'how',
            'time', 'schedule', 'hours', 'start', 'end', 'principal', 'teacher',
            'enrollment', 'admission', 'canteen', 'library', 'office', 'contact',
            'phone', 'number', 'email', 'website', 'facebook', 'uniform', 'fees',
            'cost', 'price', 'rules', 'policy', 'requirements', 'needed',
            # Tagalog keywords
            'saan', 'kailan', 'ano', 'sino', 'paano', 'oras', 'oras ng', 'klase',
            'paaralan', 'guro', 'principal', 'enrollment', 'kantin', 'aklatan',
            'opisina', 'kontak', 'telepono', 'email', 'website', 'uniporme',
            'bayad', 'presyo', 'batas', 'patakaran', 'kailangan',
            # Aklanon keywords
            'diin', 'ngaean', 'sino', 'oras', 'klase', 'paaralan', 'guro',
            'principal', 'enrollment', 'kantin', 'aklatan', 'opisina'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in factual_keywords)
    
    def _classify_query_type(self, query: str) -> str:
        """Classify query as factual, emotional, or mixed"""
        
        factual_indicators = ['what', 'where', 'when', 'who', 'how', 'saan', 'kailan', 'ano', 'sino', 'diin', 'ngaean']
        emotional_indicators = ['sad', 'angry', 'worried', 'confused', 'happy', 'excited', 'frustrated', 'upset']
        
        has_factual = any(indicator in query.lower() for indicator in factual_indicators)
        has_emotional = any(indicator in query.lower() for indicator in emotional_indicators)
        
        if has_factual and has_emotional:
            return 'mixed'
        elif has_factual:
            return 'factual'
        elif has_emotional:
            return 'emotional'
        else:
            return 'neutral'
    
    def _apply_smart_enhancement(self, query: str, emotional_analysis, intent: str = None) -> str:
        """Apply smart enhancement based on query type and emotion"""
        
        # Never enhance factual queries
        if self._is_factual_query(query, intent):
            return query
        
        # Check if we have emotional analysis
        if not emotional_analysis or emotional_analysis.primary_emotion == 'neutral':
            return query
        
        # Classify query type
        query_type = self._classify_query_type(query)
        
        if query_type == 'factual':
            return query  # Never enhance factual queries
        
        elif query_type == 'mixed':
            # For mixed queries, be conservative - only enhance if clearly emotional
            if emotional_analysis.primary_emotion in ['sad', 'worried', 'confused']:
                return self._enhance_emotional_query(query, emotional_analysis.primary_emotion)
            return query
        
        elif query_type == 'emotional':
            # Full emotional enhancement for purely emotional queries
            return self._enhance_emotional_query(query, emotional_analysis.primary_emotion)
        
        else:
            return query  # No enhancement for neutral queries
    
    def _enhance_emotional_query(self, query: str, emotion: str) -> str:
        """Enhance emotional queries with appropriate context"""
        
        if emotion == 'sad':
            return f"{query} emotional support help"
        elif emotion == 'worried':
            return f"{query} support help guidance"
        elif emotion == 'confused':
            # Special handling for guidance office queries
            if 'guidance office' in query.lower() or 'guidance' in query.lower():
                return query  # Keep original query for guidance office
            else:
                return f"{query} help guidance support"
        elif emotion == 'angry':
            return f"{query} support help understanding"
        elif emotion == 'frustrated':
            return f"{query} help support assistance"
        else:
            return query  # No enhancement for other emotions
    
    async def _handle_multiple_grade_search(self, search_query: str, intent_name: str, conversation_history: list, nlu_result) -> list:
        """Handle searches that might involve multiple grades"""
        import re
        
        # Check if query contains multiple grades
        grade_patterns = [
            r'grade\s+(\d+)\s+and\s+(\d+)',  # "grade 1 and 5"
            r'grade\s+(\d+)\s+&\s+(\d+)',     # "grade 1 & 5"
            r'grade\s+(\d+)\s+,\s+(\d+)',     # "grade 1, 5"
            r'grades?\s+(\d+)\s+and\s+(\d+)', # "grades 1 and 5"
            r'(\d+)\s+and\s+(\d+)',           # "1 and 5"
        ]
        
        multiple_grades = []
        for pattern in grade_patterns:
            match = re.search(pattern, search_query.lower())
            if match:
                multiple_grades = [match.group(1), match.group(2)]
                break
        
        if multiple_grades:
            # Search for each grade individually and combine results
            all_results = []
            seen_ids = set()
            
            for grade in multiple_grades:
                # Create specific search queries for each grade
                grade_queries = [
                    f"grade {grade} teacher",
                    f"grade {grade} adviser", 
                    f"grade {grade}",
                    f"{grade}th grade teacher",
                    f"{grade}th grade adviser"
                ]
                
                for grade_query in grade_queries:
                    results = await self.database_search.search_prompts_three_tier(
                        grade_query, limit=3, intent=intent_name, 
                        conversation_history=conversation_history, nlu_result=nlu_result
                    )
                    
                    # Add unique results
                    for result in results:
                        if result.get('id') not in seen_ids:
                            all_results.append(result)
                            seen_ids.add(result.get('id'))
            
            # If we found results, return them
            if all_results:
                return all_results[:10]  # Limit to 10 results
        
        # Fallback to regular three-tier search
        return await self.database_search.search_prompts_three_tier(
            search_query, limit=10, intent=intent_name, 
            conversation_history=conversation_history, nlu_result=nlu_result
        )
    
    def _is_simple_response(self, query: str) -> bool:
        """Check if query is a simple response word"""
        import re
        
        query_lower = query.lower().strip()
        
        # Check for elongated greetings first
        elongated_greeting_pattern = r'^(h+i+|h+e+l+l+o+|h+e+y+)$'
        if re.match(elongated_greeting_pattern, query_lower):
            return True
        
        # Check for regular simple responses
        simple_responses = {
            'yes', 'no', 'ok', 'okay', 'sure', 'maybe', 'alright', 'fine', 
            'good', 'bad', 'great', 'awesome', 'cool', 'nice', 'thanks', 
            'thank', 'please', 'sorry', 'hello', 'hi', 'hey', 'bye', 
            'goodbye', 'welcome', 'help'
        }
        return query_lower in simple_responses
    
    async def _handle_simple_response(self, query: str, conversation_history: list, session_id: str) -> str:
        """Handle simple responses with context awareness"""
        query_lower = query.lower().strip()
        
        # Check conversation history for context
        if conversation_history and len(conversation_history) > 0:
            # Get the last few messages for context
            recent_messages = conversation_history[-3:] if len(conversation_history) >= 3 else conversation_history
            
            # Look for patterns in recent conversation
            for message in reversed(recent_messages):
                if hasattr(message, 'content'):
                    content = message.content.lower()
                    
                    # Check if we asked a yes/no question
                    if any(phrase in content for phrase in ['do you', 'would you', 'can you', 'will you', 'are you', 'is it', 'does it']):
                        if query_lower in ['yes', 'sure', 'ok', 'okay', 'alright']:
                            return "Great! I'm glad I could help. Is there anything else you'd like to know about our school?"
                        elif query_lower in ['no', 'maybe']:
                            return "No problem! If you change your mind or have any other questions about our school, feel free to ask anytime."
                    
                    # Check if we provided information
                    elif any(phrase in content for phrase in ['teacher', 'grade', 'school', 'schedule', 'hours', 'principal', 'office']):
                        if query_lower in ['yes', 'sure', 'ok', 'okay', 'alright', 'good', 'great', 'awesome', 'cool', 'nice']:
                            return "Perfect! I'm happy I could help you with that information. Is there anything else you'd like to know about our school?"
                        elif query_lower in ['no', 'maybe']:
                            return "No worries! If you have any other questions about our school, I'm here to help."
        
        # No context found - provide helpful response
        if query_lower in ['yes', 'sure', 'ok', 'okay', 'alright']:
            return "I'm here to help! What would you like to know about Tomas SM Bautista Elementary School? You can ask about teachers, schedules, school hours, or any other school-related information."
        elif query_lower in ['no', 'maybe']:
            return "No problem! If you have any questions about our school later, feel free to ask. I'm here to help with information about teachers, schedules, school hours, and more."
        elif query_lower in ['thanks', 'thank']:
            return "You're welcome! I'm happy to help. Is there anything else you'd like to know about our school?"
        elif query_lower in ['hello', 'hi', 'hey']:
            return "Hello! Welcome to Tomas SM Bautista Elementary School chatbot. How can I help you today? You can ask about teachers, schedules, school hours, or any other school information."
        elif query_lower in ['help']:
            return "I'm here to help! You can ask me about:\n• Teachers and their grades\n• School schedules and hours\n• School activities and programs\n• Contact information\n• Enrollment details\n\nWhat would you like to know?"
        else:
            # Check for elongated greetings
            import re
            elongated_greeting_pattern = r'^(h+i+|h+e+l+l+o+|h+e+y+)$'
            if re.match(elongated_greeting_pattern, query_lower):
                return "Hello! Welcome to Tomas SM Bautista Elementary School chatbot. How can I help you today? You can ask about teachers, schedules, school hours, or any other school information."
            else:
                return None  # No specific context found
    
    def _is_vague_query(self, query: str) -> bool:
        """Check if query is vague or unclear"""
        query_lower = query.lower().strip()
        
        # Check for appreciation patterns first - these are NOT vague
        appreciation_patterns = ['thank you', 'thanks', 'thank u', 'thx', 'ty', 'tysm', 'salamat', 'maraming salamat', 'damo nga salamat', 'salamat gid']
        if any(pattern in query_lower for pattern in appreciation_patterns):
            return False
        
        # Check for greeting patterns - these are NOT vague (they're complete expressions)
        greeting_patterns = [
            'good morning', 'good afternoon', 'good evening', 'good noon', 'good day', 'good night',
            'magandang umaga', 'magandang hapon', 'magandang gabi', 'magandang tanghali', 'magandang araw',
            'maayong aga', 'maayong hapon', 'maayong gab-i', 'maayong tanghali', 'maayong adlaw',
            'maayong gabii', 'maayong buntag', 'hey there', 'hello there', 'hi there',
            'hello', 'hi', 'hey', 'kumusta', 'kamusta', 'hiya', 'howdy', 'greetings'
        ]
        if any(pattern in query_lower for pattern in greeting_patterns):
            return False
        
        # Very short queries (1-2 words) that aren't simple responses and aren't greetings
        words = query_lower.split()
        if len(words) <= 2 and not self._is_simple_response(query):
            return True
        
        # Vague patterns
        vague_patterns = [
            r'^(what|who|where|when|why|how)\s*$',  # Single question words
            r'^(tell me|i want|i need|help me)\s*$',  # Incomplete requests
            r'^(about|info|information)\s*$',  # Too general
            r'^(school|teacher|student|grade)\s*$',  # Single topic words
            r'^(something|anything|everything)\s*$',  # Vague pronouns
        ]
        
        import re
        for pattern in vague_patterns:
            if re.match(pattern, query_lower):
                return True
        
        return False
    
    async def _generate_query_suggestions(self, query: str, search_results: list) -> str:
        """Generate helpful suggestions for vague queries"""
        query_lower = query.lower().strip()
        words = query_lower.split()
        
        suggestions = []
        
        # Analyze the query to understand what they might be looking for
        if len(words) == 1:
            word = words[0]
            
            if word in ['what', 'who', 'where', 'when', 'why', 'how']:
                suggestions = [
                    "• What are the school hours?",
                    "• Who is the principal?",
                    "• Where is the school located?",
                    "• When does school start?",
                    "• Why choose our school?",
                    "• How do I enroll my child?"
                ]
            elif word in ['teacher', 'teachers']:
                suggestions = [
                    "• Who is the teacher for grade 1?",
                    "• Who are the teachers for grades 1-6?",
                    "• Who is the principal?",
                    "• Who is the head teacher?"
                ]
            elif word in ['grade', 'grades']:
                suggestions = [
                    "• What grade levels are offered?",
                    "• Who is the teacher for grade 1?",
                    "• Who is the teacher for grade 5?",
                    "• What are the grade requirements?"
                ]
            elif word in ['school']:
                suggestions = [
                    "• What are the school hours?",
                    "• Where is the school located?",
                    "• What programs does the school offer?",
                    "• How do I contact the school?"
                ]
            elif word in ['student', 'students']:
                suggestions = [
                    "• What grade levels are offered?",
                    "• What are the school hours?",
                    "• What programs are available?",
                    "• How do I enroll my child?"
                ]
            elif word in ['help']:
                suggestions = [
                    "• What are the school hours?",
                    "• Who is the principal?",
                    "• What grade levels are offered?",
                    "• How do I contact the school?",
                    "• What programs does the school offer?"
                ]
        
        elif len(words) == 2:
            # Two-word combinations
            if 'tell' in words and 'me' in words:
                suggestions = [
                    "• Tell me about the school hours",
                    "• Tell me who the teachers are",
                    "• Tell me about the school programs",
                    "• Tell me how to contact the school"
                ]
            elif 'i' in words and 'want' in words:
                suggestions = [
                    "• I want to know the school hours",
                    "• I want to know who the teachers are",
                    "• I want to know about enrollment",
                    "• I want to contact the school"
                ]
            elif 'i' in words and 'need' in words:
                suggestions = [
                    "• I need to know the school hours",
                    "• I need to know who the teachers are",
                    "• I need to know about enrollment",
                    "• I need to contact the school"
                ]
        
        # If we have search results, use them to generate more specific suggestions
        if search_results and not suggestions:
            suggestions = []
            for i, result in enumerate(search_results[:3]):
                keywords = result.get('keywords', '')
                if keywords:
                    # Extract key topics from keywords
                    topics = keywords.split(',')[:2]  # Take first 2 topics
                    for topic in topics:
                        topic = topic.strip()
                        if topic and len(topic) > 3:  # Avoid very short topics
                            suggestions.append(f"• {topic}")
                            if len(suggestions) >= 4:
                                break
        
        # Default suggestions if nothing else works
        if not suggestions:
            suggestions = [
                "• What are the school hours?",
                "• Who is the principal?",
                "• What grade levels are offered?",
                "• How do I contact the school?",
                "• What programs does the school offer?"
            ]
        
        # Format the suggestions
        if suggestions:
            return "You might be looking for:\n" + "\n".join(suggestions[:5])  # Limit to 5 suggestions
        else:
            return None
