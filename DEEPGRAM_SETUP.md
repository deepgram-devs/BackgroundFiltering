# Deepgram Nova-3 Setup Guide

## 🚀 Quick Setup

### 1. Get Your Deepgram API Key
1. Go to [Deepgram Console](https://console.deepgram.com/)
2. Sign up for a free account (includes $200 in free credits)
3. Navigate to "API Keys" in the dashboard
4. Create a new API key and copy it

### 2. Set Up Environment Variables
Create a `.env` file in your project root:

```bash
# .env file
DEEPGRAM_API_KEY=your_deepgram_api_key_here
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python assistant.py
```

## 🎯 Features

- **Nova-3 Model**: Latest Deepgram speech-to-text model
- **Real-time Transcription**: Live audio streaming
- **High Accuracy**: Optimized for conversational AI
- **Smart Formatting**: Automatic punctuation and capitalization

## 🔧 Configuration Options

The current setup uses:
- **Model**: `nova-2` (you can change to `nova-3` when available)
- **Language**: English (US)
- **Sample Rate**: 16kHz
- **Channels**: Mono
- **Format**: Linear16

## 💡 Usage Tips

1. **Clear Speech**: Speak clearly and at normal pace
2. **Quiet Environment**: Minimize background noise
3. **Microphone**: Use a good quality microphone for best results
4. **Commands**: Say commands like "Question", "When am I free today?", etc.

## 🔍 Troubleshooting

- **API Key Issues**: Make sure your `.env` file is in the project root
- **Audio Issues**: Check microphone permissions
- **Connection Issues**: Verify internet connection and API key validity 