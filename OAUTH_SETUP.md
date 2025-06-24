# Google OAuth2 Setup for Voice Assistant

This guide will help you set up OAuth2 authentication to replace the service account approach.

## 🔧 Prerequisites

1. A Google Cloud Project
2. Google Calendar API enabled
3. OAuth2 credentials configured

## 📋 Step-by-Step Setup

### Step 1: Create OAuth2 Credentials in Google Cloud Console

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Select your project** (or create a new one)
3. **Enable Google Calendar API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Calendar API"
   - Click on it and press "Enable"

4. **Create OAuth2 Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop application" as the application type
   - Give it a name (e.g., "Voice Assistant")
   - Click "Create"

5. **Download credentials**:
   - After creating, click the download button (⬇️) next to your OAuth client
   - Save the file as `client_secret.json` in your project directory

### Step 2: Configure OAuth2 Settings

1. **Set up OAuth consent screen** (if not already done):
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External" for user type (unless you have Google Workspace)
   - Fill in the required information:
     - App name: "Voice Assistant"
     - User support email: Your email
     - Developer contact information: Your email
   - Add scopes: `https://www.googleapis.com/auth/calendar`
   - Add test users (your email address)

2. **Authorized redirect URIs**:
   - In your OAuth2 client settings, add: `http://localhost:8080`

### Step 3: Install Dependencies

```bash
pip3 install google-auth-oauthlib google-auth-httplib2
```

### Step 4: File Structure

Your project should have these files:
```
AI-Voice-Assistant/
├── client_secret.json          # OAuth2 credentials (download from Google Cloud)
├── token.json                  # Auto-generated after first authentication
├── google_oauth.py            # OAuth2 authentication module
├── assistant.py               # Updated main application
├── assistantTools.py          # Updated calendar tools
└── ...
```

## 🔐 Security Notes

1. **Never commit `client_secret.json`** to version control
2. **Never commit `token.json`** to version control
3. Add both files to your `.gitignore`:
   ```
   client_secret.json
   token.json
   ```

## 🚀 How It Works

1. **First Run**: When you click "Sign In to Google", a browser window opens
2. **Authentication**: You sign in with your Google account and authorize calendar access
3. **Token Storage**: Your access/refresh tokens are saved locally in `token.json`
4. **Automatic Refresh**: Tokens are automatically refreshed when needed
5. **Primary Calendar**: The app accesses your primary Google Calendar

## 🔄 Key Differences from Service Account

| Aspect | Service Account | OAuth2 User Auth |
|--------|----------------|------------------|
| **Authentication** | Service account key file | User signs in with Google account |
| **Calendar Access** | Specific calendar by email | User's primary calendar |
| **Permissions** | Calendar shared with service account | User's own calendar data |
| **User Experience** | No user interaction needed | One-time sign-in per user |
| **Security** | Service account key management | OAuth2 flow, refresh tokens |

## 🛠️ Troubleshooting

### Common Issues:

1. **"Missing OAuth2 Credentials" Error**:
   - Ensure `client_secret.json` exists in your project directory
   - Verify the file was downloaded correctly from Google Cloud Console

2. **"Authorization Failed" Error**:
   - Check that your OAuth consent screen is configured
   - Verify you're added as a test user
   - Ensure the redirect URI `http://localhost:8080` is configured

3. **"Authentication Error" During Flow**:
   - Make sure port 8080 is available
   - Check your firewall settings
   - Try restarting the application

4. **API Quota Exceeded**:
   - Check your Google Cloud Console for API usage
   - Ensure you haven't exceeded daily limits

### Reset Authentication:
If you need to reset authentication, simply:
1. Click "Revoke Access" in the app, OR
2. Delete the `token.json` file

## 🔍 Testing

1. Start the Voice Assistant
2. Check authentication status (should show "Not Authenticated")
3. Click "Sign In to Google"
4. Complete the OAuth flow in your browser
5. Verify status changes to "Authenticated"
6. Test calendar voice commands

## 📧 Support

If you encounter issues:
1. Check the console output for error messages
2. Verify your Google Cloud Console settings
3. Ensure all required APIs are enabled
4. Check that OAuth2 credentials are properly configured 