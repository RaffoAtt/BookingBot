from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime

def get_calendar_service(creds_json):
    """Crea il client Google Calendar usando i token salvati."""
    creds = Credentials.from_authorized_user_info(creds_json)
    return build('calendar', 'v3', credentials=creds)

def fetch_busy_slots(creds_json, start_date):
    """Recupera gli eventi esistenti da Google per una data specifica."""
    service = get_calendar_service(creds_json)
    
    # Definiamo l'inizio e la fine del giorno in formato ISO (UTC)
    time_min = start_date.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
    time_max = start_date.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
    
    events_result = service.events().list(
        calendarId='primary', timeMin=time_min, timeMax=time_max,
        singleEvents=True, orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    busy = []
    for e in events:
        start = e['start'].get('dateTime') or e['start'].get('date')
        end = e['end'].get('dateTime') or e['end'].get('date')
        busy.append((datetime.fromisoformat(start.replace('Z', '+00:00')), 
                     datetime.fromisoformat(end.replace('Z', '+00:00'))))
    return busy

def create_event(creds_json, summary, start_time, end_time):
    """Crea l'appuntamento sul calendario del cliente."""
    service = get_calendar_service(creds_json)
    event = {
        'summary': summary,
        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Europe/Rome'},
        'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Europe/Rome'},
    }
    return service.events().insert(calendarId='primary', body=event).execute()
