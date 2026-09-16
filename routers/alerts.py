"""
routers/alerts.py — Email refill reminders and generic savings alerts.
"""
from fastapi import APIRouter, HTTPException
from agents.alarm_agent import send_refill_reminder, send_generic_savings_alert
from schemas.prescription import RefillReminderRequest, SavingsAlertRequest

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post("/refill-reminder")
def refill_reminder(body: RefillReminderRequest):
    """
    Send an email refill reminder for a specific medicine.

    Body:
        medicine_name — name of the medicine
        days_left     — how many days of supply remain
        to_email      — recipient email address
    """
    if not body.to_email:
        raise HTTPException(status_code=400, detail="to_email is required")

    result = send_refill_reminder(
        medicine_name=body.medicine_name,
        days_left=body.days_left,
        to_email=body.to_email,
    )

    if result.get("email"):
        return {"message": "Refill reminder sent successfully", "success": True}

    raise HTTPException(
        status_code=500,
        detail="Failed to send email. Check EMAIL_ADDRESS and EMAIL_PASSWORD in .env",
    )


@router.post("/savings-alert")
def savings_alert(body: SavingsAlertRequest):
    """
    Send an email listing generic medicine savings opportunities.

    Body:
        medicines — list of medicine dicts (from parsed prescription)
        to_email  — recipient email address
    """
    if not body.to_email:
        raise HTTPException(status_code=400, detail="to_email is required")

    savings_meds = [
        m for m in body.medicines
        if m.get("generic_cost_saving")
        and m.get("generic_cost_saving") != "Not specified"
    ]

    if not savings_meds:
        return {
            "message": "No generic savings found in this prescription",
            "success": True,
            "sent": False,
        }

    result = send_generic_savings_alert(
        medicines=savings_meds,
        to_email=body.to_email,
    )

    if result.get("email"):
        return {"message": "Savings alert sent successfully", "success": True}

    raise HTTPException(
        status_code=500,
        detail="Failed to send email. Check EMAIL_ADDRESS and EMAIL_PASSWORD in .env",
    )
