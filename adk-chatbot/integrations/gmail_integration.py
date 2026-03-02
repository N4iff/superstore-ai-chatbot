"""
Gmail Integration - Send approved reports via email
"""
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
from config.settings import GMAIL_RECIPIENT_EMAIL


# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def get_gmail_service():
    """
    Get authenticated Gmail service
    
    Returns:
        Gmail API service object
    """
    creds = None
    token_path = 'token.pickle'
    
    # Load existing credentials
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # This will open browser for OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(
                'gmail_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)


def send_report_email(report_html: str, subject: str = "BI Analytics Report") -> bool:
    """
    Send report via Gmail
    
    Args:
        report_html: The HTML report content
        subject: Email subject line
        
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        service = get_gmail_service()
        
        # Create email
        message = MIMEMultipart('alternative')
        message['To'] = GMAIL_RECIPIENT_EMAIL
        message['Subject'] = subject
        
        # Add HTML email template
        html_body = f"""
<html>
<head>
<style>
body {{ 
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
    line-height: 1.8; 
    color: #2c3e50; 
    background-color: #f4f4f4; 
    padding: 20px; 
}}
.container {{ 
    max-width: 800px; 
    margin: 0 auto; 
    background: white; 
    padding: 40px; 
    border-radius: 8px; 
    box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
}}
h1 {{ 
    color: #2c3e50; 
    border-bottom: 3px solid #3498db; 
    padding-bottom: 15px; 
    margin-bottom: 30px; 
    font-size: 24px; 
}}
h2 {{ 
    color: #34495e; 
    margin-top: 35px; 
    margin-bottom: 15px; 
    font-size: 18px; 
    border-left: 4px solid #3498db; 
    padding-left: 15px; 
}}
.metric-group {{ 
    margin-left: 25px; 
    margin-bottom: 20px; 
    padding: 15px; 
    background: #f8f9fa; 
    border-radius: 5px; 
}}
hr {{ 
    border: none; 
    border-top: 1px solid #e0e0e0; 
    margin: 30px 0; 
}}
.footer {{ 
    margin-top: 40px; 
    padding-top: 20px; 
    border-top: 2px solid #ecf0f1; 
    font-size: 12px; 
    color: #95a5a6; 
    text-align: center; 
}}
</style>
</head>
<body>
<div class="container">
{report_html}
<div class="footer">
This report was generated automatically by BI Analytics System
</div>
</div>
</body>
</html>
        """
        
        html_part = MIMEText(html_body, 'html')
        message.attach(html_part)
        
        # Encode and send
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        send_message = {'raw': raw_message}
        
        service.users().messages().send(userId='me', body=send_message).execute()
        
        print(f"✅ Email sent successfully to {GMAIL_RECIPIENT_EMAIL}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False