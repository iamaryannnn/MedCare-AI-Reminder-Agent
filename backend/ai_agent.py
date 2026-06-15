import os
import json
import re
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from langchain_core.prompts import ChatPromptTemplate
# pyrefly: ignore [missing-import]
from langchain_openai import ChatOpenAI, AzureChatOpenAI

load_dotenv()

def get_llm():
    """
    Initializes the LLM, prioritizing Azure OpenAI, falling back to standard OpenAI,
    and returning None if credentials are missing to trigger graceful degradation.
    """
    # 1. Try Azure OpenAI
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if azure_key and azure_endpoint:
        try:
            return AzureChatOpenAI(
                azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
                openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
                azure_endpoint=azure_endpoint,
                api_key=azure_key,
                temperature=0.7
            )
        except Exception:
            pass # fall through to standard OpenAI if init fails

    # 2. Try Standard OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            return ChatOpenAI(
                model="gpt-4",
                openai_api_key=openai_key,
                temperature=0.7
            )
        except Exception:
            pass

    return None

def generate_reminder_message(
    patient_name: str,
    age: int,
    language: str,
    accessibility_needs: str,
    med_name: str,
    dosage: str,
    instructions: str
) -> str:
    """
    Generates a personalized, empathetic reminder message.
    """
    # Determine tone based on age
    tone = "gentle, warm, and reassuring" if age >= 65 else "brief, direct, and action-oriented"
    
    llm = get_llm()
    if llm:
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are MedCare AI, an empathetic digital healthcare agent. "
                    "Your goal is to write a personalized medication reminder. "
                    "Adapt your tone based on the patient profile. "
                    "Language: {language}. "
                    "Tone preference: {tone}. "
                    "Accessibility focus: {accessibility_needs}."
                )),
                ("user", (
                    "Generate a reminder for {patient_name}. "
                    "Medication: {med_name} "
                    "Dosage: {dosage} "
                    "Special Instructions: {instructions}. "
                    "Write only the notification text."
                ))
            ])
            
            chain = prompt | llm
            response = chain.invoke({
                "language": language,
                "tone": tone,
                "accessibility_needs": accessibility_needs,
                "patient_name": patient_name,
                "med_name": med_name,
                "dosage": dosage,
                "instructions": instructions
            })
            return response.content.strip()
        except Exception as e:
            # Fall back to template on LLM failure
            pass

    # GRACEFUL FALLBACK (Simulates LLM Output)
    return format_fallback_reminder(patient_name, age, language, med_name, dosage, instructions)

def generate_missed_dose_plan(
    patient_name: str,
    med_name: str,
    hours_late: float,
    safety_advice: str,
    language: str
) -> str:
    """
    Generates a comforting, non-judgmental recovery plan message.
    """
    llm = get_llm()
    if llm:
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are MedCare AI, an empathetic health partner. "
                    "A patient has missed a medication dose. Write a non-judgmental, "
                    "reassuring message explaining the safety recovery action to take. "
                    "Keep instructions clear. "
                    "Language: {language}."
                )),
                ("user", (
                    "Patient: {patient_name}. "
                    "Medication: {med_name}. "
                    "Hours late: {hours_late} hours. "
                    "Clinical Safety Action to relay: {safety_advice}. "
                    "Keep the tone highly supportive and write only the message text."
                ))
            ])
            
            chain = prompt | llm
            response = chain.invoke({
                "patient_name": patient_name,
                "med_name": med_name,
                "hours_late": hours_late,
                "safety_advice": safety_advice,
                "language": language
            })
            return response.content.strip()
        except Exception:
            pass

    # GRACEFUL FALLBACK (Simulates LLM Output)
    return format_fallback_missed_dose(patient_name, med_name, hours_late, safety_advice, language)

# --- Fallback Formatting Helpers ---

def format_fallback_reminder(patient_name: str, age: int, language: str, med_name: str, dosage: str, instructions: str) -> str:
    lang = language.lower()
    
    # Simple localization mocks
    if "span" in lang:
        if age >= 65:
            return f"Hola {patient_name}. Con cariño, le recordamos tomar su {med_name} ({dosage}). Instrucción: {instructions}. ¡Que tenga un lindo día!"
        return f"Recordatorio MedCare: {patient_name}, tome su {med_name} ({dosage}). Instrucción: {instructions}."
    elif "hind" in lang:
        if age >= 65:
            return f"नमस्ते {patient_name} जी। कृपया अपनी {med_name} ({dosage}) लें। निर्देश: {instructions}। अपना ध्यान रखें!"
        return f"मेडकेयर रिमाइंडर: {patient_name}, अपनी {med_name} ({dosage}) लें। निर्देश: {instructions}।"
    else:  # Default English
        if age >= 65:
            return f"Good morning {patient_name}. This is your gentle reminder to take your {med_name} ({dosage}). Please remember: {instructions}. Take your time and have a wonderful day!"
        return f"MedCare Alert: {patient_name}, time for your {med_name} ({dosage}). Instructions: {instructions}."

def format_fallback_missed_dose(patient_name: str, med_name: str, hours_late: float, safety_advice: str, language: str) -> str:
    lang = language.lower()
    
    if "span" in lang:
        return f"Hola {patient_name}, no se preocupe por el retraso de {hours_late} horas con su {med_name}. Plan de acción: {safety_advice}."
    elif "hind" in lang:
        return f"नमस्ते {patient_name}, {med_name} में {hours_late} घंटे की देरी के लिए चिंता न करें। आपका रिकवरी प्लान: {safety_advice}।"
    else:
        return f"Hello {patient_name}. Please don't worry about being {hours_late}h late for your {med_name}. Here is what you should do: {safety_advice} We've updated your schedule log accordingly."

def parse_medication_nlp(raw_text: str) -> dict:
    """
    Parses conversational patient statements into structured medication variables.
    """
    llm = get_llm()
    if llm:
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are a precise clinical data extraction helper. "
                    "Parse the patient's medication instructions and return ONLY a valid JSON object. "
                    "Do NOT wrap the JSON in markdown code blocks (e.g., do not use ```json). "
                    "The JSON must have the following keys:\n"
                    "- 'name': string (the name of the drug, capitalized, e.g., 'Metformin')\n"
                    "- 'dosage': string (dose amount, e.g., '500mg' or '1 tablet')\n"
                    "- 'frequency': string (must be exactly one of: 'Once daily', 'Twice daily', 'Three times daily')\n"
                    "- 'timing_constraint': string (must be exactly one of: 'Morning', 'With meals', 'Before meals', 'Afternoon', 'Evening', 'Before bed', 'None')\n\n"
                    "If you cannot determine a key, use 'None' or default to a reasonable clinical value based on standard instructions."
                )),
                ("user", "Parse this: {text}")
            ])
            
            chain = prompt | llm
            response = chain.invoke({"text": raw_text})
            content = response.content.strip()
            
            # Remove any markdown code block wraps
            content = re.sub(r"^```json\s*", "", content, flags=re.IGNORECASE)
            content = re.sub(r"\s*```$", "", content)
            
            return json.loads(content)
        except Exception:
            pass

    # Fallback to offline regex parser
    return parse_fallback_regex(raw_text)

def parse_fallback_regex(text: str) -> dict:
    text_lower = text.lower()
    
    # 1. Regex to extract drug name and dosage
    pattern = r'([a-zA-Z\-]+)\s+(\d+\s*(?:mg|mcg|ml|g|capsule|tablet|tab|pill|unit)s?)'
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        name = match.group(1).capitalize()
        dosage = match.group(2)
    else:
        # Simple split fallback
        words = text.split()
        name = "Unknown Medication"
        dosage = "1 tablet"
        for idx, word in enumerate(words):
            if any(char.isdigit() for char in word) and idx > 0:
                name = words[idx-1].strip(",.").capitalize()
                if idx + 1 < len(words):
                    dosage = f"{word} {words[idx+1].strip(',.')}"
                else:
                    dosage = word
                break
                
    # 2. Extract frequency
    if any(x in text_lower for x in ["three times", "3x", "3 times", "tid"]):
        frequency = "Three times daily"
    elif any(x in text_lower for x in ["twice", "2x", "2 times", "bid"]):
        frequency = "Twice daily"
    else:
        frequency = "Once daily"
        
    # 3. Extract timing constraint
    if "before meal" in text_lower:
        timing_constraint = "Before meals"
    elif "meal" in text_lower or "food" in text_lower or "breakfast" in text_lower or "lunch" in text_lower or "dinner" in text_lower:
        timing_constraint = "With meals"
    elif any(x in text_lower for x in ["bed", "night", "sleep"]):
        timing_constraint = "Before bed"
    elif any(x in text_lower for x in ["morning", "breakfast", "wake"]):
        timing_constraint = "Morning"
    elif any(x in text_lower for x in ["evening", "dinner"]):
        timing_constraint = "Evening"
    elif any(x in text_lower for x in ["afternoon", "lunch"]):
        timing_constraint = "Afternoon"
    else:
        timing_constraint = "None"
        
    return {
        "name": name,
        "dosage": dosage,
        "frequency": frequency,
        "timing_constraint": timing_constraint
    }

def run_agent_chat(
    patient_name: str,
    language: str,
    meds_list: list,
    adherence_score: float,
    message: str
) -> str:
    """
    Runs the agentic chat assistant, injecting patient-specific context.
    Degrades gracefully if no API key is present.
    """
    llm = get_llm()
    meds_context = "\n".join([
        f"- {m['name']} ({m['dosage']}): scheduled at {', '.join(m['schedules'])} (Constraint: {m['timing_constraint']})"
        for m in meds_list
    ])
    
    if llm:
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are MedCare AI, an empathetic and highly precise medication advisor and clinical support agent. "
                    "Your patient is {patient_name} (Language: {language}). "
                    "Here is their current medication regimen:\n"
                    "{meds_context}\n\n"
                    "Their current adherence compliance score is: {adherence_score}%.\n\n"
                    "Guidelines:\n"
                    "1. Respond directly and empathetically to the patient's request.\n"
                    "2. If they ask about a missed or late dose, evaluate safety. Metformin late doses are safe within 4 hours; blood pressure pills within 2 hours; blood thinners like Warfarin within 3 hours. Otherwise tell them to skip and resume tomorrow.\n"
                    "3. If they ask about drug interactions, check their regimen. Warfarin + Ibuprofen or Warfarin + Aspirin is dangerous. Metformin + Contrast Dye is moderate danger. Sildenafil + Nitroglycerin is critical. Otherwise, state there are no known conflicts.\n"
                    "4. Always include this disclaimer at the end of clinical advice: 'Disclaimer: MedCare AI is an assistive decision-support tool. It does not replace professional medical advice.'\n"
                    "5. Keep the response concise, patient-friendly, and in the patient's preferred language ({language})."
                )),
                ("user", "{user_message}")
            ])
            
            chain = prompt | llm
            response = chain.invoke({
                "patient_name": patient_name,
                "language": language,
                "meds_context": meds_context,
                "adherence_score": adherence_score,
                "user_message": message
            })
            return response.content.strip()
        except Exception:
            pass
            
    # FALLBACK ROUTER
    return parse_fallback_chat(patient_name, language, meds_list, adherence_score, message)

def parse_fallback_chat(
    patient_name: str,
    language: str,
    meds_list: list,
    adherence_score: float,
    message: str
) -> str:
    lang = language.lower()
    msg_lower = message.lower()
    
    # 1. Missed/Late dose recovery checks
    if any(x in msg_lower for x in ["miss", "late", "forgot", "delay", "omitted"]):
        # Check which med they missed
        target_med = "your medication"
        for m in meds_list:
            if m["name"].lower() in msg_lower:
                target_med = m["name"]
                break
                
        if "span" in lang:
            return (
                f"Hola {patient_name}. Si se retrasó menos de 3 horas con {target_med}, puede tomarlo ahora. "
                f"Si es más tarde, es mejor omitir la dosis y continuar con su horario habitual mañana. No duplique la dosis.\n\n"
                f"Aviso: MedCare AI es una herramienta de soporte. Consulte a su médico."
            )
        elif "hind" in lang:
            return (
                f"नमस्ते {patient_name}। यदि आप {target_med} लेने में 3 घंटे से कम लेट हैं, तो इसे अभी ले सकते हैं। "
                f"यदि देरी अधिक है, तो इसे छोड़ दें और कल नियमित समय पर लें। डबल खुराक न लें।\n\n"
                f"अस्वीकरण: मेडकेयर एआई एक सहायक उपकरण है। डॉक्टर से सलाह लें।"
            )
        else:
            return (
                f"Hello {patient_name}. If you are less than 3 hours late for {target_med}, it is generally safe to take it now. "
                f"If it's later than that, please skip the missed dose and resume your regular schedule tomorrow. Do not double-dose.\n\n"
                f"Disclaimer: MedCare AI is an assistive decision-support tool. It does not replace professional medical advice."
            )

    # 2. Drug safety / interaction checks
    elif any(x in msg_lower for x in ["safety", "conflict", "interact", "danger", "warning"]):
        # Check if they have warfarin and ibuprofen
        med_names = [m["name"].lower() for m in meds_list]
        has_warfarin = "warfarin" in med_names or "warfarin" in msg_lower
        has_ibuprofen = "ibuprofen" in med_names or "ibuprofen" in msg_lower
        has_aspirin = "aspirin" in med_names or "aspirin" in msg_lower
        
        if has_warfarin and (has_ibuprofen or has_aspirin):
            conflict_warning = "Critical Warning: Mixing Warfarin (blood thinner) with NSAIDs like Ibuprofen or Aspirin increases bleeding risk."
        else:
            conflict_warning = "Your current medication list shows no clinical conflicts."
            
        if "span" in lang:
            return f"Control de seguridad: {conflict_warning}\n\nAviso: MedCare AI es una herramienta de soporte. Consulte a su médico."
        elif "hind" in lang:
            return f"सुरक्षा जाँच: {conflict_warning}\n\nअस्वीकरण: मेडकेयर एआई एक सहायक उपकरण है। डॉक्टर से सलाह लें।"
        else:
            return f"Safety Check: {conflict_warning}\n\nDisclaimer: MedCare AI is an assistive decision-support tool. It does not replace professional medical advice."

    # 3. Schedule check
    elif any(x in msg_lower for x in ["schedule", "time", "plan", "routines"]):
        meds_summary = ", ".join([f"{m['name']} at {', '.join(m['schedules'])}" for m in meds_list])
        if "span" in lang:
            return f"Su horario de medicación actual: {meds_summary}."
        elif "hind" in lang:
            return f"आपका वर्तमान शेड्यूल: {meds_summary}।"
        else:
            return f"Your current medication schedule: {meds_summary}."

    # 4. Adherence check
    elif any(x in msg_lower for x in ["adherence", "score", "percent", "compliance"]):
        if "span" in lang:
            return f"Su tasa de cumplimiento de adherencia actual es {adherence_score}%."
        elif "hind" in lang:
            return f"आपका वर्तमान एडहेरेंस स्कोर {adherence_score}% है।"
        else:
            return f"Your current adherence compliance score is {adherence_score}%."

    # 5. Default supportive chat
    else:
        if "span" in lang:
            return f"Hola {patient_name}, ¿en qué puedo ayudarle hoy con sus medicamentos? Puedo aconsejarle sobre dosis olvidadas o verificar interacciones."
        elif "hind" in lang:
            return f"नमस्ते {patient_name}, मैं आपकी दवाइयों के संबंध में क्या सहायता कर सकता हूँ? मैं छूटी हुई खुराक या सुरक्षा जाँच में मदद कर सकता हूँ।"
        else:
            return f"Hello {patient_name}, how can I assist you with your medications today? You can ask me about missed/late doses, check drug safety, or view your compliance."
