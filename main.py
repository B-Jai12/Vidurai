"""
main.py — Vidur FastAPI application entry point.

Run with:
    uvicorn main:app --reload --port 8000

Swagger UI: http://localhost:8000/docs
ReDoc:       http://localhost:8000/redoc
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database.db import init_db
from routers import auth, prescriptions, medicines, voice, alerts, nearby, reports, caregiver, chat
from schemas.common import HealthResponse

load_dotenv()


# ── Lifespan: initialise DB on startup ────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("✅ Vidur API started — database initialised")
    yield
    print("🛑 Vidur API shutting down")


# ── App instance ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Vidur — Vernacular Medical Prescription Parser API",
    description=(
        "A production-ready backend API for parsing, translating, and managing "
        "medical prescriptions for Indian families. "
        "Powered by Groq (LLaMA) and Google Gemini."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ─────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(prescriptions.router)
app.include_router(medicines.router)
app.include_router(voice.router)
app.include_router(alerts.router)
app.include_router(nearby.router)
app.include_router(reports.router)
app.include_router(caregiver.router)
app.include_router(chat.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    """Simple health check — returns 200 if the API is running."""
    return HealthResponse()


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Vidur API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
    }


# ── Dev runner ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
