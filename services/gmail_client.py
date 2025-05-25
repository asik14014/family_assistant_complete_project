# services/gmail_client.py
import os
import pickle
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify"
]
TOKEN_PATH = "token_gmail.pickle"
CREDS_PATH = "credentials.json"


def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)


def send_email(to, subject, message_text, attachments: Optional[List[str]] = None):
    service = get_gmail_service()
    message = MIMEMultipart()
    message['to'] = to
    message['subject'] = subject
    message.attach(MIMEText(message_text, 'plain'))

    if attachments:
        for file_path in attachments:
            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={os.path.basename(file_path)}'
                )
                message.attach(part)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw}
    sent_message = service.users().messages().send(userId="me", body=body).execute()
    return sent_message.get("id")


def get_unread_email_summary(label_ids: List[str] = ['INBOX']):
    service = get_gmail_service()
    try:
        response = service.users().messages().list(userId="me", labelIds=label_ids, q="is:unread").execute()
        messages = response.get("messages", [])
        return f"You have {len(messages)} unread emails."
    except Exception as e:
        return f"Failed to fetch emails: {e}"
