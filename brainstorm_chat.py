# brainstorm_chat.py - Deepgram Voice Agent for Brainstorming Sessions
import asyncio
import threading
import sys
import os
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    AgentWebSocketEvents,
    SettingsOptions,
    Input,
    Output,
)
from embedded_config import EmbeddedConfig

# Global voice agent connection
voice_agent = None
current_session = None

# GUI callback for streaming summaries to main interface
gui_callback = None

def set_gui_callback(callback_func):
    """Set a callback function to send messages to the GUI"""
    global gui_callback
    gui_callback = callback_func
    print("✅ GUI callback registered for brainstorming summaries")

def send_to_gui(message):
    """Thread-safe way to send messages to the GUI"""
    global gui_callback
    if gui_callback:
        try:
            # Import here to avoid circular imports
            import tkinter as tk
            
            def update_gui():
                try:
                    gui_callback(message)
                except Exception as e:
                    print(f"⚠️ Error in GUI callback: {e}")
            
            # Schedule GUI update in the main thread if we're in a different thread
            import threading
            if threading.current_thread() != threading.main_thread():
                # For tkinter, we need to schedule updates in the main thread
                # This will work if the main thread has a tkinter mainloop running
                try:
                    # Try to get the root window and schedule the update
                    root = tk._default_root
                    if root:
                        root.after(0, update_gui)
                    else:
                        # Fallback to direct call if no root window
                        update_gui()
                except:
                    # Final fallback
                    update_gui()
            else:
                update_gui()
                
        except Exception as e:
            print(f"⚠️ Error sending to GUI: {e}")
    else:
        print("📝 No GUI callback registered - summary only in terminal")

class VoiceBrainstormSession:
    """Manages a voice brainstorming session using Deepgram's voice agent"""
    
    def __init__(self):
        self.is_active = False
        self.deepgram = None
        self.connection = None
        self.topic = None
        self.should_end = False
        self.conversation_log = []  # Track conversation for summaries
        self.session_start_time = None
        
    def initialize_voice_agent(self):
        """Initialize Deepgram voice agent"""
        try:
            api_key = EmbeddedConfig.get_deepgram_key()
            if not api_key:
                print("❌ Deepgram API key not found")
                return False
                
            # Configure Deepgram client for voice agent
            config = DeepgramClientOptions(
                options={
                    "keepalive": "true",
                    "microphone_record": "true",
                    "speaker_playback": "true",
                    "diarize": "true",
                }
            )
            
            self.deepgram = DeepgramClient(api_key, config)
            self.connection = self.deepgram.agent.websocket.v("1")
            
            print("✅ Deepgram voice agent initialized for brainstorming")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing voice agent: {e}")
            return False
    
    def configure_brainstorm_agent(self, topic=None):
        """Configure the voice agent for brainstorming conversations"""
        options = SettingsOptions()

        # Configure audio settings
        options.audio.input = Input(
            encoding="linear16",
            sample_rate=16000
        )
        options.audio.output = Output(
            encoding="linear16",
            sample_rate=16000,
            container="none"
        )

        # Configure the brainstorming AI personality
        options.agent.think.provider.type = "open_ai"
        options.agent.think.provider.model = "gpt-4o-mini"
        
        # Brainstorming-focused prompt
        brainstorm_prompt = (
            "You are an enthusiastic brainstorming partner and creative thinking coach. "
            "Your goal is to help users explore ideas, think outside the box, and develop concepts through conversation.\n\n"
            "Brainstorming Guidelines:\n"
            "- Ask thought-provoking, open-ended questions\n"
            "- Use 'Yes, and...' thinking to build on ideas\n"
            "- Suggest alternative perspectives and approaches\n"
            "- Encourage wild, creative, and unconventional ideas\n"
            "- Help break down complex topics into manageable parts\n"
            "- Keep responses under 2 sentences and conversational\n"
            "- Be energetic, supportive, and inspiring\n\n"
            "SPECIAL COMMANDS:\n"
            "- If the user says 'summary', respond with: 'Let me provide you with a summary of our brainstorming session so far!' and then the system will automatically generate a detailed summary.\n"
            "- Continue the conversation naturally after providing summaries\n\n"
        )
        
        if topic:
            brainstorm_prompt += f"Today's brainstorming focus: {topic}\n"
            brainstorm_prompt += "Help the user explore this topic thoroughly and creatively.\n\n"
        
        brainstorm_prompt += (
            "Remember: This is a voice conversation. Speak naturally and keep the creative energy flowing! "
            "The user will manually stop the assistant when they want to end the brainstorming session."
        )
        
        options.agent.think.prompt = brainstorm_prompt

        # Voice recognition settings with speaker diarization
        options.agent.listen.provider.model = "nova-3"
        options.agent.listen.provider.type = "deepgram"
        options.agent.listen.provider.diarize = True  # Enable speaker diarization
        options.agent.listen.provider.keyterms = ["idea", "creative", "brainstorm", "think", "summary", "summarize", "end", "stop", "finish", "quit"]
        
        # Voice synthesis
        options.agent.speak.provider.type = "deepgram"

        # Dynamic greeting with speaker diarization
        if topic:
            options.agent.greeting = f"Hey! Ready to brainstorm about {topic}? Let's dive in and explore some amazing ideas together! I have speaker diarization enabled to focus on your voice. Say 'summary' anytime for a recap, or 'end brainstorm' when you're done."
        else:
            options.agent.greeting = "Hello! I'm your brainstorming buddy. What exciting topic shall we explore today? I have speaker diarization enabled to focus on your voice. Say 'summary' anytime for a recap, or 'end brainstorm' when you're done."

        return options
    
    def setup_event_handlers(self):
        """Setup event handlers for the voice agent"""
        
        # Capture reference to the session object for use in event handlers
        session = self
        
        def on_open(self, open, **kwargs):
            print("🚀 Voice brainstorm session opened")

        def on_welcome(self, welcome, **kwargs):
            print("👋 Welcome to voice brainstorming session")

        def on_conversation_text(self, conversation_text, **kwargs):
            content = conversation_text.content
            print(f"💬 Conversation: {content}")
            
            # Check if user wants to end the brainstorming session
            content_lower = content.lower()
            if ('end brainstorm' in content_lower or 
                ('end' in content_lower and 'brainstorm' in content_lower) or
                ('stop brainstorm' in content_lower) or
                ('finish brainstorm' in content_lower) or
                ('quit brainstorm' in content_lower)) and len(content.split()) < 8:  # Short command
                
                print("🛑 User requested to end brainstorming session")
                send_to_gui("🛑 Brainstorming session ended by user voice command.\n\n📝 Press 'Start Listening' to resume regular dictation.")
                session.end_session()
                return
            
            # Check if user is requesting a summary
            if 'summary' in content.lower() and len(content.split()) < 10:  # Short message with "summary"
                print("\n" + "="*50)
                print("📋 BRAINSTORMING SESSION SUMMARY")
                print("="*50)
                summary = get_brainstorm_summary()
                print(summary)
                print("="*50 + "\n")
                
                # Send summary to GUI if callback is available
                gui_summary = f"📋 BRAINSTORMING SESSION SUMMARY\n{'='*50}\n{summary}\n{'='*50}"
                send_to_gui(gui_summary)
            
            # Log conversation for summaries with timestamp
            import time
            timestamp = time.time()
            
            # Determine if this is user speech or AI response
            # AI responses typically start with certain patterns or are longer
            is_ai_response = (
                len(content) > 50 or  # Longer messages are likely AI
                content.lower().startswith(('hello', 'hey', 'great', 'that\'s', 'what about', 'how about', 'yes', 'and', 'summary:', 'here\'s a summary', 'let me provide'))
            )
            
            conversation_entry = {
                'timestamp': timestamp,
                'content': content,
                'type': 'ai_response' if is_ai_response else 'user_input',
                'word_count': len(content.split())
            }
            
            session.conversation_log.append(conversation_entry)
            
            # Keep conversation log manageable (last 100 exchanges)
            if len(session.conversation_log) > 100:
                session.conversation_log = session.conversation_log[-100:]
            
            # Note: Session end is now handled manually by user stopping the assistant

        def on_agent_thinking(self, agent_thinking, **kwargs):
            print("🤔 Agent is thinking...")

        def on_agent_started_speaking(self, agent_started_speaking, **kwargs):
            print("🗣️ Agent started speaking")

        def on_error(self, error, **kwargs):
            print(f"❌ Voice agent error: {error}")

        # Register event handlers
        if self.connection:
            self.connection.on(AgentWebSocketEvents.Open, on_open)
            self.connection.on(AgentWebSocketEvents.Welcome, on_welcome)
            self.connection.on(AgentWebSocketEvents.ConversationText, on_conversation_text)
            self.connection.on(AgentWebSocketEvents.AgentThinking, on_agent_thinking)
            self.connection.on(AgentWebSocketEvents.AgentStartedSpeaking, on_agent_started_speaking)
            self.connection.on(AgentWebSocketEvents.Error, on_error)
    
    async def start_brainstorm_session(self, topic=None):
        """Start a voice brainstorming session"""
        try:
            if not self.initialize_voice_agent():
                return False
            
            self.topic = topic
            self.conversation_log = []  # Reset conversation log
            
            # Set session start time
            import time
            self.session_start_time = time.time()
            
            self.setup_event_handlers()
            
            # Configure for brainstorming
            options = self.configure_brainstorm_agent(topic)
            
            print(f"🎯 Starting voice brainstorming session...")
            if topic:
                print(f"💡 Topic: {topic}")
            
            if not self.connection.start(options):
                print("❌ Failed to start voice brainstorming session")
                return False
            
            self.is_active = True
            
            print("✅ Voice brainstorming session started! Start speaking...")
            print("🎤 Speaker diarization enabled - will focus on primary speaker")
            print("📝 Say 'summary' anytime for a recap of your session")
            print("🛑 Say 'end brainstorm' to end brainstorming")
            print("Press 'Stop Listening' to end session and 'Start Listening' to resume regular dictation")
            return True
            
        except Exception as e:
            print(f"❌ Error starting voice brainstorm: {e}")
            return False
    
    def end_session(self):
        """End the voice brainstorming session"""
        try:
            self.should_end = True
            self.is_active = False
            print("🛑 Ending brainstorming session")
            
            if self.connection:
                try:
                    self.connection.finish()
                except:
                    pass  # Ignore cleanup errors
            
        except Exception as e:
            print(f"⚠️ Session end warning: {e}")

def brainstorm(topic_or_question):
    """Start a voice brainstorming session - stops current assistant completely"""
    global current_session
    
    try:
        print(f"🧠 Starting voice brainstorming session...")
        print("🛑 Stopping main assistant for brainstorming...")
        
        if topic_or_question:
            print(f"💡 Topic: {topic_or_question}")
        
        # End any existing session
        if current_session and current_session.is_active:
            current_session.end_session()
        
        # Create new session
        current_session = VoiceBrainstormSession()
        
        # Start the session in a separate thread to avoid blocking the GUI
        def run_brainstorm():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    current_session.start_brainstorm_session(topic_or_question)
                )
                if result:
                    print("🎤 Voice brainstorming is now active. Speak to interact!")
                    return "Voice brainstorming session started! You can now speak to brainstorm ideas."
                else:
                    return "Failed to start voice brainstorming session."
            except Exception as e:
                print(f"❌ Error in brainstorm thread: {e}")
                return f"Error starting brainstorming: {str(e)}"
            finally:
                loop.close()
        
        # Run in background thread
        brainstorm_thread = threading.Thread(target=run_brainstorm, daemon=True)
        brainstorm_thread.start()
        
        # Give it a moment to start
        import time
        time.sleep(1)
        
        if current_session and current_session.is_active:
            return f"🎯 Voice brainstorming started! Topic: {topic_or_question if topic_or_question else 'Open brainstorming'}\n\n🎤 You can now speak to have a voice conversation about ideas!\n📝 Say 'summary' anytime for a recap\n🛑 Say 'end brainstorm' to end session\n🛑 Press 'Stop Listening' ro reset the dictation"
        else:
            return "Starting voice brainstorming session... Please wait a moment then start speaking.\n🛑 Press 'Stop Listening' when you want to end the session."
            
    except Exception as e:
        print(f"❌ Error starting brainstorm: {e}")
        return f"Sorry, I encountered an error starting the brainstorming session: {str(e)}"

def end_brainstorm():
    """End the current brainstorming session"""
    global current_session
    
    if current_session and current_session.is_active:
        current_session.end_session()
        current_session = None
        return "Voice brainstorming session ended manually."
    else:
        return "No active brainstorming session to end."

def is_brainstorming():
    """Check if a brainstorming session is currently active"""
    global current_session
    return current_session and current_session.is_active

def get_brainstorm_summary():
    """Get a comprehensive summary of the current brainstorming session"""
    global current_session
    
    if not current_session or not current_session.is_active:
        return "No active brainstorming session to summarize."
    
    if not current_session.conversation_log:
        return "No conversation yet to summarize. Start brainstorming and say 'summary' later!"
    
    # Calculate session duration
    import time
    session_duration = time.time() - current_session.session_start_time if current_session.session_start_time else 0
    duration_minutes = int(session_duration / 60)
    
    # Separate user inputs and AI responses
    user_inputs = [entry for entry in current_session.conversation_log if entry['type'] == 'user_input']
    ai_responses = [entry for entry in current_session.conversation_log if entry['type'] == 'ai_response']
    
    # Extract key topics and ideas from user inputs
    user_content = " ".join([entry['content'] for entry in user_inputs])
    
    # Build summary structure
    summary_parts = []
    
    # Session overview
    topic_info = f"Topic: {current_session.topic}" if current_session.topic else "Topic: Open brainstorming"
    summary_parts.append(f"📊 Session Overview:")
    summary_parts.append(f"  • {topic_info}")
    summary_parts.append(f"  • Duration: {duration_minutes} minutes")
    summary_parts.append(f"  • Exchanges: {len(current_session.conversation_log)} total")
    summary_parts.append(f"  • Your contributions: {len(user_inputs)} inputs")
    summary_parts.append("")
    
    # Key ideas from user inputs
    if user_inputs:
        summary_parts.append("💡 Your Key Ideas & Inputs:")
        recent_user_inputs = user_inputs[-10:]  # Last 10 user inputs
        for i, entry in enumerate(recent_user_inputs, 1):
            content_preview = entry['content'][:100] + "..." if len(entry['content']) > 100 else entry['content']
            summary_parts.append(f"  {i}. {content_preview}")
        summary_parts.append("")
    
    # Recent conversation highlights
    summary_parts.append("🔄 Recent Discussion Highlights:")
    recent_exchanges = current_session.conversation_log[-6:]  # Last 6 exchanges
    for entry in recent_exchanges:
        role = "You:" if entry['type'] == 'user_input' else "AI:"
        content_preview = entry['content'][:80] + "..." if len(entry['content']) > 80 else entry['content']
        summary_parts.append(f"  • {role} {content_preview}")
    
    summary_text = "\n".join(summary_parts)
    
    # Log the summary request
    print(f"📋 Generated brainstorming summary ({len(summary_parts)} sections)")
    
    return summary_text

def get_conversation_stats():
    """Get detailed statistics about the current brainstorming session"""
    global current_session
    
    if not current_session or not current_session.is_active:
        return "No active session."
    
    if not current_session.conversation_log:
        return "No conversation data yet."
    
    user_inputs = [entry for entry in current_session.conversation_log if entry['type'] == 'user_input']
    ai_responses = [entry for entry in current_session.conversation_log if entry['type'] == 'ai_response']
    
    user_word_count = sum(entry['word_count'] for entry in user_inputs)
    ai_word_count = sum(entry['word_count'] for entry in ai_responses)
    
    stats = {
        'total_exchanges': len(current_session.conversation_log),
        'user_inputs': len(user_inputs),
        'ai_responses': len(ai_responses),
        'user_words': user_word_count,
        'ai_words': ai_word_count,
        'avg_user_words': user_word_count / len(user_inputs) if user_inputs else 0,
        'avg_ai_words': ai_word_count / len(ai_responses) if ai_responses else 0
    }
    
    return stats

# Initialize for testing
if __name__ == "__main__":
    print("🧪 Testing Deepgram Voice Brainstorming...")
    
    result = brainstorm("Creative problem solving techniques")
    print(f"Result: {result}")
    
    # Keep the session running for testing
    import time
    time.sleep(30)  # Run for 30 seconds
    
    end_result = end_brainstorm()
    print(f"End result: {end_result}") 