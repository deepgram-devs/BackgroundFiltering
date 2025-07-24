#!/usr/bin/env python3
"""
Sierra Voice Filter - Demo Setup Script
Quick setup for the voice diarization and filtering demo
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header():
    """Print Sierra branding header"""
    print("=" * 60)
    print("🎯 SIERRA VOICE FILTER - Demo Setup")
    print("=" * 60)
    print("🎤 Speaker Diarization & Voice Filtering Demo")
    print("🔒 Focus on voice locking and filtering technology")
    print("🎨 Sierra AI branded interface")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required. Please upgrade Python.")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    requirements_file = Path("sierra_requirements.txt")
    if not requirements_file.exists():
        print("❌ sierra_requirements.txt not found!")
        print("Please ensure sierra_requirements.txt is in the current directory.")
        return False
    
    try:
        # Install dependencies
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "sierra_requirements.txt"
        ], capture_output=True, text=True, check=True)
        
        print("✅ Dependencies installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("Error output:")
        print(e.stderr)
        return False

def check_env_file():
    """Check if .env file exists and help create it"""
    print("\n🔑 Checking environment configuration...")
    
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
        # Check if it has the required key
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                if "DEEPGRAM_API_KEY" in content and not content.find("your_deepgram_api_key_here"):
                    print("✅ Deepgram API key appears to be configured")
                    return True
                else:
                    print("⚠️ .env file exists but API key may not be set properly")
        except Exception as e:
            print(f"⚠️ Error reading .env file: {e}")
    
    print("❌ .env file missing or incomplete")
    print("\n📝 Creating .env file...")
    
    # Create .env file
    env_content = """# Sierra Voice Filter Configuration
# Get your API key from: https://console.deepgram.com/

DEEPGRAM_API_KEY=your_deepgram_api_key_here
"""
    
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ .env file created!")
        print("\n🔧 IMPORTANT: Edit .env file and add your Deepgram API key")
        print("   1. Visit: https://console.deepgram.com/")
        print("   2. Create account (free credits available)")
        print("   3. Copy your API key") 
        print("   4. Replace 'your_deepgram_api_key_here' in .env file")
        return False  # Return False because user needs to add API key
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def test_audio():
    """Test if audio system is working"""
    print("\n🎤 Testing audio system...")
    
    try:
        import pyaudio
        
        # Try to initialize PyAudio
        p = pyaudio.PyAudio()
        
        # Check for input devices
        device_count = p.get_device_count()
        input_devices = []
        
        for i in range(device_count):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices.append(device_info['name'])
        
        p.terminate()
        
        if input_devices:
            print(f"✅ Audio system working! Found {len(input_devices)} input device(s)")
            print(f"   Default input device: {input_devices[0]}")
            return True
        else:
            print("❌ No audio input devices found")
            return False
            
    except ImportError:
        print("⚠️ PyAudio not installed - will be installed with dependencies")
        return True
    except Exception as e:
        print(f"⚠️ Audio system warning: {e}")
        return True

def check_demo_file():
    """Check if main demo file exists"""
    print("\n📄 Checking demo files...")
    
    demo_file = Path("sierra_voice_filter.py")
    if demo_file.exists():
        print("✅ Sierra Voice Filter demo file found")
        return True
    else:
        print("❌ sierra_voice_filter.py not found!")
        print("Please ensure sierra_voice_filter.py is in the current directory.")
        return False

def print_next_steps(api_key_needed=False):
    """Print next steps for user"""
    print("\n" + "=" * 60)
    print("🎯 SETUP COMPLETE - Next Steps:")
    print("=" * 60)
    
    if api_key_needed:
        print("1. 🔑 Add your Deepgram API key to .env file:")
        print("   - Visit https://console.deepgram.com/")
        print("   - Create account (free credits available)")
        print("   - Copy API key and paste into .env file")
        print()
        print("2. 🚀 Run the demo:")
        print("   python sierra_voice_filter.py")
    else:
        print("🚀 Ready to run! Start the demo with:")
        print("   python sierra_voice_filter.py")
    
    print("\n🎤 Demo Features:")
    print("   - Real-time speaker diarization")
    print("   - Voice locking (first speaker)")
    print("   - Live filtering of other voices")
    print("   - Terminal showing filtering activity")
    print("   - Sierra AI branded interface")
    
    print("\n🔧 Usage Tips:")
    print("   - Speak clearly for best results")
    print("   - First person to speak gets voice lock")
    print("   - Use 'Reset Speaker Lock' to change speakers")
    print("   - Say 'exit sierra' to stop demo")
    
    print("\n" + "=" * 60)

def main():
    """Main setup function"""
    print_header()
    
    # Step 1: Check Python version
    if not check_python_version():
        return 1
    
    # Step 2: Check demo file exists
    if not check_demo_file():
        return 1
    
    # Step 3: Install dependencies
    if not install_dependencies():
        return 1
    
    # Step 4: Test audio system
    test_audio()
    
    # Step 5: Check/create .env file
    api_key_needed = not check_env_file()
    
    # Step 6: Show next steps
    print_next_steps(api_key_needed)
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 