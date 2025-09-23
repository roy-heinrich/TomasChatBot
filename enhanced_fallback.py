# enhanced_fallback.py
import logging
from typing import Dict, Optional, Tuple, List
import asyncio

logger = logging.getLogger(__name__)

FB_MESSENGER_LINK = "https://m.me/114901716621736"

class EnhancedFallbackHandler:
    """
    Advanced fallback handler with NLP/NLU integration for intelligent failure handling.
    """
    
    def __init__(self, session=None, nlu_engine=None, entity_extractor=None, sentiment_analyzer=None):
        # If no session dict is passed, create one automatically
        self.session = session if session is not None else {}
        
        # NLP/NLU components (inject from main chatbot)
        self.nlu_engine = nlu_engine
        self.entity_extractor = entity_extractor
        self.sentiment_analyzer = sentiment_analyzer
        
        # Failure tracking for progressive escalation
        self.failure_count = self.session.get('failure_count', 0)
        self.last_failed_intent = self.session.get('last_failed_intent', None)

    def get_state(self, key, default=None):
        return self.session.get(key, default)

    def set_state(self, key, value):
        self.session[key] = value
        logger.debug(f"[EnhancedFallbackHandler] State updated: {key}={value}")

    def reset_state(self):
        self.session.clear()
        self.failure_count = 0
        self.last_failed_intent = None
        logger.debug("[EnhancedFallbackHandler] Session state reset")

    async def get_intelligent_fallback(self, query: str, language="en", chatbot_instance=None, sentiment_context=None) -> str:
        """
        Main entry point for intelligent fallback using NLP/NLU analysis.
        Now accepts sentiment_context to integrate with chatbot's sentiment analysis.
        """
        try:
            # Increment failure tracking
            self.failure_count += 1
            self.set_state('failure_count', self.failure_count)
            
            # 1. INTENT CLASSIFICATION - Understand what the user was trying to do
            intent_info = await self._analyze_failed_intent(query, chatbot_instance)
            
            # 2. ENTITY EXTRACTION - Find specific things they mentioned
            entities = await self._extract_entities_from_query(query, chatbot_instance)
            
            # 3. SENTIMENT ANALYSIS - Use provided sentiment context or analyze
            if sentiment_context:
                logger.info("📥 Using provided sentiment context from chatbot")
                sentiment_info = {
                    'sentiment': sentiment_context.get('sentiment'),
                    'emotion': sentiment_context.get('emotion'),
                    'urgency': sentiment_context.get('urgency', 1),
                    'tone_adjustments': sentiment_context.get('tone_adjustments', {}),
                    'confidence': 0.95  # High confidence since it's from main analysis
                }
            else:
                sentiment_info = await self._analyze_user_sentiment(query, chatbot_instance)
            
            # 4. GENERATE INTELLIGENT RESPONSE
            response = await self._generate_context_aware_fallback(
                query=query,
                intent_info=intent_info,
                entities=entities,
                sentiment_info=sentiment_info,
                language=language
            )
            
            logger.info(f"🧠 Generated intelligent fallback for intent: {intent_info.get('intent', 'unknown')} "
                       f"(confidence: {intent_info.get('confidence', 0):.2f})")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in intelligent fallback: {e}")
            # Fallback to simple response if NLP fails
            return self.generate_simple_fallback_message(language)

    async def _analyze_failed_intent(self, query: str, chatbot_instance) -> Dict:
        """Analyze what the user was trying to accomplish."""
        try:
            # PRIORITY 1: Check for non-existence indicators first (override NLU)
            simple_result = self._simple_intent_analysis(query)
            if simple_result['intent'] == 'non_existent_inquiry':
                return simple_result
            
            # PRIORITY 2: Use chatbot's NLU engine for other intents
            if chatbot_instance and hasattr(chatbot_instance, 'nlu_engine'):
                # Use the main chatbot's NLU engine (correct method name)
                nlu_result = await chatbot_instance.nlu_engine.analyze_intent(query)
                intent = str(nlu_result.intent)  # Convert enum to string
                confidence = nlu_result.confidence
                
                # Store for progressive learning
                self.last_failed_intent = intent
                self.set_state('last_failed_intent', intent)
                
                return {
                    'intent': intent,
                    'confidence': confidence,
                    'category': self._categorize_intent(intent)
                }
            else:
                # Fallback to simple keyword analysis
                return simple_result
                
        except Exception as e:
            logger.warning(f"Intent analysis failed: {e}")
            return self._simple_intent_analysis(query)  # Use simple analysis as fallback

    async def _extract_entities_from_query(self, query: str, chatbot_instance) -> List[Dict]:
        """Extract entities from the failed query for contextual responses."""
        try:
            if chatbot_instance and hasattr(chatbot_instance, 'entity_extractor'):
                # Use the main chatbot's entity extractor (synchronous, not async)
                entities = chatbot_instance.entity_extractor.extract_entities(query)
                # Convert ExtractedEntity objects to dicts if needed
                entity_dicts = []
                for entity in entities:
                    if hasattr(entity, '__dict__'):
                        entity_dicts.append({
                            'type': getattr(entity, 'entity_type', 'unknown'),
                            'value': getattr(entity, 'value', ''),
                            'confidence': getattr(entity, 'confidence', 0.5)
                        })
                    elif isinstance(entity, dict):
                        entity_dicts.append(entity)
                return entity_dicts if entity_dicts else []
            else:
                # Fallback to simple name detection
                return self._simple_entity_detection(query)
                
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
            return self._simple_entity_detection(query)  # Use simple detection as fallback

    async def _analyze_user_sentiment(self, query: str, chatbot_instance) -> Dict:
        """Analyze user sentiment to adapt response tone."""
        try:
            if chatbot_instance and hasattr(chatbot_instance, 'sentiment_analyzer'):
                # Use the main chatbot's sentiment analyzer
                sentiment_result = await chatbot_instance.sentiment_analyzer.analyze_sentiment(query)
                return sentiment_result
            else:
                # Simple frustration detection
                return self._simple_sentiment_detection(query)
                
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return {'sentiment': 'neutral', 'confidence': 0.5}

    def _categorize_intent(self, intent: str) -> str:
        """Categorize intents for targeted fallback responses."""
        # Convert intent to lowercase string for matching
        intent_str = str(intent).lower()
        
        intent_categories = {
            'staff_inquiry': 'staff',
            'intent.staff_inquiry': 'staff',
            'location_inquiry': 'location',
            'intent.location_inquiry': 'location', 
            'enrollment_inquiry': 'enrollment',
            'intent.enrollment_inquiry': 'enrollment',
            'academic_inquiry': 'academic',
            'intent.academic_inquiry': 'academic',
            'contact_inquiry': 'contact',
            'intent.contact_inquiry': 'contact',
            'greeting_formal': 'greeting',
            'intent.greeting_formal': 'greeting',
            'greeting_casual': 'greeting',
            'intent.greeting_casual': 'greeting',
            'off_topic_inquiry': 'off_topic',
            'non_existent_inquiry': 'non_existent',
            'unknown': 'general'
        }
        return intent_categories.get(intent_str, 'general')

    def _simple_intent_analysis(self, query: str) -> Dict:
        """Simple keyword-based intent detection as fallback."""
        query_lower = query.lower()
        
        # Off-topic queries (highest priority)
        off_topic_keywords = [
            # Weather
            'weather', 'rain', 'sunny', 'cloudy', 'temperature', 'forecast', 'umulan', 'init', 'lamig',
            # Sports
            'basketball', 'football', 'soccer', 'sports', 'game', 'team', 'player', 'championship',
            # Politics
            'president', 'election', 'vote', 'government', 'politics', 'mayor', 'governor',
            # Entertainment
            'movie', 'music', 'song', 'actor', 'actress', 'celebrity', 'tv show', 'netflix',
            # Technology
            'computer', 'phone', 'internet', 'wifi', 'software', 'app', 'website',
            # General knowledge
            'history', 'science', 'math', 'recipe', 'cooking', 'travel', 'vacation'
        ]
        if any(keyword in query_lower for keyword in off_topic_keywords):
            return {'intent': 'off_topic_inquiry', 'confidence': 0.9, 'category': 'off_topic'}
        
        # Check for non-existence indicators first (higher priority) - be more specific
        non_existence_words = ['doesn\'t exist', 'does not exist', 'don\'t exist', 'not exist', 'doesn\'t work', 'not real', 'fake', 'fictional', 'imaginary', 'made up', 'wala ba', 'way ba']
        if any(word in query_lower for word in non_existence_words):
            return {'intent': 'non_existent_inquiry', 'confidence': 0.8, 'category': 'general'}
        
        if any(word in query_lower for word in ['teacher', 'principal', 'staff', 'head teacher', 'meliza']):
            return {'intent': 'staff_inquiry', 'confidence': 0.7, 'category': 'staff'}
        elif any(word in query_lower for word in ['location', 'address', 'where', 'saan']):
            return {'intent': 'location_inquiry', 'confidence': 0.7, 'category': 'location'}
        elif any(word in query_lower for word in ['enroll', 'admission', 'register']):
            return {'intent': 'enrollment_inquiry', 'confidence': 0.7, 'category': 'enrollment'}
        else:
            return {'intent': 'unknown', 'confidence': 0.3, 'category': 'general'}

    def _simple_entity_detection(self, query: str) -> List[Dict]:
        """Simple entity detection for fallback."""
        entities = []
        query_lower = query.lower()
        
        # Detect non-existent entities mentioned
        import re
        
        # Extract names that are described as non-existent
        non_exist_patterns = [
            r'(mr\.|mrs\.|ms\.)?\s*([a-z]+\s+[a-z]+)\s+(?:teacher|staff|principal)?\s*(?:who|that)?\s*(?:doesn\'t|does not|don\'t)\s+exist',
            r'([a-z]+\s+[a-z]+)\s+(?:who|that)?\s*(?:doesn\'t|does not|don\'t)\s+exist'
        ]
        
        for pattern in non_exist_patterns:
            matches = re.findall(pattern, query_lower, re.IGNORECASE)
            for match in matches:
                # Handle both single name and (title, name) tuple formats
                if isinstance(match, tuple):
                    name = ' '.join([part for part in match if part]).strip()
                else:
                    name = match.strip()
                
                if name:
                    entities.append({
                        'type': 'non_existent_person', 
                        'value': name.title(), 
                        'confidence': 0.9
                    })
        
        # Known staff names
        if 'meliza' in query_lower:
            entities.append({'type': 'person', 'value': 'Meliza A. Delgado', 'confidence': 0.9})
        
        # Grade levels
        grade_match = re.search(r'grade\s*(\d+)', query_lower)
        if grade_match:
            entities.append({'type': 'grade_level', 'value': f'Grade {grade_match.group(1)}', 'confidence': 0.8})
        
        return entities

    def _simple_sentiment_detection(self, query: str) -> Dict:
        """Simple frustration/emotion detection."""
        query_lower = query.lower()
        
        # Frustration indicators
        frustration_words = ['help', 'please', 'urgent', 'asap', 'frustrated', 'confused', 'cant', 'wont', 'doesnt work']
        if any(word in query_lower for word in frustration_words):
            return {'sentiment': 'frustrated', 'confidence': 0.7, 'emotion': 'frustrated'}
        
        # Politeness indicators
        polite_words = ['thank you', 'please', 'could you', 'would you']
        if any(word in query_lower for word in polite_words):
            return {'sentiment': 'positive', 'confidence': 0.6, 'emotion': 'polite'}
        
        return {'sentiment': 'neutral', 'confidence': 0.5, 'emotion': 'neutral'}

    async def _generate_context_aware_fallback(self, query: str, intent_info: Dict, entities: List[Dict], 
                                             sentiment_info: Dict, language: str) -> str:
        """Generate intelligent fallback based on NLP analysis."""
        
        intent = intent_info.get('intent', 'unknown')
        category = intent_info.get('category', 'general')
        confidence = intent_info.get('confidence', 0.0)
        sentiment = sentiment_info.get('sentiment', 'neutral')
        
        # 1. HIGH CONFIDENCE INTENT - Provide specific guidance
        if confidence > 0.6:
            return self._get_intent_specific_fallback(intent, entities, language, sentiment)
        
        # 2. LOW CONFIDENCE - Suggest query reformulation
        elif confidence > 0.3:
            return self._get_reformulation_suggestion(intent, language, sentiment)
        
        # 3. VERY LOW CONFIDENCE - General helpful response
        else:
            return self._get_general_intelligent_fallback(entities, language, sentiment)

    def _get_intent_specific_fallback(self, intent: str, entities: List[Dict], language: str, sentiment: str) -> str:
        """Provide specific guidance based on detected intent."""
        
        # Adapt tone based on sentiment
        tone_prefix = self._get_tone_prefix(sentiment, language)
        
        if intent == 'staff_inquiry':
            staff_entities = [e for e in entities if e.get('type') in ['person', 'staff_role']]
            if staff_entities:
                entity_value = staff_entities[0].get('value', '')
                if language.startswith('akl'):
                    return f"{tone_prefix}Para sa impormasyon sang mga staff kag si {entity_value}, bisitahi it admin office."
                elif language.startswith('tl'):
                    return f"{tone_prefix}Para sa impormasyon ng mga staff at si {entity_value}, bumisita sa admin office."
                else:
                    return f"{tone_prefix}For staff information about {entity_value}, please visit the admin office."
            else:
                if language.startswith('akl'):
                    return f"{tone_prefix}Para sa impormasyon sang mga magtutudlo, bisitahi it admin office."
                elif language.startswith('tl'):
                    return f"{tone_prefix}Para sa impormasyon ng mga guro, bumisita sa admin office."
                else:
                    return f"{tone_prefix}For staff information, please visit the admin office."
        
        elif intent == 'location_inquiry':
            if language.startswith('akl'):
                return f"{tone_prefix}Para sa detalye sang lokasyon, makadto sa admin office."
            elif language.startswith('tl'):
                return f"{tone_prefix}Para sa detalye ng lokasyon, pumunta sa admin office."
            else:
                return f"{tone_prefix}For location details, please visit the admin office."
        
        elif intent == 'enrollment_inquiry':
            if language.startswith('akl'):
                return f"{tone_prefix}Para sa enrollment kag admission, makadto sa admin office o tawagan ang (123) 456-7890."
            elif language.startswith('tl'):
                return f"{tone_prefix}Para sa enrollment at admission, pumunta sa admin office o tumawag sa (123) 456-7890."
            else:
                return f"{tone_prefix}For enrollment and admission information, please visit the admin office or call (123) 456-7890."
        
        elif intent == 'off_topic_inquiry':
            # Handle completely off-topic queries
            if language.startswith('akl'):
                return (
                    f"{tone_prefix}Pasensya, pero ako isa ka school assistant para sa Tomas SM. Bautista Elementary School. "
                    "Indi ko matubag ang mga pamangkot nga wala sa school. "
                    "Kon may pamangkot kamo parte sa school, enrollment, teachers, ukon school activities, "
                    "pwede ko kamo matabangan. Ano ang gusto nyo mahibaluan parte sa amon school?"
                )
            elif language.startswith('tl'):
                return (
                    f"{tone_prefix}Pasensya na po, pero ako ay school assistant para sa Tomas SM. Bautista Elementary School. "
                    "Hindi ko masasagot ang mga tanong na hindi tungkol sa school. "
                    "Kung may tanong kayo tungkol sa school, enrollment, mga guro, o school activities, "
                    "makakatulong ako sa inyo. Ano ang gusto ninyong malaman tungkol sa aming school?"
                )
            else:
                return (
                    f"{tone_prefix}I'm sorry, but I'm a school assistant for Tomas SM. Bautista Elementary School. "
                    "I can't answer questions that aren't related to our school. "
                    "If you have questions about our school, enrollment, teachers, or school activities, "
                    "I'd be happy to help you. What would you like to know about our school?"
                )
        
        elif intent == 'non_existent_inquiry':
            # Handle queries about non-existent things
            extracted_entities = [e.get('value', '') for e in entities if e.get('value')]
            entity_mention = f" about {extracted_entities[0]}" if extracted_entities else ""
            
            if language.startswith('akl'):
                return f"{tone_prefix}Wala gid ini sa amon mga record{entity_mention}. Para sa tama nga impormasyon, bisitahi it admin office."
            elif language.startswith('tl'):
                return f"{tone_prefix}Wala po ito sa aming mga record{entity_mention}. Para sa tamang impormasyon, bumisita sa admin office."
            else:
                return f"{tone_prefix}I understand you're asking{entity_mention}, but this doesn't exist in our school records. For information about our actual staff and services, please visit the admin office."
        
        else:
            # Default case
            return self._get_general_intelligent_fallback(entities, language, sentiment)

    def _get_reformulation_suggestion(self, intent: str, language: str, sentiment: str) -> str:
        """Suggest how to rephrase the query."""
        tone_prefix = self._get_tone_prefix(sentiment, language)
        
        suggestions = {
            'staff_inquiry': {
                'en': f"{tone_prefix}I might be able to help if you ask about specific staff members like 'Who is the head teacher?' or 'Tell me about Grade 1 teachers.'",
                'tl': f"{tone_prefix}Makakatulong ako kung magtanong kayo tungkol sa mga specific na staff tulad ng 'Sino ang head teacher?' o 'Sabihin mo sa akin ang tungkol sa Grade 1 teachers.'",
                'akl': f"{tone_prefix}Mabuligan ta kamo kon magpamangkot kamo parte sa mga specific nga staff bilang 'Sin-o ang head teacher?' o 'Hambalon mo sa akon ang parte sa Grade 1 teachers.'"
            },
            'location_inquiry': {
                'en': f"{tone_prefix}Try asking 'Where is the school located?' or 'What is the school address?'",
                'tl': f"{tone_prefix}Subukan ninyong itanong 'Saan nakatayo ang paaralan?' o 'Ano ang address ng paaralan?'",
                'akl': f"{tone_prefix}Subukan nyo nga ihambal 'Diin nakatindog ang eskwelahan?' o 'Ano ang address sang eskwelahan?'"
            }
        }
        
        lang_key = 'akl' if language.startswith('akl') else 'tl' if language.startswith('tl') else 'en'
        return suggestions.get(intent, {}).get(lang_key, self._get_general_intelligent_fallback([], language, sentiment))

    def _get_general_intelligent_fallback(self, entities: List[Dict], language: str, sentiment: str) -> str:
        """Generate a general but intelligent fallback response."""
        tone_prefix = self._get_tone_prefix(sentiment, language)
        
        messenger_button = self._get_messenger_button()
        
        # If we found entities, acknowledge them
        entity_acknowledgment = ""
        if entities:
            entity_names = [e.get('value', '') for e in entities if e.get('value')]
            if entity_names and language.startswith('en'):
                entity_acknowledgment = f"I understand you're asking about {', '.join(entity_names[:2])}. "
        
        if language.startswith('akl'):
            return (
                f"{tone_prefix}{entity_acknowledgment}"
                "Indi ko matubag ini nga pamangkot, pero ang admin office makabulig sa inyo. "
                f"Kon gusto nyo makipag-istorya sa tawo, pwede nyo sila kontakon gamit ang {messenger_button}"
            )
        elif language.startswith('tl'):
            return (
                f"{tone_prefix}{entity_acknowledgment}"
                "Hindi ko masagot ang tanong na ito, pero makakatulong sa inyo ang admin office. "
                f"Kung gusto ninyong makipag-usap sa tao, maaari ninyong kontakin sila gamit ang {messenger_button}"
            )
        else:
            return (
                f"{tone_prefix}{entity_acknowledgment}"
                "I can't answer this specific question, but the admin office can help you. "
                f"If you'd like to speak with a person, you can contact them at {messenger_button}"
            )

    def _get_tone_prefix(self, sentiment, language: str) -> str:
        """Get appropriate tone prefix based on sentiment."""
        # Handle both string and enum sentiment values
        sentiment_value = str(sentiment).lower() if sentiment else 'neutral'
        
        if sentiment_value in ['frustrated', 'negative']:
            if language.startswith('akl'):
                return "Nakatalawag gid ako kon indi ko natabangan kamo. "
            elif language.startswith('tl'):
                return "Nakakalungkot na hindi ko kayo natulungan. "
            else:
                return "I understand this can be frustrating. "
        elif sentiment_value in ['positive', 'happy']:
            if language.startswith('akl'):
                return "Salamat sa inyong pasensya. "
            elif language.startswith('tl'):
                return "Salamat sa inyong pasensya. "
            else:
                return "Thank you for your patience. "
        elif sentiment_value == 'urgent':
            if language.startswith('akl'):
                return "Nakita ko nga importante ini para sa inyo. "
            elif language.startswith('tl'):
                return "Nakita ko na importante ito para sa inyo. "
            else:
                return "I understand this is urgent for you. "
        else:
            return ""  # Neutral tone

    def _get_messenger_button(self) -> str:
        """Generate messenger contact button."""
        return (
            f'<a href="{FB_MESSENGER_LINK}" target="_blank" '
            'style="background-color:#0084FF; color:white; padding:10px 18px; '
            'border-radius:20px; font-weight:bold; text-decoration:none; '
            'font-family:sans-serif; display:inline-block;">'
            '💬 Contact Us'
            '</a>'
        )

    def generate_simple_fallback_message(self, language="en"):
        """
        Simple fallback when NLP processing fails.
        """
        messenger_button = self._get_messenger_button()

        if language.startswith("akl"):
            return (
                "Paumanhin kon indi ko masabat inyo nga pamangkot. "
                "Maabot nyo it admin office para sa dugang nga bulig. "
                f"Kon gusto nyo magstorya sa tawo, pwede nyo sila kontakon sa {messenger_button}"
            )
        elif language.startswith("tl"):
            return (
                "Paumanhin po kung hindi ko masagot ang inyong katanungan. "
                "Maaari po kayong lumapit sa admin office para sa karagdagang tulong. "
                f"Kung nais niyo pong makipag-ugnayan sa isang tao, maari niyo po silang makontak gamit ang {messenger_button}"
            )
        else:
            return (
                "I'm sorry I couldn't answer your questions. "
                "You may visit the admin office for further assistance. "
                f"If you'd like to talk to a person, you can contact them at {messenger_button}"
            )

    # Legacy methods for backward compatibility
    def generate_fallback_message(self, language="en"):
        return self.generate_simple_fallback_message(language)

    def get_context_sensitive_fallback(self, query: str, language="en"):
        # Simple sync version for backward compatibility
        return asyncio.run(self.get_intelligent_fallback(query, language))