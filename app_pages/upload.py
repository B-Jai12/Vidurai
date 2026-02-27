import streamlit as st
import json
from agents.ocr_agent import extract_text
from agents.prescription_agent import parse_prescription
from agents.authenticity_agent import check_authenticity
from database.db import get_session
from database.models import Prescription, Medicine
from datetime import datetime, timedelta

DEMO_PARSED = {
    "doctor_name": "Dr. Ramesh Sharma",
    "doctor_registration": "MCI-12345",
    "hospital_name": "Apollo Hospitals, Hyderabad",
    "prescription_date": "27/02/2025",
    "patient_name": "Ravi Kumar",
    "patient_age": "52",
    "diagnosis": "Type 2 Diabetes, Hypertension",
    "medicines": [
        {
            "name": "Metformin",
            "generic_name": "Metformin HCl",
            "generic_cost_saving": "Save Rs.180 by using generic Metformin",
            "dosage": "500mg",
            "frequency": "BD",
            "timing": "After food",
            "duration": "30 days",
            "quantity": "60 tablets",
            "instructions": "Take twice daily after meals with water",
            "simple_explanation": "This medicine controls your blood sugar. It helps your body use insulin properly so sugar does not build up in your blood.",
            "what_it_treats": "Type 2 Diabetes",
            "side_effects": ["Nausea", "Stomach upset", "Diarrhea initially"],
            "food_interactions": ["Avoid alcohol", "Take after meals to reduce stomach upset"],
            "drug_class": "Biguanide",
            "can_crush": True,
            "refrigeration_needed": False
        },
        {
            "name": "Atorvastatin",
            "generic_name": "Atorvastatin Calcium",
            "generic_cost_saving": "Save Rs.220 by using generic Atorvastatin",
            "dosage": "10mg",
            "frequency": "OD",
            "timing": "At bedtime",
            "duration": "30 days",
            "quantity": "30 tablets",
            "instructions": "Take once daily at night",
            "simple_explanation": "This medicine reduces bad cholesterol in your blood. It protects your heart by cleaning your blood vessels.",
            "what_it_treats": "High Cholesterol",
            "side_effects": ["Muscle pain", "Headache", "Mild liver changes"],
            "food_interactions": ["Avoid grapefruit juice", "Limit alcohol"],
            "drug_class": "Statin",
            "can_crush": False,
            "refrigeration_needed": False
        },
        {
            "name": "Amlodipine",
            "generic_name": "Amlodipine Besylate",
            "generic_cost_saving": "Save Rs.150 by using generic Amlodipine",
            "dosage": "5mg",
            "frequency": "OD",
            "timing": "Before food",
            "duration": "30 days",
            "quantity": "30 tablets",
            "instructions": "Take once daily in the morning",
            "simple_explanation": "This medicine relaxes your blood vessels so your heart does not have to work too hard. It lowers your blood pressure.",
            "what_it_treats": "Hypertension",
            "side_effects": ["Swollen ankles", "Flushing", "Dizziness"],
            "food_interactions": ["Avoid grapefruit", "Limit salt intake"],
            "drug_class": "Calcium Channel Blocker",
            "can_crush": True,
            "refrigeration_needed": False
        },
        {
            "name": "Aspirin",
            "generic_name": "Acetylsalicylic Acid",
            "generic_cost_saving": "Save Rs.50 by using generic Aspirin",
            "dosage": "75mg",
            "frequency": "OD",
            "timing": "After food",
            "duration": "30 days",
            "quantity": "30 tablets",
            "instructions": "Take once daily after breakfast",
            "simple_explanation": "This medicine thins your blood slightly to prevent clots. It protects against heart attack and stroke.",
            "what_it_treats": "Blood clot prevention",
            "side_effects": ["Stomach irritation", "Bleeding risk"],
            "food_interactions": ["Always take after food", "Avoid alcohol"],
            "drug_class": "Antiplatelet",
            "can_crush": False,
            "refrigeration_needed": False
        }
    ],
    "special_instructions": "Monitor BP weekly. Low salt diet. Walk 30 minutes daily.",
    "follow_up_date": "27/03/2025",
    "drug_interactions": [
        {
            "medicines": ["Aspirin", "Metformin"],
            "severity": "Mild",
            "description": "Aspirin may slightly affect blood sugar levels when combined with Metformin.",
            "action": "Monitor blood sugar regularly. Inform your doctor."
        }
    ],
    "red_flags": []
}


def save_and_show(parsed, auth_score, raw_text):
    db = get_session()

    prescription = Prescription(
        user_id=st.session_state.user_id,
        upload_date=datetime.utcnow(),
        raw_ocr_text=raw_text,
        parsed_json=json.dumps(parsed),
        authenticity_score=auth_score,
        is_active=True
    )
    db.add(prescription)
    db.flush()          # assigns prescription.id WITHOUT closing session
    pres_id = prescription.id   # grab it NOW while session is open

    for med in parsed.get("medicines", []):
        try:
            duration = int(
                str(med.get("duration", "30"))
                .replace(" days", "").replace("days", "").strip()
            )
        except:
            duration = 30
        try:
            qty = int(
                str(med.get("quantity", "30"))
                .replace(" tablets", "").replace("tabs", "").strip()
            )
        except:
            qty = 30

        medicine = Medicine(
            prescription_id=pres_id,   # use the captured id
            name=med.get("name", ""),
            dosage=med.get("dosage", ""),
            frequency=med.get("frequency", ""),
            timing=med.get("timing", ""),
            duration_days=duration,
            quantity_given=qty,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=duration)
        )
        db.add(medicine)

    db.commit()
    db.close()

    # Now safe to store in session
    st.session_state.current_prescription = parsed
    st.session_state.prescription_id = pres_id   # use captured id

    st.success("Prescription analysed successfully! ✅")

    if auth_score >= 8:
        st.success(f"Authenticity Score: {auth_score}/10 ✅ Verified")
    elif auth_score >= 5:
        st.warning(f"Authenticity Score: {auth_score}/10 ⚠️ Verify with pharmacist")
    else:
        st.error(f"Authenticity Score: {auth_score}/10 ❌ May be invalid")

    st.divider()

    interactions = parsed.get("drug_interactions", [])
    if interactions:
        st.error("### ⚠️ Drug Interaction Warnings")
        for interaction in interactions:
            meds = " + ".join(interaction.get("medicines", []))
            st.markdown(f"""
            <div style='background:#FCE8E6;border-left:4px solid #EA4335;
            padding:12px 16px;border-radius:8px;margin-bottom:8px;'>
                <strong>{meds}</strong><br>
                {interaction.get('description', '')}
                <br><small>{interaction.get('action', '')}</small>
            </div>
            """, unsafe_allow_html=True)

    red_flags = parsed.get("red_flags", [])
    if red_flags:
        st.warning("### 🚩 Red Flags")
        for flag in red_flags:
            st.markdown(f"- {flag}")

    st.divider()
    st.markdown("### Your Medicines")
    medicines = parsed.get("medicines", [])

    if st.session_state.language != "English":
        from agents.translation_agent import translate_medicines
        with st.spinner("Translating..."):
            medicines = translate_medicines(medicines, st.session_state.language)

    for i, med in enumerate(medicines):
        with st.expander(
            f"💊 {med.get('name', '')} — {med.get('dosage', '')}",
            expanded=True
        ):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Frequency:** {med.get('frequency', 'N/A')}")
                st.markdown(f"**Timing:** {med.get('timing', 'N/A')}")
                st.markdown(f"**Duration:** {med.get('duration', 'N/A')}")
            with col2:
                st.markdown(f"**Generic Name:** {med.get('generic_name', 'N/A')}")
                st.markdown(f"**Drug Class:** {med.get('drug_class', 'N/A')}")
                if med.get('generic_cost_saving'):
                    st.success(f"💰 {med.get('generic_cost_saving')}")
            with col3:
                st.markdown(f"**Treats:** {med.get('what_it_treats', 'N/A')}")

            st.markdown("---")
            st.markdown(f"**What it does:** {med.get('simple_explanation', 'N/A')}")
            st.markdown(f"**Instructions:** {med.get('instructions', 'N/A')}")

            side_effects = med.get('side_effects', [])
            if side_effects:
                with st.expander("Side Effects"):
                    for effect in side_effects:
                        st.markdown(f"- {effect}")

            food = med.get('food_interactions', [])
            if food:
                with st.expander("Food Interactions"):
                    for item in food:
                        st.markdown(f"- {item}")

            from agents.voice_agent import speak
            from utils.constants import LANGUAGES
            if st.button("🔊 Listen", key=f"voice_{i}"):
                lang_code = LANGUAGES.get(st.session_state.language, "en")
                speak(med.get('simple_explanation', ''), lang_code)

    st.divider()
    if st.button("Go to Dashboard →", type="primary", use_container_width=True):
        st.rerun()


def show():
    if "demo_mode" not in st.session_state:
        st.session_state.demo_mode = False

    st.markdown("## Upload Prescription")
    st.markdown("*Upload any prescription — photo, PDF or screenshot*")
    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### Upload Your Prescription")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["jpg", "jpeg", "png", "pdf", "webp"],
            help="Supports photos, PDFs and screenshots"
        )
        st.markdown("---")
        st.markdown("#### No prescription? Try Demo")

        if st.button("Load Sample Prescription", use_container_width=True):
            st.session_state.demo_mode = True
            st.rerun()

    with col2:
        if uploaded_file:
            if uploaded_file.type.startswith("image"):
                st.image(uploaded_file, caption="Uploaded Prescription", use_container_width=True)
            else:
                st.info("PDF uploaded successfully.")
        elif st.session_state.demo_mode:
            st.success("✅ Sample prescription loaded and ready!")
            st.markdown("""
            **Dr. Ramesh Sharma** | Apollo Hospitals
            **Patient:** Ravi Kumar, 52 years
            **Diagnosis:** Type 2 Diabetes, Hypertension
            **Medicines:** Metformin, Atorvastatin, Amlodipine, Aspirin
            """)

    st.divider()

    if st.session_state.demo_mode or uploaded_file:
        if st.button("Analyse Prescription", type="primary", use_container_width=True):
            if st.session_state.demo_mode:
                st.session_state.demo_mode = False
                save_and_show(DEMO_PARSED, 9.0, "demo")
            elif uploaded_file:
                with st.spinner("Reading prescription..."):
                    file_bytes = uploaded_file.read()
                    raw_text, confidence, method = extract_text(file_bytes, uploaded_file.type)
                with st.spinner("Analysing medicines..."):
                    parsed = parse_prescription(raw_text)
                with st.spinner("Checking authenticity..."):
                    auth_score = check_authenticity(parsed)

                if parsed and parsed.get("medicines"):
                    save_and_show(parsed, auth_score, raw_text)
                else:
                    st.error("Could not analyse prescription. Please try a clearer image.")