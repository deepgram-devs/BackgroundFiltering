import os
import json
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import tkinter as tk
from tkinter import messagebox, simpledialog
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build

# OAuth 2.0 configuration
SCOPES = ['https://www.googleapis.com/auth/calendar']
CLIENT_SECRETS_FILE = 'client_secret.json'  # OAuth2 credentials file
TOKEN_FILE = 'token.json'  # Stored user credentials
REDIRECT_URI = 'http://localhost:8080'

class OAuthHandler(BaseHTTPRequestHandler):
    """HTTP server handler for OAuth2 callback"""
    
    def do_GET(self):
        """Handle GET request from OAuth2 callback"""
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        if 'code' in query_params:
            # Store the authorization code
            self.server.auth_code = query_params['code'][0]
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html_content = '''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Authentication Successful - AI Voice Assistant</title>
                    <style>
                        * {
                            margin: 0;
                            padding: 0;
                            box-sizing: border-box;
                        }
                        
                        body {
                            font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
                            background: #0d1117;
                            color: #f0f6fc;
                            min-height: 100vh;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            padding: 20px;
                        }
                        
                        .container {
                            background: #21262d;
                            border: 1px solid #30363d;
                            border-radius: 12px;
                            padding: 40px;
                            text-align: center;
                            max-width: 500px;
                            width: 100%;
                            box-shadow: 0 16px 32px rgba(0, 0, 0, 0.4);
                        }
                        
                        .header {
                            background: #161b22;
                            margin: -40px -40px 30px -40px;
                            padding: 20px 40px;
                            border-radius: 12px 12px 0 0;
                            border-bottom: 1px solid #30363d;
                        }
                        
                        .app-title {
                            font-size: 18px;
                            font-weight: 600;
                            color: #f0f6fc;
                            margin: 0;
                        }
                        
                        .app-subtitle {
                            font-size: 12px;
                            color: #8b949e;
                            margin-top: 5px;
                        }
                        
                        .success-icon {
                            font-size: 64px;
                            margin-bottom: 20px;
                            animation: bounce 0.8s ease-in-out;
                        }
                        
                        @keyframes bounce {
                            0%, 20%, 50%, 80%, 100% { 
                                transform: translateY(0) scale(1); 
                            }
                            40% { 
                                transform: translateY(-10px) scale(1.1); 
                            }
                            60% { 
                                transform: translateY(-5px) scale(1.05); 
                            }
                        }
                        
                        h1 {
                            font-size: 24px;
                            font-weight: 600;
                            color: #3fb950;
                            margin-bottom: 15px;
                        }
                        
                        .status-badge {
                            display: inline-flex;
                            align-items: center;
                            background: #238636;
                            color: #f0f6fc;
                            padding: 6px 12px;
                            border-radius: 20px;
                            font-size: 14px;
                            font-weight: 500;
                            margin-bottom: 20px;
                        }
                        
                        .message {
                            font-size: 16px;
                            line-height: 1.5;
                            color: #e6edf3;
                            margin-bottom: 25px;
                        }
                        
                        .features {
                            background: #0d1117;
                            border: 1px solid #30363d;
                            border-radius: 8px;
                            padding: 20px;
                            margin: 20px 0;
                            text-align: left;
                        }
                        
                        .features h3 {
                            color: #f0f6fc;
                            font-size: 14px;
                            font-weight: 600;
                            margin-bottom: 12px;
                            text-align: center;
                        }
                        
                        .feature-list {
                            list-style: none;
                            padding: 0;
                        }
                        
                        .feature-list li {
                            color: #8b949e;
                            font-size: 14px;
                            margin-bottom: 8px;
                            padding-left: 20px;
                            position: relative;
                        }
                        
                        .feature-list li:before {
                            content: "✓";
                            color: #3fb950;
                            font-weight: bold;
                            position: absolute;
                            left: 0;
                        }
                        
                        .close-btn {
                            background: #238636;
                            color: #f0f6fc;
                            border: none;
                            padding: 12px 24px;
                            border-radius: 6px;
                            font-size: 14px;
                            font-weight: 500;
                            cursor: pointer;
                            transition: all 0.2s ease;
                            margin-top: 10px;
                        }
                        
                        .close-btn:hover {
                            background: #2ea043;
                            transform: translateY(-1px);
                        }
                        
                        .close-btn:active {
                            transform: translateY(0);
                        }
                        
                        .auto-close {
                            font-size: 12px;
                            color: #8b949e;
                            margin-top: 15px;
                        }
                        
                        .countdown {
                            color: #1f6feb;
                            font-weight: 600;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div class="app-title">🎤 AI Voice Assistant</div>
                            <div class="app-subtitle">Powered by Deepgram & OpenAI</div>
                        </div>
                        
                        <div class="success-icon">🎉</div>
                        
                        <h1>Authentication Successful!</h1>
                        
                        <div class="status-badge">
                            ✅ Google Calendar Connected
                        </div>
                        
                        <div class="message">
                            Your AI Voice Assistant is now connected to Google Calendar and ready to help manage your schedule.
                        </div>
                        
                        <div class="features">
                            <h3>🚀 Available Features</h3>
                            <ul class="feature-list">
                                <li>View today's and weekly events</li>
                                <li>Create events with voice commands</li>
                                <li>Find free time slots</li>
                                <li>Search and manage calendar events</li>
                                <li>Move and reschedule events</li>
                            </ul>
                        </div>
                        
                        <button class="close-btn" onclick="window.close()">
                            🔙 Return to Voice Assistant
                        </button>
                        
                        <div class="auto-close">
                            This window will close automatically in <span class="countdown" id="countdown">5</span> seconds
                        </div>
                    </div>
                    
                    <script>
                        // Countdown timer
                        let timeLeft = 5;
                        const countdownElement = document.getElementById('countdown');
                        
                        const timer = setInterval(() => {
                            timeLeft--;
                            countdownElement.textContent = timeLeft;
                            
                            if (timeLeft <= 0) {
                                clearInterval(timer);
                                window.close();
                            }
                        }, 1000);
                        
                        // Close on Escape key
                        document.addEventListener('keydown', function(event) {
                            if (event.key === 'Escape') {
                                window.close();
                            }
                        });
                    </script>
                </body>
                </html>
            '''
            
            self.wfile.write(html_content.encode('utf-8'))
        elif 'error' in query_params:
            # Handle authorization error
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f'''
                <html>
                <body>
                <h1>Authorization Failed</h1>
                <p>Error: {query_params['error'][0]}</p>
                </body>
                </html>
            '''.encode())
        
        # Shutdown the server after handling the request
        threading.Thread(target=self.server.shutdown).start()
    
    def log_message(self, format, *args):
        """Suppress server logs"""
        pass

class GoogleOAuth:
    """Google OAuth2 authentication manager"""
    
    def __init__(self):
        self.credentials = None
        self.service = None
        self.flow = None
        
    def load_existing_credentials(self):
        """Load existing user credentials from token file"""
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'r') as token_file:
                    token_data = json.load(token_file)
                
                self.credentials = google.oauth2.credentials.Credentials.from_authorized_user_info(
                    token_data, SCOPES
                )
                
                # Check if credentials are valid
                if self.credentials and self.credentials.valid:
                    self.service = build('calendar', 'v3', credentials=self.credentials)
                    return True
                elif self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    # Try to refresh the token
                    try:
                        self.credentials.refresh(google.auth.transport.requests.Request())
                        self.save_credentials()
                        self.service = build('calendar', 'v3', credentials=self.credentials)
                        return True
                    except Exception as e:
                        print(f"Error refreshing token: {e}")
                        return False
            except Exception as e:
                print(f"Error loading existing credentials: {e}")
                return False
        return False
    
    def save_credentials(self):
        """Save user credentials to token file"""
        if self.credentials:
            with open(TOKEN_FILE, 'w') as token_file:
                token_file.write(self.credentials.to_json())
    
    def authenticate_user(self):
        """Authenticate user using OAuth2 flow with embedded credentials"""
        try:
            # Import embedded config
            from embedded_config import EmbeddedConfig
            
            # Get embedded credentials using the new method
            client_id, client_secret = EmbeddedConfig.get_google_credentials()
            
            if not client_id or not client_secret:
                # No embedded credentials available
                messagebox.showerror(
                    "Google OAuth Not Available", 
                    "Google Calendar integration is not available in this build.\n\n"
                    "The application will work without calendar features.\n"
                    "You can still use voice commands, AI questions, and brainstorming."
                )
                return False
            
            # Use embedded credentials to create OAuth flow
            print("🔑 Using embedded Google OAuth credentials")
            client_config = {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [REDIRECT_URI]
                }
            }
            
            self.flow = google_auth_oauthlib.flow.Flow.from_client_config(
                client_config,
                scopes=SCOPES
            )
            
            self.flow.redirect_uri = REDIRECT_URI
            
            # Generate authorization URL
            auth_url, _ = self.flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'  # Force consent screen to get refresh token
            )
            
            # Show instructions to user
            result = messagebox.askquestion(
                "Google Authentication Required",
                "You need to authorize access to your Google Calendar.\n\n"
                "A web browser will open for authentication.\n"
                "After authorization, return to this application.\n\n"
                "Continue?",
                icon='question'
            )
            
            if result != 'yes':
                return False
            
            # Start local server to handle callback
            server = HTTPServer(('localhost', 8080), OAuthHandler)
            server.auth_code = None
            
            # Open browser for authentication
            webbrowser.open(auth_url)
            
            # Handle the callback (this will block until callback is received)
            print("Waiting for Google authentication...")
            server.handle_request()
            
            if not hasattr(server, 'auth_code') or not server.auth_code:
                messagebox.showerror("Authentication Failed", "No authorization code received.")
                return False
            
            # Exchange authorization code for credentials
            self.flow.fetch_token(code=server.auth_code)
            self.credentials = self.flow.credentials
            
            # Save credentials for future use
            self.save_credentials()
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=self.credentials)
            
            messagebox.showinfo("Success", "Google Calendar authentication successful!")
            return True
            
        except Exception as e:
            messagebox.showerror("Authentication Error", f"Error during authentication: {str(e)}")
            return False
    
    def get_service(self):
        """Get authenticated Google Calendar service"""
        if not self.service:
            # Try to load existing credentials first
            if not self.load_existing_credentials():
                # If no valid credentials, authenticate user
                if not self.authenticate_user():
                    return None
        return self.service
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        return self.service is not None
    
    def revoke_credentials(self):
        """Revoke and clear stored credentials"""
        if self.credentials:
            try:
                # Revoke the token
                import google.oauth2.utils
                google.oauth2.utils.revoke_token(self.credentials.token)
            except:
                pass  # Ignore errors during revocation
        
        # Clear stored credentials
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        
        self.credentials = None
        self.service = None
        
        messagebox.showinfo("Success", "Google Calendar access has been revoked.")

# Global OAuth manager instance
oauth_manager = GoogleOAuth()

def get_calendar_service():
    """Get authenticated Google Calendar service"""
    return oauth_manager.get_service()

def is_authenticated():
    """Check if user is authenticated"""
    return oauth_manager.is_authenticated()

def authenticate():
    """Trigger user authentication"""
    return oauth_manager.authenticate_user()

def revoke_access():
    """Revoke user access"""
    oauth_manager.revoke_credentials() 