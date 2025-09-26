"""
Context-Aware Translation System
Maintains conversation context across languages
"""
import logging
from typing import Dict, List, Optional, Tuple
import time

logger = logging.getLogger(__name__)

class ContextTranslator:
    """Context-aware translation system that maintains conversation flow"""
    
    def __init__(self):
        self.conversation_context = {}
        self.translation_cache = {}
        self.cache_ttl = 1800  # 30 minutes
        self.last_cleanup = time.time()
    
    def translate_with_context(self, text: str, target_lang: str, 
                             conversation_history: List[Dict] = None,
                             session_id: str = None) -> Tuple[str, float]:
        """Translate text while maintaining conversation context"""
        
        try:
            # Clean cache periodically
            if time.time() - self.last_cleanup > 3600:  # 1 hour
                self._clean_cache()
                self.last_cleanup = time.time()
            
            # Get conversation context
            context = self._get_conversation_context(conversation_history, session_id)
            
            # Check cache first
            cache_key = f"{text}_{target_lang}_{context.get('context_hash', '')}"
            if cache_key in self.translation_cache:
                cached_result, timestamp = self.translation_cache[cache_key]
                if time.time() - timestamp < self.cache_ttl:
                    return cached_result
            
            # Perform context-aware translation
            translated_text, confidence = self._translate_with_nlp_context(
                text, target_lang, context
            )
            
            # Cache the result
            self.translation_cache[cache_key] = ((translated_text, confidence), time.time())
            
            # Update conversation context
            if session_id:
                self._update_conversation_context(session_id, text, translated_text, target_lang)
            
            logger.info(f"🌐 Translated: '{text[:30]}...' -> '{translated_text[:30]}...' (confidence: {confidence:.2f})")
            return translated_text, confidence
            
        except Exception as e:
            logger.error(f"Context translation failed: {e}")
            return text, 0.5
    
    def _get_conversation_context(self, conversation_history: List[Dict] = None, 
                                session_id: str = None) -> Dict:
        """Extract conversation context for better translation"""
        
        context = {
            'recent_messages': [],
            'language_patterns': {},
            'topic_context': '',
            'context_hash': ''
        }
        
        if conversation_history:
            # Analyze recent messages for context
            recent_messages = conversation_history[-5:]  # Last 5 messages
            context['recent_messages'] = recent_messages
            
            # Analyze language patterns
            context['language_patterns'] = self._analyze_language_patterns(recent_messages)
            
            # Extract topic context
            context['topic_context'] = self._extract_topic_context(recent_messages)
        
        if session_id and session_id in self.conversation_context:
            # Merge with existing session context
            session_context = self.conversation_context[session_id]
            context.update(session_context)
        
        # Create context hash for caching
        context['context_hash'] = self._create_context_hash(context)
        
        return context
    
    def _analyze_language_patterns(self, messages: List[Dict]) -> Dict:
        """Analyze language patterns in conversation"""
        
        patterns = {
            'primary_language': 'en',
            'language_mix': False,
            'common_phrases': [],
            'formality_level': 'neutral'
        }
        
        if not messages:
            return patterns
        
        # Analyze language distribution
        languages = []
        for msg in messages:
            if msg.get('role') == 'user':
                # Simple language detection
                content = msg.get('content', '').lower()
                if any(word in content for word in ['ang', 'ng', 'sa', 'na', 'ay']):
                    languages.append('tl')
                elif any(word in content for word in ['ngaean', 'sang', 'imo', 'unga']):
                    languages.append('akl')
                else:
                    languages.append('en')
        
        if languages:
            # Determine primary language
            from collections import Counter
            lang_counts = Counter(languages)
            patterns['primary_language'] = lang_counts.most_common(1)[0][0]
            patterns['language_mix'] = len(set(languages)) > 1
        
        # Analyze formality
        formal_indicators = ['po', 'opo', 'sir', 'maam', 'please', 'thank you']
        informal_indicators = ['hey', 'hi', 'yo', 'kumusta', 'kamusta']
        
        all_content = ' '.join([msg.get('content', '') for msg in messages])
        if any(indicator in all_content.lower() for indicator in formal_indicators):
            patterns['formality_level'] = 'formal'
        elif any(indicator in all_content.lower() for indicator in informal_indicators):
            patterns['formality_level'] = 'informal'
        
        return patterns
    
    def _extract_topic_context(self, messages: List[Dict]) -> str:
        """Extract topic context from conversation"""
        
        if not messages:
            return ''
        
        # Extract key topics from recent messages
        topics = []
        for msg in messages:
            content = msg.get('content', '').lower()
            
            # School-related topics
            if any(word in content for word in ['enrollment', 'enroll', 'admission']):
                topics.append('enrollment')
            elif any(word in content for word in ['schedule', 'time', 'class']):
                topics.append('schedule')
            elif any(word in content for word in ['contact', 'phone', 'number']):
                topics.append('contact')
            elif any(word in content for word in ['location', 'address', 'where']):
                topics.append('location')
            elif any(word in content for word in ['grade', 'subject', 'course']):
                topics.append('academic')
        
        return ', '.join(set(topics)) if topics else ''
    
    def _translate_with_nlp_context(self, text: str, target_lang: str, 
                                   context: Dict) -> Tuple[str, float]:
        """Enhanced context-aware translation with better language detection integration"""
        
        try:
            # Use context to improve translation
            context_prompt = self._build_context_prompt(text, target_lang, context)
            
            # Enhanced translation methods with better confidence scoring
            translation_methods = [
                (self._translate_with_ai_context, 0.9),  # AI-powered with highest priority
                (self._translate_with_deep_translator, 0.8),
                (self._translate_with_context_rules, 0.7),
                (self._translate_with_fallback, 0.5)
            ]
            
            best_translation = None
            best_confidence = 0.0
            
            for method, base_confidence in translation_methods:
                try:
                    translated_text, confidence = method(text, target_lang, context_prompt)
                    
                    # Apply context-based confidence boost
                    enhanced_confidence = self._enhance_confidence_with_context(
                        confidence, context, target_lang
                    )
                    
                    if enhanced_confidence > best_confidence:
                        best_translation = translated_text
                        best_confidence = enhanced_confidence
                        
                    # Accept if confidence is very good
                    if enhanced_confidence > 0.8:
                        logger.info(f"🌐 High confidence translation: {enhanced_confidence:.2f}")
                        return translated_text, enhanced_confidence
                        
                except Exception as e:
                    logger.warning(f"Translation method failed: {e}")
                    continue
            
            # Return best translation found
            if best_translation and best_confidence > 0.4:
                return best_translation, best_confidence
            
            # Fallback to simple translation
            return self._translate_with_fallback(text, target_lang, context_prompt)
            
        except Exception as e:
            logger.error(f"Enhanced NLP translation failed: {e}")
            return text, 0.3
    
    def _translate_with_ai_context(self, text: str, target_lang: str, 
                                 context_prompt: str) -> Tuple[str, float]:
        """AI-powered context-aware translation"""
        try:
            # This would integrate with the AI providers for better translation
            # For now, use enhanced deep translator with context
            from deep_translator import GoogleTranslator
            
            # Map language codes
            lang_map = {'en': 'en', 'tl': 'tl', 'akl': 'tl'}
            target_lang_code = lang_map.get(target_lang, 'en')
            
            # Use context to improve translation
            enhanced_text = self._enhance_text_with_context(text, context_prompt)
            
            if target_lang_code == 'en':
                translator = GoogleTranslator(source='auto', target='en')
            else:
                translator = GoogleTranslator(source='auto', target=target_lang_code)
            
            translated = translator.translate(enhanced_text)
            
            # Calculate confidence based on context match
            confidence = self._calculate_ai_translation_confidence(
                text, translated, target_lang, context_prompt
            )
            
            return translated, confidence
            
        except Exception as e:
            logger.warning(f"AI context translation failed: {e}")
            raise e
    
    def _enhance_text_with_context(self, text: str, context_prompt: str) -> str:
        """Enhance text with context information"""
        try:
            # Extract context elements
            context_elements = context_prompt.split(' | ')
            
            # Add context to text for better translation
            enhanced_text = text
            
            # Add topic context if available
            for element in context_elements:
                if element.startswith('Topic:'):
                    topic = element.replace('Topic:', '').strip()
                    enhanced_text = f"{text} (context: {topic})"
                    break
            
            return enhanced_text
            
        except Exception as e:
            logger.error(f"Text enhancement failed: {e}")
            return text
    
    def _calculate_ai_translation_confidence(self, original: str, translated: str, 
                                           target_lang: str, context_prompt: str) -> float:
        """Calculate confidence for AI-powered translation"""
        try:
            base_confidence = 0.8
            
            # Boost confidence for school-specific terms
            school_terms = ['enrollment', 'schedule', 'contact', 'office', 'teacher', 'student']
            if any(term in original.lower() for term in school_terms):
                base_confidence += 0.1
            
            # Boost confidence for context match
            if 'context:' in context_prompt:
                base_confidence += 0.05
            
            # Boost confidence for language-specific patterns
            if target_lang == 'tl' and any(word in translated.lower() for word in ['ang', 'ng', 'sa', 'na']):
                base_confidence += 0.05
            elif target_lang == 'akl' and any(word in translated.lower() for word in ['ngaean', 'sang', 'imo']):
                base_confidence += 0.05
            
            return min(base_confidence, 0.95)
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.8
    
    def _enhance_confidence_with_context(self, base_confidence: float, context: Dict, 
                                       target_lang: str) -> float:
        """Enhance confidence based on context analysis"""
        try:
            enhanced_confidence = base_confidence
            
            # Boost confidence for language pattern match
            if context.get('language_patterns', {}).get('primary_language') == target_lang:
                enhanced_confidence += 0.1
            
            # Boost confidence for topic context match
            if context.get('topic_context'):
                enhanced_confidence += 0.05
            
            # Boost confidence for recent message context
            if context.get('recent_messages'):
                enhanced_confidence += 0.05
            
            # Boost confidence for formality level match
            formality = context.get('language_patterns', {}).get('formality_level', 'neutral')
            if formality != 'neutral':
                enhanced_confidence += 0.05
            
            return min(enhanced_confidence, 0.95)
            
        except Exception as e:
            logger.error(f"Confidence enhancement failed: {e}")
            return base_confidence
    
    def _build_context_prompt(self, text: str, target_lang: str, context: Dict) -> str:
        """Build context-aware translation prompt"""
        
        prompt_parts = [f"Translate to {target_lang}:"]
        
        # Add conversation context
        if context.get('topic_context'):
            prompt_parts.append(f"Topic: {context['topic_context']}")
        
        # Add language patterns
        if context.get('language_patterns', {}).get('formality_level') != 'neutral':
            formality = context['language_patterns']['formality_level']
            prompt_parts.append(f"Formality: {formality}")
        
        # Add recent context
        if context.get('recent_messages'):
            recent_context = self._summarize_recent_context(context['recent_messages'])
            if recent_context:
                prompt_parts.append(f"Context: {recent_context}")
        
        prompt_parts.append(f"Text: {text}")
        
        return " | ".join(prompt_parts)
    
    def _summarize_recent_context(self, messages: List[Dict]) -> str:
        """Summarize recent conversation context"""
        
        if not messages:
            return ''
        
        # Extract key information from recent messages
        context_elements = []
        
        for msg in messages[-3:]:  # Last 3 messages
            content = msg.get('content', '')
            if len(content) > 50:
                content = content[:50] + "..."
            context_elements.append(content)
        
        return " | ".join(context_elements)
    
    def _translate_with_deep_translator(self, text: str, target_lang: str, 
                                       context_prompt: str) -> Tuple[str, float]:
        """Translate using deep_translator with context"""
        
        try:
            from deep_translator import GoogleTranslator
            
            # Map language codes
            lang_map = {'en': 'en', 'tl': 'tl', 'akl': 'tl'}  # Aklanon maps to Tagalog
            target_lang_code = lang_map.get(target_lang, 'en')
            
            if target_lang_code == 'en':
                translator = GoogleTranslator(source='auto', target='en')
            else:
                translator = GoogleTranslator(source='auto', target=target_lang_code)
            
            translated = translator.translate(text)
            confidence = 0.8  # Deep translator is generally reliable
            
            return translated, confidence
            
        except Exception as e:
            logger.warning(f"Deep translator failed: {e}")
            raise e
    
    def _translate_with_context_rules(self, text: str, target_lang: str, 
                                    context_prompt: str) -> Tuple[str, float]:
        """Translate using context-aware rules"""
        
        # School-specific translation rules
        school_terms = {
            'enrollment': {'en': 'enrollment', 'tl': 'pagpapatala', 'akl': 'pagpapatala'},
            'schedule': {'en': 'schedule', 'tl': 'iskedyul', 'akl': 'iskedyul'},
            'contact': {'en': 'contact', 'tl': 'kontak', 'akl': 'kontak'},
            'location': {'en': 'location', 'tl': 'lokasyon', 'akl': 'lokasyon'},
            'office': {'en': 'office', 'tl': 'opisina', 'akl': 'opisina'},
            'teacher': {'en': 'teacher', 'tl': 'guro', 'akl': 'guro'},
            'student': {'en': 'student', 'tl': 'mag-aaral', 'akl': 'mag-aaral'},
            'school': {'en': 'school', 'tl': 'paaralan', 'akl': 'paaralan'}
        }
        
        # Check for school terms
        text_lower = text.lower()
        for term, translations in school_terms.items():
            if term in text_lower:
                if target_lang in translations:
                    # Replace the term with translated version
                    translated_text = text.replace(term, translations[target_lang])
                    return translated_text, 0.9
        
        # If no school terms found, use basic translation
        return self._translate_with_fallback(text, target_lang, context_prompt)
    
    def _translate_with_fallback(self, text: str, target_lang: str, 
                               context_prompt: str) -> Tuple[str, float]:
        """Fallback translation method"""
        
        # Simple word-by-word translation for common phrases
        common_phrases = {
            'hello': {'en': 'hello', 'tl': 'kumusta', 'akl': 'kumusta'},
            'hi': {'en': 'hi', 'tl': 'kumusta', 'akl': 'kumusta'},
            'thank you': {'en': 'thank you', 'tl': 'salamat', 'akl': 'salamat'},
            'please': {'en': 'please', 'tl': 'pakisuyo', 'akl': 'pakisuyo'},
            'yes': {'en': 'yes', 'tl': 'oo', 'akl': 'huo'},
            'no': {'en': 'no', 'tl': 'hindi', 'akl': 'indi'},
            'good morning': {'en': 'good morning', 'tl': 'magandang umaga', 'akl': 'maayong aga'},
            'good afternoon': {'en': 'good afternoon', 'tl': 'magandang hapon', 'akl': 'maayong hapon'},
            'good evening': {'en': 'good evening', 'tl': 'magandang gabi', 'akl': 'maayong gabi'}
        }
        
        text_lower = text.lower()
        for phrase, translations in common_phrases.items():
            if phrase in text_lower and target_lang in translations:
                translated_text = text.replace(phrase, translations[target_lang])
                return translated_text, 0.7
        
        # If no translation found, return original text
        return text, 0.3
    
    def _update_conversation_context(self, session_id: str, original_text: str, 
                                   translated_text: str, target_lang: str):
        """Update conversation context for future translations"""
        
        if session_id not in self.conversation_context:
            self.conversation_context[session_id] = {
                'translation_history': [],
                'language_preferences': {},
                'context_accumulated': ''
            }
        
        # Update translation history
        self.conversation_context[session_id]['translation_history'].append({
            'original': original_text,
            'translated': translated_text,
            'target_lang': target_lang,
            'timestamp': time.time()
        })
        
        # Keep only recent history (last 10 translations)
        if len(self.conversation_context[session_id]['translation_history']) > 10:
            self.conversation_context[session_id]['translation_history'] = \
                self.conversation_context[session_id]['translation_history'][-10:]
        
        # Update language preferences
        if target_lang not in self.conversation_context[session_id]['language_preferences']:
            self.conversation_context[session_id]['language_preferences'][target_lang] = 0
        self.conversation_context[session_id]['language_preferences'][target_lang] += 1
    
    def _create_context_hash(self, context: Dict) -> str:
        """Create a hash for context caching"""
        import hashlib
        
        context_str = str(context.get('topic_context', '')) + \
                     str(context.get('language_patterns', {})) + \
                     str(len(context.get('recent_messages', [])))
        
        return hashlib.md5(context_str.encode()).hexdigest()[:8]
    
    def _clean_cache(self):
        """Clean expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.translation_cache.items()
            if current_time - timestamp > self.cache_ttl
        ]
        for key in expired_keys:
            del self.translation_cache[key]
    
    def get_conversation_context(self, session_id: str) -> Dict:
        """Get conversation context for a session"""
        return self.conversation_context.get(session_id, {})
    
    def clear_conversation_context(self, session_id: str):
        """Clear conversation context for a session"""
        if session_id in self.conversation_context:
            del self.conversation_context[session_id]
