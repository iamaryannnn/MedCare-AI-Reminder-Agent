import os
import sys

# Ensure backend directory is in python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))
if backend_path not in sys.path:
    sys.path.append(backend_path)

# pyrefly: ignore [missing-import]
from ai_agent import parse_fallback_regex, parse_medication_nlp

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
