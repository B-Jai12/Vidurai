import streamlit as st
import json
from database.db import get_session
from database.models import FamilyProfile, Prescription, Medicine
from agents.prescription_agent import chat_with_assistant
from agents.voice_agent import speak
from agents.report_agent import generate_report
from agents.alarm_agent import send_refill_reminder, send_generic_savings_alert
from utils.constants import LANGUAGES
from datetime import datetime

def show():
    st.markdown("## Caregiver Mode")
    st.markdown("*Manage prescriptions for your entire family*")
    st.divider()

    user_id = st.session_state.get("user_id")
    db = get_session()

    # ── FAMILY MEMBERS ────────────────────────────────────
    members = db.query(FamilyProfile).filter(
        FamilyProfile.owner_user_id == user_id
    ).all()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Family Members")

    with col2:
        if st.button("Add Member", use_container_width=True):
            st.session_state.show_add_member = True

    # ── ADD MEMBER FORM ───────────────────────────────────
    if st.session_state.get("show_add_member"):
        with st.form("add_member_form"):
            st.markdown("#### Add Family Member")
            col1, col2 = st.columns(2)
            with col1:
                member_name = st.text_input(
                    "Name",
                    placeholder="e.g. Grandma"
                )
                age = st.number_input(
                    "Age",
                    min_value=0,
                    max_value=120,
                    value=60
                )
            with col2:
                relationship = st.selectbox(
                    "Relationship",
                    [
                        "Parent", "Spouse", "Child",
                        "Grandparent", "Sibling", "Other"
                    ]
                )
                language = st.selectbox(
                    "Preferred Language",
                    list(LANGUAGES.keys())
                )

            col1, col2 = st.columns(2)
            with col1:
                add = st.form_submit_button(
                    "Add Member",
                    use_container_width=True
                )
            with col2:
                cancel = st.form_submit_button(
                    "Cancel",
                    use_container_width=True
                )

            if add and member_name:
                new_member = FamilyProfile(
                    owner_user_id=user_id,
                    member_name=member_name,
                    age=age,
                    relationship=relationship,
                    preferred_language=language
                )
                db.add(new_member)
                db.commit()
                st.success(f"{member_name} added!")
                st.session_state.show_add_member = False
                st.rerun()

            if cancel:
                st.session_state.show_add_member = False
                st.rerun()

    # ── SHOW MEMBERS ──────────────────────────────────────
    if not members:
        st.info(
            "No family members added yet. "
            "Click 'Add Member' to get started."
        )
        db.close()
        return

    # Member selector
    member_names = [m.member_name for m in members]
    selected_name = st.selectbox(
        "Select Family Member",
        member_names
    )
    selected = next(
        (m for m in members if m.member_name == selected_name),
        None
    )

    if not selected:
        db.close()
        return

    # Member card
    st.markdown(f"""
    <div style='background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);
    border-radius:12px;padding:20px;margin:16px 0;'>
        <h3 style='margin:0 0 8px 0;color:#E2E8F0;'>
            {selected.member_name}
        </h3>
        <p style='margin:0;color:#A0AEC0;font-size:14px;'>
            {selected.relationship} &nbsp;|&nbsp;
            Age: {selected.age} &nbsp;|&nbsp;
            Language: {selected.preferred_language}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── MEMBER PRESCRIPTIONS ──────────────────────────────
    # Query prescriptions: try family_profile_id first, then fall back to user_id
    prescriptions = db.query(Prescription).filter(
        Prescription.family_profile_id == selected.id
    ).order_by(Prescription.upload_date.desc()).all()

    # If no prescriptions linked to family member, show user's own prescriptions
    if not prescriptions:
        prescriptions = db.query(Prescription).filter(
            Prescription.user_id == user_id
        ).order_by(Prescription.upload_date.desc()).all()

    st.markdown(f"### Prescriptions for {selected.member_name}")

    tab1, tab2, tab3 = st.tabs([
        "Active Prescription",
        "History",
        "Send Notifications"
    ])

    # ── TAB 1 — ACTIVE PRESCRIPTION ──────────────────────
    with tab1:
        if not prescriptions:
            st.info(
                f"No prescriptions uploaded for {selected.member_name} yet."
            )

            # Allow uploading for this member
            if st.button("Upload Prescription for this Member", type="primary", use_container_width=True):
                st.session_state.caregiver_member_id = selected.id
                st.session_state.nav_page = 0  # 0 = "Upload Prescription"
                st.rerun()
        else:
            latest = prescriptions[0]
            try:
                parsed = json.loads(latest.parsed_json)
            except:
                parsed = {}

            # Auth score
            auth = latest.authenticity_score or 0
            if auth >= 8:
                st.success(f"Authenticity Score: {auth}/10 ✅")
            elif auth >= 5:
                st.warning(f"Authenticity Score: {auth}/10 ⚠️")
            else:
                st.error(f"Authenticity Score: {auth}/10 ❌")

            # Patient info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Doctor",
                    parsed.get("doctor_name", "N/A")
                )
            with col2:
                st.metric(
                    "Date",
                    parsed.get("prescription_date", "N/A")
                )
            with col3:
                st.metric(
                    "Follow Up",
                    parsed.get("follow_up_date", "N/A")
                )

            # Diagnosis
            diagnosis = parsed.get("diagnosis", "")
            if diagnosis:
                st.info(f"**Diagnosis:** {diagnosis}")

            # Drug interactions
            interactions = parsed.get("drug_interactions", [])
            if interactions:
                st.error("⚠️ Drug Interaction Warnings Detected")
                for i in interactions:
                    meds = " + ".join(i.get("medicines", []))
                    st.markdown(f"- **{meds}**: {i.get('description','')}")

            st.divider()

            # Medicines
            lang = selected.preferred_language
            lang_code = LANGUAGES.get(lang, "en")
            medicines = parsed.get("medicines", [])

            if lang != "English" and medicines:
                from agents.translation_agent import translate_medicines
                with st.spinner(f"Translating to {lang}..."):
                    medicines = translate_medicines(medicines, lang)

            st.markdown(
                f"### Medicines — *{lang}*"
            )

            for i, med in enumerate(medicines):
                with st.expander(
                    f"💊 {med.get('name','')} — {med.get('dosage','')}",
                    expanded=(i == 0)
                ):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Frequency:** {med.get('frequency','N/A')}")
                        st.markdown(f"**Timing:** {med.get('timing','N/A')}")
                        st.markdown(f"**Duration:** {med.get('duration','N/A')}")
                    with col2:
                        st.markdown(f"**Generic:** {med.get('generic_name','N/A')}")
                        st.markdown(f"**Treats:** {med.get('what_it_treats','N/A')}")
                        savings = med.get("generic_cost_saving","")
                        if savings and savings != "Not specified":
                            st.success(f"💰 {savings}")

                    st.markdown(
                        f"**Simple explanation:** "
                        f"{med.get('simple_explanation','N/A')}"
                    )

                    if st.button(
                        "🔊 Listen",
                        key=f"cg_voice_{i}"
                    ):
                        speak(
                            med.get("simple_explanation",""),
                            lang_code
                        )

            # Download report
            st.divider()
            if st.button(
                "Download PDF Report",
                use_container_width=True
            ):
                with st.spinner("Generating..."):
                    pdf_path = generate_report(
                        parsed,
                        selected.member_name
                    )
                if pdf_path:
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    st.download_button(
                        "Download PDF",
                        data=pdf_bytes,
                        file_name=f"Vidur_{selected.member_name}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

    # ── TAB 2 — HISTORY ───────────────────────────────────
    with tab2:
        if not prescriptions:
            st.info("No prescription history found.")
        else:
            for i, pres in enumerate(prescriptions):
                try:
                    parsed = json.loads(pres.parsed_json)
                    med_count = len(parsed.get("medicines", []))
                    doctor = parsed.get("doctor_name", "Unknown")
                except:
                    med_count = 0
                    doctor = "Unknown"

                with st.expander(
                    f"Prescription {i+1} — "
                    f"{pres.upload_date.strftime('%d %b %Y')} "
                    f"| Dr. {doctor} | {med_count} medicines"
                ):
                    auth = pres.authenticity_score or 0
                    if auth >= 8:
                        st.success(f"Auth Score: {auth}/10")
                    elif auth >= 5:
                        st.warning(f"Auth Score: {auth}/10")
                    else:
                        st.error(f"Auth Score: {auth}/10")

                    if st.button(
                        "Load this prescription",
                        key=f"load_cg_{i}"
                    ):
                        try:
                            st.session_state.current_prescription = (
                                json.loads(pres.parsed_json)
                            )
                            st.session_state.prescription_id = pres.id
                            st.success("Prescription loaded!")
                        except:
                            st.error("Could not load prescription.")

    # ── TAB 3 — NOTIFICATIONS ─────────────────────────────
    with tab3:
        st.markdown(
            f"### Send Alerts for {selected.member_name}"
        )

        notify_email = st.text_input(
            "📧 Email",
            placeholder="caregiver@gmail.com",
            key="cg_email"
        )

        if prescriptions:
            try:
                parsed = json.loads(prescriptions[0].parsed_json)
                medicines = parsed.get("medicines", [])
            except Exception:
                medicines = []

            savings_meds = [
                m for m in medicines
                if m.get("generic_cost_saving")
                and m.get("generic_cost_saving") != "Not specified"
            ]

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "💰 Send Savings Alert",
                    use_container_width=True,
                    key="cg_savings"
                ):
                    if not notify_email:
                        st.error("Enter an email address.")
                    else:
                        with st.spinner("Sending..."):
                            results = send_generic_savings_alert(
                                savings_meds,
                                to_email=notify_email
                            )
                        if results.get("email"):
                            st.success("✅ Email sent!")
                        else:
                            st.error("Failed to send. Check email credentials.")

            with col2:
                if st.button(
                    "💊 Send Refill Reminder",
                    use_container_width=True,
                    key="cg_refill"
                ):
                    if not notify_email:
                        st.error("Enter an email address.")
                    elif medicines:
                        with st.spinner("Sending..."):
                            results = send_refill_reminder(
                                medicines[0].get("name", "Medicine"),
                                3,
                                to_email=notify_email
                            )
                        if results.get("email"):
                            st.success("✅ Refill reminder emailed!")
                        else:
                            st.error("Failed to send. Check email credentials.")
        else:
            st.info(
                "Upload a prescription first to send notifications."
            )

    db.close()