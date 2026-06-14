# MedCare AI – Intelligent Medication Reminder Agent

**MedCare AI** is an enterprise-grade, HIPAA-aligned, agentic AI medication adherence companion built for the **Capgemini Exceller AgentifAI Buildathon 2026**.

It addresses the systemic healthcare crisis of medication non-adherence by replacing rigid static alarm alerts with an active, empathetic reasoning agent. The platform automates drug schedule creation, scans for dangerous interactions in real-time, adjusts notifications dynamically matching patient routines, and escalates missed critical doses to caregivers.

---

## 🚀 Key Features Implemented

1. **Patient Profile Management (CRUD)**: Keeps track of demographics, wake/sleep schedules, timezone offsets, and accessibility constraints (SQLite).
2. **Conflict-Free Schedule Solver (`schedule_engine.py`)**: Computes optimal dosing slots staggered by 30-minute intervals to avoid overlap conflicts.
3. **Clinical Interaction safety checks (`interaction_checker.py`)**: Inspects medications for critical drug-drug conflicts (e.g. Warfarin + Ibuprofen) and returns warnings and disclaimers.
4. **LangChain AI reasoning Agent (`ai_agent.py`)**: Prompts Azure OpenAI/GPT-4o to write custom reminder prompts with age-adapted tone scales (gentle for seniors, short for busy professionals) and provides missed-dose safety advice. Includes a robust local fallback to prevent demo errors offline.
5. **Multi-Channel Alert Dispatcher (`notifications.py`)**: Manages Twilio SMS logs, SMTP email logs, and Text-to-Speech (TTS) audio alert rendering using `gTTS`.
6. **Accessible Client UI (`frontend/index.html`)**: Single Page React application optimized with relative font layouts (`rem`), 48px tap targets, high-contrast dark panels, and customizable text-size scalings for elderly users.

---

## 📁 Project Structure

```text
medcare-ai/
├── backend/
│   ├── main.py (FastAPI core server routers)
│   ├── models.py (SQLAlchemy SQLite database schemas)
│   ├── database.py (Session database engine connection)
│   ├── schedule_engine.py (Dosing conflict solver calculations)
│   ├── interaction_checker.py (Mock drug interaction scanner)
│   ├── ai_agent.py (LangChain agent prompting and fallbacks)
│   ├── notifications.py (Twilio, SMTP, and TTS audio creators)
│   ├── seed.py (Database seeder for fast demo startup)
│   ├── static/ (FastAPI static mount folder for frontend interface)
│   │   ├── index.html (FastAPI-served copy of React client)
│   │   └── src/index.css (Static copy of custom stylesheet)
│   └── requirements.txt (Python packages)
├── frontend/
│   ├── index.html (Vite React index file)
│   ├── package.json (Standard packaging)
│   ├── vite.config.js (Vite server bundler config)
│   └── src/
│       └── index.css (Custom CSS style tokens)
├── docs/
│   ├── ARCHITECTURE.md (High level layout flow and Mermaid diagram)
│   ├── API.md (REST API endpoint specifications)
│   └── SETUP.md (Virtualenv install and running commands)
└── README.md
```

---

## 🛠 Quick Start Guide

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Set up virtual environment and install packages:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Initialize the database and pre-populate demo patients:
   ```bash
   python seed.py
   ```
4. Run the server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
5. View the dashboard:
   Open **[http://localhost:8000/static/index.html](http://localhost:8000/static/index.html)** in your browser.

*For detailed endpoint structures and advanced settings, refer to **[docs/SETUP.md](file:///Users/aryanmahajan/Documents/Medcare.Ai/docs/SETUP.md)**.*
