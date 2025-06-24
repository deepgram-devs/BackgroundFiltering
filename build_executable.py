#!/usr/bin/env python3
"""
AI Voice Assistant - Deployment Builder
Creates a professional executable for distribution
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ExecutableBuilder:
    def __init__(self):
        self.project_dir = Path.cwd()
        self.dist_dir = self.project_dir / "dist"
        self.build_dir = self.project_dir / "build"
        self.temp_dir = self.project_dir / "temp_build"
        
        print("🚀 AI Voice Assistant - Consumer Distribution Builder")
        print("=" * 60)
        
    def step_1_validate_environment(self):
        """Validate build environment and API keys"""
        print("\n📋 Step 1: Validating Environment")
        print("-" * 40)
        
        # Check for required API keys for consumer build
        required_keys = {
            'DEEPGRAM_API_KEY': 'Deepgram (for voice transcription)',
            'OPENAI_API_KEY': 'OpenAI (for AI responses)',
        }
        
        # Check for recommended but optional keys
        recommended_keys = {
            'GOOGLE_CLIENT_ID': 'Google OAuth (for calendar integration)',
            'GOOGLE_CLIENT_SECRET': 'Google OAuth (for calendar integration)',
        }
        
        missing_keys = []
        for key, description in required_keys.items():
            value = os.getenv(key)
            if not value or value.startswith('your_') or value == 'placeholder':
                missing_keys.append(f"  - {key}: {description}")
                print(f"❌ Missing: {key}")
            else:
                print(f"✅ Found: {key} (length: {len(value)})")
        
        # Check optional Google credentials
        google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        if google_client_id and google_client_secret:
            print(f"✅ Found: GOOGLE_CLIENT_ID (length: {len(google_client_id)})")
            print(f"✅ Found: GOOGLE_CLIENT_SECRET (length: {len(google_client_secret)})")
            print("🎉 Full calendar integration will be available")
        else:
            print(f"⚠️ Google OAuth credentials not found - calendar features will be disabled")
            print(f"   Users can still use voice, AI, and brainstorming features")
        
        if missing_keys:
            print(f"\n❌ Missing required environment variables for consumer build:")
            for key in missing_keys:
                print(key)
            print(f"\nFor consumer distribution, you need to provide YOUR API keys")
            print(f"that will be embedded in the executable for end users.")
            print(f"\nAdd these to your .env file:")
            print(f"DEEPGRAM_API_KEY=your_actual_deepgram_api_key")
            print(f"OPENAI_API_KEY=your_actual_openai_api_key")
            print(f"\nOptional for calendar features:")
            print(f"GOOGLE_CLIENT_ID=your_google_client_id")
            print(f"GOOGLE_CLIENT_SECRET=your_google_client_secret")
            return False
            
        print("✅ All required API keys found for consumer build")
        return True
        
    def step_2_create_embedded_config(self):
        """Create production version of embedded_config.py with real API keys"""
        print("\n🔧 Step 2: Creating Embedded Configuration")
        print("-" * 40)
        
        try:
            # Create temp directory
            self.temp_dir.mkdir(exist_ok=True)
            
            # Read the template embedded_config.py
            config_file = self.project_dir / "embedded_config.py"
            if not config_file.exists():
                print("❌ embedded_config.py not found!")
                return False
                
            config_content = config_file.read_text()
            
            # Replace placeholders with actual API keys
            replacements = {
                '{{DEEPGRAM_KEY_PLACEHOLDER}}': os.getenv('DEEPGRAM_API_KEY', ''),
                '{{OPENAI_KEY_PLACEHOLDER}}': os.getenv('OPENAI_API_KEY', ''),
                '{{GOOGLE_CLIENT_ID_PLACEHOLDER}}': os.getenv('GOOGLE_CLIENT_ID', ''),
                '{{GOOGLE_CLIENT_SECRET_PLACEHOLDER}}': os.getenv('GOOGLE_CLIENT_SECRET', ''),
            }
            
            for placeholder, real_value in replacements.items():
                if real_value:
                    config_content = config_content.replace(placeholder, real_value)
                    print(f"✅ Replaced {placeholder}")
                else:
                    print(f"⚠️ No value for {placeholder} - will use development fallback")
            
            # Write production config to temp directory
            temp_config = self.temp_dir / "embedded_config.py"
            temp_config.write_text(config_content)
            print(f"✅ Created production embedded_config.py")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating embedded config: {e}")
            return False
    
    def step_3_prepare_files(self):
        """Prepare all necessary files for the build"""
        print("\n📁 Step 3: Preparing Build Files")
        print("-" * 40)
        
        try:
            # Copy all necessary files to temp directory
            files_to_copy = [
                "assistant.py",
                "openai_chat.py", 
                "brainstorm_chat.py",
                "assistantTools.py",
                "calendar_events.py",
                "google_oauth.py",
                "user_profile.py",
                "requirements.txt"
            ]
            
            for file_name in files_to_copy:
                src = self.project_dir / file_name
                if src.exists():
                    dst = self.temp_dir / file_name
                    shutil.copy2(src, dst)
                    print(f"✅ Copied {file_name}")
                else:
                    print(f"⚠️ File not found: {file_name}")
            
            print("✅ All necessary files prepared for embedded distribution")
            return True
            
        except Exception as e:
            print(f"❌ Error preparing files: {e}")
            return False
    
    def step_4_install_dependencies(self):
        """Install dependencies in temp environment"""
        print("\n📦 Step 4: Installing Dependencies")
        print("-" * 40)
        
        try:
            # Install requirements
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], cwd=self.temp_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
                return True
            else:
                print(f"❌ Error installing dependencies: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False
    
    def step_5_build_executable(self):
        """Build the executable using PyInstaller"""
        print("\n🔨 Step 5: Building Executable")
        print("-" * 40)
        
        try:
            # PyInstaller command for consumer distribution
            cmd = [
                "pyinstaller",
                "--onefile",
                "--windowed",
                "--name=AI-Voice-Assistant",
                "--icon=icon.ico" if (self.project_dir / "icon.ico").exists() else "",
                "--hidden-import=deepgram",
                "--hidden-import=openai",
                "--hidden-import=google.oauth2",
                "--hidden-import=google.auth",
                "--hidden-import=googleapiclient",
                "--hidden-import=tkinter",
                "--hidden-import=pyaudio",
                "--hidden-import=dotenv",
                "--hidden-import=asyncio",
                "--hidden-import=threading",
                "--hidden-import=brainstorm_chat",
                "assistant.py"
            ]
            
            # Remove empty icon parameter if no icon exists
            cmd = [arg for arg in cmd if arg]
            
            print(f"🔨 Running PyInstaller...")
            result = subprocess.run(cmd, cwd=self.temp_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Executable built successfully")
                return True
            else:
                print(f"❌ PyInstaller error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error building executable: {e}")
            return False
    
    def step_6_create_distribution_package(self):
        """Create final distribution package"""
        print("\n📦 Step 6: Creating Distribution Package")
        print("-" * 40)
        
        try:
            # Create distribution directory
            dist_name = "AI-Voice-Assistant-Consumer"
            final_dist = self.dist_dir / dist_name
            final_dist.mkdir(parents=True, exist_ok=True)
            
            # Copy executable
            exe_name = "AI-Voice-Assistant.exe" if os.name == 'nt' else "AI-Voice-Assistant"
            exe_src = self.temp_dir / "dist" / exe_name
            exe_dst = final_dist / exe_name
            
            if exe_src.exists():
                shutil.copy2(exe_src, exe_dst)
                print(f"✅ Copied executable: {exe_name}")
            else:
                print(f"❌ Executable not found: {exe_src}")
                return False
            
            # Create user documentation
            readme_content = self.create_consumer_readme()
            readme_file = final_dist / "README.txt"
            readme_file.write_text(readme_content)
            print("✅ Created user documentation")
            
            print("✅ Distribution package created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error creating distribution: {e}")
            return False
    
    def create_consumer_readme(self):
        """Create README for consumer distribution"""
        return """🎤 AI Voice Assistant - Ready to Use!
===============================================

Thank you for downloading the AI Voice Assistant! This app is ready to use immediately.

✅ WHAT'S INCLUDED:
- Voice transcription (powered by Deepgram)
- AI question answering (powered by OpenAI GPT-4o-mini)  
- Interactive brainstorming sessions (voice conversations)
- Calendar integration (Google Calendar)
- Custom voice commands
- Speaker identification

🚀 QUICK START:
1. Double-click "AI-Voice-Assistant.exe" to launch
2. Click "Authenticate Google" to connect your calendar
3. Start talking! Try saying "What events do I have today?"

🎯 VOICE COMMANDS:
- "What events do I have today?"
- "When am I free today?"
- "Question: What's the weather like?"
- "Create event: Meeting tomorrow at 2 PM"
- "Find event: Doctor appointment"
- "Brainstorm marketing ideas" (starts creative voice session)
- "End brainstorm" (ends brainstorming session)

🧠 BRAINSTORMING FEATURE:
Start interactive voice conversations to explore ideas creatively:
- Say "Brainstorm [topic]" to start a focused session
- Say "Brainstorm" for open-ended creative thinking
- The AI will ask questions and help develop your ideas
- Say "End brainstorm" to finish the session
- Examples: "Brainstorm app features", "Brainstorm business ideas"

⚙️ GOOGLE CALENDAR SETUP:
The app needs access to your Google Calendar for scheduling features.
On first use, you'll be guided through a simple authentication process.

🔧 CUSTOMIZATION:
- Custom Commands: Add your own voice phrases
- Settings: Adjust voice sensitivity and preferences
- All your data stays on your computer

💡 TIPS:
- Speak clearly and wait for the microphone indicator
- Use the "Reset Speaker" button if voice recognition gets confused
- Check the "Custom Commands" tab to add your own phrases

🆘 SUPPORT:
If you encounter any issues:
1. Try restarting the application
2. Check your internet connection
3. Make sure your microphone is working

📊 USAGE:
This app uses AI services with reasonable daily limits:
- 30 minutes of voice transcription per day
- 50 AI questions per day
- Unlimited calendar operations

Enjoy your AI Voice Assistant! 🎉
"""
    
    def step_7_cleanup(self):
        """Clean up temporary files"""
        print("\n🧹 Step 7: Cleaning Up")
        print("-" * 40)
        
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print("✅ Cleaned up temporary files")
            
            if self.build_dir.exists():
                shutil.rmtree(self.build_dir)
                print("✅ Cleaned up build directory")
            
            return True
            
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
            return True  # Don't fail build on cleanup issues
    
    def build(self):
        """Execute the complete build process"""
        print(f"Building consumer distribution with embedded API keys...")
        print(f"This will create a ready-to-use executable for end users.\n")
        
        steps = [
            self.step_1_validate_environment,
            self.step_2_create_embedded_config,
            self.step_3_prepare_files,
            self.step_4_install_dependencies,
            self.step_5_build_executable,
            self.step_6_create_distribution_package,
            self.step_7_cleanup
        ]
        
        for i, step in enumerate(steps, 1):
            if not step():
                print(f"\n❌ Build failed at step {i}")
                return False
        
        print("\n" + "=" * 60)
        print("🎉 BUILD SUCCESSFUL!")
        print("=" * 60)
        print(f"📦 Distribution package created in: {self.dist_dir}")
        print(f"🚀 Users can now download and run the executable immediately!")
        print(f"💡 The executable contains your API keys and works without setup.")
        return True

if __name__ == "__main__":
    builder = ExecutableBuilder()
    success = builder.build()
    
    if success:
        print(f"\n✅ Ready for distribution!")
        print(f"📤 Upload the contents of the 'dist' folder to share with users.")
    else:
        print(f"\n❌ Build failed. Please check the errors above.")
        sys.exit(1) 