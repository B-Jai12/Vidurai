import os
import time
from datetime import datetime
from utils.constants import CONTROLLED_SUBSTANCES
from dotenv import load_dotenv

load_dotenv()

def check_authenticity(parsed_json):
    try:
        score = 10.0
        reasons = []

        if not parsed_json:
            return 0.0

        prescription_date = parsed_json.get("prescription_date", "")
        if not prescription_date or prescription_date == "Not specified":
            score -= 3
            reasons.append("Prescription date missing")
        else:
            try:
                for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"]:
                    try:
                        date_obj = datetime.strptime(prescription_date, fmt)
                        days_old = (datetime.now() - date_obj).days
                        if days_old > 30:
                            score -= 3
                            reasons.append(f"Prescription is {days_old} days old")
                        break
                    except:
                        continue
            except:
                pass

        doctor_reg = parsed_json.get("doctor_registration", "")
        if not doctor_reg or doctor_reg == "Not specified":
            score -= 2
            reasons.append("Doctor registration number missing")

        hospital = parsed_json.get("hospital_name", "")
        if not hospital or hospital == "Not specified":
            score -= 1
            reasons.append("Hospital name missing")

        patient = parsed_json.get("patient_name", "")
        if not patient or patient == "Not specified":
            score -= 1
            reasons.append("Patient name missing")

        medicines = parsed_json.get("medicines", [])
        for med in medicines:
            med_name = med.get("name", "").lower()
            for controlled in CONTROLLED_SUBSTANCES:
                if controlled in med_name:
                    if not doctor_reg or doctor_reg == "Not specified":
                        score -= 2
                        reasons.append(f"{med.get('name')} is a controlled substance")
                    break

        import streamlit as st
        st.session_state.authenticity_reasons = reasons

        return max(0.0, min(10.0, score))

    except Exception as e:
        return 5.0