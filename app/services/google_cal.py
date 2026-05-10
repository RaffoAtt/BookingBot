import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Gli SCOPES devono corrispondere a quelli messi nella Google Console
SCOPES = ['https://www.googleapis.com/auth/calendar.events', 'https://www.googleapis.com/auth/calendar.readonly']
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

def get_flow():
    """Configura il flusso di autenticazione usando le variabili d'ambiente di Railway."""
    client_config = {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    # Creiamo il flow specificando esplicitamente il redirect_uri
    return Flow.from_client_config(
        client_config,
        scopes=['https://www.googleapis.com/auth/calendar.events', 'https://www.googleapis.com/auth/calendar.readonly'],
        redirect_uri=REDIRECT_URI
    )

def get_auth_url():
    flow = get_flow()
    # Genera l'URL. Google richiede state per sicurezza.
    auth_url, state = flow.authorization_url(prompt='consent', access_type='offline')
    return auth_url

def fetch_token(code):
    flow = get_flow()
    # Fondamentale: fetch_token deve ricostruire lo stesso contesto
    flow.fetch_token(code=code)
    creds = flow.credentials
    return {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }

def get_calendar_service(creds_json):
    """Crea il client Google Calendar usando i token salvati."""
    creds = Credentials.from_authorized_user_info(creds_json)
    return build('calendar', 'v3', credentials=creds)

def fetch_busy_slots(creds_json, start_date):
    """Recupera gli impegni esistenti per non sovrapporre prenotazioni."""
    try:
        service = get_calendar_service(creds_json)
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
            busy.append((
                datetime.fromisoformat(start.replace('Z', '+00:00')).replace(tzinfo=None), 
                datetime.fromisoformat(end.replace('Z', '+00:00')).replace(tzinfo=None)
            ))
        return busy
    except Exception as e:
        print(f"Errore fetch_busy_slots: {e}")
        return []

def create_event(biz_creds, booking, service_name):
    """Crea l'evento sul calendario dopo la prenotazione."""
    try:
        service = get_calendar_service(biz_creds)
        start_dt = datetime.combine(booking.booking_date, booking.start_time)
        end_dt = datetime.combine(booking.booking_date, booking.end_time)

        event = {
            'summary': f'Booking: {booking.customer_name}',
            'description': f'Servizio: {service_name}\nTel: {booking.customer_phone}',
            'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Europe/Rome'},
            'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Europe/Rome'},
        }

        result = service.events().insert(calendarId='primary', body=event).execute()
        return result.get('id')
    except Exception as e:
        print(f"Errore creazione evento Google: {e}")
        return None
