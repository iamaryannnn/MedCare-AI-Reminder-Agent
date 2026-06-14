import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
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
