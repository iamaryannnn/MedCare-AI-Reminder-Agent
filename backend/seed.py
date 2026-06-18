from database import SessionLocal, Base, engine
import models
import schedule_engine
from datetime import date, datetime, timedelta
import random

def seed_database():
    # Clear existing tables and recreate them
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    random.seed(42)
    try:
        print("Seeding database with demo patient profiles...")
        
        # 1. Add Margaret (Elderly Care Persona)
        margaret = models.Patient(
            name="Margaret Thatcher",
            age=72,
            conditions="Hypertension, Type-2 Diabetes",
            language="English",
            timezone="EST",
            accessibility_needs="Voice Alerts",
            wake_time="08:00",
            sleep_time="22:00"
        )
        db.add(margaret)
        db.commit()
        db.refresh(margaret)

        # Add initial medication for Margaret: Warfarin (5mg, Once daily, Morning)
        warfarin = models.Medication(
            patient_id=margaret.id,
            name="Warfarin",
            dosage="5mg",
            frequency="Once daily",
            timing_constraint="Morning",
            remaining_doses=18,
            total_doses=30
        )
        db.add(warfarin)
        db.commit()
        db.refresh(warfarin)

        # Calculate scheduling times for Margaret
        margaret_existing_schedules = []
        computed_times_margaret = schedule_engine.schedule_medication(
            new_med_name="Warfarin",
            frequency="Once daily",
            timing_constraint="Morning",
            patient_wake=margaret.wake_time,
            patient_sleep=margaret.sleep_time,
            existing_schedules=margaret_existing_schedules
        )
        
        # Save schedules
        for time_slot in computed_times_margaret:
            sched = models.Schedule(
                patient_id=margaret.id,
                medication_id=warfarin.id,
                scheduled_time=time_slot,
                instructions="Morning"
            )
            db.add(sched)
            db.commit()
            db.refresh(sched)
            
            # Generate 30 days of historical logs
            for days_ago in range(30, 0, -1):
                log_date = (datetime.now() - timedelta(days=days_ago)).date().isoformat()
                status = random.choices(["Taken", "Late", "Missed"], weights=[80, 10, 10])[0]
                logged_time = None
                if status == "Taken":
                    logged_time = f"{log_date}T{time_slot}:05"
                elif status == "Late":
                    logged_time = f"{log_date}T10:45:00"
                
                log = models.AdherenceLog(
                    patient_id=margaret.id,
                    schedule_id=sched.id,
                    scheduled_time=f"{log_date}T{time_slot}:00",
                    status=status,
                    logged_time=logged_time,
                    notes="Seeded history"
                )
                db.add(log)
            db.commit()
            
            # Add missed log entry for today (will display on Dashboard)
            today_date = date.today().isoformat()
            log = models.AdherenceLog(
                patient_id=margaret.id,
                schedule_id=sched.id,
                scheduled_time=f"{today_date}T{time_slot}:00",
                status="Missed"
            )
            db.add(log)
            db.commit()

        # 2. Add Vikram (Busy Professional Persona)
        vikram = models.Patient(
            name="Vikram Dev",
            age=32,
            conditions="General Vitamin Deficiency",
            language="English",
            timezone="IST",
            accessibility_needs="None",
            wake_time="07:00",
            sleep_time="23:00"
        )
        db.add(vikram)
        db.commit()
        db.refresh(vikram)

        # Add initial medication for Vikram: Multivitamins (1 capsule, Once daily, With meals)
        multivitamins = models.Medication(
            patient_id=vikram.id,
            name="Multivitamins",
            dosage="1 capsule",
            frequency="Once daily",
            timing_constraint="With meals",
            remaining_doses=28,
            total_doses=30
        )
        db.add(multivitamins)
        db.commit()
        db.refresh(multivitamins)

        # Calculate scheduling times for Vikram
        vikram_existing_schedules = []
        computed_times_vikram = schedule_engine.schedule_medication(
            new_med_name="Multivitamins",
            frequency="Once daily",
            timing_constraint="With meals",
            patient_wake=vikram.wake_time,
            patient_sleep=vikram.sleep_time,
            existing_schedules=vikram_existing_schedules
        )
        
        for time_slot in computed_times_vikram:
            sched = models.Schedule(
                patient_id=vikram.id,
                medication_id=multivitamins.id,
                scheduled_time=time_slot,
                instructions="With meals"
            )
            db.add(sched)
            db.commit()
            db.refresh(sched)
            
            # Generate 30 days of historical logs
            for days_ago in range(30, 0, -1):
                log_date = (datetime.now() - timedelta(days=days_ago)).date().isoformat()
                status = random.choices(["Taken", "Late", "Missed"], weights=[85, 10, 5])[0]
                logged_time = None
                if status == "Taken":
                    logged_time = f"{log_date}T{time_slot}:10"
                elif status == "Late":
                    logged_time = f"{log_date}T14:30:00"
                
                log = models.AdherenceLog(
                    patient_id=vikram.id,
                    schedule_id=sched.id,
                    scheduled_time=f"{log_date}T{time_slot}:00",
                    status=status,
                    logged_time=logged_time,
                    notes="Seeded history"
                )
                db.add(log)
            db.commit()
            
            # Add taken log entry for today
            today_date = date.today().isoformat()
            log = models.AdherenceLog(
                patient_id=vikram.id,
                schedule_id=sched.id,
                scheduled_time=f"{today_date}T{time_slot}:00",
                status="Taken",
                logged_time=f"{today_date}T{time_slot}:10"
            )
            db.add(log)
            db.commit()

        print("Database seeded successfully!")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
