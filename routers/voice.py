"""
routers/voice.py — Text-to-speech endpoints, return MP3 audio.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from agents.voice_agent import speak, speak_full_prescription, speak_drug_warning
from schemas.prescription import SpeakRequest, SpeakFullRequest, DrugWarningRequest

router = APIRouter(prefix="/voice", tags=["Voice / TTS"])

_MP3 = "audio/mpeg"


@router.post("/speak")
def tts_speak(body: SpeakRequest):
    """Convert a text string to MP3 audio."""
    if not body.text:
        raise HTTPException(status_code=400, detail="text is required")
    audio = speak(body.text, body.language_code)
    if not audio:
        raise HTTPException(status_code=500, detail="TTS generation failed")
    return Response(content=audio, media_type=_MP3)


@router.post("/speak-full")
def tts_speak_full(body: SpeakFullRequest):
    """Narrate an entire prescription medicine list as MP3 audio."""
    if not body.medicines:
        raise HTTPException(status_code=400, detail="medicines list is empty")
    audio = speak_full_prescription(body.medicines, body.language_code)
    if not audio:
        raise HTTPException(status_code=500, detail="TTS generation failed")
    return Response(content=audio, media_type=_MP3)


@router.post("/drug-warning")
def tts_drug_warning(body: DrugWarningRequest):
    """Narrate drug interaction warnings as MP3 audio."""
    if not body.interactions:
        raise HTTPException(status_code=400, detail="interactions list is empty")
    audio = speak_drug_warning(body.interactions, body.language_code)
    if not audio:
        raise HTTPException(status_code=500, detail="TTS generation failed")
    return Response(content=audio, media_type=_MP3)
