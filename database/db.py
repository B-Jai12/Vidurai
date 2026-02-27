from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
import os
from dotenv import load_dotenv

load_dotenv()

# ── DATABASE CONNECTION ─────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///vidur.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ── CREATE ALL TABLES ───────────────────────────────────
def init_db():
    Base.metadata.create_all(bind=engine)

# ── GET DATABASE SESSION ────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── HELPER — get a direct session ──────────────────────
def get_session():
    return SessionLocal()
