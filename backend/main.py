import os
from datetime import datetime, date
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Depends, HTTPException, status
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

# OpenTelemetry Imports
# pyrefly: ignore [missing-import]
from opentelemetry import trace
# pyrefly: ignore [missing-import]
from opentelemetry.sdk.trace import TracerProvider
# pyrefly: ignore [missing-import]
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
# pyrefly: ignore [missing-import]
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# MedCare AI Engine Modules
from database import engine, Base, get_db
import models
import schedule_engine
import interaction_checker
import ai_agent
import notifications

# Setup OpenTelemetry console tracing
provider = TracerProvider()
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("medcare-tracer")

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MedCare AI API Gateway",
    description="Intelligent Medication Reminder Agent backend for Capgemini Hackathon.",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder for voice TTS playback files
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)


# --- Pydantic Schemas ---

class PatientCreate(BaseModel):
    name: str
    age: int
    conditions: str
    language: Optional[str] = "English"
    timezone: Optional[str] = "UTC"
    accessibility_needs: Optional[str] = "None"
    wake_time: Optional[str] = "08:00"
    sleep_time: Optional[str] = "22:00"

class PatientResponse(PatientCreate):
    id: int
    class Config:
        from_attributes = True

class MedicationCreate(BaseModel):
    patient_id: int
    name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None  # e.g., "Once daily", "Twice daily", "Three times daily"
    timing_constraint: Optional[str] = None  # e.g., "With meals", "Before bed", "Morning", "None"
    raw_nlp_text: Optional[str] = None
    override_safety: Optional[bool] = False

class MedicationResponse(BaseModel):
    id: int
    patient_id: int
    name: str
    dosage: str
    frequency: str
    timing_constraint: str
    schedules: List[str]
    class Config:
        from_attributes = True

class MedicationDetailResponse(BaseModel):
    id: int
    patient_id: int
    name: str
    dosage: str
    frequency: str
    timing_constraint: str
    class Config:
        from_attributes = True

class AdherenceLogCreate(BaseModel):
    schedule_id: int
    status: str  # "Taken", "Missed", "Late"
    notes: Optional[str] = ""

class AdherenceResponse(BaseModel):
    id: int
    patient_id: int
    schedule_id: int
    scheduled_time: str
    logged_time: Optional[str] = None
    status: str
    notes: Optional[str] = None
    class Config:
        from_attributes = True

class SafetyResponse(BaseModel):
    is_safe: bool
    conflicts: List[dict]
    disclaimer: str

# --- Endpoints ---

# 1. Patient Profile endpoints (CRUD)

@app.post("/api/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    with tracer.start_as_current_span("create_patient_db"):
        db_patient = models.Patient(**patient.model_dump())
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)
        return db_patient

@app.get("/api/patients", response_model=List[PatientResponse])
def get_patients(db: Session = Depends(get_db)):
    return db.query(models.Patient).all()

@app.get("/api/patients/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient

@app.put("/api/patients/{patient_id}", response_model=PatientResponse)
def update_patient(patient_id: int, patient_update: PatientCreate, db: Session = Depends(get_db)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    for key, value in patient_update.model_dump().items():
        setattr(db_patient, key, value)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@app.delete("/api/patients/{patient_id}")
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(db_patient)
    db.commit()
    return {"message": "Patient deleted successfully"}


# 2. Medication Management with Safety Checks & Staggered Scheduling

@app.post("/api/medications", response_model=MedicationResponse)
def add_medication(med: MedicationCreate, db: Session = Depends(get_db)):
    with tracer.start_as_current_span("add_medication_workflow"):
        # Fetch Patient profile
        patient = db.query(models.Patient).filter(models.Patient.id == med.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Conversational NLP parsing if text is supplied
        if med.raw_nlp_text:
            extracted = ai_agent.parse_medication_nlp(med.raw_nlp_text)
            med.name = extracted.get("name")
            med.dosage = extracted.get("dosage")
            med.frequency = extracted.get("frequency")
            med.timing_constraint = extracted.get("timing_constraint")

        if not med.name or not med.dosage:
            raise HTTPException(status_code=400, detail="Could not extract medication details from text.")

        # 1. Run Clinical Safety Interaction Checks
        existing_meds = db.query(models.Medication).filter(models.Medication.patient_id == med.patient_id).all()
        med_names = [m.name for m in existing_meds]
        
        # Test current drug safety including new drug candidate
        safety_assessment = interaction_checker.verify_drug_safety(med_names + [med.name])
        
        # Filter conflicts to only include those involving the new medication candidate
        new_med_lower = med.name.strip().lower()
        new_conflicts = [
            c for c in safety_assessment["conflicts"]
            if c["medication_a"].lower().strip() == new_med_lower or c["medication_b"].lower().strip() == new_med_lower
        ]
        
        if len(new_conflicts) > 0 and not med.override_safety:
            # Block registration and return safety conflicts
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Drug interaction conflict detected",
                    "conflicts": new_conflicts,
                    "disclaimer": safety_assessment["disclaimer"]
                }
            )

        # 2. Add Medication
        db_med = models.Medication(
            patient_id=med.patient_id,
            name=med.name,
            dosage=med.dosage,
            frequency=med.frequency,
            timing_constraint=med.timing_constraint
        )
        db.add(db_med)
        db.commit()
        db.refresh(db_med)

        # 3. Schedule Engine: Compute Optimal Conflict-free slots
        existing_schedules = []
        for em in existing_meds:
            for es in em.schedules:
                if es.is_active:
                    existing_schedules.append({"medication_name": em.name, "time": es.scheduled_time})

        computed_times = schedule_engine.schedule_medication(
            new_med_name=med.name,
            frequency=med.frequency,
            timing_constraint=med.timing_constraint,
            patient_wake=patient.wake_time,
            patient_sleep=patient.sleep_time,
            existing_schedules=existing_schedules
        )

        # Save generated schedules in DB
        schedules_list = []
        for time_slot in computed_times:
            db_schedule = models.Schedule(
                patient_id=med.patient_id,
                medication_id=db_med.id,
                scheduled_time=time_slot,
                instructions=med.timing_constraint
            )
            db.add(db_schedule)
            schedules_list.append(time_slot)
        
        db.commit()

        # Seed Adherence entries for today based on these schedules
        today_date = date.today().isoformat()
        for time_slot in computed_times:
            db_log = models.AdherenceLog(
                patient_id=med.patient_id,
                schedule_id=db_schedule.id,  # Link to last created schedule structure for simplicity
                scheduled_time=f"{today_date}T{time_slot}:00",
                status="Missed"  # default to missed until checked taken
            )
            db.add(db_log)
        db.commit()

        return MedicationResponse(
            id=db_med.id,
            patient_id=db_med.patient_id,
            name=db_med.name,
            dosage=db_med.dosage,
            frequency=db_med.frequency,
            timing_constraint=db_med.timing_constraint,
            schedules=schedules_list
        )

@app.get("/api/patients/{patient_id}/medications", response_model=List[MedicationDetailResponse])
def get_patient_medications(patient_id: int, db: Session = Depends(get_db)):
    return db.query(models.Medication).filter(models.Medication.patient_id == patient_id).all()

@app.delete("/api/medications/{med_id}")
def delete_medication(med_id: int, db: Session = Depends(get_db)):
    db_med = db.query(models.Medication).filter(models.Medication.id == med_id).first()
    if not db_med:
        raise HTTPException(status_code=404, detail="Medication not found")
    db.delete(db_med)
    db.commit()
    return {"message": "Medication deleted successfully"}


# 3. Schedule & Today's Intake Tracking

@app.get("/api/patients/{patient_id}/schedule/today")
def get_todays_schedule(patient_id: int, db: Session = Depends(get_db)):
    # Find all active schedules for the patient
    schedules = db.query(models.Schedule).filter(models.Schedule.patient_id == patient_id).all()
    today_date = date.today().isoformat()
    
    results = []
    for s in schedules:
        # Check if an adherence log for today exists
        log = db.query(models.AdherenceLog).filter(
            models.AdherenceLog.schedule_id == s.id,
            models.AdherenceLog.scheduled_time.like(f"{today_date}%")
        ).first()

        # If it doesn't exist, create it (lazily populate)
        if not log:
            log = models.AdherenceLog(
                patient_id=patient_id,
                schedule_id=s.id,
                scheduled_time=f"{today_date}T{s.scheduled_time}:00",
                status="Missed"
            )
            db.add(log)
            db.commit()
            db.refresh(log)

        results.append({
            "schedule_id": s.id,
            "medication_name": s.medication.name,
            "dosage": s.medication.dosage,
            "scheduled_time": s.scheduled_time,
            "instructions": s.instructions,
            "log_id": log.id,
            "status": log.status,
            "logged_time": log.logged_time
        })
    
    # Sort chronologically
    results.sort(key=lambda x: x["scheduled_time"])
    return results


# 4. Adherence Logging & Analytics

@app.post("/api/adherence/log", response_model=AdherenceResponse)
def log_adherence_event(log_data: AdherenceLogCreate, db: Session = Depends(get_db)):
    today_date = date.today().isoformat()
    # Fetch log entry for today linked to this schedule
    log = db.query(models.AdherenceLog).filter(
        models.AdherenceLog.schedule_id == log_data.schedule_id,
        models.AdherenceLog.scheduled_time.like(f"{today_date}%")
    ).first()

    if not log:
        # Fetch schedule details
        schedule = db.query(models.Schedule).filter(models.Schedule.id == log_data.schedule_id).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule slot not found")
        log = models.AdherenceLog(
            patient_id=schedule.patient_id,
            schedule_id=log_data.schedule_id,
            scheduled_time=f"{today_date}T{schedule.scheduled_time}:00"
        )
        db.add(log)

    log.status = log_data.status
    log.logged_time = datetime.now().isoformat()
    log.notes = log_data.notes
    db.commit()
    db.refresh(log)
    return log

@app.get("/api/patients/{patient_id}/adherence/summary")
def get_adherence_summary(patient_id: int, db: Session = Depends(get_db)):
    logs = db.query(models.AdherenceLog).filter(models.AdherenceLog.patient_id == patient_id).all()
    total = len(logs)
    if total == 0:
        return {
            "adherence_rate": 100.0,
            "total_doses": 0,
            "taken_count": 0,
            "missed_count": 0,
            "late_count": 0
        }

    taken = sum(1 for l in logs if l.status == "Taken")
    late = sum(1 for l in logs if l.status == "Late")
    missed = sum(1 for l in logs if l.status == "Missed")

    adherence_rate = round(((taken + late) / total) * 100, 2)
    return {
        "adherence_rate": adherence_rate,
        "total_doses": total,
        "taken_count": taken,
        "missed_count": missed,
        "late_count": late
    }


# 5. Reminder Messaging & Simulated Notification Dispatch (Trigger Demo)

@app.post("/api/schedules/{schedule_id}/trigger")
def trigger_reminder_dispatch(schedule_id: int, db: Session = Depends(get_db)):
    with tracer.start_as_current_span("trigger_notification_dispatch"):
        schedule = db.query(models.Schedule).filter(models.Schedule.id == schedule_id).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        patient = schedule.patient
        med = schedule.medication

        # 1. Ask LangChain Agent for personalized, tone-adapted message
        personalized_message = ai_agent.generate_reminder_message(
            patient_name=patient.name,
            age=patient.age,
            language=patient.language,
            accessibility_needs=patient.accessibility_needs,
            med_name=med.name,
            dosage=med.dosage,
            instructions=schedule.instructions
        )

        # 2. Dispatch notifications
        # SMS dispatch (fake or real Twilio)
        phone = patient.phone_number if hasattr(patient, "phone_number") and patient.phone_number else "+15555555555"
        notifications.send_sms(to_phone=phone, message=personalized_message)
        
        # Email dispatch (fake or real SMTP)
        email = f"{patient.name.lower().replace(' ', '')}@medcareai.com"
        notifications.send_email(to_email=email, subject=f"Time for your {med.name}", body=personalized_message)

        # Voice alert (TTS mp3 creation)
        audio_filename = f"reminder_{patient.id}_{schedule_id}.mp3"
        audio_path = notifications.generate_voice_alert(
            message=personalized_message,
            output_dir=STATIC_DIR,
            filename=audio_filename,
            language=patient.language
        )

        # Save notification log
        db_notif = models.NotificationLog(
            patient_id=patient.id,
            schedule_id=schedule.id,
            type="SMS",
            message_body=personalized_message,
            status="Delivered",
            dispatched_at=datetime.now().isoformat()
        )
        db.add(db_notif)
        db.commit()

        # Generate audio playback URL relative path
        audio_url = f"/static/{audio_filename}"
        if audio_path.endswith(".txt"):
            audio_url = f"/static/{audio_filename.replace('.mp3', '.txt')}"

        return {
            "status": "triggered",
            "message_sent": personalized_message,
            "audio_url": audio_url
        }

@app.post("/api/patients/{patient_id}/missed-dose-recovery")
def trigger_missed_dose_recovery(patient_id: int, med_name: str, hours_late: float, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Mock safety advice calculations
    if hours_late < 2.0:
        safety_advice = "It is safe to take your dose now. Eat a small snack first."
    elif hours_late < 4.0:
        safety_advice = "Take a half dose now and adjust your next dose to be 2 hours later."
    else:
        safety_advice = "Skip this dose entirely. Do not take a double dose to make up. Resume tomorrow at your regular time."

    # Ask LangChain Agent to write comforting advice
    recovery_plan = ai_agent.generate_missed_dose_plan(
        patient_name=patient.name,
        med_name=med_name,
        hours_late=hours_late,
        safety_advice=safety_advice,
        language=patient.language
    )

    return {
        "hours_late": hours_late,
        "action_required": safety_advice,
        "recovery_message": recovery_plan
    }
