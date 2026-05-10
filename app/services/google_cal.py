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

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta

def create_event(biz_creds, booking, service_name):
    """
    biz_creds: i dati JSON salvati nel DB dopo l'autenticazione
    booking: l'oggetto Booking dal tuo database
    """
    # Trasforma i dati del DB in credenziali valide
    creds = Credentials.from_authorized_user_info(biz_creds)
    service = build('calendar', 'v3', credentials=creds)

    # Formatta le date per Google (ISO 8601)
    # Uniamo booking_date e start_time
    start_dt = datetime.combine(booking.booking_date, booking.start_time)
    end_dt = datetime.combine(booking.booking_date, booking.end_time)

    event = {
        'summary': f'Prenotazione: {booking.customer_name}',
        'location': 'Tua Sede',
        'description': f'Servizio: {service_name}',
        'start': {
            'dateTime': start_dt.isoformat(),
            'timeZone': 'Europe/Rome',
        },
        'end': {
            'dateTime': end_dt.isoformat(),
            'timeZone': 'Europe/Rome',
        },
        'reminders': {
            'useDefault': True,
        },
    }

    try:
        event_result = service.events().insert(calendarId='primary', body=event).execute()
        return event_result.get('id')
    except Exception as e:
        print(f"Errore Google Calendar: {e}")
        return None
