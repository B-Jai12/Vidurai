"""
routers/caregiver.py — Manage family member profiles and their prescriptions.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import FamilyProfile, Prescription
from schemas.prescription import FamilyMemberCreate
from routers.auth import get_current_user

router = APIRouter(prefix="/caregiver", tags=["Caregiver"])


@router.get("/members")
def list_members(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all family members for the authenticated user."""
    members = (
        db.query(FamilyProfile)
        .filter(FamilyProfile.owner_user_id == current_user.get("uid", ""))
        .all()
    )
    return {
        "members": [
            {
                "id": m.id,
                "member_name": m.member_name,
                "age": m.age,
                "relationship": m.relationship,
                "preferred_language": m.preferred_language,
            }
            for m in members
        ]
    }


@router.post("/members", status_code=201)
def add_member(
    body: FamilyMemberCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a new family member profile."""
    member = FamilyProfile(
        owner_user_id=current_user.get("uid", ""),
        member_name=body.member_name,
        age=body.age,
        relationship=body.relationship,
        preferred_language=body.preferred_language,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return {
        "message": "Family member added",
        "id": member.id,
        "member_name": member.member_name,
    }


@router.delete("/members/{member_id}")
def delete_member(
    member_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a family member profile."""
    member = db.query(FamilyProfile).filter(
        FamilyProfile.id == member_id,
        FamilyProfile.owner_user_id == current_user.get("uid", ""),
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    db.delete(member)
    db.commit()
    return {"message": "Family member removed", "success": True}


@router.get("/members/{member_id}/prescriptions")
def member_prescriptions(
    member_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all prescriptions for a specific family member."""
    member = db.query(FamilyProfile).filter(
        FamilyProfile.id == member_id,
        FamilyProfile.owner_user_id == current_user.get("uid", ""),
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    prescriptions = (
        db.query(Prescription)
        .filter(
            Prescription.family_profile_id == member_id,
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
            "diagnosis": parsed.get("diagnosis", "N/A"),
            "medicine_count": len(parsed.get("medicines", [])),
        })

    return {
        "member": member.member_name,
        "prescriptions": results,
        "total": len(results),
    }
