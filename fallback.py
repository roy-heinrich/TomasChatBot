#fallback.py
import logging

logger = logging.getLogger("fallback")

class FallbackHandler:
    def __init__(self, session):
        self.session = session

        self.messages = {
            "en": {
                "no_answer": "I'm sorry, I don't have the answer right now. Would you like me to connect you with a live agent or raise a support ticket?",
                "low_confidence": "I may not be completely certain. Do you want to talk to a person for more accurate help?",
                "confirm_live_agent": "Do you want me to connect you with a school staff member? (Your information will be protected under the Data Privacy Act of 2012.)",
                "agent_connected": "✅ Your request has been noted. A staff member will reach out to you shortly.",
                "agent_declined": "Okay, I understand. Is there anything else I can help you with?",
                "please_confirm": "Please answer yes or no so I can proceed.",
                "greeting": "Hello! How can I assist you today?",
                "goodbye": "Goodbye! Thank you for visiting Tomas SM. Bautista Elementary School."
            },
            "tl": {
                "no_answer": "Pasensya na po, wala akong tiyak na sagot sa ngayon. Gusto niyo po bang i-connect ko kayo sa school staff o gumawa ng support ticket?",
                "low_confidence": "Hindi po ako ganap na sigurado. Gusto niyo po bang makipag-usap sa tao para mas malinaw na tulong?",
                "confirm_live_agent": "Gusto niyo po bang i-connect ko kayo sa kawani ng paaralan? (Ang inyong impormasyon ay poprotektahan sa ilalim ng Data Privacy Act of 2012.)",
                "agent_connected": "✅ Nakatala na po ang inyong kahilingan. May kawani po ng paaralan na makikipag-ugnayan sa inyo.",
                "agent_declined": "Okay po, naiintindihan ko. May iba pa po ba kayong concern?",
                "please_confirm": "Pakisagot po ng oo o hindi para makapag-tuloy ako.",
                "greeting": "Magandang araw po! Paano ko po kayo matutulungan?",
                "goodbye": "Paalam po! Salamat sa pagbisita sa Tomas SM. Bautista Elementary School."
            }
        }

        # Define trigger words for better organization
        self.live_agent_triggers = [
            "live agent", "human", "tao", "staff", "gusto ko makausap", 
            "connect", "person", "representative", "kawani", "makipag-usap"
        ]
        
        self.yes_words = ["yes", "oo", "opo", "sige", "connect", "gusto", "okay"]
        self.no_words = ["no", "hindi", "ayoko", "wag", "cancel"]

    def get_messages(self, lang):
        """Get messages based on language preference"""
        return self.messages.get(lang, self.messages["en"])

    def check_for_live_agent_trigger(self, query):
        """Check if user is requesting a live agent"""
        query_lower = query.lower()
        return any(trigger in query_lower for trigger in self.live_agent_triggers)

    def handle_no_answer_fallback(self, query):
        """Handle when no answer is found in knowledge base"""
        lang = self.session.get("language", "en")
        messages = self.get_messages(lang)
        
        # Set session state to await confirmation
        self.session["awaiting_confirmation"] = True
        self.session["fallback_type"] = "no_answer"
        
        logger.info("No answer fallback triggered - awaiting user confirmation")
        return messages["no_answer"]

    def handle_low_confidence_fallback(self, query):
        """Handle when confidence in answer is low"""
        lang = self.session.get("language", "en")
        messages = self.get_messages(lang)
        
        # Set session state to await confirmation
        self.session["awaiting_confirmation"] = True
        self.session["fallback_type"] = "low_confidence"
        
        logger.info("Low confidence fallback triggered - awaiting user confirmation")
        return messages["low_confidence"]

    def handle_fallback_request(self, query):
        """Handle direct request for live agent"""
        lang = self.session.get("language", "en")
        messages = self.get_messages(lang)
        
        # Set session state to await confirmation
        self.session["awaiting_confirmation"] = True
        self.session["fallback_type"] = "direct_request"
        
        logger.info("Direct live agent request - awaiting user confirmation")
        return messages["confirm_live_agent"]

    def handle_confirmation_response(self, query):
        """Handle user's yes/no response to live agent confirmation"""
        lang = self.session.get("language", "en")
        messages = self.get_messages(lang)
        query_lower = query.lower()
        
        if any(word in query_lower for word in self.yes_words):
            # User wants live agent
            self._clear_session_state()
            logger.info("User confirmed live agent request")
            return messages["agent_connected"]
            
        elif any(word in query_lower for word in self.no_words):
            # User declined live agent
            self._clear_session_state()
            logger.info("User declined live agent request")
            return messages["agent_declined"]
            
        else:
            # Unclear response, ask for clarification
            logger.info("Unclear confirmation response, asking for clarification")
            return messages["please_confirm"]

    def is_awaiting_confirmation(self):
        """Check if we're waiting for user confirmation"""
        return self.session.get("awaiting_confirmation", False)

    def _clear_session_state(self):
        """Clear fallback-related session state"""
        self.session.pop("awaiting_confirmation", None)
        self.session.pop("fallback_type", None)

    def handle(self, query):
        """Main handler method - routes to appropriate handler based on session state"""
        if self.is_awaiting_confirmation():
            return self.handle_confirmation_response(query)
        elif self.check_for_live_agent_trigger(query):
            return self.handle_fallback_request(query)
        else:
            # This shouldn't normally be called directly, but handle gracefully
            return self.handle_no_answer_fallback(query)