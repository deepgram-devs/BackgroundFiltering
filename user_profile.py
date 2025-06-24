# user_profile.py - Individual user customization
import json
import os
import uuid
from pathlib import Path

class UserProfile:
    """
    Manages per-user data and customization for the AI Voice Assistant.
    Each user gets their own custom commands file stored locally.
    """
    
    def __init__(self):
        self.user_dir = self.get_user_directory()
        self.user_id = self.get_or_create_user_id()
        self.custom_commands_file = self.user_dir / "custom_commands.json"
        self.usage_file = self.user_dir / "usage_tracking.json"
        self.settings_file = self.user_dir / "settings.json"
        
        # Initialize user data
        self.initialize_user_data()
        
    def get_user_directory(self):
        """Get or create user-specific directory for app data"""
        if os.name == 'nt':  # Windows
            # Use AppData/Roaming for user-specific app data
            app_data = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
            user_dir = app_data / "AI Voice Assistant"
        elif os.name == 'posix':  # macOS/Linux
            if 'darwin' in os.uname().sysname.lower():  # macOS
                user_dir = Path.home() / "Library" / "Application Support" / "AI Voice Assistant"
            else:  # Linux
                user_dir = Path.home() / ".config" / "ai-voice-assistant"
        else:
            # Fallback
            user_dir = Path.home() / ".ai_voice_assistant"
        
        # Create directory if it doesn't exist
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def get_or_create_user_id(self):
        """Generate or retrieve unique user ID"""
        user_id_file = self.user_dir / "user_id.txt"
        
        if user_id_file.exists():
            try:
                user_id = user_id_file.read_text().strip()
                if user_id:  # Make sure it's not empty
                    return user_id
            except:
                pass  # Fall through to create new ID
        
        # Create new user ID
        user_id = str(uuid.uuid4())
        try:
            user_id_file.write_text(user_id)
        except Exception as e:
            print(f"⚠️ Could not save user ID: {e}")
        
        return user_id
    
    def initialize_user_data(self):
        """Initialize default user data files"""
        self.initialize_custom_commands()
        self.initialize_settings()
    
    def initialize_custom_commands(self):
        """Create default custom commands for new users"""
        if not self.custom_commands_file.exists():
            default_commands = {
                "what events do i have today": [
                    "What's on my schedule today?",
                    "Today's agenda",
                    "Show me today's calendar",
                    "What do I have today?"
                ],
                "when am i free today": [
                    "When can I schedule something today?",
                    "What time slots are available?",
                    "Show my free time today",
                    "When am I available?"
                ],
                "what events do i have this week": [
                    "What's my week looking like?",
                    "Weekly schedule",
                    "Show this week's events",
                    "What's coming up this week?"
                ],
                "create event": [
                    "Schedule a meeting",
                    "Add to calendar",
                    "Book an appointment",
                    "Set up a meeting"
                ],
                "find event": [
                    "Look for event",
                    "Search my calendar",
                    "Where is my meeting",
                    "Find my appointment"
                ],
                "question": [
                    "I have a question",
                    "Ask AI",
                    "Hey assistant",
                    "Help me with"
                ]
            }
            
            try:
                with open(self.custom_commands_file, 'w') as f:
                    json.dump(default_commands, f, indent=2)
                print(f"✅ Created default custom commands for user")
            except Exception as e:
                print(f"❌ Could not create custom commands file: {e}")
    
    def initialize_settings(self):
        """Create default settings for new users"""
        if not self.settings_file.exists():
            default_settings = {
                "first_run": True,
                "timezone": "auto",
                "voice_feedback": True,
                "minimize_to_tray": False,
                "auto_start_listening": True,
                "theme": "dark"
            }
            
            try:
                with open(self.settings_file, 'w') as f:
                    json.dump(default_settings, f, indent=2)
            except Exception as e:
                print(f"❌ Could not create settings file: {e}")
    
    def load_custom_commands(self):
        """Load user's custom commands"""
        try:
            if self.custom_commands_file.exists():
                with open(self.custom_commands_file, 'r') as f:
                    commands = json.load(f)
                print(f"✅ Loaded {len(commands)} custom command categories for user {self.user_id[:8]}...")
                return commands
            else:
                print("📝 No custom commands found, using defaults")
                self.initialize_custom_commands()
                return self.load_custom_commands()
        except Exception as e:
            print(f"❌ Error loading custom commands: {e}")
            return {}
    
    def save_custom_commands(self, commands):
        """Save user's custom commands"""
        try:
            with open(self.custom_commands_file, 'w') as f:
                json.dump(commands, f, indent=2)
            print(f"✅ Saved custom commands for user {self.user_id[:8]}...")
            return True
        except Exception as e:
            print(f"❌ Error saving custom commands: {e}")
            return False
    
    def load_settings(self):
        """Load user settings"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            else:
                self.initialize_settings()
                return self.load_settings()
        except Exception as e:
            print(f"❌ Error loading settings: {e}")
            return {}
    
    def save_settings(self, settings):
        """Save user settings"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error saving settings: {e}")
            return False
    
    def get_user_info(self):
        """Get user information for display"""
        return {
            "user_id": self.user_id,
            "user_dir": str(self.user_dir),
            "custom_commands_count": len(self.load_custom_commands()),
            "first_run": self.load_settings().get("first_run", True)
        }