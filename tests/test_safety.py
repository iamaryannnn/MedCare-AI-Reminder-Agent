import os
import sys

# Ensure backend directory is in python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))
if backend_path not in sys.path:
    sys.path.append(backend_path)

# pyrefly: ignore [missing-import]
from interaction_checker import verify_drug_safety

def test_safe_medication_list():
    meds = ["Metformin", "Lisinopril", "Lipitor"]
    safety_check = verify_drug_safety(meds)
    
    assert safety_check["is_safe"] is True
    assert len(safety_check["conflicts"]) == 0
    assert "Disclaimer" in safety_check["disclaimer"]

def test_conflicting_medication_list():
    # Warfarin and Ibuprofen are a known critical conflict pair
    meds = ["Warfarin", "Lisinopril", "Ibuprofen"]
    safety_check = verify_drug_safety(meds)
    
    assert safety_check["is_safe"] is False
    assert len(safety_check["conflicts"]) == 1
    conflict = safety_check["conflicts"][0]
    
    assert conflict["severity"] == "Critical"
    assert "bleeding" in conflict["description"].lower()
    assert {conflict["medication_a"].lower(), conflict["medication_b"].lower()} == {"warfarin", "ibuprofen"}
