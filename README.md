# Vidur — Your Family Health Companion

> **AI-powered prescription reader for India's families.**  
> Snap a prescription photo. Vidur explains every medicine in your language, flags drug interactions, finds generic savings, and sends refill reminders.

---

## Features

| Feature | Description |
|---------|-------------|
| 📸 **OCR Prescription Reading** | Upload any photo, PDF, or screenshot of a prescription |
| 🤖 **AI Parsing** | Extracts medicines, dosages, timing, instructions via Gemini AI |
| 🌐 **7 Indian Languages** | Hindi, Telugu, Tamil, Bengali, Kannada, Marathi + English |
| 🔊 **Voice Output** | Listen to medicine explanations in your language |
| ⚠️ **Drug Interaction Alerts** | Flags dangerous medicine combinations |
| 💰 **Generic Savings** | Identifies cheaper generic alternatives |
| ⏰ **Refill Reminders** | Email alerts before medicines run out |
| 🏥 **Nearby Hospitals & Pharmacies** | Live map search via OpenStreetMap (no API key needed) |
| 👨‍👩‍👧 **Caregiver Mode** | Manage prescriptions for your whole family |
| 📄 **PDF Reports** | Download a complete prescription summary |
| ✅ **Authenticity Scoring** | AI checks if the prescription looks genuine |
| 📋 **History** | All past prescriptions in one searchable place |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend / UI** | [Streamlit](https://streamlit.io) |
| **Database** | SQLite via [SQLAlchemy](https://sqlalchemy.org) |
| **AI / LLM** | Google Gemini 1.5 Flash (`google-generativeai`) |
| **OCR** | Google Gemini Vision (image-to-text) |
| **Translation** | Google Gemini (free translation via prompt) |
| **Voice** | `gTTS` (Google Text-to-Speech) |
| **Nearby Places** | OpenStreetMap Overpass API (free, no key) |
| **Location** | `ipapi.co` (IP geolocation, free) |
| **Email Alerts** | Gmail SMTP (`smtplib`) |
| **PDF Reports** | `reportlab` |
| **Auth** | `bcrypt` password hashing |

---

## Project Structure

```
vidur-backend/
├── app.py                  # Main Streamlit entry point
├── .env                    # 🔑 API keys & credentials (not committed)
├── requirements.txt        # Python dependencies
├── vidur.db                # SQLite database (auto-created)
│
├── app_pages/
│   ├── home.py             # Login / Sign-up page
│   ├── upload.py           # Prescription upload & analysis
│   ├── dashboard.py        # Main dashboard (meds, AI chat, nearby, alerts)
│   ├── caregiver.py        # Family member management
│   ├── history.py          # Prescription history
│   └── settings.py         # Profile & preferences
│
├── agents/
│   ├── ocr_agent.py        # Extracts text from images/PDFs
│   ├── prescription_agent.py # Parses prescriptions + AI chat
│   ├── translation_agent.py  # Translates medicine info
│   ├── voice_agent.py        # Text-to-speech
│   ├── alarm_agent.py        # Email refill & savings alerts
│   ├── pharmacy_agent.py     # Nearby hospitals & pharmacies
│   ├── report_agent.py       # PDF generation
│   └── authenticity_agent.py # Prescription authenticity check
│
├── database/
│   ├── db.py               # SQLAlchemy session
│   └── models.py           # ORM models (User, Prescription, Medicine, etc.)
│
└── utils/
    └── constants.py        # Languages, frequency maps, colour palette
```

---

## Setup & Installation

### 1. Prerequisites
- Python 3.10 or later
- A Gmail account (for email alerts)
- A [Google AI Studio](https://aistudio.google.com) API key (free tier works)

### 2. Clone & Install

```bash
git clone <your-repo-url>
cd vidur-backend

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root (or edit the existing one):

```env
# Google Gemini AI — get free key at https://aistudio.google.com
GEMINI_API_KEY=your_gemini_api_key_here

# Gmail SMTP — for email refill reminders & savings alerts
# Enable "App Passwords" in your Google Account security settings
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
```

> **Gmail App Password**: Go to [myaccount.google.com](https://myaccount.google.com) → Security → 2-Step Verification → App Passwords. Generate a password for "Mail".

### 4. Run

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## Quick Demo (No Upload Needed)

1. Create an account and log in
2. Go to **Upload Prescription**
3. Click **"Load Sample Prescription"** → **"Analyse Prescription"**
4. Explore all dashboard features with realistic demo data

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key |
| `EMAIL_ADDRESS` | ✅ For alerts | Gmail address for sending alerts |
| `EMAIL_PASSWORD` | ✅ For alerts | Gmail App Password |

---

## Notes

- **No data leaves your device** except API calls to Google Gemini (for OCR/parsing) and Gmail (for email alerts).
- **Nearby hospitals/pharmacies** use the free OpenStreetMap Overpass API — no API key required.
- Vidur is **not a substitute for professional medical advice**. Always consult your doctor.

---

## License

MIT — free to use, modify, and distribute.
