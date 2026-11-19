# RECODA — Autonomous Data Quality & Repair Engine

> **Autonomous Data Quality Profiling, Safe Deterministic Repair, and Human-in-the-Loop Reconciliation**

RECODA is an intelligent data repair platform that inspects structured datasets (CSV, XLSX, XLS), profiles data-quality health, automatically resolves deterministic issues using safe AI rules, and routes critical or ambiguous anomalies to humans for review.

---

## 🌟 Key Features

- **Boolean Quality Classification (GREEN / RED):**
  - **Correct Data (GREEN):** Validated clean records or records safely standardized by deterministic AI rules.
  - **Action Required! (RED):** Records with missing critical data, suspicious numbers, invalid formats, or ambiguous values that require human decisions.
- **Categorized Error Explorer:**
  - Dynamic breakdown of errors by type: Missing Values, Whitespace, Date Formats, Suspicious Numeric, Anomalies, Duplicates, and Invalid Formats.
  - Interactive dropdowns and filters to isolate and inspect records by exact issue.
- **Strict Data Integrity:**
  - AI repairs only what can be safely and unambiguously inferred (e.g. whitespace stripping, ISO date standardization).
  - Never fabricates real-world business facts (salaries, names, IDs, dates of birth).
- **Safe Human-in-the-Loop Reconciliation:**
  - Download a pre-formatted correction template with stable DataFix serial numbers (`DFX-XXXXXX`).
  - Edit offline in Excel or any CSV editor and upload back.
  - Validates all human updates before merging and maintains a complete, rollback-capable audit trail.
- **3D Quality Visualizer:**
  - Interactive Three.js 3D sphere visualization providing an immediate visual sense of dataset health and issue density.
- **Clean Export:**
  - Export final clean data containing only original dataset columns—no internal metadata or tracking columns are injected.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+
- Modern Web Browser (Chrome, Edge, Firefox)

### 2. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. API Key Configuration (Optional for AI Diagnosis)
RECODA works fully offline for profiling, detection, and repairs. For Gemini AI-powered natural language diagnostic summaries:
1. Copy `api_key.example.txt` to `api_key.txt`:
   ```bash
   cp api_key.example.txt api_key.txt
   ```
2. Paste your Google Gemini API key inside `api_key.txt` (or set `GEMINI_API_KEY` in your environment).

> 🔒 **Security Notice:** `api_key.txt`, database files, uploads, and exports are git-ignored and never committed.

### 4. Run RECODA

**Using the launch script:**
- Double-click `run_recoda.bat`

**Or via terminal (from backend directory):**
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Once running, navigate to:
👉 **http://127.0.0.1:8000**

---

## 📁 Project Structure

```
RECODA/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI REST endpoints
│   │   ├── models/          # SQLite models & audit logging
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Profiling, detectors, repairs, reconciliation, AI explainer
│   │   └── utils/           # Helper functions & serializers
│   ├── database/            # SQLite storage (git-ignored)
│   ├── exports/             # Exported clean/template datasets (git-ignored)
│   ├── samples/             # Sample datasets for testing
│   ├── tests/               # Automated unit & integration tests
│   ├── uploads/             # Working directory for uploads (git-ignored)
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── css/                 # Glassmorphic & modern theme styles
│   ├── js/
│   │   ├── api.js           # Backend API client
│   │   ├── app.js           # Core frontend logic & interactive error views
│   │   └── chart3d.js       # Three.js 3D data visualization
│   └── index.html           # Main single-page interface
├── api_key.example.txt      # Template for Gemini API key
├── run_recoda.bat           # Quick launcher script
└── README.md                # Project documentation
```

---

## 🧪 Running Automated Tests

```bash
cd backend
python -m unittest discover tests -v
```

---

## 📄 License
Developed for Hackathon • INNOVEDGE Innovation & Entrepreneurship Development Club.
