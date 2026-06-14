# Setup and Execution Instructions

Follow these steps to run the MedCare AI prototype locally.

## Prerequisite: Python Environment Setup

We recommend creating a Python virtual environment to manage dependencies:

```bash
# Navigate to the backend folder
cd backend

# Create virtual env
python3 -m venv venv

# Activate virtual env
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install all backend packages
pip install -r requirements.txt
```

---

## 1. Environment Configurations

Make a copy of `.env.example` as `.env` (already pre-configured with default SQLite database URL):

```bash
cp .env.example .env
```

To run the AI agent in real mode, configure either Azure OpenAI or standard OpenAI keys inside the `.env` file:
* Set `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` for Azure OpenAI, or
* Set `OPENAI_API_KEY` for standard OpenAI.

*Note: If no API keys are provided, the application will degrade gracefully to localized template fallbacks, ensuring 100% demo-readiness offline.*

---

## 2. Seed the Database

Populate the local SQLite database (`medcare.db`) with sample patients, medications, and logs:

```bash
python seed.py
```

---

## 3. Run the Backend FastAPI Server

Launch the FastAPI application:

```bash
uvicorn main:app --reload --port 8000
```

The documentation and Swagger UI will be active at:
* Interactive Swagger: `http://localhost:8000/docs`

---

## 4. Run/View the Frontend Interface

Because Node/npm is not required to run the frontend SPA interface, you can load it instantly in two ways:

### Method A (FastAPI Static Server - Recommended)
1. Ensure the FastAPI backend server is running.
2. Open your web browser and navigate to:
   `http://localhost:8000/static/index.html`

### Method B (Direct File Access)
1. Open the file browser.
2. Double-click or open `frontend/index.html` in Chrome, Safari, or Firefox.
3. Keep the backend running on port 8000, and the REST calls will integrate across ports.
