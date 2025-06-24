# openai_chat.py - OpenAI GPT-4o-mini integration for question responses
from openai import OpenAI
import os
from dotenv import load_dotenv
from embedded_config import EmbeddedConfig

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with embedded configuration
client = None

def initialize_openai_client():
    """Initialize OpenAI client with embedded API key"""
    global client
    try:
        api_key = EmbeddedConfig.get_openai_key()
        if not api_key:
            print("❌ Warning: OpenAI API key not found")
            print("Please set your OpenAI API key in .env file for development")
            return False
        
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing OpenAI client: {e}")
        return False

def gen(question):
    """Generate a response to a question using GPT-4o-mini"""
    global client
    
    # Initialize client if not already done
    if client is None:
        if not initialize_openai_client():
            return "Sorry, I'm unable to answer questions right now. Please check the API configuration."
    
    try:
        print(f"🤖 Asking GPT-4o-mini: {question}")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using the fastest GPT-4o model
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful AI assistant. Provide clear, concise, and accurate answers to user questions. Keep responses conversational and friendly."
                },
                {
                    "role": "user", 
                    "content": question
                }
            ],
            max_tokens=500,  # Reasonable limit for voice responses
            temperature=0.7  # Balanced creativity
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"✅ GPT-4o-mini response: {answer}")
        return answer
        
    except Exception as e:
        print(f"❌ Error generating response: {e}")
        return f"Sorry, I encountered an error while processing your question: {str(e)}"

# Initialize client on module import
initialize_openai_client()

if __name__ == "__main__":
    # Test the function
    print("🧪 Testing OpenAI GPT-4o-mini integration...")
    test_response = gen("What is the capital of France?")
    print(f"Test response: {test_response}") 