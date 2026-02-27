from gtts import gTTS
import streamlit as st
import tempfile
import os
from utils.constants import LANGUAGES

def speak(text, language_code="en"):
    try:
        if not text or text == "Not specified":
            st.warning("Nothing to speak.")
            return

        # Create temp file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3"
        ) as f:
            tts = gTTS(
                text=text,
                lang=language_code,
                slow=False
            )
            tts.save(f.name)
            temp_path = f.name

        # Play in streamlit
        with open(temp_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/mp3")

        # Clean up
        os.unlink(temp_path)

    except Exception as e:
        st.error(f"Voice output failed. Please try again.")


def speak_full_prescription(medicines, language_code="en"):
    try:
        if not medicines:
            st.warning("No medicines to read.")
            return

        # Build full text
        full_text = "Your prescription summary. "

        for i, med in enumerate(medicines, 1):
            name = med.get("name", "")
            explanation = med.get("simple_explanation", "")
            instructions = med.get("instructions", "")
            frequency = med.get("frequency", "")
            timing = med.get("timing", "")

            full_text += f"Medicine {i}. {name}. "
            full_text += f"{explanation}. "
            full_text += f"Take {frequency}. "
            full_text += f"{timing}. "
            full_text += f"{instructions}. "

        full_text += "Please consult your doctor for final advice."

        # Create and play
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3"
        ) as f:
            tts = gTTS(
                text=full_text,
                lang=language_code,
                slow=False
            )
            tts.save(f.name)
            temp_path = f.name

        with open(temp_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/mp3")

        os.unlink(temp_path)

    except Exception as e:
        st.error("Could not read prescription. Please try again.")


def speak_drug_warning(interactions, language_code="en"):
    try:
        if not interactions:
            return

        warning_text = "Drug interaction warning. "

        for interaction in interactions:
            medicines = " and ".join(
                interaction.get("medicines", [])
            )
            description = interaction.get("description", "")
            action = interaction.get("action", "")

            warning_text += f"{medicines}. {description}. {action}. "

        warning_text += "Please consult your doctor immediately."

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3"
        ) as f:
            tts = gTTS(
                text=warning_text,
                lang=language_code,
                slow=True
            )
            tts.save(f.name)
            temp_path = f.name

        with open(temp_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/mp3")

        os.unlink(temp_path)

    except Exception as e:
        st.error("Could not read warning. Please try again.")