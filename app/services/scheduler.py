from datetime import datetime, timedelta

def get_available_slots(opening_hours, busy_slots, service_duration, selected_date_obj, buffer=15):
    """
    opening_hours: ["09:00", "18:00"]
    busy_slots: lista di tuple (start, end)
    selected_date_obj: oggetto datetime.date (il giorno scelto dall'utente)
    """
    slots = []
    
    # 1. Definiamo i confini usando la data selezionata, non "now"
    try:
        day_start_str, day_end_str = opening_hours
    except (ValueError, TypeError):
        # Protezione se opening_hours non è una lista di 2 elementi
        return []

    # Creiamo il punto di inizio e fine per il GIORNO SCELTO
    current_time = datetime.combine(
        selected_date_obj, 
        datetime.strptime(day_start_str, "%H:%M").time()
    )
    end_working_day = datetime.combine(
        selected_date_obj, 
        datetime.strptime(day_end_str, "%H:%M").time()
    )

    now = datetime.now()

    # 2. Iteriamo sulla giornata
    while current_time + timedelta(minutes=service_duration) <= end_working_day:
        slot_start = current_time
        slot_end = current_time + timedelta(minutes=service_duration)
        
        is_free = True
        for b_start, b_end in busy_slots:
            # Rimuoviamo fuso orario per confronto
            if b_start.tzinfo: b_start = b_start.replace(tzinfo=None)
            if b_end.tzinfo: b_end = b_end.replace(tzinfo=None)
            
            # Controllo sovrapposizione
            if not (slot_end <= b_start or slot_start >= b_end):
                is_free = False
                break
        
        # Non mostrare slot passati (confronto con l'ora esatta di adesso)
        if is_free and slot_start > now:
            slots.append(slot_start.strftime("%H:%M"))
        
        # Avanzamento fisso di 30 min (o puoi usare service_duration)
        current_time += timedelta(minutes=30)
        
    return slots
