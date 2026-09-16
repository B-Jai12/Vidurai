import json
import re
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-flash-latest")


def translate_medicines(medicines, target_language):
    try:
        if target_language == "English":
            return medicines

        prompt = f"""Translate the following medicine explanations into {target_language}.

Rules:
1. Keep ALL medicine names in English (e.g. Metformin, Atorvastatin)
2. Keep ALL dosage numbers in English (e.g. 500mg, 10mg)
3. Keep ALL frequency codes in English (e.g. BD, TDS, OD)
4. CRITICAL: Maintain exact medical accuracy in the translation. Do not hallucinate or omit details.
5. Translate the following fields ONLY into the target language using simple, accessible everyday vocabulary:
   - simple_explanation
   - instructions
   - side_effects
   - food_interactions
   - what_it_treats
6. Return the exact same JSON array structure.
7. Return ONLY the JSON array. absolutely no conversational text, formatting, or markdown wrappers.

Medicines JSON:
{json.dumps(medicines, indent=2)}"""

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=4000,
            )
        )

        response_text = response.text.strip()
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        response_text = response_text.strip()

        translated = json.loads(response_text)
        return translated

    except Exception as e:
        print(f"translate_medicines error: {e}")
        return medicines


def translate_text(text, target_language):
    try:
        if target_language == "English":
            return text

        prompt = f"""Translate this text into {target_language}.
Use simple everyday words.
Return ONLY the translated text. Nothing else.

Text: {text}"""

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=500,
            )
        )

        return response.text.strip()

    except Exception as e:
        print(f"translate_text error: {e}")
        return text


def translate_full_prescription(parsed_json, target_language):
    try:
        if target_language == "English":
            return parsed_json

        prompt = f"""Translate all explanation fields in this prescription JSON into {target_language}.

Rules:
1. Keep medicine names in English
2. Keep dosage numbers in English
3. Keep frequency codes in English (BD, TDS, OD)
4. Keep doctor name, hospital name, dates in original
5. CRITICAL: Maintain exact medical accuracy in the translation. Explain complex terms simply.
6. Translate these explicitly into the target language: simple_explanation, instructions, side_effects, food_interactions, what_it_treats, special_instructions, drug_interactions descriptions, red_flags.
7. Return the exact same JSON structure.
8. Return ONLY the JSON. No conversational text or markdown blocks.

Prescription JSON:
{json.dumps(parsed_json, indent=2)}"""

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=4000,
            )
        )

        response_text = response.text.strip()
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        response_text = response_text.strip()

        translated = json.loads(response_text)
        return translated

    except Exception as e:
        print(f"translate_full_prescription error: {e}")
        return parsed_json