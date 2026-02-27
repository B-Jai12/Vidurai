import json
import re
from groq import Groq

GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"


def translate_medicines(medicines, target_language):
    try:
        if target_language == "English":
            return medicines

        prompt = f"""Translate the following medicine explanations into {target_language}.

Rules:
1. Keep ALL medicine names in English (Metformin, Atorvastatin etc)
2. Keep ALL dosage numbers in English (500mg, 10mg etc)
3. Keep ALL frequency codes in English (BD, TDS, OD etc)
4. ONLY translate these fields:
   - simple_explanation
   - instructions
   - side_effects
   - food_interactions
   - what_it_treats
5. Return the exact same JSON array structure
6. Use simple everyday words
7. Return ONLY the JSON array. No extra text. No markdown.

Medicines JSON:
{json.dumps(medicines, indent=2)}"""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.1
        )

        response_text = response.choices[0].message.content.strip()
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

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )

        return response.choices[0].message.content.strip()

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
5. Translate: simple_explanation, instructions, side_effects,
   food_interactions, what_it_treats, special_instructions,
   drug_interactions descriptions, red_flags
6. Return the exact same JSON structure
7. Return ONLY the JSON. No extra text. No markdown.

Prescription JSON:
{json.dumps(parsed_json, indent=2)}"""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.1
        )

        response_text = response.choices[0].message.content.strip()
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        response_text = response_text.strip()

        translated = json.loads(response_text)
        return translated

    except Exception as e:
        print(f"translate_full_prescription error: {e}")
        return parsed_json