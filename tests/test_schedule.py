import os
import sys

# Ensure backend directory is in python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))
if backend_path not in sys.path:
    sys.path.append(backend_path)

# pyrefly: ignore [missing-import]
from schedule_engine import schedule_medication, time_to_minutes, minutes_to_time

def test_time_conversion():
    assert time_to_minutes("08:00") == 8 * 60
    assert time_to_minutes("13:30") == 13 * 60 + 30
    assert minutes_to_time(480) == "08:00"
    assert minutes_to_time(810) == "13:30"

def test_schedule_once_daily_no_conflict():
    # Test scheduling a single medication with no prior schedules
    existing = []
    scheduled_times = schedule_medication(
        new_med_name="Lipitor",
        frequency="Once daily",
        timing_constraint="Morning",
        patient_wake="08:00",
        patient_sleep="22:00",
        existing_schedules=existing
    )
    # Default Morning slot is wake + 30 mins -> 08:30
    assert len(scheduled_times) == 1
    assert scheduled_times[0] == "08:30"

def test_schedule_conflict_resolution_staggering():
    # Test conflict staggering: existing medication is scheduled at 08:30
    existing = [{"medication_name": "Warfarin", "time": "08:30"}]
    
    # Scheduling a new morning medication should overlap-check and shift by 30 mins -> 09:00
    scheduled_times = schedule_medication(
        new_med_name="Lisinopril",
        frequency="Once daily",
        timing_constraint="Morning",
        patient_wake="08:00",
        patient_sleep="22:00",
        existing_schedules=existing
    )
    assert len(scheduled_times) == 1
    assert scheduled_times[0] == "09:00"
