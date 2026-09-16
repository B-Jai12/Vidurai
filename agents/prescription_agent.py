import os
from dotenv import load_dotenv

load_dotenv()

import json
import re
import google.generativeai as genai
from openai import OpenAI

XAI_API_KEY = os.getenv("XAI_API_KEY")
client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
MODEL = "grok-2-latest"

def parse_prescription(raw_text):
    try:
        prompt = f"""You are a senior clinical pharmacist and medical prescription parser.
Given this raw handwritten prescription text, extract and return a highly accurate JSON object.

CRITICAL RULES:
1. ONLY extract what is explicitly written. Do NOT hallucinate or guess missing fields.
2. If a field is missing, you MUST set its value exactly to "Not specified".
3. Medicine Normalization: Extract the exact medicine name written, but intelligently map it to its generic name in the `generic_name` field. DO NOT duplicate dosages in the name (e.g. if it says "Clavam 625 625mg", output name: "Clavam 625").
4. Safety Classification: Every medicine MUST have a `status` field. It can ONLY be one of these three values:
   - "Normal" (Standard safe medicine)
   - "Monitor" (Needs monitoring, e.g., BP or diabetes meds, mild interactions)
   - "Caution" (High risk, antibiotics, strong painkillers, severe interactions)
5. Explain things simply as if speaking to a patient with Class 5 education.
6. Return ONLY valid JSON matching this exact structure. No markdown blocks, no text outside JSON.

Return this exact structure:
{{
  "doctor_name": "",
  "doctor_registration": "",
  "hospital_name": "",
  "prescription_date": "",
  "patient_name": "",
  "patient_age": "",
  "diagnosis": "",
  "medicines": [
    {{
      "name": "",
      "generic_name": "",
      "generic_cost_saving": "",
      "dosage": "",
      "frequency": "",
      "timing": "",
      "duration": "",
      "quantity": "",
      "instructions": "",
      "simple_explanation": "",
      "what_it_treats": "",
      "status": "Normal | Monitor | Caution",
      "side_effects": [],
      "food_interactions": [],
      "drug_class": "",
      "can_crush": false,
      "refrigeration_needed": false
    }}
  ],
  "special_instructions": "",
  "follow_up_date": "",
  "drug_interactions": [
    {{
      "medicines": [],
      "severity": "low | high",
      "description": "",
      "action": ""
    }}
  ],
  "red_flags": []
}}

Raw prescription text:
{raw_text}"""

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.1
            )
            response_text = response.choices[0].message.content.strip()
        except Exception as grok_e:
            print(f"xAI Grok parsing failed: {grok_e}. Falling back to Gemini.")
            gemini_model = genai.GenerativeModel("gemini-flash-latest")
            gemini_response = gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=8000,
                    response_mime_type="application/json",
                )
            )
            response_text = gemini_response.text.strip()

        # Clean markdown if present
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'^```\s*', '', response_text)
        response_text = re.sub(r'```$', '', response_text)
        response_text = response_text.strip()

        parsed_json = json.loads(response_text)
        return parsed_json

    except json.JSONDecodeError as e:
        print(f"JSON Parsing Error: {e}")
        print(f"Raw Output causing error:\n{response_text}")
        return None
    except Exception as e:
        print(f"parse_prescription error: {e}")
        return None


def chat_with_assistant(user_message, prescription_json, chat_history, language):
    try:
        system_prompt = f"""You are Vidur, a caring and knowledgeable medical assistant.
You have been given the full details of the patient's current prescription.

Your rules:
1. ALWAYS respond in the exact same language the user writes in.
   If they write in Hindi — respond in Hindi.
   If Telugu — respond in Telugu.
   If English — respond in English.

2. Use the prescription context below to give specific accurate answers.

3. You can answer questions about:
   - What each medicine does
   - When to take medicines
   - What to do if a dose is missed
   - Food and drink interactions
   - Common side effects
   - Generic alternatives and cost savings

4. You MUST REFUSE to change dosages, recommend stopping medicine, or prescribe new medicines.

5. Always end serious answers with: Please consult your doctor for final advice.

6. Keep responses SHORT and SIMPLE. Maximum 3 sentences.

Current Prescription:
{json.dumps(prescription_json, indent=2)}

User preferred language: {language}"""

        messages = [{"role": "system", "content": system_prompt}]

        for msg in chat_history:
            messages.append({"role": "user", "content": msg["user"]})
            messages.append({"role": "assistant", "content": msg["assistant"]})

        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"chat error: {e}")
        return "Sorry, I could not process your question. Please try again."