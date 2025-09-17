# fallback.py
import logging

logger = logging.getLogger(__name__)

FB_MESSENGER_LINK = "https://m.me/114901716621736"

class FallbackHandler:
    def __init__(self, session=None):
        # If no session dict is passed, create one automatically
        self.session = session if session is not None else {}

    def get_state(self, key, default=None):
        return self.session.get(key, default)

    def set_state(self, key, value):
        self.session[key] = value
        logger.debug(f"[FallbackHandler] State updated: {key}={value}")

    def reset_state(self):
        self.session.clear()
        logger.debug("[FallbackHandler] Session state reset")

    def generate_fallback_message(self, language="en"):
        """
        Generates a polite fallback message based on language.
        """
        messenger_button = (
            f'<a href="{FB_MESSENGER_LINK}" target="_blank" '
            'style="background-color:#0084FF; color:white; padding:10px 18px; '
            'border-radius:20px; font-weight:bold; text-decoration:none; '
            'font-family:sans-serif; display:inline-block;">'
            '💬 Contact Us'
            '</a>'
        )

        if language.startswith("akl"):  # Aklanon
            return (
                "Paumanhin kon indi nako masabat inyo nga pamangkot. "
                "Maabot nyo it admin office para sa dugang nga bulig. "
                f"Kon gusto nyo magstorya sa tawo, pwede nyo sila kontakon sa {messenger_button}"
            )
        elif language.startswith("tl"):  # Tagalog
            return (
                "Paumanhin po kung hindi ko masagot ang inyong katanungan. "
                "Maaari po kayong lumapit sa admin office para sa karagdagang tulong. "
                f"Kung nais niyo pong makipag-ugnayan sa isang tao, maari niyo po silang makontak gamit ang {messenger_button}"
            )
        else:  # Default English
            return (
                "I'm sorry I couldn't answer your questions. "
                "You may visit the admin office for further assistance. "
                f"If you'd like to talk to a person, you can contact them at {messenger_button}"
            )

    def get_context_sensitive_fallback(self, query: str, language="en"):
        """
        Generate context-aware fallback based on query content.
        """
        query_lower = query.lower()
        
        # Staff/Personnel queries
        if any(word in query_lower for word in ["teacher", "principal", "staff", "faculty", "head teacher"]):
            if language.startswith("akl"):
                return "Para sa impormasyon sang mga magtutudlo, bisitahi it admin office."
            elif language.startswith("tl"):
                return "Para sa impormasyon ng mga guro, bumisita sa admin office."
            else:
                return "For staff information, please visit the admin office."
        
        # Contact/Communication queries  
        elif any(word in query_lower for word in ["contact", "phone", "email", "address", "location"]):
            if language.startswith("akl"):
                return "Para sa contact details, makadto sa admin office."
            elif language.startswith("tl"):
                return "Para sa contact details, pumunta sa admin office."
            else:
                return "For contact information, please visit the admin office."
        
        # Enrollment/Academic queries
        elif any(word in query_lower for word in ["enrollment", "admission", "register", "tuition", "fees"]):
            if language.startswith("akl"):
                return "Para sa enrollment, makadto sa admin office."
            elif language.startswith("tl"):
                return "Para sa enrollment, pumunta sa admin office."
            else:
                return "For enrollment information, please visit the admin office."
        
        # Default fallback
        else:
            return self.generate_fallback_message(language)

    def get_smart_keyword_response(self, query: str, language="en"):
        """
        Enhanced keyword matching for common school information.
        """
        query_lower = query.lower()
        
        # Common name queries with better responses
        name_responses = {
            "meliza delgado": {
                "en": "Meliza Delgado is the Head Teacher. For more details, visit the admin office.",
                "tl": "Si Meliza Delgado ang Head Teacher. Para sa mas detalyadong impormasyon, pumunta sa admin office.",
                "akl": "Si Meliza Delgado ang Head Teacher. Para sa dugang nga detalye, makadto sa admin office."
            },
            "maria santos": {
                "en": "Maria Santos is the Principal. For more details, visit the admin office.",
                "tl": "Si Maria Santos ang Principal. Para sa mas detalyadong impormasyon, pumunta sa admin office.",
                "akl": "Si Maria Santos ang Principal. Para sa dugang nga detalye, makadto sa admin office."
            }
        }
        
        # Check for name matches
        for name, responses in name_responses.items():
            if name in query_lower:
                return responses.get(language[:2], responses["en"])
        
        # Fallback to context-sensitive response
        return self.get_context_sensitive_fallback(query, language)

    def get_progressive_help_escalation(self, query: str, language="en", attempt_count=1):
        """
        Progressive escalation - more helpful with each failed attempt.
        """
        if attempt_count == 1:
            return self.get_context_sensitive_fallback(query, language)
        elif attempt_count == 2:
            # Second attempt - provide more specific guidance
            if language.startswith("akl"):
                return (
                    "Indi gid nako matubag ini. Kon importante ini, "
                    "direkta na lang makadto sa admin office o kontakon ang (123) 456-7890."
                )
            elif language.startswith("tl"):
                return (
                    "Hindi ko pa rin nasagot ito. Kung importante ito, "
                    "direkta na sa admin office o tumawag sa (123) 456-7890."
                )
            else:
                return (
                    "I still can't answer this. If it's urgent, "
                    "please go directly to the admin office or call (123) 456-7890."
                )
        else:
            # Third+ attempt - escalate to human
            return self.generate_fallback_message(language)

