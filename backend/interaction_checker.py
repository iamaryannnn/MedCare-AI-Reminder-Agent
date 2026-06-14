# Mock Clinical Drug-Drug Interaction Database

INTERACTIONS = {
    ("warfarin", "ibuprofen"): {
        "severity": "Critical",
        "description": "Ibuprofen increases the blood-thinning effect of Warfarin, significantly raising the risk of gastrointestinal bleeding."
    },
    ("warfarin", "aspirin"): {
        "severity": "High",
        "description": "Co-administration of Aspirin and Warfarin increases overall bleeding risk. Monitor clotting markers closely."
    },
    ("lisinopril", "spironolactone"): {
        "severity": "High",
        "description": "Concurrent use may lead to severe hyperkalemia (dangerous levels of potassium in the blood)."
    },
    ("metformin", "contrast dye"): {
        "severity": "Moderate",
        "description": "Lactic acidosis risk. Temporarily suspend Metformin prior to or at the time of iodinated contrast imaging procedures."
    },
    ("sildenafil", "nitroglycerin"): {
        "severity": "Critical",
        "description": "Life-threatening hypotension risk. Nitroglycerin and other nitrates must never be taken with Sildenafil."
    },
    ("simvastatin", "amiodarone"): {
        "severity": "Moderate",
        "description": "Amiodarone increases Simvastatin concentrations, escalating the risk of myopathy and muscle breakdown."
    }
}

MEDICAL_DISCLAIMER = (
    "Disclaimer: MedCare AI is an assistive decision-support tool. It does not replace professional medical advice. "
    "Please consult your healthcare provider or physician before starting or modifying any treatment plan."
)

def verify_drug_safety(med_list: list) -> dict:
    """
    Checks a list of medications for safety conflicts.
    
    :param med_list: List of medication name strings (e.g., ["Warfarin", "Ibuprofen", "Metformin"])
    :return: Dict containing safety assessment details
    """
    # Normalize drug names (strip whitespace and lowercase)
    normalized_meds = [med.strip().lower() for med in med_list if med]
    found_conflicts = []

    for i in range(len(normalized_meds)):
        for j in range(i + 1, len(normalized_meds)):
            med1 = normalized_meds[i]
            med2 = normalized_meds[j]

            # Check both permutation pairs in database
            pair1 = (med1, med2)
            pair2 = (med2, med1)

            conflict_details = None
            if pair1 in INTERACTIONS:
                conflict_details = INTERACTIONS[pair1]
                matched_pair = (med_list[i], med_list[j])
            elif pair2 in INTERACTIONS:
                conflict_details = INTERACTIONS[pair2]
                matched_pair = (med_list[j], med_list[i])

            if conflict_details:
                found_conflicts.append({
                    "medication_a": matched_pair[0],
                    "medication_b": matched_pair[1],
                    "severity": conflict_details["severity"],
                    "description": conflict_details["description"]
                })

    is_safe = len(found_conflicts) == 0

    return {
        "is_safe": is_safe,
        "conflicts": found_conflicts,
        "disclaimer": MEDICAL_DISCLAIMER
    }
