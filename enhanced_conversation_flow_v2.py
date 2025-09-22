"""
Enhanced Conversation Flow V2 - Advanced Multi-Turn Conversation Handling
=======================================================================

This module provides advanced conversation flow improvements:
- Multi-turn conversation state management
- Response continuity and context awareness
- Conversation thread tracking
- Enhanced response generation for follow-up questions
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from collections import defaultdict
import json

logger = logging.getLogger(__name__)

@dataclass
class ConversationThread:
    """Represents a conversation thread with context"""
    thread_id: str
    topic: str
    current_step: int
    total_steps: int
    conversation_history: List[Dict] = field(default_factory=list)
    context_variables: Dict[str, Any] = field(default_factory=dict)
    last_intent: str = ""
    conversation_stage: str = "initial"  # initial, ongoing, concluding
    user_engagement_level: str = "medium"  # low, medium, high
    
    def add_turn(self, user_message: str, bot_response: str, intent: str):
        """Add a conversation turn to the thread"""
        self.conversation_history.append({
            "role": "user", 
            "content": user_message,
            "timestamp": datetime.now().isoformat(),
            "intent": intent
        })
        self.conversation_history.append({
            "role": "assistant", 
            "content": bot_response,
            "timestamp": datetime.now().isoformat()
        })
        self.last_intent = intent
        self.current_step += 1
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of conversation context"""
        return {
            "topic": self.topic,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "last_intent": self.last_intent,
            "conversation_stage": self.conversation_stage,
            "user_engagement_level": self.user_engagement_level,
            "context_variables": self.context_variables,
            "recent_messages": self.conversation_history[-4:] if len(self.conversation_history) > 4 else self.conversation_history
        }

@dataclass
class ConversationFlowPattern:
    """Defines a conversation flow pattern"""
    name: str
    topic: str
    expected_steps: List[str]
    step_intents: List[str]
    context_building: Dict[str, str]  # step -> context variable
    response_templates: Dict[str, str]  # step -> response template

class EnhancedConversationFlowV2:
    """
    Advanced conversation flow system with multi-turn handling
    """
    
    def __init__(self):
        self.conversation_threads: Dict[str, ConversationThread] = {}
        
        # Define conversation flow patterns
        self.flow_patterns = {
            "enrollment_inquiry": ConversationFlowPattern(
                name="Enrollment Inquiry",
                topic="enrollment",
                expected_steps=[
                    "initial_inquiry",
                    "document_requirements", 
                    "deadline_information",
                    "conclusion"
                ],
                step_intents=[
                    "enrollment_inquiry",
                    "enrollment_documents", 
                    "enrollment_deadline",
                    "appreciation"
                ],
                context_building={
                    "initial_inquiry": "user_wants_to_enroll",
                    "document_requirements": "documents_discussed",
                    "deadline_information": "deadline_discussed"
                },
                response_templates={
                    "initial_inquiry": "I'd be happy to help you with enrollment! Let me guide you through the process step by step. We'll cover the required documents, deadlines, and procedures to ensure a smooth enrollment experience for your child.",
                    "document_requirements": "For enrollment, you'll need the following requirements and documents: birth certificate, report card, and 2x2 ID photos. These documents are essential requirements for completing your child's enrollment and ensuring we have all the necessary information.",
                    "deadline_information": "The enrollment deadline is typically in May. I recommend starting the process early to secure your child's spot, as we have limited capacity and enrollment is on a first-come, first-served basis.",
                    "conclusion": "You're all set with the enrollment information! Feel free to ask if you need any clarification or have additional questions about our school programs and facilities."
                }
            ),
            "school_information": ConversationFlowPattern(
                name="School Information",
                topic="school_info",
                expected_steps=[
                    "general_inquiry",
                    "grade_levels",
                    "facilities",
                    "fees"
                ],
                step_intents=[
                    "school_info",
                    "grade_levels",
                    "facilities_inquiry", 
                    "financial_inquiry"
                ],
                context_building={
                    "general_inquiry": "school_overview_discussed",
                    "grade_levels": "grades_discussed",
                    "facilities": "facilities_discussed"
                },
                response_templates={
                    "general_inquiry": "Tomas SM. Bautista Elementary School is a quality educational institution in Fatima, New Washington, Aklan. We provide comprehensive elementary education with modern facilities and dedicated teachers committed to student success.",
                    "grade_levels": "We offer grades 1-6, providing comprehensive elementary education for children aged 6-12. Our curriculum covers all elementary levels from Grade 1 to Grade 6, designed to develop both academic skills and character building in a supportive environment.",
                    "facilities": "Our school has modern classrooms and a library that is available but with limited resources as of today. We are currently working on establishing a computer lab which is in the making, and playground facilities are planned for future development. While we don't have a cafeteria, we do have a canteen that serves all your needs with various food options.",
                    "fees": "For detailed fee information and cost breakdown, please contact our school office at the school office. Our fees are competitive and include various payment options to accommodate different family situations."
                }
            )
        }
    
    def detect_conversation_pattern(self, user_message: str, conversation_history: List[Dict]) -> Optional[str]:
        """Detect if the current conversation matches a known pattern"""
        message_lower = user_message.lower()
        
        # 🎯 FIX: ALL queries should go to database search first
        # Return None for all queries to force database search
        return None
        
        # Check if we're continuing an existing pattern
        if conversation_history:
            # Look for enrollment-related content in recent conversation
            recent_content = []
            for turn in conversation_history[-6:]:  # Look at last 6 turns (3 exchanges)
                if turn.get("role") == "user":
                    recent_content.append(turn.get("content", "").lower())
                elif turn.get("role") == "assistant":
                    recent_content.append(turn.get("content", "").lower())
            
            recent_text = " ".join(recent_content)
            
            # Check for enrollment pattern continuation - be more specific
            if any(word in recent_text for word in ["enroll", "enrollment", "register", "documents", "birth certificate", "report card", "id photos", "deadline"]):
                # Only continue enrollment if there are clear enrollment-related terms
                # Exclude "requirements" as it's too generic and catches queries that should go to database
                return "enrollment_inquiry"
            
            # Check for school info pattern continuation
            elif any(word in recent_text for word in ["school", "about", "information", "grades", "facilities", "tomas", "bautista"]):
                # If we're in a school info conversation, continue it for any follow-up
                return "school_information"
        
        return None
    
    def get_or_create_thread(self, session_id: str, pattern_name: str) -> ConversationThread:
        """Get or create a conversation thread"""
        thread_id = f"{session_id}_{pattern_name}"
        
        if thread_id not in self.conversation_threads:
            pattern = self.flow_patterns.get(pattern_name)
            if pattern:
                self.conversation_threads[thread_id] = ConversationThread(
                    thread_id=thread_id,
                    topic=pattern.topic,
                    current_step=0,
                    total_steps=len(pattern.expected_steps)
                )
            else:
                # Create a default thread if pattern not found
                self.conversation_threads[thread_id] = ConversationThread(
                    thread_id=thread_id,
                    topic="general",
                    current_step=0,
                    total_steps=1
                )
        
        return self.conversation_threads[thread_id]
    
    def determine_conversation_step(self, user_message: str, thread: ConversationThread, detected_intent: str) -> Tuple[int, str]:
        """Determine the current step in the conversation flow"""
        # Find the pattern by topic
        pattern = None
        for pattern_name, pattern_obj in self.flow_patterns.items():
            if pattern_obj.topic == thread.topic:
                pattern = pattern_obj
                break
        
        if not pattern:
            return 0, "unknown"
        
        message_lower = user_message.lower()
        current_step = thread.current_step
        
        # Map intent to step - handle enrollment pattern specifically
        if pattern.topic == "enrollment":
            # Handle enrollment-specific intents
            if detected_intent in ["enrollment_inquiry"]:
                return 0, "initial_inquiry"
            elif detected_intent in ["enrollment_documents"]:
                return 1, "document_requirements"
            elif detected_intent in ["schedule_inquiry"] and any(word in message_lower for word in ["deadline", "when", "time", "due"]):
                return 2, "deadline_information"
            elif detected_intent in ["appreciation"] and any(word in message_lower for word in ["thank", "thanks", "appreciate"]):
                return 3, "conclusion"
        
        # 🎯 FIX: Enhanced keyword-based step determination for school information
        if pattern.topic == "school_info":
            # Handle specific queries about grades
            if any(word in message_lower for word in ["grades", "grade", "levels", "level", "offer", "teach", "what grades", "which grades"]):
                logger.info(f"🔍 Step determination: Detected grades query, routing to grade_levels")
                return 1, "grade_levels"
            # Handle specific queries about facilities - EXPANDED KEYWORDS
            elif any(word in message_lower for word in ["facilities", "facility", "library", "cafeteria", "lab", "playground", "classroom", "computer lab", "science lab", "multipurpose", "hall", "canteen", "gym", "gymnasium", "clinic", "office", "amenities", "buildings", "rooms", "areas", "spaces"]):
                logger.info(f"🔍 Step determination: Detected facilities query, routing to facilities")
                return 2, "facilities"
            # Handle specific queries about fees
            elif any(word in message_lower for word in ["fees", "fee", "tuition", "cost", "price", "money", "pay", "how much", "payment", "bayad", "magkano"]):
                logger.info(f"🔍 Step determination: Detected fees query, routing to fees")
                return 3, "fees"
        
        # Map intent to step for other patterns (fallback)
        if detected_intent in pattern.step_intents:
            step_index = pattern.step_intents.index(detected_intent)
            return step_index, pattern.expected_steps[step_index]
        
        # Fallback: determine step based on keywords
        if current_step == 0 and any(word in message_lower for word in ["enroll", "register"]):
            return 0, "initial_inquiry"
        elif current_step == 1 and any(word in message_lower for word in ["document", "paper", "requirement"]):
            return 1, "document_requirements"
        elif any(word in message_lower for word in ["deadline", "when", "time", "due"]):
            return 2, "deadline_information"
        elif any(word in message_lower for word in ["thank", "thanks", "appreciate", "goodbye", "bye"]):
            return 3, "conclusion"
        
        # Default to next step
        next_step = min(current_step + 1, len(pattern.expected_steps) - 1)
        return next_step, pattern.expected_steps[next_step]
    
    def generate_contextual_response(self, user_message: str, thread: ConversationThread, step_name: str, base_response: str) -> str:
        """Generate a contextual response based on conversation flow"""
        # Find the pattern by topic
        pattern = None
        for pattern_name, pattern_obj in self.flow_patterns.items():
            if pattern_obj.topic == thread.topic:
                pattern = pattern_obj
                break
        
        if not pattern:
            return base_response
        
        # 🎯 FIX: Prioritize database search results over hardcoded templates
        # Only use hardcoded templates if base_response is generic or empty
        if base_response and len(base_response) > 50 and not base_response.startswith("I can't answer") and not base_response.startswith("I don't have"):
            # Use database search result as primary source
            template = base_response
        else:
            # Fallback to hardcoded template only if no database result
            template = pattern.response_templates.get(step_name, base_response)
        
        # 🎯 FIX: If base_response is a structured response (contains sentence format), use it directly
        if base_response and ("You can contact" in base_response or "Maaari kayong makipag-ugnayan" in base_response or "Makig-istorya kamo" in base_response):
            template = base_response
        # 🎯 FIX: If base_response is already a structured response with bullet points, convert to sentence format
        elif base_response and "•" in base_response and ("Admin Building" in base_response or "Monday - Friday" in base_response):
            # Convert bullet point format to sentence format
            lines = base_response.split('\n')
            sentences = []
            for line in lines:
                if line.strip() and not line.startswith('Additional Context:'):
                    # Remove bullet points and convert to sentence
                    clean_line = line.replace('•', '').strip()
                    if clean_line:
                        sentences.append(clean_line)
            
            # Create sentence format
            if sentences:
                template = " ".join(sentences) + "."
            else:
                template = base_response
        
        # Add conversation continuity elements
        continuity_elements = []
        
        # Add step progression context
        if thread.current_step > 0:
            continuity_elements.append(f"Continuing with {thread.topic.replace('_', ' ')}...")
        
        # Add context from previous steps
        if step_name == "document_requirements" and "user_wants_to_enroll" in thread.context_variables:
            continuity_elements.append("As you mentioned wanting to enroll your child,")
        elif step_name == "deadline_information" and "documents_discussed" in thread.context_variables:
            continuity_elements.append("Now that we've covered the required documents,")
        
        # Add engagement elements
        if thread.user_engagement_level == "high":
            engagement_elements = [
                "I appreciate your detailed questions.",
                "Thank you for being thorough.",
                "I can see you're really interested in this topic."
            ]
        else:
            engagement_elements = [
                "Let me provide you with the information you need.",
                "I'm here to help with any questions.",
                "Feel free to ask for clarification."
            ]
        
        # Combine elements
        if continuity_elements:
            continuity_text = " ".join(continuity_elements)
            enhanced_response = f"{continuity_text} {template}"
        else:
            enhanced_response = template
        
        # Add engagement element
        import random
        engagement = random.choice(engagement_elements)
        enhanced_response += f" {engagement}"
        
        # Ensure response meets quality requirements
        if len(enhanced_response) < 20:
            enhanced_response += " Please let me know if you need more information."
        
        if enhanced_response.count('.') < 1:
            enhanced_response += "."
        
        # Additional quality checks for conversation flow
        if len(enhanced_response) < 50:  # Ensure substantial responses
            if step_name == "initial_inquiry":
                enhanced_response += " I'm here to guide you through the entire enrollment process step by step."
            elif step_name == "document_requirements":
                enhanced_response += " These documents are essential for completing your child's enrollment."
            elif step_name == "deadline_information":
                enhanced_response += " I recommend starting the enrollment process as soon as possible to secure your child's spot."
            elif step_name == "conclusion":
                enhanced_response += " Feel free to ask if you have any other questions about our school."
            else:
                enhanced_response += " I'm here to help with any additional questions you might have."
        
        return enhanced_response
    
    def update_thread_context(self, thread: ConversationThread, step_name: str, user_message: str, response: str, intent: str):
        """Update thread context with new information"""
        # Find the pattern by topic
        pattern = None
        for pattern_name, pattern_obj in self.flow_patterns.items():
            if pattern_obj.topic == thread.topic:
                pattern = pattern_obj
                break
        
        if not pattern:
            return
        
        # Update context variables
        if step_name in pattern.context_building:
            context_var = pattern.context_building[step_name]
            thread.context_variables[context_var] = True
        
        # Update conversation stage
        if thread.current_step == 0:
            thread.conversation_stage = "initial"
        elif thread.current_step < thread.total_steps - 1:
            thread.conversation_stage = "ongoing"
        else:
            thread.conversation_stage = "concluding"
        
        # Update engagement level based on message length and complexity
        if len(user_message.split()) > 10:
            thread.user_engagement_level = "high"
        elif len(user_message.split()) > 5:
            thread.user_engagement_level = "medium"
        else:
            thread.user_engagement_level = "low"
        
        # Add turn to thread
        thread.add_turn(user_message, response, intent)
    
    async def process_conversation_turn(self, 
                                      user_message: str, 
                                      session_id: str, 
                                      conversation_history: List[Dict],
                                      detected_intent: str,
                                      base_response: str) -> Tuple[str, ConversationThread]:
        """Process a conversation turn with enhanced flow handling"""
        
        # Detect conversation pattern
        pattern_name = self.detect_conversation_pattern(user_message, conversation_history)
        logger.info(f"🔍 Pattern detection for '{user_message}': {pattern_name}")
        
        if pattern_name:
            # Get or create conversation thread
            thread = self.get_or_create_thread(session_id, pattern_name)
            
            # Determine current step
            step_index, step_name = self.determine_conversation_step(user_message, thread, detected_intent)
            thread.current_step = step_index
            
            logger.info(f"🔍 Step determination: {step_index} -> {step_name}")
            
            # Generate contextual response
            enhanced_response = self.generate_contextual_response(user_message, thread, step_name, base_response)
            
            # Update thread context
            self.update_thread_context(thread, step_name, user_message, enhanced_response, detected_intent)
            
            logger.info(f"🧠 Enhanced conversation flow: {pattern_name} - Step {step_index + 1}/{thread.total_steps} ({step_name})")
            
            return enhanced_response, thread
        else:
            # No pattern detected, return base response
            logger.info(f"🔍 No pattern detected for '{user_message}', using base response")
            return base_response, None

# Global instance
enhanced_conversation_flow_v2 = EnhancedConversationFlowV2()
