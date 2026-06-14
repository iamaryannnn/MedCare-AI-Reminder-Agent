from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    conditions = Column(String)  # Comma-separated list of conditions
    language = Column(String, default="English")
    timezone = Column(String, default="UTC")
    accessibility_needs = Column(String, default="None")  # e.g. "Voice Alerts", "Large Font", "None"
    wake_time = Column(String, default="08:00")  # HH:MM format
    sleep_time = Column(String, default="22:00")  # HH:MM format

    medications = relationship("Medication", back_populates="patient", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="patient", cascade="all, delete-orphan")
    adherence_logs = relationship("AdherenceLog", back_populates="patient", cascade="all, delete-orphan")
    notifications = relationship("NotificationLog", back_populates="patient", cascade="all, delete-orphan")

class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"))
    name = Column(String, index=True)
    dosage = Column(String)  # e.g., "500mg", "1 tablet"
    frequency = Column(String)  # e.g., "Once daily", "Twice daily", "Three times daily"
    timing_constraint = Column(String)  # e.g., "With meals", "Before meals", "Before bed", "Morning", "None"

    patient = relationship("Patient", back_populates="medications")
    schedules = relationship("Schedule", back_populates="medication", cascade="all, delete-orphan")

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"))
    medication_id = Column(Integer, ForeignKey("medications.id", ondelete="CASCADE"))
    scheduled_time = Column(String)  # HH:MM format
    instructions = Column(String)  # e.g., "Take with food"
    is_active = Column(Boolean, default=True)

    patient = relationship("Patient", back_populates="schedules")
    medication = relationship("Medication", back_populates="schedules")
    adherence_logs = relationship("AdherenceLog", back_populates="schedule", cascade="all, delete-orphan")
    notifications = relationship("NotificationLog", back_populates="schedule", cascade="all, delete-orphan")

class AdherenceLog(Base):
    __tablename__ = "adherence_logs"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"))
    schedule_id = Column(Integer, ForeignKey("schedules.id", ondelete="CASCADE"))
    scheduled_time = Column(String)  # ISO DateTime format (YYYY-MM-DDTHH:MM:SS)
    logged_time = Column(String)  # ISO DateTime format
    status = Column(String)  # "Taken", "Missed", "Late"
    notes = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="adherence_logs")
    schedule = relationship("Schedule", back_populates="adherence_logs")

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"))
    schedule_id = Column(Integer, ForeignKey("schedules.id", ondelete="CASCADE"))
    type = Column(String)  # "SMS", "Email", "Voice"
    message_body = Column(String)
    status = Column(String)  # "Sent", "Failed", "Delivered"
    dispatched_at = Column(String)  # ISO DateTime format

    patient = relationship("Patient", back_populates="notifications")
    schedule = relationship("Schedule", back_populates="notifications")
