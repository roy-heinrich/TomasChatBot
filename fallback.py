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

        if language.startswith("tl"):  # Tagalog
            return (
                "Paumanhin po kung hindi ko masagot ang inyong katanungan. "
                "Maaari po kayong lumapit sa admin office para sa karagdagang tulong. "
                f"Kung nais niyo pong makipag-ugnayan sa isang tao, maari niyo po silang makontak gamit ang {messenger_button}"
            )
        else:  # Default English
            return (
                "I'm sorry I couldn't answer your questions. "
                "You may visit the admin office for further assistance. "
                f"If you’d like to talk to a person, you can contact them at {messenger_button}"
            )

