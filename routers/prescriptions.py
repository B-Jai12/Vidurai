"""
routers/prescriptions.py — Upload, parse, list, and delete prescriptions.
"""
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Prescription, Medicine
from agents.ocr_agent import extract_text
from agents.prescription_agent import parse_prescription
from agents.authenticity_agent import check_authenticity
from schemas.prescription import ParseTextRequest
from routers.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])


def _save_prescription_to_db(
    db: Session,
    uid: str,          # Firebase UID (string)
    raw_text: str,
    parsed: dict,
    auth_score: float,
    family_profile_id: int | None = None,
) -> Prescription:
    """Persist a parsed prescription and its medicines to the SQLite database."""
    pres = Prescription(
        user_id=uid,   # stored as string Firebase UID
        family_profile_id=family_profile_id,
        raw_ocr_text=raw_text,
        parsed_json=json.dumps(parsed),
        authenticity_score=auth_score,
        upload_date=datetime.utcnow(),
    )
    db.add(pres)
    db.flush()

    for med_data in parsed.get("medicines", []):
        med = Medicine(
            prescription_id=pres.id,
            name=med_data.get("name", "Unknown"),
            dosage=med_data.get("dosage"),
            frequency=med_data.get("frequency"),
            timing=med_data.get("timing"),
        )
        db.add(med)

    db.commit()
    db.refresh(pres)
    return pres


# ── POST /prescriptions/upload ────────────────────────────────────────────────
@router.post("/upload", status_code=201)
async def upload_prescription(
    file: UploadFile = File(..., description="Image or PDF of the prescription"),
    family_profile_id: int | None = Form(default=None),
    current_user: Optional[dict] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Upload a prescription image or PDF.
    Works for both authenticated users (saves to DB) and guests (returns result only).
    """
    allowed_types = {"image/jpeg", "image/png", "image/jpg",
                     "application/pdf", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Use JPEG, PNG, WebP, or PDF.",
        )

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

    # OCR — try to extract text
    raw_text, confidence, method = extract_text(file_bytes, file.content_type)
    if not raw_text or len(raw_text.strip()) < 10:
        raise HTTPException(
            status_code=422,
            detail=(
                "OCR could not extract readable text. The image may be blurry or low-contrast. "
                "Try: better lighting, hold camera steady, or use 'Type Manually' instead."
            ),
        )

    # AI parsing
    try:
        parsed = parse_prescription(raw_text)
        if not parsed or not isinstance(parsed, dict) or "medicines" not in parsed:
            raise ValueError("Invalid format returned by AI.")
    except Exception as e:
        print(f"AI Parsing Error: {e}")
        raise HTTPException(
            status_code=422,
            detail="AI could not parse the prescription reliably. Please ensure it is a valid medical prescription or try a clearer image.",
        )

    # Authenticity check
    auth_score, auth_reasons = check_authenticity(parsed)

    result = {
        "authenticity_score": auth_score,
        "authenticity_reasons": auth_reasons,
        "ocr_confidence": round(confidence, 1),
        "ocr_method": method,
        "parsed": parsed,
        "prescription_id": None,
        "saved": False,
    }

    # Save to DB only if authenticated
    if current_user:
        uid = current_user.get("uid", "guest")
        pres = _save_prescription_to_db(
            db, uid, raw_text, parsed, auth_score, family_profile_id
        )
        result["prescription_id"] = pres.id
        result["saved"] = True

    return result


# ── POST /prescriptions/parse-text ───────────────────────────────────────────
@router.post("/parse-text")
def parse_text(
    body: ParseTextRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Parse raw prescription text without uploading a file.
    Works for guests (no save) or authenticated users (saves to DB if save=true).
    """
    if not body.text or len(body.text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Text is too short to parse")

    parsed = parse_prescription(body.text)
    if not parsed:
        raise HTTPException(status_code=422, detail="Could not parse the text")

    auth_score, auth_reasons = check_authenticity(parsed)
    result = {
        "authenticity_score": auth_score,
        "authenticity_reasons": auth_reasons,
        "parsed": parsed,
        "prescription_id": None,
        "saved": False,
    }

    if body.save and current_user:
        uid = current_user.get("uid", "guest")
        pres = _save_prescription_to_db(db, uid, body.text, parsed, auth_score)
        result["prescription_id"] = pres.id
        result["saved"] = True

    return result


# ── GET /prescriptions/ ───────────────────────────────────────────────────────
@router.get("/")
def list_prescriptions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all prescriptions for the authenticated user."""
    uid = current_user.get("uid", "")
    prescriptions = (
        db.query(Prescription)
        .filter(
            Prescription.user_id == uid,
            Prescription.is_active == True,
        )
        .order_by(Prescription.upload_date.desc())
        .all()
    )

    results = []
    for p in prescriptions:
        parsed = {}
        if p.parsed_json:
            try:
                parsed = json.loads(p.parsed_json)
            except Exception:
                pass
        results.append({
            "id": p.id,
            "upload_date": p.upload_date,
            "authenticity_score": p.authenticity_score,
            "doctor_name": parsed.get("doctor_name", "N/A"),
            "hospital_name": parsed.get("hospital_name", "N/A"),
            "prescription_date": parsed.get("prescription_date", "N/A"),
            "diagnosis": parsed.get("diagnosis", "N/A"),
            "medicine_count": len(parsed.get("medicines", [])),
        })

    return {"prescriptions": results, "total": len(results)}


# ── GET /prescriptions/{id} ───────────────────────────────────────────────────
@router.get("/{prescription_id}")
def get_prescription(
    prescription_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the full detail of a single prescription."""
    uid = current_user.get("uid", "")
    pres = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.user_id == uid,
        Prescription.is_active == True,
    ).first()

    if not pres:
        raise HTTPException(status_code=404, detail="Prescription not found")

    parsed = {}
    if pres.parsed_json:
        try:
            parsed = json.loads(pres.parsed_json)
        except Exception:
            pass

    return {
        "id": pres.id,
        "upload_date": pres.upload_date,
        "authenticity_score": pres.authenticity_score,
        "raw_ocr_text": pres.raw_ocr_text,
        "parsed": parsed,
    }


# ── DELETE /prescriptions/{id} ────────────────────────────────────────────────
@router.delete("/{prescription_id}")
def delete_prescription(
    prescription_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft-delete a prescription."""
    uid = current_user.get("uid", "")
    pres = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.user_id == uid,
    ).first()

    if not pres:
        raise HTTPException(status_code=404, detail="Prescription not found")

    pres.is_active = False
    db.commit()
    return {"message": "Prescription deleted", "success": True}
