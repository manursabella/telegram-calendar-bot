import os
import pickle
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request

from config import GOOGLE_CLIENT_SECRET_FILE, GOOGLE_TOKEN_FILE, GOOGLE_SCOPES

def get_calendar_service():
    creds = None
    
    if os.path.exists(GOOGLE_TOKEN_FILE):
        with open(GOOGLE_TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CLIENT_SECRET_FILE, GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(GOOGLE_TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds)

def create_event(summary, description, start_time, end_time, recurrence_rule=None):
    try:
        service = get_calendar_service()
        
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'America/Argentina/Buenos_Aires',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'America/Argentina/Buenos_Aires',
            },
        }
        
        if recurrence_rule:
            event['recurrence'] = [recurrence_rule]
        
        event = service.events().insert(calendarId='primary', body=event).execute()
        return True, event.get('htmlLink')
    except HttpError as error:
        return False, str(error)

def list_events(max_results=10):
    try:
        service = get_calendar_service()
        now = datetime.utcnow().isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])
    except HttpError as error:
        return []

def delete_event(event_id):
    try:
        service = get_calendar_service()
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return True
    except HttpError:
        return False
