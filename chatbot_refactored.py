"""
Refactored ChatBot - Clean, Modular, and Fixed
Main chatbot class with all underlying issues resolved
"""
import os
import logging
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our clean modules
from core.database_search import DatabaseSearchEngine
# PgVector semantic search removed for lightweight version
from core.language_detector import LanguageDetector
from core.response_generator import ResponseGenerator
from core.keyword_matcher import KeywordMatcher
from core.conversation_memory import ConversationMemory
# Context-aware NLU removed - using simple logic instead
# ML enhancements removed - they cause hallucinations

# Import existing modules
from nlu_engine import NLUEngine, Intent, NLUResult
from entity_extractor import AdvancedEntityExtractor, ExtractedEntity
from core.security import sql_protector

# Import advanced AI modules
from core.conversation_analyzer import ConversationAnalyzer, ConversationContext
from core.emotional_intelligence import EmotionalIntelligence, EmotionalAnalysis
from core.response_personalizer import ResponsePersonalizer, PersonalizedResponse

logger = logging.getLogger(__name__)

@dataclass
class ChatResponse:
    """Clean response structure"""
    response: List[str]  # Can be single message or split messages
    entities: List[Dict[str, Any]]
    detected_language: str
    language_confidence: float
    is_split: bool
    message_count: int
    intent: Optional[str] = None  # Add intent field

class ChatBot:
    """Clean, refactored chatbot with fixed underlying issues"""
    
    def __init__(self, groq_key: str):
        # Initialize core components
        self.language_detector = LanguageDetector()
        self.response_generator = ResponseGenerator(groq_key)
        self.keyword_matcher = KeywordMatcher()
        
        # Initialize database search
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        self.database_search = DatabaseSearchEngine(supabase_url, supabase_key)
        
        # PgVector semantic search removed for lightweight version
        
        # Initialize NLP components
        self.nlu_engine = NLUEngine()
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
        
        # logger.info("✅ ChatBot initialized with clean, modular architecture")  # Reduced for Railway
    
    def _extract_user_name(self, conversation_history: List[Dict]) -> str:
        """Extract user name from conversation history using NLP entity extraction"""
        for msg in reversed(conversation_history):
            if not isinstance(msg, dict):
                # Removed verbose warning logging
                continue
            if msg.get("role") == "user":
                content = msg.get("content", "")
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
            if not isinstance(msg, dict):
                # Removed verbose warning logging
                continue
            if msg.get("role") == "user":
                content = msg.get("content", "").lower()
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
                if not isinstance(msg, dict):
                    # Removed verbose warning logging
                    continue
                if msg.get("role") == "user":
                    content = msg.get("content", "")
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
            "makausap", "makipag-usap", "magistryo", "tao", "staff", "principal",
            "kausapin", "gusto ko kausapin", "admin lang", "wala, admin lang"
        ]
        
        # Only count user messages, not assistant responses
        user_messages = [msg for msg in recent_messages if isinstance(msg, dict) and msg.get('role') == 'user']
        
        for message in user_messages:
            content = message.get('content', '').lower()
            
            # Check for escalation patterns
            if any(pattern in content for pattern in escalation_patterns):
                escalation_count += 1
        
        # 🚨 ADJUSTED: Lower threshold for persistence - if user mentions admin/contact 1+ times, consider it persistent
        # This ensures users get the messenger link when they specifically ask for admin contact
        is_persistent = escalation_count >= 1
        # logger.info(f"🔍 PERSISTENCE CHECK: Found {escalation_count} escalation patterns, persistent: {is_persistent}")
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
        
        # Common question patterns
        question_indicators = [
            r'\?',  # Question marks
            r'\b(what|where|when|who|how|why|which|can|could|would|should|is|are|do|does|did|will|have|has)\b',
            r'\b(ano|saan|kailan|sino|paano|bakit|alin|pwed|maaari|gusto|kailangan)\b',  # Tagalog
            r'\b(ginausoy|hinahanap|gusto ko|kailangan ko|pwede|maaari)\b'  # Aklanon
        ]
        
        # Count question indicators
        question_count = 0
        for pattern in question_indicators:
            matches = re.findall(pattern, query, re.IGNORECASE)
            question_count += len(matches)
        
        # Special handling for comma-separated questions
        # If we have commas and question words, it's likely multiple questions
        comma_count = query.count(',')
        if comma_count > 0 and question_count >= 2:
            # Boost the question count for comma-separated patterns
            question_count += comma_count
        
        # Enhanced detection for space-separated questions
        # Look for patterns like "What is X? where is Y" (question mark followed by lowercase)
        space_separated_pattern = r'\?\s+[a-z]'
        if re.search(space_separated_pattern, query, re.IGNORECASE):
            question_count += 1
        
        # Look for multiple question words in sequence - but be more careful
        # Only count as multiple if they're clearly separate questions, not part of one question
        # Pattern: question word + content + question word + content (with significant separation)
        sequential_questions = r'\b(what|where|when|who|how|why|which|can|could|would|should|is|are|do|does|did|will|have|has|ano|saan|kailan|sino|paano|bakit|alin|pwed|maaari|gusto|kailangan)\b.*?(?:\?|\.|,|;).*?\b(what|where|when|who|how|why|which|can|could|would|should|is|are|do|does|did|will|have|has|ano|saan|kailan|sino|paano|bakit|alin|pwed|maaari|gusto|kailangan)\b'
        if re.search(sequential_questions, query, re.IGNORECASE):
            question_count += 1
        
        # Debug: Print question count for troubleshooting
        # print(f"DEBUG: Query='{query}', Question count={question_count}")
        
        # Special case: Don't split questions that are clearly single questions
        # Check for common single question patterns that shouldn't be split
        single_question_patterns = [
            r'does\s+\w+\s+\w+\s+have\s+',  # "does the grade five have"
            r'do\s+\w+\s+\w+\s+have\s+',    # "do the students have"
            r'is\s+\w+\s+\w+\s+',           # "is the school"
            r'are\s+\w+\s+\w+\s+',          # "are the students"
            r'can\s+\w+\s+\w+\s+',          # "can the school"
            r'will\s+\w+\s+\w+\s+',         # "will the school"
            r'does\s+the\s+\w+\s+\w+\s+',   # "does the grade five"
            r'saan\s+ang\s+\w+\s+',         # "saan ang guidance office" (Tagalog)
            r'ano\s+ang\s+\w+\s+',          # "ano ang school" (Tagalog)
            r'sino\s+ang\s+\w+\s+',         # "sino ang teacher" (Tagalog)
            r'kailan\s+ang\s+\w+\s+',        # "kailan ang exam" (Tagalog)
            r'paano\s+ang\s+\w+\s+',        # "paano ang enrollment" (Tagalog)
        ]
        
        is_single_question = any(re.search(pattern, query, re.IGNORECASE) for pattern in single_question_patterns)
        
        # If we have multiple question indicators, try to split
        if question_count >= 2 and not is_single_question:
            # First try simple separators
            simple_separators = [
                r'\s+and\s+',  # "and" with spaces
                r'\s+at\s+',   # "at" (Tagalog "and")
                r'\s+,\s+',    # Comma with spaces (more specific)
                r'\s+\.\s+',   # Period with spaces
                r'\s+;\s*',    # Semicolon
                r'\s+also\s+', # "also"
                r'\s+din\s+', # "din" (Tagalog "also")
                r'\s+pati\s+', # "pati" (Tagalog "including")
                r'\s+plus\s+', # "plus"
                r'\s+at\s+saka\s+', # "at saka" (Tagalog "and also")
                r'\s*,\s*',    # Comma with optional spaces (fallback)
                r'\?\s+',      # Question mark followed by space (for "What is X? where is Y")
            ]
            
            questions = [query]  # Start with original query
            
            # Try simple separators first
            for separator in simple_separators:
                new_questions = []
                for q in questions:
                    parts = re.split(separator, q, flags=re.IGNORECASE)
                    if len(parts) > 1:
                        # Check if each part looks like a question
                        for part in parts:
                            part = part.strip()
                            if len(part) > 10:  # Minimum length for a question
                                # Check if it has question characteristics
                                has_question_mark = '?' in part
                                has_question_word = any(re.search(pattern, part, re.IGNORECASE) for pattern in question_indicators[1:])
                                
                                if has_question_mark or has_question_word:
                                    new_questions.append(part)
                                else:
                                    # If no clear question indicators, keep as is
                                    new_questions.append(part)
                    else:
                        new_questions.append(q)
                questions = new_questions
                
                # If we found multiple questions, stop here
                if len(questions) > 1:
                    break
            
            # If simple separators didn't work, try intelligent question word splitting
            if len(questions) == 1:
                # Look for patterns like "What is X who is Y what is Z"
                question_word_pattern = r'\b(what|where|when|who|how|why|which|can|could|would|should|is|are|do|does|did|will|have|has|ano|saan|kailan|sino|paano|bakit|alin|pwed|maaari|gusto|kailangan)\b'
                
                # Find all question word positions
                matches = list(re.finditer(question_word_pattern, query, re.IGNORECASE))
                
                if len(matches) >= 2:
                    # Split at question word boundaries
                    new_questions = []
                    for i, match in enumerate(matches):
                        start = match.start()
                        if i == 0:
                            # First question starts from beginning
                            end = matches[i + 1].start() if i + 1 < len(matches) else len(query)
                        else:
                            # Subsequent questions start from this match
                            end = matches[i + 1].start() if i + 1 < len(matches) else len(query)
                        
                        question_part = query[start:end].strip()
                        if len(question_part) > 10:  # Minimum length
                            new_questions.append(question_part)
                    
                    if len(new_questions) >= 2:
                        questions = new_questions
            
            # Filter out very short questions and clean up
            filtered_questions = []
            for q in questions:
                q = q.strip()
                if len(q) > 15:  # Minimum meaningful question length
                    # Remove leading/trailing punctuation
                    q = re.sub(r'^[.,;:\s]+|[.,;:\s]+$', '', q)
                    if q:
                        filtered_questions.append(q)
            
            # Limit to 5 questions maximum
            if len(filtered_questions) > 5:
                filtered_questions = filtered_questions[:5]
            
            # Only consider it multiple questions if we have 2-5 valid questions
            if 2 <= len(filtered_questions) <= 5:
                return True, filtered_questions
        
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
            current_conversation_history = conversation_history or []
            
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
            # 0. Typo correction for individual questions
            question = self._correct_common_typos(question)
            
            # Use the existing chat logic but with multi-question context
            # This is essentially the same as the main chat method but with additional context
            
            # 0.1. Security validation
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
            
            # 5. Database search with multi-question context
            intent_name = nlu_result.intent.name.lower() if nlu_result and nlu_result.intent else None
            search_results = await self.database_search.search_prompts(question, limit=10, intent=intent_name)
            
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
            
            response_text = await self.response_generator.generate_response(
                question, context, response_lang, conversation_history, nlu_info, user_name, entities, float(confidence), context_analysis
            )
            
            # Split response if needed
            split_messages = response_text if isinstance(response_text, list) else [response_text]
            
            return ChatResponse(
                response=split_messages,
                entities=[{"entity_type": e.entity_type, "value": e.value, "confidence": e.confidence} for e in entities],
                detected_language=response_lang,
                language_confidence=confidence,
                is_split=len(split_messages) > 1,
                message_count=len(split_messages),
                intent=nlu_result.intent.value if nlu_result and nlu_result.intent else 'unknown'
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

    def _correct_common_typos(self, query: str) -> str:
        """Real fuzzy matching typo correction using string similarity"""
        import re
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
            'social', 'studies', 'physical', 'education', 'computer', 'technology'
        ]
        
        words = query.split()
        corrected_words = []
        
        for word in words:
            # Clean the word (remove punctuation for matching)
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            if len(clean_word) < 3:  # Skip very short words
                corrected_words.append(word)
                continue
            
            # Find the best match using fuzzy matching
            best_match = None
            best_ratio = 0.0
            
            for vocab_word in school_vocabulary:
                # Calculate similarity ratio
                ratio = SequenceMatcher(None, clean_word, vocab_word.lower()).ratio()
                
                # If similarity is high enough (threshold: 0.7)
                if ratio > 0.7 and ratio > best_ratio:
                    best_ratio = ratio
                    best_match = vocab_word
            
            # Use the best match if found, otherwise keep original
            if best_match and best_ratio > 0.7:
                # Preserve original capitalization pattern
                if word.isupper():
                    corrected_words.append(best_match.upper())
                elif word.istitle():
                    corrected_words.append(best_match.title())
                else:
                    corrected_words.append(best_match)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)

    async def chat(self, query: str, conversation_history: List[Dict] = None, 
                   user_timezone: str = None, session_id: str = None) -> ChatResponse:
        """Main chat method - Groq-first approach for natural responses with multi-question support"""
        try:
            # 0. Typo correction
            original_query = query
            query = self._correct_common_typos(query)
            
            # 0.1. Multi-question detection and processing
            is_multi_question, questions = self._detect_multiple_questions(query)
            
            if is_multi_question:
                # Process multiple questions
                return await self._handle_multiple_questions(questions, conversation_history, user_timezone, session_id)
            
            # 0.2. Security validation - check for SQL injection attempts
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
            # logger.info(f"🌍 Language detection: {detected_lang} (confidence: {confidence:.2f})")
            
            # Map detected language to response language
            response_lang = self._map_to_response_language(detected_lang)
            # logger.info(f"🌍 Language mapping: {detected_lang} → {response_lang}")  # Reduced for Railway
            
            # Check for mixed-language input
            if confidence < 0.7:
                # logger.info("🔍 Low confidence language detection - may be mixed language")  # Commented out debug logs
                # Use context-aware translation for mixed languages
                if conversation_history:
                    context_lang, context_confidence = self._detect_context_language(conversation_history)
                    if context_confidence > confidence:
                        detected_lang = context_lang
                        response_lang = self._map_to_response_language(detected_lang)
                        confidence = context_confidence
                        # logger.info(f"🌍 Context-based language detection: {detected_lang} → {response_lang} (confidence: {confidence:.2f})")  # Commented out debug logs
            
            # 2. Get NLU analysis for intent
            nlu_result = await self.nlu_engine.analyze_intent(query)
            
            # Semantic intent classification removed - using simple NLU only
            
            # logger.info(f"🎯 NLU Intent: {nlu_result.intent.value} for query: {query}")  # Reduced for Railway
            
            # CRITICAL SAFETY: Check for medical emergencies (HIGHEST PRIORITY)
            if nlu_result.intent.value == "emergency":
                # Removed verbose emergency logging
                return self._handle_emergency_response(query, response_lang)
            
            # 2.5. Advanced AI Analysis - Conversation Intelligence
            conversation_context = None
            emotional_analysis = None
            
            try:
                # Analyze conversation context
                conversation_context = await self.conversation_analyzer.analyze_conversation_context(
                    current_query=query,
                    conversation_history=conversation_history or [],
                    nlu_result=nlu_result,
                    entities=[]  # Will be populated later
                )
                # logger.info(f"🧠 Conversation analysis: {conversation_context.topic_flow}, urgency: {conversation_context.urgency_level}")  # Reduced for Railway
                
                # Analyze emotions
                emotional_analysis = await self.emotional_intelligence.analyze_emotions(
                    current_query=query,
                    conversation_history=conversation_history or [],
                    language=detected_lang
                )
                # logger.info(f"💭 Emotional analysis: {emotional_analysis.primary_emotion} (intensity: {emotional_analysis.emotion_intensity:.2f})")
                
            except Exception as e:
                logger.warning(f"⚠️ Advanced AI analysis failed: {e}")
                # Continue with basic processing
            
            # 3. Enhanced entity extraction with relationships
            entities = self.entity_extractor.extract_entities(query, nlu_result.intent.value if nlu_result else None)
            
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
                # logger.info(f"🧠 Updated memory for user: {user_memory.name}, topics: {list(user_memory.topics.keys())}")  # Commented out debug logs
                
                # Debug: Check if name was actually stored
                stored_name = self.conversation_memory.get_user_name(session_id)
                # logger.info(f"🧠 Memory verification - Stored name: '{stored_name}'")  # Commented out debug logs
            
            # Special case: Handle name-related queries directly
            if any(phrase in query.lower() for phrase in ["what's my name", "what is my name", "my name", "who am i", "do you know my name"]):
                if user_name:
                    # logger.info(f"👤 User asking about their name - we know it's: {user_name}")  # Commented out debug logs
                    # Skip database search and provide direct response
                    search_results = []
                    best_result = None
                    context = f"User is asking about their name. Their name is {user_name}. Provide a friendly response confirming their name."
                else:
                    # logger.info("👤 User asking about their name - we don't know it yet")  # Commented out debug logs
                    # Skip database search and ask for their name
                    search_results = []
                    best_result = None
                    context = "User is asking about their name but we don't have it in memory. Ask them to introduce themselves."
            else:
                # 🚨 CRITICAL: Check for special intents FIRST before database search
                # These intents should skip database search entirely
                if nlu_result and nlu_result.intent.value == 'contact_escalation':
                    # logger.info("👥 Contact escalation requested - checking conversation history for persistence")
                    
                    # Check if user has been persistent about wanting to talk to someone
                    persistent_escalation = self._check_persistent_escalation(conversation_history)
                    
                    if persistent_escalation:
                        # logger.info("👥 Persistent escalation detected - providing direct contact option")
                        # Provide direct escalation response
                        search_results = []
                        best_result = None
                        context = "User has been persistent about wanting to talk to a live person/admin. Provide the Facebook Messenger contact link immediately."
                    else:
                        # logger.info("👥 First escalation request - using helpful approach first")
                        # Use helpful approach for first request
                        search_results = []
                        best_result = None
                        context = "User wants to talk to someone from the school - be helpful first by offering assistance with school topics, enrollment, schedules, or other school information. Only mention contact options if they specifically ask again after being helpful."
                else:
                    # 3. Perform traditional database search to get context for Groq
                    intent_name = nlu_result.intent.name.lower() if nlu_result and nlu_result.intent else None
                    
                    # Enhance search with emotional context
                    search_query = query
                    if emotional_analysis and emotional_analysis.primary_emotion != 'neutral':
                        # Add emotional context to search for better results
                        if emotional_analysis.primary_emotion == 'sad':
                            search_query = f"{query} emotional support help support aide"
                        elif emotional_analysis.primary_emotion == 'worried':
                            search_query = f"{query} support help guidance"
                        elif emotional_analysis.primary_emotion == 'confused':
                            # Special handling for guidance office queries - don't enhance them
                            if 'guidance office' in query.lower() or 'guidance' in query.lower():
                                search_query = query  # Keep original query for guidance office
                            else:
                                search_query = f"{query} help guidance support"
                        # logger.info(f"💭 Enhanced search query: '{search_query}' (emotion: {emotional_analysis.primary_emotion})")
                    
                    search_results = await self.database_search.search_prompts(search_query, limit=10, intent=intent_name)
                    
                    # 4. Simple logic: Use top database result if available
                    best_result = None
                    if search_results:
                        # Skip contact escalation queries - don't use irrelevant database results
                        if nlu_result and nlu_result.intent.value == 'contact_escalation':
                            # logger.info("🚨 Contact escalation detected - not using database results")
                            pass
                        else:
                            # Use the top-ranked result (scoring algorithm already ranked by relevance)
                            best_result = search_results[0]
                            # logger.info(f"🏆 Using top-ranked result: {best_result.get('keywords', 'No keywords')}")
                
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
                                    detected_language=response_lang,
                                    language_confidence=confidence,
                                    is_split=False,
                                    message_count=1,
                                    intent=nlu_result.intent.value if nlu_result and nlu_result.intent else 'unknown'
                                )
                            elif grade_num > 12:
                                return ChatResponse(
                                    response=[f"Grade {grade_num} is not a valid grade level. Elementary schools typically offer grades 1-6."],
                                    entities=entities,
                                    detected_language=response_lang,
                                    language_confidence=confidence,
                                    is_split=False,
                                    message_count=1,
                                    intent=nlu_result.intent.value if nlu_result and nlu_result.intent else 'unknown'
                                )
                    
                    # 3. Perform traditional database search to get context for Groq
                    intent_name = nlu_result.intent.name.lower() if nlu_result and nlu_result.intent else None
                    
                    # Enhance search with emotional context
                    search_query = query
                    if emotional_analysis and emotional_analysis.primary_emotion != 'neutral':
                        # Add emotional context to search for better results
                        if emotional_analysis.primary_emotion == 'sad':
                            search_query = f"{query} emotional support help support aide"
                        elif emotional_analysis.primary_emotion == 'worried':
                            search_query = f"{query} support help guidance"
                        elif emotional_analysis.primary_emotion == 'confused':
                            # Special handling for guidance office queries - don't enhance them
                            if 'guidance office' in query.lower() or 'guidance' in query.lower():
                                search_query = query  # Keep original query for guidance office
                            else:
                                search_query = f"{query} help guidance support"
                        # logger.info(f"💭 Enhanced search query: '{search_query}' (emotion: {emotional_analysis.primary_emotion})")
                    
                    search_results = await self.database_search.search_prompts(search_query, limit=10, intent=intent_name)
                    # logger.info(f"🔍 Traditional search found {len(search_results)  # Commented out debug logs} results")
                    
                    # 4. Simple logic: Use top database result if available
                    best_result = None
                    if search_results:
                        # Skip contact escalation queries - don't use irrelevant database results
                        if nlu_result and nlu_result.intent.value == 'contact_escalation':
                            # logger.info("🚨 Contact escalation detected - not using database results")
                            pass
                        else:
                            # Use the top-ranked result (scoring algorithm already ranked by relevance)
                            best_result = search_results[0]
                            # logger.info(f"🏆 Using top-ranked result: {best_result.get('keywords', 'No keywords')}")
            
            # 5. Generate response using Groq with context-aware analysis
            if best_result:
                # logger.info("📚 Using database context for response generation")
                # Provide complete database information as context
                if isinstance(best_result, dict):
                    keywords = best_result.get('keywords', '')
                    response = best_result.get('response', '')
                    context = f"Database Information: {keywords} - {response}"
                    # logger.info(f"📚 DEBUG: Context built: {context[:200]}...")
                    # logger.info(f"📚 DEBUG: Keywords: '{keywords}'")
                    # logger.info(f"📚 DEBUG: Response: '{response[:100]}...'")
                else:
                    logger.warning(f"⚠️ Best result is not a dict: {type(best_result)} - {best_result}")
                    context = f"Database Information: {best_result}"
                
                # 🎯 FIX: Add explicit clarification for grade level questions
                if 'grade' in query.lower() and 'grade level' in context.lower():
                    context += "\n\nIMPORTANT: If the database says 'kindergarten through grade 6', this means Grade 7 and above are NOT offered."
                
                # 🎯 NEW: Handle grade validation responses
                if isinstance(best_result, dict) and best_result.get('is_grade_validation'):
                    # This is a grade validation response - use it directly
                    response_text = best_result.get('response', '')
                    # logger.info(f"🎯 Grade validation response: {response_text}")
                    return ChatResponse(
                        response=[response_text],
                        entities=entities,
                        detected_language=response_lang,
                        language_confidence=confidence,
                        is_split=False,
                        message_count=1,
                        intent=nlu_result.intent.value if nlu_result and nlu_result.intent else 'unknown'
                    )
                
                # 🎯 FIX: Enhance context for Tagalog queries
                if detected_lang in ['tl', 'akl']:
                    # Add more comprehensive context for Tagalog queries
                    if len(context) < 200:  # If context is too short, add more information
                        context += "\n\nADDITIONAL CONTEXT: Answer in natural, grammatically correct Tagalog. Be conversational but professional. Use proper Tagalog grammar and natural sentence structure."
            else:
                # Context-aware NLU determined not to use database context
                # logger.info("🎯 Context-aware NLU: Not using database context")
                if nlu_result and nlu_result.intent.value == 'contact_escalation':
                    context = "User wants to talk to someone from the school - be helpful first by offering assistance with school topics, enrollment, schedules, or other school information. Only mention contact options if they specifically ask again after being helpful."
                else:
                    context = "No specific information available in database for this query"
                # logger.info(f"🔍 DEBUG: No best_result, context set to: {context}")
            
            # Debug: Log the final context before sending to AI
            # logger.info(f"🔍 FINAL CONTEXT: {context[:200]}...")  # Reduced for Railway
            
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
                if nlu_result and nlu_result.intent.value in ['name_introduction', 'greeting_with_name']:
                    # logger.info(f"👋 {nlu_result.intent.value} detected - handling with Groq even without database context")  # Commented out debug logs
                    # For name introductions, we don't need database context
                    context = "User is introducing themselves with their name"
                elif nlu_result and nlu_result.intent.value == 'emotional_expression':
                    # logger.info(f"😊 {nlu_result.intent.value} detected - handling emotional expression")  # Commented out debug logs
                    # For emotional expressions, provide empathetic response
                    context = "User is expressing their emotional state"
                elif nlu_result and nlu_result.intent.value == 'appreciation':
                    # logger.info(f"🙏 {nlu_result.intent.value} detected - handling appreciation/thanks")  # Commented out debug logs
                    # For appreciation/thanks, provide friendly acknowledgment
                    context = "User is expressing appreciation or thanks"
                elif nlu_result and nlu_result.intent.value == 'greeting_simple':
                    # logger.info(f"👋 {nlu_result.intent.value} detected - handling simple greeting")  # Commented out debug logs
                    # For simple greetings, provide friendly response
                    context = "User is giving a simple greeting"
                elif nlu_result and nlu_result.intent.value == 'medical_emergency':
                    # logger.info(f"🚨 {nlu_result.intent.value} detected - handling medical emergency")  # Commented out debug logs
                    # For medical emergencies, provide immediate emergency response
                    context = "MEDICAL EMERGENCY DETECTED - User is experiencing a medical emergency requiring immediate attention"
                elif nlu_result and nlu_result.intent.value == 'contact_escalation':
                    # logger.info(f"👥 {nlu_result.intent.value} detected - using helpful approach first")  # Commented out debug logs
                    # For contact escalation, use helpful approach: ask about other school topics first
                    context = "User wants to talk to someone from the school - use helpful approach to suggest other school topics first before offering contact escalation"
                # Remove the old fallback logic - let Groq handle all cases intelligently
            
            # Generate response with Groq (professional, factual, humane, jolly, no roleplay)
            # Pass enhanced NLP/NLU information for better response generation
            nlu_info_dict = nlu_info  # Use the enhanced nlu_info with emotional analysis
            
            response_text = await self.response_generator.generate_response(
                query, context, response_lang, conversation_history, nlu_info_dict, user_name, entities, float(confidence), None
            )
            
            # Add Messenger link for contact escalation requests
            if nlu_result and nlu_result.intent.value == 'contact_escalation':
                response_text = self.response_generator.add_messenger_link_if_needed(
                    response_text, query, context, response_lang
                )
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
            if detected_lang != "en" and confidence < 0.8:
                # logger.info("🌐 Applying context-aware translation")  # Commented out debug logs
                # Handle both string and list responses
                if isinstance(response_text, list):
                    # Translate each message in the list
                    translated_messages = []
                    for message in response_text:
                        translated_message, translation_confidence = self.context_translator.translate_with_context(
                            message, detected_lang, conversation_history, session_id
                        )
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
                    if translation_confidence > 0.7:
                        response_text = translated_response
                    # logger.info(f"🌐 Context-aware translation applied (confidence: {translation_confidence:.2f})  # Commented out debug logs")
            
            # 6. Response is already split by generate_response
            split_messages = response_text if isinstance(response_text, list) else [response_text]
            
            return ChatResponse(
                response=split_messages,
                entities=[{"entity_type": e.entity_type, "value": e.value, "confidence": e.confidence} for e in entities],
                detected_language=response_lang,
                language_confidence=confidence,
                is_split=len(split_messages) > 1,
                message_count=len(split_messages),
                intent=nlu_result.intent.value if nlu_result and nlu_result.intent else 'unknown'
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
            
            return self._create_error_response(detected_lang if 'detected_lang' in locals() else "en")
    
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
                detected_language=response_lang,  # Use mapped response language
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
                detected_language=response_lang,  # Use mapped response language
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
    
    def _handle_emergency_response(self, query: str, response_lang: str) -> ChatResponse:
        """Handle medical emergency responses with immediate action guidance"""
        logger.warning(f"🚨 PROCESSING EMERGENCY: {query}")
        
        # Emergency response messages in multiple languages
        emergency_responses = {
            'en': [
                "🚨 MEDICAL EMERGENCY DETECTED! Please call 911 or your local emergency services immediately.",
                "This is a life-threatening situation that requires immediate medical attention. Do not wait - call emergency services now!",
                "If you are having a heart attack, stroke, or any medical emergency, call 911 immediately.",
                "Do not use this chatbot for medical emergencies. Call emergency services right now!",
                "Your safety is the top priority. Please hang up and call 911 immediately."
            ],
            'tl': [
                "🚨 MEDICAL EMERGENCY DETECTED! Tawagan ang 911 o ang inyong lokal na emergency services kaagad.",
                "Ito ay isang life-threatening na sitwasyon na nangangailangan ng agarang medical attention. Huwag maghintay - tawagan ang emergency services ngayon!",
                "Kung kayo ay may heart attack, stroke, o anumang medical emergency, tawagan ang 911 kaagad.",
                "Huwag gamitin ang chatbot na ito para sa medical emergencies. Tawagan ang emergency services ngayon!",
                "Ang inyong kaligtasan ang pinakamahalaga. Pakitawagan ang 911 kaagad."
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
            detected_language=response_lang,
            language_confidence=1.0,
            entities=[],
            intent="emergency",
            is_split=len(response_text) > 1,
            message_count=len(response_text)
        )
