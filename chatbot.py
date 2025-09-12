import json
import os
import re
from typing import Dict, List, Optional, Tuple
from supabase import create_client, Client
import openai
from deep_translator import GoogleTranslator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AklanonDictionary:
    """Handles Aklanon to English translation using the dictionary"""
    
    def __init__(self, dictionary_path: str = "aklanon_dict.json"):
        self.dictionary = {}
        self.load_dictionary(dictionary_path)
    
    def load_dictionary(self, dictionary_path: str):
        """Load the Aklanon dictionary from JSON file"""
        try:
            if os.path.exists(dictionary_path):
                with open(dictionary_path, 'r', encoding='utf-8') as f:
                    dict_data = json.load(f)
                
                # Convert to lookup dictionary for faster access
                for entry in dict_data:
                    word = entry.get('word', '').lower().strip()
                    definition = entry.get('def', '')
                    if word and definition:
                        self.dictionary[word] = definition
                
                logger.info(f"Loaded {len(self.dictionary)} Aklanon words")
            else:
                logger.warning(f"Dictionary file {dictionary_path} not found")
        except Exception as e:
            logger.error(f"Error loading dictionary: {e}")
    
    def translate_word(self, word: str) -> Optional[str]:
        """Translate a single Aklanon word to English"""
        word_clean = word.lower().strip()
        return self.dictionary.get(word_clean)
    
    def translate_text(self, text: str) -> str:
        """Translate Aklanon text to English using dictionary lookup"""
        if not text.strip():
            return text
        
        # Split text into words while preserving punctuation
        words = re.findall(r'\w+|[^\w\s]', text.lower())
        translated_words = []
        
        for word in words:
            if word.isalpha():
                translation = self.translate_word(word)
                if translation:
                    # Use the first definition if multiple exist
                    if ';' in translation:
                        translation = translation.split(';')[0].strip()
                    translated_words.append(translation)
                else:
                    # Keep original word if no translation found
                    translated_words.append(word)
            else:
                # Keep punctuation as is
                translated_words.append(word)
        
        return ' '.join(translated_words)
    
    def is_aklanon(self, text: str) -> bool:
        """Check if text contains Aklanon words"""
        if not text.strip():
            return False
        
        words = re.findall(r'\w+', text.lower())
        aklanon_count = 0
        
        for word in words:
            if self.translate_word(word):
                aklanon_count += 1
        
        # Consider it Aklanon if more than 30% of words are in dictionary
        return aklanon_count > 0 and (aklanon_count / len(words)) > 0.3

class LanguageDetector:
    """Detects and handles multiple languages"""
    
    def __init__(self, aklanon_dict: AklanonDictionary):
        self.aklanon_dict = aklanon_dict
        self.tagalog_indicators = [
            'ako', 'ikaw', 'siya', 'kami', 'kayo', 'sila', 
            'ang', 'ng', 'sa', 'mga', 'ay', 'at', 'na', 'pa',
            'kumusta', 'salamat', 'oo', 'hindi', 'tayo'
        ]
    
    def detect_language(self, text: str) -> str:
        """Detect the language of input text"""
        if not text.strip():
            return 'english'
        
        text_lower = text.lower()
        
        # Check for Aklanon first
        if self.aklanon_dict.is_aklanon(text):
            return 'aklanon'
        
        # Check for Tagalog indicators
        words = re.findall(r'\w+', text_lower)
        tagalog_count = sum(1 for word in words if word in self.tagalog_indicators)
        
        if tagalog_count > 0 and (tagalog_count / len(words)) > 0.2:
            return 'tagalog'
        
        return 'english'

class MultilingualChatbot:
    """Main chatbot class with multilingual support"""
    
    def __init__(self):
        # Initialize Supabase
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize OpenAI
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        # Initialize language components
        self.aklanon_dict = AklanonDictionary()
        self.language_detector = LanguageDetector(self.aklanon_dict)
        
        # Translation setup
        self.tagalog_translator = GoogleTranslator(source='tl', target='en')
        self.english_to_tagalog = GoogleTranslator(source='en', target='tl')
        
        logger.info("Multilingual chatbot initialized")
    
    def save_conversation(self, user_input: str, bot_response: str, language: str):
        """Save conversation to Supabase"""
        try:
            data = {
                'user_input': user_input,
                'bot_response': bot_response,
                'language': language,
                'timestamp': 'now()'
            }
            result = self.supabase.table('conversations').insert(data).execute()
            logger.info("Conversation saved to database")
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
    
    def get_ai_response(self, text: str) -> str:
        """Get AI response using OpenAI"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Be friendly and conversational."},
                    {"role": "user", "content": text}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return "I'm sorry, I'm having trouble processing your request right now."
    
    def process_message(self, user_input: str) -> Tuple[str, str]:
        """Process user message and return response with detected language"""
        if not user_input.strip():
            return "Hello! How can I help you?", 'english'
        
        # Detect language
        detected_language = self.language_detector.detect_language(user_input)
        logger.info(f"Detected language: {detected_language}")
        
        # Process based on detected language
        if detected_language == 'aklanon':
            # Translate Aklanon to English
            english_text = self.aklanon_dict.translate_text(user_input)
            logger.info(f"Aklanon translated: '{user_input}' -> '{english_text}'")
            
            # Get AI response in English
            ai_response = self.get_ai_response(english_text)
            
            # Try to translate response back to Aklanon (basic word substitution)
            aklanon_response = self.translate_english_to_aklanon(ai_response)
            
            # If no Aklanon translation available, keep in English with note
            if aklanon_response == ai_response:
                final_response = f"{ai_response}\n\n(Aklanon translation not available for this response)"
            else:
                final_response = aklanon_response
            
            return final_response, detected_language
            
        elif detected_language == 'tagalog':
            # Translate Tagalog to English
            try:
                english_text = self.tagalog_translator.translate(user_input)
                logger.info(f"Tagalog translated: '{user_input}' -> '{english_text}'")
                
                # Get AI response
                ai_response = self.get_ai_response(english_text)
                
                # Translate response back to Tagalog
                tagalog_response = self.english_to_tagalog.translate(ai_response)
                return tagalog_response, detected_language
                
            except Exception as e:
                logger.error(f"Tagalog translation error: {e}")
                # Fallback to English
                ai_response = self.get_ai_response(user_input)
                return ai_response, 'english'
        
        else:
            # English - direct processing
            ai_response = self.get_ai_response(user_input)
            return ai_response, detected_language
    
    def translate_english_to_aklanon(self, english_text: str) -> str:
        """Attempt to translate English back to Aklanon (reverse dictionary lookup)"""
        # This is a basic implementation - in reality, you'd need a proper English-to-Aklanon dictionary
        # For now, we'll just keep it in English
        return english_text
    
    def chat(self):
        """Main chat loop"""
        print("🤖 Multilingual Chatbot Ready!")
        print("Languages supported: English, Tagalog, Aklanon")
        print("Type 'quit' to exit\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Process message
                response, language = self.process_message(user_input)
                
                print(f"Bot ({language}): {response}\n")
                
                # Save to database
                self.save_conversation(user_input, response, language)
                
            except KeyboardInterrupt:
                print("\n👋 Chat interrupted. Goodbye!")
                break
            except Exception as e:
                logger.error(f"Chat error: {e}")
                print("Sorry, something went wrong. Please try again.\n")

def main():
    """Main function to run the chatbot"""
    # Check for required environment variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these variables before running the chatbot.")
        return
    
    # Create and run chatbot
    chatbot = MultilingualChatbot()
    chatbot.chat()

if __name__ == "__main__":
    main()