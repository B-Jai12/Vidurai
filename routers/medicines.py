"""
routers/medicines.py — Per-prescription medicine retrieval and translation.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Prescription
from agents.translation_agent import translate_medicines
from schemas.prescription import TranslateRequest
from routers.auth import get_current_user

router = APIRouter(prefix="/medicines", tags=["Medicines"])


@router.get("/{prescription_id}")
def get_medicines(
    prescription_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the full medicine list for a prescription."""
    pres = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.user_id == current_user.get("uid", ""),
        Prescription.is_active == True,
    ).first()

    if not pres:
        raise HTTPException(status_code=404, detail="Prescription not found")

    if not pres.parsed_json:
        return {"medicines": [], "drug_interactions": [], "red_flags": []}

    try:
        parsed = json.loads(pres.parsed_json)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to parse stored prescription data")

    return {
        "medicines": parsed.get("medicines", []),
        "drug_interactions": parsed.get("drug_interactions", []),
        "red_flags": parsed.get("red_flags", []),
        "special_instructions": parsed.get("special_instructions", ""),
    }


@router.post("/translate")
def translate(body: TranslateRequest):
    """
    Translate medicine explanation fields into the given Indian language.
    Medicine names, dosages, and frequency codes are preserved in English.
    """
    if not body.medicines:
        raise HTTPException(status_code=400, detail="No medicines provided")

    if body.language == "English":
        return {"medicines": body.medicines, "language": "English"}

    translated = translate_medicines(body.medicines, body.language)
    return {"medicines": translated, "language": body.language}
