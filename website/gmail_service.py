""" This module provides a function to send an email using the Gmail API. """
from __future__ import print_function
import os
import base64
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_credentials():
    """Get Gmail API credentials.
    Returns:
        google.oauth2.credentials.Credentials: The credentials object.
    """
    creds = None
    # Get the current working directory
    cwd = os.path.dirname(os.path.abspath(__file__))
    credentials_path = os.path.join(cwd, 'credentials.json')
    token_path = os.path.join(cwd, 'token.json')
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                os.remove(token_path)
                return get_credentials()
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    return creds

def send_email(to, subject, body):
    """Send an email using the Gmail API.
    Args:
        to (str): The recipient's email address.
        subject (str): The email subject.
        body (str): The email body.
    """
    service = build('gmail', 'v1', credentials=get_credentials())
    
    message = MIMEMultipart()
    message['to'] = to
    message['subject'] = subject
    message.attach(MIMEText(body, 'plain'))
    
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    message = service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
    print(f"Message Id: {message['id']}")
