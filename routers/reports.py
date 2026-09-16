"""
routers/reports.py — Generate and download PDF prescription reports.
"""
import json
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Prescription
from agents.report_agent import generate_report
from routers.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate/{prescription_id}")
def generate_pdf_report(
    prescription_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a PDF report for a prescription and return it as a downloadable file.
    """
    pres = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.user_id == current_user.get("uid", ""),
        Prescription.is_active == True,
    ).first()

    if not pres:
        raise HTTPException(status_code=404, detail="Prescription not found")

    if not pres.parsed_json:
        raise HTTPException(status_code=422, detail="No parsed data available for this prescription")

    try:
        parsed = json.loads(pres.parsed_json)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read prescription data")

    patient_name = parsed.get("patient_name", current_user.get("name", "Patient"))
    pdf_path = generate_report(parsed, patient_name=patient_name)

    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="PDF generation failed")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=os.path.basename(pdf_path),
    )
