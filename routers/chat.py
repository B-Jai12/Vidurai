"""
routers/chat.py — AI medicine assistant chat endpoint.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Prescription, ChatHistory
from agents.prescription_agent import chat_with_assistant
from schemas.prescription import ChatRequest
from routers.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["AI Chat"])


@router.post("/ask")
def ask(
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Ask the AI medicine assistant a question about a prescription.

    The assistant answers based on the patient's specific prescription,
    responds in the requested language, and refuses to change dosages
    or prescribe new medicines.
    """
    pres = db.query(Prescription).filter(
        Prescription.id == body.prescription_id,
        Prescription.user_id == current_user.get("uid", ""),
        Prescription.is_active == True,
    ).first()

    if not pres:
        raise HTTPException(status_code=404, detail="Prescription not found")

    if not pres.parsed_json:
        raise HTTPException(status_code=422, detail="No parsed prescription data available")

    try:
        parsed = json.loads(pres.parsed_json)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read prescription data")

    # Load previous chat history for this prescription
    history_rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.prescription_id == body.prescription_id)
        .order_by(ChatHistory.timestamp)
        .limit(10)
        .all()
    )
    chat_history = [
        {"user": row.message, "assistant": row.response}
        for row in history_rows
    ]

    # Get AI response
    response = chat_with_assistant(
        user_message=body.question,
        prescription_json=parsed,
        chat_history=chat_history,
        language=body.language,
    )

    # Save to DB
    log = ChatHistory(
        user_id=current_user.get("uid", ""),
        prescription_id=body.prescription_id,
        message=body.question,
        response=response,
        language=body.language,
    )
    db.add(log)
    db.commit()

    return {
        "question": body.question,
        "answer": response,
        "language": body.language,
    }


@router.get("/history/{prescription_id}")
def chat_history(
    prescription_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve the full chat history for a prescription."""
    rows = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.prescription_id == prescription_id,
            ChatHistory.user_id == current_user.get("uid", ""),
        )
        .order_by(ChatHistory.timestamp)
        .all()
    )

    return {
        "history": [
            {
                "message": r.message,
                "response": r.response,
                "language": r.language,
                "timestamp": r.timestamp,
            }
            for r in rows
        ]
    }
