# embedded_config.py
# Configuration for consumer distribution with embedded API keys
import os
from dotenv import load_dotenv

# Load environment variables for development
load_dotenv()

class EmbeddedConfig:
    """
    Configuration class for embedded API keys in consumer distribution.
    
    For development: Uses environment variables from .env
    For production build: Placeholders get replaced with actual keys
    """
    
    # These placeholders get replaced during production build
    # For development, falls back to environment variables
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "{{DEEPGRAM_KEY_PLACEHOLDER}}")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "{{OPENAI_KEY_PLACEHOLDER}}")
    
    # Usage limits to control costs in consumer distribution
    DAILY_VOICE_MINUTES = 60      # ~$4/month per active user
    DAILY_AI_QUERIES = 20         # ~$2/month per active user
    DAILY_CALENDAR_OPERATIONS = 100
    
    # Google OAuth for external app - now with placeholder support
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "{{GOOGLE_CLIENT_ID_PLACEHOLDER}}")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "{{GOOGLE_CLIENT_SECRET_PLACEHOLDER}}")
    
    # App metadata
    APP_NAME = "AI Voice Assistant"
    APP_VERSION = "1.0.0"
    
    @classmethod
    def is_production_build(cls):
        """Check if this is a production build with embedded keys"""
        return not cls.DEEPGRAM_API_KEY.startswith("{{")
    
    @classmethod
    def has_embedded_google_credentials(cls):
        """Check if Google OAuth credentials are embedded"""
        return (cls.GOOGLE_CLIENT_ID and 
                cls.GOOGLE_CLIENT_SECRET and 
                not cls.GOOGLE_CLIENT_ID.startswith("{{") and 
                not cls.GOOGLE_CLIENT_SECRET.startswith("{{"))
    
    @classmethod
    def get_deepgram_key(cls):
        """Get Deepgram API key with fallback logic"""
        if cls.is_production_build():
            print("🔑 Using embedded Deepgram API key")
            return cls.DEEPGRAM_API_KEY
        else:
            # Development mode - use environment variable
            key = os.getenv("DEEPGRAM_API_KEY")
            if key:
                print("🔑 Using development Deepgram API key")
                return key
            else:
                print("❌ No Deepgram API key found - check .env file")
                return None
    
    @classmethod
    def get_openai_key(cls):
        """Get OpenAI API key with fallback logic"""
        if cls.is_production_build():
            print("🔑 Using embedded OpenAI API key")
            return cls.OPENAI_API_KEY
        else:
            # Development mode - use environment variable
            key = os.getenv("OPENAI_API_KEY")
            if key:
                print("🔑 Using development OpenAI API key")
                return key
            else:
                print("❌ No OpenAI API key found - check .env file")
                return None
    
    @classmethod
    def get_google_credentials(cls):
        """Get Google OAuth credentials with fallback logic"""
        if cls.has_embedded_google_credentials():
            print("🔑 Using embedded Google OAuth credentials")
            return cls.GOOGLE_CLIENT_ID, cls.GOOGLE_CLIENT_SECRET
        else:
            # Development mode or missing credentials
            client_id = os.getenv("GOOGLE_CLIENT_ID")
            client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
            if client_id and client_secret:
                print("🔑 Using development Google OAuth credentials")
                return client_id, client_secret
            else:
                print("⚠️ No Google OAuth credentials found - calendar features will require manual setup")
                return None, None

# For backward compatibility during development
def get_deepgram_key():
    """Legacy function for backward compatibility"""
    return EmbeddedConfig.get_deepgram_key()

def get_openai_key():
    """Legacy function for backward compatibility"""
    return EmbeddedConfig.get_openai_key()