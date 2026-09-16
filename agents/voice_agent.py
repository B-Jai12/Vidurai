"""
voice_agent.py — Text-to-speech using gTTS.
Returns MP3 audio bytes. No Streamlit dependency.
"""
from gtts import gTTS
import tempfile
import io
import os


def _text_to_mp3_bytes(text: str, language_code: str = "en", slow: bool = False) -> bytes:
    """Convert text to MP3 bytes using gTTS."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tts = gTTS(text=text, lang=language_code, slow=slow)
        tts.save(f.name)
        temp_path = f.name

    with open(temp_path, "rb") as audio_file:
        audio_bytes = audio_file.read()

    os.unlink(temp_path)
    return audio_bytes


def speak(text: str, language_code: str = "en") -> bytes:
    """
    Convert a single text string to MP3 audio bytes.
    Returns empty bytes if text is missing.
    """
    if not text or text == "Not specified":
        return b""
    try:
        return _text_to_mp3_bytes(text, language_code)
    except Exception as e:
        print(f"speak() error: {e}")
        return b""


def speak_full_prescription(medicines: list, language_code: str = "en") -> bytes:
    """
    Build a narrated summary of all medicines and return as MP3 bytes.
    """
    if not medicines:
        return b""

    try:
        full_text = "Your prescription summary. "

        for i, med in enumerate(medicines, 1):
            name        = med.get("name", "")
            explanation = med.get("simple_explanation", "")
            frequency   = med.get("frequency", "")
            timing      = med.get("timing", "")
            instructions = med.get("instructions", "")

            full_text += f"Medicine {i}. {name}. "
            full_text += f"{explanation}. "
            full_text += f"Take {frequency}. "
            full_text += f"{timing}. "
            full_text += f"{instructions}. "

        full_text += "Please consult your doctor for final advice."

        return _text_to_mp3_bytes(full_text, language_code)

    except Exception as e:
        print(f"speak_full_prescription() error: {e}")
        return b""


def speak_drug_warning(interactions: list, language_code: str = "en") -> bytes:
    """
    Narrate drug interaction warnings and return as MP3 bytes.
    """
    if not interactions:
        return b""

    try:
        warning_text = "Drug interaction warning. "

        for interaction in interactions:
            medicines    = " and ".join(interaction.get("medicines", []))
            description  = interaction.get("description", "")
            action       = interaction.get("action", "")
            warning_text += f"{medicines}. {description}. {action}. "

        warning_text += "Please consult your doctor immediately."

        return _text_to_mp3_bytes(warning_text, language_code, slow=True)

    except Exception as e:
        print(f"speak_drug_warning() error: {e}")
        return b""