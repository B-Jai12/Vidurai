import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
client = Groq(api_key=GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"

def parse_prescription(raw_text):
    try:
        prompt = f"""You are a senior clinical pharmacist and medical prescription parser.
Given this raw prescription text, extract and return a valid JSON object.
Be accurate. If a field is unclear use your medical knowledge to infer it.
Never leave a field blank — use "Not specified" if truly absent.
For simple_explanation: explain as if speaking to a patient with Class 5 education.
For drug_interactions: check ALL medicine combinations in this prescription.
For red_flags: flag any dangerous dosages, duplicates, or unusual combinations.
Return ONLY the JSON. No markdown, no explanation, no code blocks.

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
      "severity": "",
      "description": "",
      "action": ""
    }}
  ],
  "red_flags": []
}}

Raw prescription text:
{raw_text}"""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.1
        )

        response_text = response.choices[0].message.content.strip()

        # Clean markdown if present
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        response_text = response_text.strip()

        parsed = json.loads(response_text)
        return parsed

    except json.JSONDecodeError:
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return None

    except Exception as e:
        print(f"parse_prescription error: {e}")
        return None


def chat_with_assistant(user_message, prescription_json, chat_history, language):
    try:
        system_prompt = f"""You are MedSaathi, a caring and knowledgeable medical assistant.
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