from datetime import datetime, timedelta

def get_available_slots(opening_hours, busy_slots, service_duration, buffer=15):
    """
    Calcola gli slot disponibili.
    opening_hours: ["09:00", "18:00"]
    busy_slots: lista di tuple (start, end) da google_cal
    service_duration: durata in minuti
    """
    slots = []
    
    # 1. Definiamo i confini della giornata lavorativa
    day_start_str, day_end_str = opening_hours
    # Esempio semplificato: assumiamo che start_date sia oggi
    now = datetime.now()
    current_time = now.replace(hour=int(day_start_str[:2]), minute=int(day_start_str[3:]), second=0, microsecond=0)
    end_working_day = now.replace(hour=int(day_end_str[:2]), minute=int(day_end_str[3:]), second=0, microsecond=0)

    # 2. Iteriamo sulla giornata
    while current_time + timedelta(minutes=service_duration) <= end_working_day:
        slot_start = current_time
        slot_end = current_time + timedelta(minutes=service_duration)
        
        # 3. Verifichiamo se lo slot collide con eventi Google
        is_free = True
        for b_start, b_end in busy_slots:
            # Rimuoviamo il fuso orario per il confronto se necessario
            b_start = b_start.replace(tzinfo=None)
            b_end = b_end.replace(tzinfo=None)
            
            # Condizione di sovrapposizione
            if not (slot_end <= b_start or slot_start >= b_end):
                is_free = False
                break
        
        if is_free and slot_start > datetime.now(): # Non mostrare slot nel passato
            slots.append(slot_start.strftime("%H:%M"))
        
        # 4. Avanziamo (es. di 30 minuti o della durata servizio + buffer)
        current_time += timedelta(minutes=30)
        
    return slots
