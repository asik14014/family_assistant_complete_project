import os
import pickle
from datetime import datetime, timedelta
from typing import Optional, List
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_PATH = "token_calendar.pickle"
CREDS_PATH = "credentials_calendar.json"

def get_calendar_service():
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
    return build('calendar', 'v3', credentials=creds)

def create_event(summary: str, description: str, start_time: datetime, duration_minutes: int = 60, attendees: Optional[List[str]] = None):
    service = get_calendar_service()
    end_time = start_time + timedelta(minutes=duration_minutes)
    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'UTC'},
        'end': {'dateTime': end_time.isoformat(), 'timeZone': 'UTC'},
        'attendees': [{'email': email} for email in attendees] if attendees else [],
    }
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return created_event.get("id")

def get_upcoming_events(max_results: int = 10):
    service = get_calendar_service()
    now = datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary', timeMin=now,
        maxResults=max_results, singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    return [{
        'summary': e.get('summary'),
        'start': e['start'].get('dateTime', e['start'].get('date')),
        'id': e.get('id')
    } for e in events]

def update_event(event_id: str, summary: Optional[str] = None, description: Optional[str] = None):
    service = get_calendar_service()
    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    if summary:
        event['summary'] = summary
    if description:
        event['description'] = description
    updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
    return updated_event.get("id")

def delete_event(event_id: str):
    service = get_calendar_service()
    service.events().delete(calendarId='primary', eventId=event_id).execute()
    return f"Event {event_id} deleted."

def find_event_by_summary(search_summary: str, max_results: int = 10):
    events = get_upcoming_events(max_results)
    return [e for e in events if search_summary.lower() in (e['summary'] or '').lower()]
