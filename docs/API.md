# MedCare AI - REST API Specifications

The MedCare AI FastAPI server runs at `http://localhost:8000`.

---

## 1. Patient Profile Endpoints

### Create Patient
* **Method**: `POST /api/patients`
* **Request Body**:
  ```json
  {
    "name": "Margaret Thatcher",
    "age": 72,
    "conditions": "Hypertension, Type-2 Diabetes",
    "language": "English",
    "timezone": "EST",
    "accessibility_needs": "Voice Alerts",
    "wake_time": "08:00",
    "sleep_time": "22:00"
  }
  ```
* **Response (201 Created)**: Returns the saved Patient profile including dynamic `id`.

### List Patients
* **Method**: `GET /api/patients`
* **Response (200 OK)**: JSON array of patient profiles.

---

## 2. Medication & Scheduling Endpoints

### Add Medication (with Safety Check)
* **Method**: `POST /api/medications`
* **Request Body**:
  ```json
  {
    "patient_id": 1,
    "name": "Ibuprofen",
    "dosage": "400mg",
    "frequency": "Three times daily",
    "timing_constraint": "With meals",
    "override_safety": false
  }
  ```
* **Response (409 Conflict - Safety Interaction Found)**:
  ```json
  {
    "detail": {
      "error": "Drug interaction conflict detected",
      "conflicts": [
        {
          "medication_a": "Warfarin",
          "medication_b": "Ibuprofen",
          "severity": "Critical",
          "description": "Ibuprofen increases the blood-thinning effect of Warfarin..."
        }
      ],
      "disclaimer": "Disclaimer: MedCare AI is an assistive decision-support tool..."
    }
  }
  ```
* **Response (200 OK - Success or Overridden)**:
  ```json
  {
    "id": 2,
    "patient_id": 1,
    "name": "Ibuprofen",
    "dosage": "400mg",
    "frequency": "Three times daily",
    "timing_constraint": "With meals",
    "schedules": ["08:30", "13:30", "19:00"]
  }
  ```

---

## 3. Today's Schedule & Adherence Logging

### Get Today's Schedule
* **Method**: `GET /api/patients/{patient_id}/schedule/today`
* **Response (200 OK)**:
  ```json
  [
    {
      "schedule_id": 1,
      "medication_name": "Warfarin",
      "dosage": "5mg",
      "scheduled_time": "08:30",
      "instructions": "Morning",
      "log_id": 1,
      "status": "Missed",
      "logged_time": null
    }
  ]
  ```

### Log Adherence Update
* **Method**: `POST /api/adherence/log`
* **Request Body**:
  ```json
  {
    "schedule_id": 1,
    "status": "Taken",
    "notes": "Took with breakfast"
  }
  ```

---

## 4. AI Reminders & Decision Support

### Trigger Manual AI Reminder Dispatch
* **Method**: `POST /api/schedules/{schedule_id}/trigger`
* **Response (200 OK)**:
  ```json
  {
    "status": "triggered",
    "message_sent": "Good morning Margaret. This is your gentle reminder to take your Warfarin (5mg)...",
    "audio_url": "/static/reminder_1_1.mp3"
  }
  ```

### Ask Missed-Dose Recovery Coach
* **Method**: `POST /api/patients/{patient_id}/missed-dose-recovery`
* **Query Parameters**: `med_name=Warfarin`, `hours_late=2.5`
* **Response (200 OK)**:
  ```json
  {
    "hours_late": 2.5,
    "action_required": "Take a half dose now and adjust your next dose to be 2 hours later.",
    "recovery_message": "Hello Margaret. Please don't worry about being 2.5h late for your Warfarin. Here is what you should do: Take a half dose now and adjust your next dose to be 2 hours later..."
  }
  ```
