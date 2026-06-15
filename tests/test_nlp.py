import os
import sys

# Ensure backend directory is in python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))
if backend_path not in sys.path:
    sys.path.append(backend_path)

# pyrefly: ignore [missing-import]
from ai_agent import parse_fallback_regex, parse_medication_nlp, run_agent_chat

def test_fallback_regex_metformin():
    text = "Please add Metformin 500mg twice daily with meals"
    extracted = parse_fallback_regex(text)
    
    assert extracted["name"] == "Metformin"
    assert extracted["dosage"] == "500mg"
    assert extracted["frequency"] == "Twice daily"
    assert extracted["timing_constraint"] == "With meals"

def test_fallback_regex_lipitor():
    text = "I need to take Lipitor 20mg once daily before bed"
    extracted = parse_fallback_regex(text)
    
    assert extracted["name"] == "Lipitor"
    assert extracted["dosage"] == "20mg"
    assert extracted["frequency"] == "Once daily"
    assert extracted["timing_constraint"] == "Before bed"

def test_fallback_regex_aspirin():
    text = "Take Aspirin 81mg three times a day"
    extracted = parse_fallback_regex(text)
    
    assert extracted["name"] == "Aspirin"
    assert extracted["dosage"] == "81mg"
    assert extracted["frequency"] == "Three times daily"
    assert extracted["timing_constraint"] == "None"

def test_fallback_regex_simple_split():
    # Test simple split fallback logic for non-matching patterns
    text = "Take one capsule of Metformin 500mg daily"
    extracted = parse_fallback_regex(text)
    
    # Simple split fallback looks for digits and grabs the word before as the name
    assert extracted["name"] == "Metformin"
    assert "500mg" in extracted["dosage"]
    assert extracted["frequency"] == "Once daily"

def test_parse_medication_nlp_offline_mode():
    # With no API key configured, parse_medication_nlp should fall back to regex
    text = "Please add Lisinopril 10mg once daily in the morning"
    extracted = parse_medication_nlp(text)
    
    assert extracted["name"] == "Lisinopril"
    assert extracted["dosage"] == "10mg"
    assert extracted["frequency"] == "Once daily"
    assert extracted["timing_constraint"] == "Morning"

def test_run_agent_chat_missed_dose():
    meds = [{"name": "Metformin", "dosage": "500mg", "frequency": "Twice daily", "timing_constraint": "With meals", "schedules": ["09:00", "21:00"]}]
    resp = run_agent_chat("Margaret", "English", meds, 85.0, "I missed my Metformin dose by 2 hours. What should I do?")
    assert "safe to take" in resp.lower() or "take it now" in resp.lower()
    assert "Disclaimer" in resp

def test_run_agent_chat_safety_conflict():
    meds = [
        {"name": "Warfarin", "dosage": "5mg", "frequency": "Once daily", "timing_constraint": "Before bed", "schedules": ["21:00"]},
        {"name": "Ibuprofen", "dosage": "400mg", "frequency": "Once daily", "timing_constraint": "Morning", "schedules": ["09:00"]}
    ]
    resp = run_agent_chat("Margaret", "English", meds, 80.0, "Is my medication list safe? Check for any drug interactions.")
    assert "critical warning" in resp.lower() or "mixing warfarin" in resp.lower()
    assert "Disclaimer" in resp

def test_run_agent_chat_schedule():
    meds = [{"name": "Metformin", "dosage": "500mg", "frequency": "Once daily", "timing_constraint": "Morning", "schedules": ["08:30"]}]
    resp = run_agent_chat("Margaret", "English", meds, 90.0, "What is my current medication schedule?")
    assert "metformin" in resp.lower()
    assert "08:30" in resp

def test_run_agent_chat_adherence():
    meds = []
    resp = run_agent_chat("Margaret", "English", meds, 94.5, "Can you tell me my adherence compliance score?")
    assert "94.5" in resp

def test_run_agent_chat_default_greeting():
    meds = []
    resp = run_agent_chat("Margaret", "English", meds, 100.0, "Hello!")
    assert "assist" in resp.lower() or "help" in resp.lower()

