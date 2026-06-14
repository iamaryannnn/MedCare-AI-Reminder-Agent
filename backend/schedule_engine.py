from datetime import datetime, timedelta

def time_to_minutes(time_str: str) -> int:
    """Helper to convert HH:MM string to minutes from midnight."""
    try:
        h, m = map(int, time_str.split(":"))
        return h * 60 + m
    except ValueError:
        return 9 * 60  # Default to 09:00 if parsing fails

def minutes_to_time(minutes: int) -> str:
    """Helper to convert minutes from midnight to HH:MM string."""
    minutes = minutes % (24 * 60)
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

def calculate_initial_slots(frequency: str, timing_constraint: str, wake_min: int, sleep_min: int) -> list:
    """
    Determines initial draft times (in minutes from midnight) based on frequency and constraints.
    """
    freq_clean = frequency.lower().strip()
    constraint_clean = timing_constraint.lower().strip()

    # Define standard times
    breakfast = wake_min + 30          # 30 mins after wake
    lunch = wake_min + 330             # 5.5 hours after wake (e.g. 13:30 if wake is 08:00)
    dinner = sleep_min - 180           # 3 hours before sleep (e.g. 19:00 if sleep is 22:00)
    bedtime = sleep_min - 30           # 30 mins before sleep

    slots = []

    # Frequency-based divisions
    if "three" in freq_clean or "3x" in freq_clean:
        # 3 times a day
        slots = [breakfast, lunch, dinner]
    elif "twice" in freq_clean or "2x" in freq_clean:
        # 2 times a day
        slots = [breakfast, dinner]
    elif "once" in freq_clean or "1x" in freq_clean or "daily" in freq_clean:
        # 1 time a day
        if "morning" in constraint_clean:
            slots = [breakfast]
        elif "lunch" in constraint_clean or "afternoon" in constraint_clean:
            slots = [lunch]
        elif "dinner" in constraint_clean or "evening" in constraint_clean:
            slots = [dinner]
        elif "bed" in constraint_clean or "night" in constraint_clean:
            slots = [bedtime]
        else:
            slots = [breakfast]  # default to breakfast
    else:
        # Default fallback
        slots = [breakfast + 60]  # 1 hour after wake

    return slots

def schedule_medication(new_med_name: str, frequency: str, timing_constraint: str, 
                        patient_wake: str, patient_sleep: str, existing_schedules: list) -> list:
    """
    Computes optimal, conflict-free times for a new medication.
    
    :param new_med_name: Name of the medication to schedule
    :param frequency: How often it must be taken (e.g., "Once daily", "Twice daily", "Three times daily")
    :param timing_constraint: Timing rules (e.g., "With meals", "Before bed", "Morning", "None")
    :param patient_wake: Patient's wake time string (HH:MM)
    :param patient_sleep: Patient's sleep time string (HH:MM)
    :param existing_schedules: List of existing schedules, each a dict with {"medication_name": str, "time": str (HH:MM)}
    
    :return: A list of scheduled times (HH:MM strings)
    """
    wake_min = time_to_minutes(patient_wake)
    sleep_min = time_to_minutes(patient_sleep)
    
    # Adjust for sleep time rolling over past midnight
    if sleep_min <= wake_min:
        sleep_min += 24 * 60

    draft_slots = calculate_initial_slots(frequency, timing_constraint, wake_min, sleep_min)
    
    # Extract existing times in minutes from midnight for conflict checking
    existing_minutes = []
    for sched in existing_schedules:
        m = time_to_minutes(sched["time"])
        existing_minutes.append(m)

    final_slots = []
    conflict_buffer = 30  # Stagger slots by 30 minutes if they overlap

    for slot in draft_slots:
        current_time = slot
        # Avoid conflict by checking if any existing schedule is within 15 minutes
        while any(abs(current_time - ext) < 15 for ext in existing_minutes) or \
              any(abs(current_time - fn) < 15 for fn in final_slots):
            # Increment by 30 mins to stagger the dose
            current_time += conflict_buffer
            
            # If we go past sleep time, wrap around or stagger backwards
            if current_time > sleep_min:
                current_time = wake_min + (current_time % 30)  # reset to wake plus stagger offset
                
        final_slots.append(current_time)

    # Convert back to HH:MM format
    scheduled_times = [minutes_to_time(m) for m in final_slots]
    return scheduled_times
