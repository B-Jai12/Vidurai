<div align="center">



<br/>

[[FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[[Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[[Gemini 1.5](https://img.shields.io/badge/Google_Gemini-1.5_Flash-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[[SQLite](https://img.shields.io/badge/SQLite-SQLAlchemy-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[[Swagger](https://img.shields.io/badge/API_Docs-Swagger_UI-85EA2D?style=for-the-badge&logo=swagger&logoColor=black)](http://localhost:8000/docs)
[[License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

<br/>

> **Empowering families across India to understand their healthcare.**  
> Snap a doctor's handwritten prescription — Vidur extracts every medication, clarifies dosages in your native language, alerts against dangerous drug interactions, and identifies affordable generic alternatives.

<br/>

**[Interactive Swagger Docs](#-api-documentation) &nbsp;•&nbsp; [Multi-Agent Architecture](#-multi-agent-system) &nbsp;•&nbsp; [Local Setup](#-getting-started) &nbsp;•&nbsp; [Multilingual Engine](#-supported-languages)**

<br/>

</div>

---

##  The Healthcare Challenge

Every year across India, millions of families struggle with:
- **Illegible Handwritten Prescriptions:** Critical medication instructions, dosages, and schedules remain unreadable or misinterpreted.
- **Language Barriers:** Medical instructions are overwhelmingly written in English or Latin medical jargon, creating anxiety for non-English speakers.
- **Hidden Financial Strain:** Patients frequently purchase branded medications at inflated prices unaware of chemically identical generic alternatives.
- **Dangerous Drug Interactions:** Polypharmacy without cross-checking often triggers adverse drug combinations.

Vidur AI solves this directly at the patient and caregiver level.

---

##  The Solution

Vidur AI is an autonomous, multi-agent healthcare intelligence backend. By combining **Google Gemini 1.5 Vision** with specialized domain agents, Vidur breaks down complex clinical prescriptions into plain, accessible, and spoken guidance in regional Indian languages.

```
       [ Prescription Image / PDF / Scan ]
                       │
                       ▼
          ┌─────────────────────────┐
          │     OCR Vision Agent    │  Extracts raw clinical text
          └────────────┬────────────┘
                       │
                       ▼
          ┌─────────────────────────┐
          │   Prescription Agent    │  Parses medicines, dosage, & frequencies
          └────────────┬────────────┘
                       │
       ┌───────────────┼───────────────┬───────────────┐
       ▼               ▼               ▼               ▼
┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐
│  Validation  ││  Pharmacy    ││ Translation  ││ Alarm &      │
│  & Safety    ││  & Generic   ││ & Voice      ││ Refill Agent │
│  Agent       ││  Savings     ││ (7 Languages)││ (Caregiver)  │
└──────────────┘└──────────────┘└──────────────┘└──────────────┘
```

---

##  Multi-Agent System

Vidur breaks healthcare reasoning into dedicated, decoupled agents inside `agents/`:

| Agent | Responsibility | Core Technology |
|---|---|---|
| **`ocr_agent.py`** | Clinical document ingestion from camera shots, scans, and PDFs | Gemini 1.5 Flash Vision |
| **`prescription_agent.py`** | Extracts medicine names, strengths, timings (before/after meals), duration | Pydantic Schema Parsing |
| **`authenticity_agent.py`** | Verifies prescription legitimacy, doctor credentials, and clinic metadata | Heuristic + LLM Verification |
| **`pharmacy_agent.py`** | Identifies generic salt equivalents and highlights price-saving substitutions | Clinical Knowledge Retrieval |
| **`translation_agent.py`** | Translates clinical advice into 7 regional Indian languages | Gemini Contextual Translation |
| **`voice_agent.py`** | Synthesizes regional audio instructions for illiterate or elderly patients | Speech Synthesis Integration |
| **`alarm_agent.py`** | Computes course end dates and orchestrates refill reminder alerts | Cron / Scheduling Engine |
| **`report_agent.py`** | Generates downloadable diagnostic and prescription summaries | Structured PDF & Markdown Export |

---

##  Supported Languages

Vidur is built specifically for Indian diversity, delivering clear instructions in:

- **Hindi (हिन्दी)**
- **Telugu (తెలుగు)**
- **Tamil (தமிழ்)**
- **Bengali (বাংলা)**
- **Kannada (ಕನ್ನಡ)**
- **Marathi (मराठी)**
- **English**

---

##  Tech Stack

- **Framework:** FastAPI (Python 3.10+)
- **AI / LLM Engine:** Google Gemini 1.5 Flash (`google-generativeai`)
- **Database & ORM:** SQLite with SQLAlchemy & Alembic migrations
- **Data Validation:** Pydantic v2
- **Document Ingestion:** Pillow, PyPDF2
- **Security:** CORS Middleware, JWT Auth handlers

---

##  Repository Structure

```
Vidurai/
├── agents/                  # Multi-agent intelligence modules
│   ├── ocr_agent.py         # Prescription vision extraction
│   ├── prescription_agent.py# Medical entity parsing
│   ├── pharmacy_agent.py    # Generic equivalents & cost analysis
│   ├── translation_agent.py # Regional language synthesis
│   ├── authenticity_agent.py# Credential & anomaly validation
│   ├── alarm_agent.py       # Refill & schedule computations
│   └── voice_agent.py       # Audio generation pipeline
├── database/                # Database models & connection pool
│   ├── db.py                # Database initialization
│   └── models.py            # Patient, Prescription, and Alert schemas
├── routers/                 # Modular REST API endpoints
│   ├── auth.py              # User & caregiver authentication
│   ├── prescriptions.py     # Upload and parsing lifecycle
│   ├── medicines.py         # Drug lookups & interactions
│   ├── alerts.py            # Refill notification triggers
│   ├── nearby.py            # Pharmacy & hospital locator
│   ├── reports.py           # Medical export generation
│   ├── voice.py             # Spoken instruction delivery
│   └── chat.py              # Interactive medical conversational assistant
├── schemas/                 # Pydantic request/response contracts
├── main.py                  # FastAPI application entry point
├── requirements.txt         # Production dependencies
└── pyrightconfig.json       # Strict typechecking configuration
```

---

##  Getting Started

### Prerequisites
- Python 3.10 or higher
- Google Gemini API Key ([Get one free at Google AI Studio](https://aistudio.google.com/))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/B-Jai12/Vidurai.git
   cd Vidurai
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   DATABASE_URL=sqlite:///./vidur.db
   SECRET_KEY=your_secure_jwt_secret
   ```

5. **Run the development server:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

---

##  API Documentation

Once the server is running, explore and test the interactive API docs directly:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

##  Author

**Jaideep** ([B-Jai12](https://github.com/B-Jai12))  
B.Tech AIML Student & Builder • Crafting practical AI products that solve real-world problems.
