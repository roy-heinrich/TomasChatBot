"""
Response Personalization Module
Advanced response customization based on user profile, context, and behavior
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import re

logger = logging.getLogger(__name__)

@dataclass
class PersonalizedResponse:
    """Personalized response configuration"""
    tone: str
    formality_level: str
    language_preference: str
    detail_level: str
    response_style: str
    personalization_elements: List[str]
    cultural_adaptations: List[str]

class ResponsePersonalizer:
    """
    Advanced response personalization based on user analysis
    """
    
    def __init__(self):
        self.tone_templates = self._build_tone_templates()
        self.formality_levels = self._build_formality_levels()
        self.cultural_adaptations = self._build_cultural_adaptations()
        self.personalization_patterns = self._build_personalization_patterns()
        
    async def personalize_response(self, 
                                 base_response: str,
                                 user_profile: Dict,
                                 conversation_context: Dict,
                                 emotional_analysis: Dict,
                                 language: str = "en") -> PersonalizedResponse:
        """
        Personalize response based on comprehensive user analysis
        """
        
        # 1. Determine appropriate tone
        tone = await self._determine_tone(user_profile, emotional_analysis, conversation_context)
        
        # 2. Assess formality level
        formality_level = await self._assess_formality_level(user_profile, conversation_context)
        
        # 3. Language preference
        language_preference = await self._determine_language_preference(user_profile, language)
        
        # 4. Detail level
        detail_level = await self._assess_detail_level(user_profile, conversation_context)
        
        # 5. Response style
        response_style = await self._determine_response_style(user_profile, conversation_context)
        
        # 6. Personalization elements
        personalization_elements = await self._identify_personalization_elements(user_profile, conversation_context)
        
        # 7. Cultural adaptations
        cultural_adaptations = await self._identify_cultural_adaptations(user_profile, language)
        
        return PersonalizedResponse(
            tone=tone,
            formality_level=formality_level,
            language_preference=language_preference,
            detail_level=detail_level,
            response_style=response_style,
            personalization_elements=personalization_elements,
            cultural_adaptations=cultural_adaptations
        )
    
    async def apply_personalization(self, 
                                  response: str, 
                                  personalization: PersonalizedResponse,
                                  user_name: str = None,
                                  conversation_history: List[Dict] = None) -> str:
        """
        Apply personalization to the response text
        """
        
        personalized_response = response
        
        # 1. Apply tone adjustments
        personalized_response = await self._apply_tone_adjustments(
            personalized_response, personalization.tone, personalization.formality_level
        )
        
        # 2. Apply personalization elements
        if personalization.personalization_elements:
            personalized_response = await self._apply_personalization_elements(
                personalized_response, personalization.personalization_elements, user_name
            )
        
        # 3. Apply cultural adaptations
        if personalization.cultural_adaptations:
            personalized_response = await self._apply_cultural_adaptations(
                personalized_response, personalization.cultural_adaptations
            )
        
        # 4. Apply detail level adjustments
        personalized_response = await self._apply_detail_level_adjustments(
            personalized_response, personalization.detail_level
        )
        
        # 5. Apply response style
        personalized_response = await self._apply_response_style(
            personalized_response, personalization.response_style
        )
        
        return personalized_response
    
    async def _determine_tone(self, user_profile: Dict, emotional_analysis: Dict, conversation_context: Dict) -> str:
        """Determine appropriate response tone"""
        
        # Base tone from emotional analysis
        if hasattr(emotional_analysis, 'primary_emotion') and emotional_analysis.primary_emotion:
            emotion = emotional_analysis.primary_emotion
            intensity = getattr(emotional_analysis, 'emotion_intensity', 0.5)
            
            if emotion in ['sad', 'worried', 'frustrated'] and intensity > 0.6:
                return 'empathetic_supportive'
            elif emotion in ['angry', 'frustrated'] and intensity > 0.5:
                return 'calm_reassuring'
            elif emotion in ['happy', 'excited'] and intensity > 0.6:
                return 'enthusiastic_cheerful'
            elif emotion == 'confused' and intensity > 0.5:
                return 'patient_explanatory'
        
        # User profile based tone
        if user_profile and user_profile.get('personality_traits', {}).get('formality_level') == 'formal':
            return 'professional_formal'
        elif user_profile and user_profile.get('personality_traits', {}).get('formality_level') == 'casual':
            return 'friendly_casual'
        
        # Conversation context based tone
        if conversation_context.get('urgency_level') == 'high':
            return 'direct_helpful'
        elif conversation_context.get('conversation_stage') == 'initial':
            return 'welcoming_friendly'
        elif conversation_context.get('conversation_stage') == 'closing':
            return 'warm_closing'
        
        return 'professional_friendly'  # Default
    
    async def _assess_formality_level(self, user_profile: Dict, conversation_context: Dict) -> str:
        """Assess appropriate formality level"""
        
        # User preference
        if user_profile.get('personality_traits', {}).get('formality_level'):
            return user_profile['personality_traits']['formality_level']
        
        # Conversation context
        if conversation_context.get('urgency_level') == 'high':
            return 'medium'  # Balanced for urgent situations
        
        # Default based on conversation stage
        stage = conversation_context.get('conversation_stage', 'ongoing')
        if stage in ['initial', 'greeting']:
            return 'medium'
        elif stage == 'closing':
            return 'formal'
        else:
            return 'medium'
    
    async def _determine_language_preference(self, user_profile: Dict, detected_language: str) -> str:
        """Determine user's language preference"""
        
        # User profile preference
        if user_profile.get('preferred_language'):
            return user_profile['preferred_language']
        
        # Conversation history analysis
        if user_profile.get('conversation_history'):
            languages_used = self._analyze_language_usage(user_profile['conversation_history'])
            if languages_used:
                return languages_used[0]  # Most used language
        
        return detected_language
    
    async def _assess_detail_level(self, user_profile: Dict, conversation_context: Dict) -> str:
        """Assess appropriate detail level for response"""
        
        # User expertise level
        expertise = user_profile.get('expertise_level', 'intermediate')
        if expertise == 'beginner':
            return 'detailed_explanatory'
        elif expertise == 'advanced':
            return 'concise_technical'
        
        # Query complexity
        complexity = conversation_context.get('complexity_level', 'medium')
        if complexity == 'high':
            return 'detailed_comprehensive'
        elif complexity == 'low':
            return 'simple_clear'
        
        # User behavior pattern
        behavior = user_profile.get('behavior_pattern', 'standard')
        if 'detailed_communicator' in behavior:
            return 'detailed_comprehensive'
        elif 'concise_communicator' in behavior:
            return 'concise_direct'
        
        return 'balanced'  # Default
    
    async def _determine_response_style(self, user_profile: Dict, conversation_context: Dict) -> str:
        """Determine response style"""
        
        # User communication style
        comm_style = user_profile.get('personality_traits', {}).get('communication_style', 'direct')
        if comm_style == 'detailed':
            return 'comprehensive_structured'
        elif comm_style == 'indirect':
            return 'contextual_gentle'
        
        # Conversation goals
        goals = conversation_context.get('implied_goals', [])
        if 'solve_problem' in goals:
            return 'solution_focused'
        elif 'get_information' in goals:
            return 'informative_educational'
        elif 'make_decision' in goals:
            return 'analytical_helpful'
        
        return 'conversational_helpful'  # Default
    
    async def _identify_personalization_elements(self, user_profile: Dict, conversation_context: Dict) -> List[str]:
        """Identify elements to personalize in response"""
        
        elements = []
        
        # User name personalization
        if user_profile.get('name'):
            elements.append('use_name')
        
        # Previous conversation references
        if conversation_context.get('topic_flow'):
            elements.append('reference_previous_topics')
        
        # User-specific information
        if user_profile.get('child_name'):
            elements.append('reference_child')
        
        # Expertise-based adjustments
        if user_profile.get('expertise_level') == 'beginner':
            elements.append('add_explanations')
        elif user_profile.get('expertise_level') == 'advanced':
            elements.append('technical_details')
        
        # Emotional support
        if conversation_context.get('emotional_state') in ['worried', 'frustrated', 'confused']:
            elements.append('emotional_support')
        
        return elements
    
    async def _identify_cultural_adaptations(self, user_profile: Dict, language: str) -> List[str]:
        """Identify cultural adaptations needed"""
        
        adaptations = []
        
        # Language-specific cultural elements
        if language in ['tl', 'akl']:
            adaptations.append('filipino_courtesy')
            adaptations.append('family_oriented')
        
        if language == 'akl':
            adaptations.append('aklanon_expressions')
        
        # Regional considerations
        if user_profile.get('region') == 'aklan':
            adaptations.append('local_references')
        
        # Cultural communication styles
        if user_profile.get('cultural_background') == 'filipino':
            adaptations.append('respectful_tone')
            adaptations.append('community_focused')
        
        return adaptations
    
    async def _apply_tone_adjustments(self, response: str, tone: str, formality_level: str) -> str:
        """Apply tone adjustments to response"""
        
        # Tone-specific adjustments
        if tone == 'empathetic_supportive':
            response = self._add_empathy_markers(response)
        elif tone == 'calm_reassuring':
            response = self._add_reassurance_markers(response)
        elif tone == 'enthusiastic_cheerful':
            response = self._add_enthusiasm_markers(response)
        elif tone == 'patient_explanatory':
            response = self._add_patience_markers(response)
        
        # Formality adjustments
        if formality_level == 'formal':
            response = self._make_formal(response)
        elif formality_level == 'casual':
            response = self._make_casual(response)
        
        return response
    
    async def _apply_personalization_elements(self, response: str, elements: List[str], user_name: str = None) -> str:
        """Apply personalization elements to response"""
        
        if 'use_name' in elements and user_name:
            response = self._add_name_references(response, user_name)
        
        if 'reference_previous_topics' in elements:
            response = self._add_topic_references(response)
        
        if 'reference_child' in elements:
            response = self._add_child_references(response)
        
        if 'add_explanations' in elements:
            response = self._add_explanations(response)
        
        if 'technical_details' in elements:
            response = self._add_technical_details(response)
        
        if 'emotional_support' in elements:
            response = self._add_emotional_support(response)
        
        return response
    
    async def _apply_cultural_adaptations(self, response: str, adaptations: List[str]) -> str:
        """Apply cultural adaptations to response"""
        
        if 'filipino_courtesy' in adaptations:
            response = self._add_filipino_courtesy(response)
        
        if 'family_oriented' in adaptations:
            response = self._add_family_references(response)
        
        if 'aklanon_expressions' in adaptations:
            response = self._add_aklanon_expressions(response)
        
        if 'local_references' in adaptations:
            response = self._add_local_references(response)
        
        if 'respectful_tone' in adaptations:
            response = self._add_respectful_markers(response)
        
        return response
    
    async def _apply_detail_level_adjustments(self, response: str, detail_level: str) -> str:
        """Apply detail level adjustments"""
        
        if detail_level == 'detailed_explanatory':
            response = self._expand_with_explanations(response)
        elif detail_level == 'concise_technical':
            response = self._condense_to_essentials(response)
        elif detail_level == 'detailed_comprehensive':
            response = self._add_comprehensive_details(response)
        elif detail_level == 'simple_clear':
            response = self._simplify_language(response)
        
        return response
    
    async def _apply_response_style(self, response: str, style: str) -> str:
        """Apply response style"""
        
        if style == 'comprehensive_structured':
            response = self._structure_comprehensively(response)
        elif style == 'contextual_gentle':
            response = self._add_contextual_gentleness(response)
        elif style == 'solution_focused':
            response = self._focus_on_solutions(response)
        elif style == 'informative_educational':
            response = self._add_educational_elements(response)
        elif style == 'analytical_helpful':
            response = self._add_analytical_elements(response)
        
        return response
    
    # Helper methods for applying adjustments
    def _add_empathy_markers(self, response: str) -> str:
        """Add empathy markers to response"""
        empathy_starters = [
            "I understand how you feel...",
            "I can see this is important to you...",
            "I'm here to help you with this...",
            "I completely understand your concern..."
        ]
        return f"{empathy_starters[0]} {response}"
    
    def _add_reassurance_markers(self, response: str) -> str:
        """Add reassurance markers to response"""
        reassurance_starters = [
            "Don't worry, I can help you with this.",
            "I'm confident we can resolve this together.",
            "Let me help you through this step by step.",
            "Everything will be fine, let's work through this."
        ]
        return f"{reassurance_starters[0]} {response}"
    
    def _add_enthusiasm_markers(self, response: str) -> str:
        """Add enthusiasm markers to response"""
        enthusiasm_starters = [
            "That's wonderful!",
            "I'm excited to help you with this!",
            "Great question!",
            "I'm happy to assist you with this!"
        ]
        return f"{enthusiasm_starters[0]} {response}"
    
    def _add_patience_markers(self, response: str) -> str:
        """Add patience markers to response"""
        patience_starters = [
            "Let me explain this clearly...",
            "I'll walk you through this step by step...",
            "Don't worry, I'll make sure you understand...",
            "Let me break this down for you..."
        ]
        return f"{patience_starters[0]} {response}"
    
    def _make_formal(self, response: str) -> str:
        """Make response more formal"""
        # Replace casual expressions with formal ones
        replacements = {
            "I'm": "I am",
            "don't": "do not",
            "can't": "cannot",
            "won't": "will not",
            "you're": "you are"
        }
        
        for casual, formal in replacements.items():
            response = response.replace(casual, formal)
        
        return response
    
    def _make_casual(self, response: str) -> str:
        """Make response more casual"""
        # Replace formal expressions with casual ones
        replacements = {
            "I am": "I'm",
            "do not": "don't",
            "cannot": "can't",
            "will not": "won't",
            "you are": "you're"
        }
        
        for formal, casual in replacements.items():
            response = response.replace(formal, casual)
        
        return response
    
    def _add_name_references(self, response: str, user_name: str) -> str:
        """Add name references to response"""
        if user_name and user_name not in response:
            return f"Hi {user_name}, {response.lower()}"
        return response
    
    def _add_topic_references(self, response: str) -> str:
        """Add references to previous topics"""
        # This would be implemented based on conversation history
        return response
    
    def _add_child_references(self, response: str) -> str:
        """Add references to user's child"""
        # This would be implemented based on user profile
        return response
    
    def _add_explanations(self, response: str) -> str:
        """Add explanatory content"""
        # Add simple explanations for beginners
        return response
    
    def _add_technical_details(self, response: str) -> str:
        """Add technical details for advanced users"""
        # Add technical information for advanced users
        return response
    
    def _add_emotional_support(self, response: str) -> str:
        """Add emotional support elements"""
        support_endings = [
            "I'm here to help you every step of the way.",
            "Please don't hesitate to ask if you need any clarification.",
            "I want to make sure you feel comfortable with this process.",
            "Remember, I'm here to support you through this."
        ]
        return f"{response} {support_endings[0]}"
    
    def _add_filipino_courtesy(self, response: str) -> str:
        """Add Filipino courtesy expressions"""
        # Add "po" and other Filipino courtesy markers
        return response
    
    def _add_family_references(self, response: str) -> str:
        """Add family-oriented references"""
        # Add family context where appropriate
        return response
    
    def _add_aklanon_expressions(self, response: str) -> str:
        """Add Aklanon expressions"""
        # Add local Aklanon expressions
        return response
    
    def _add_local_references(self, response: str) -> str:
        """Add local references"""
        # Add references to local places, customs, etc.
        return response
    
    def _add_respectful_markers(self, response: str) -> str:
        """Add respectful markers"""
        # Add respectful language markers
        return response
    
    def _expand_with_explanations(self, response: str) -> str:
        """Expand response with explanations"""
        # Add detailed explanations
        return response
    
    def _condense_to_essentials(self, response: str) -> str:
        """Condense response to essentials"""
        # Remove unnecessary details
        return response
    
    def _add_comprehensive_details(self, response: str) -> str:
        """Add comprehensive details"""
        # Add thorough information
        return response
    
    def _simplify_language(self, response: str) -> str:
        """Simplify language"""
        # Use simpler vocabulary and sentence structure
        return response
    
    def _structure_comprehensively(self, response: str) -> str:
        """Structure response comprehensively"""
        # Add clear structure and organization
        return response
    
    def _add_contextual_gentleness(self, response: str) -> str:
        """Add contextual gentleness"""
        # Add gentle, contextual language
        return response
    
    def _focus_on_solutions(self, response: str) -> str:
        """Focus response on solutions"""
        # Emphasize solution-oriented language
        return response
    
    def _add_educational_elements(self, response: str) -> str:
        """Add educational elements"""
        # Add learning-focused content
        return response
    
    def _add_analytical_elements(self, response: str) -> str:
        """Add analytical elements"""
        # Add analytical, decision-supporting content
        return response
    
    def _analyze_language_usage(self, conversation_history: List[Dict]) -> List[str]:
        """Analyze language usage in conversation history"""
        # Simple language detection based on common words
        languages = []
        for msg in conversation_history[-5:]:  # Last 5 messages
            content = msg.get('content', '').lower()
            
            if any(word in content for word in ['the', 'and', 'or', 'but', 'in', 'on', 'at']):
                languages.append('english')
            elif any(word in content for word in ['ang', 'ng', 'sa', 'ko', 'mo', 'niya']):
                languages.append('tagalog')
            elif any(word in content for word in ['sang', 'nga', 'gid', 'ro']):
                languages.append('aklanon')
        
        # Return most common language
        if languages:
            from collections import Counter
            return [Counter(languages).most_common(1)[0][0]]
        
        return []
    
    def _build_tone_templates(self) -> Dict:
        """Build tone templates"""
        return {
            'empathetic_supportive': {
                'starters': ["I understand how you feel...", "I can see this is important to you..."],
                'markers': ['support', 'help', 'assist', 'guide']
            },
            'calm_reassuring': {
                'starters': ["Don't worry...", "I'm confident we can resolve this..."],
                'markers': ['confident', 'resolve', 'help', 'support']
            },
            'enthusiastic_cheerful': {
                'starters': ["That's wonderful!", "I'm excited to help you!"],
                'markers': ['excited', 'happy', 'great', 'wonderful']
            },
            'professional_friendly': {
                'starters': ["I'm happy to help you with this.", "Let me assist you with that."],
                'markers': ['help', 'assist', 'support', 'guide']
            }
        }
    
    def _build_formality_levels(self) -> Dict:
        """Build formality level templates"""
        return {
            'formal': {
                'replacements': {
                    "I'm": "I am",
                    "don't": "do not",
                    "can't": "cannot"
                },
                'additions': ['please', 'thank you', 'kindly']
            },
            'casual': {
                'replacements': {
                    "I am": "I'm",
                    "do not": "don't",
                    "cannot": "can't"
                },
                'additions': ['hey', 'cool', 'awesome']
            },
            'medium': {
                'replacements': {},
                'additions': ['please', 'thank you']
            }
        }
    
    def _build_cultural_adaptations(self) -> Dict:
        """Build cultural adaptation templates"""
        return {
            'filipino_courtesy': {
                'markers': ['po', 'opo', 'salamat', 'maraming salamat'],
                'patterns': ['respectful', 'polite', 'courteous']
            },
            'family_oriented': {
                'references': ['family', 'children', 'parents', 'anak'],
                'context': ['family values', 'family support']
            },
            'aklanon_expressions': {
                'markers': ['gid', 'sang', 'nga', 'ro'],
                'greetings': ['maayong adlaw', 'maayong gabii']
            }
        }
    
    def _build_personalization_patterns(self) -> Dict:
        """Build personalization patterns"""
        return {
            'name_usage': {
                'patterns': ['Hi {name},', 'Hello {name},', '{name}, I can help you with that.'],
                'frequency': 'moderate'
            },
            'topic_references': {
                'patterns': ['As we discussed earlier...', 'Building on what you mentioned...'],
                'frequency': 'low'
            },
            'emotional_support': {
                'patterns': ['I understand your concern...', 'I am here to help you...'],
                'frequency': 'context_dependent'
            }
        }
