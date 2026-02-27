import streamlit as st
import json
from datetime import datetime
from database.db import get_session
from database.models import Prescription, Medicine
from agents.prescription_agent import chat_with_assistant
from agents.voice_agent import speak, speak_full_prescription
from agents.report_agent import generate_report
from agents.alarm_agent import (
    send_refill_reminder,
    send_generic_savings_alert,
    show_refill_status
)
from agents.pharmacy_agent import (
    get_nearby_hospitals,
    get_nearby_pharmacies,
    get_user_location_from_ip
)
from utils.constants import LANGUAGES, SPECIALTY_MAP

def show():
    st.markdown("## Dashboard")

    # ── AUTO-LOAD PRESCRIPTION FROM DB ───────────────────
    if not st.session_state.get("current_prescription"):
        user_id = st.session_state.get("user_id")
        if user_id:
            try:
                db = get_session()
                latest = (
                    db.query(Prescription)
                    .filter(Prescription.user_id == user_id)
                    .order_by(Prescription.upload_date.desc())
                    .first()
                )
                db.close()
                if latest and latest.parsed_json:
                    import json as _json
                    st.session_state.current_prescription = _json.loads(latest.parsed_json)
                    st.session_state.prescription_id = latest.id
                    st.rerun()
            except Exception as e:
                pass

    if not st.session_state.get("current_prescription"):
        st.info("📋 No prescription loaded yet. Upload one to see all features here.")
        if st.button("📤 Upload Prescription", type="primary", use_container_width=True):
            st.rerun()
        return

    parsed = st.session_state.current_prescription
    lang   = st.session_state.get("language", "English")
    lang_code = LANGUAGES.get(lang, "en")

    # ── TABS ─────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Medicines",
        "AI Assistant",
        "Nearby Help",
        "Refill & Savings",
        "Download Report"
    ])

    # ════════════════════════════════════════════════════
    # TAB 1 — MEDICINES
    # ════════════════════════════════════════════════════
    with tab1:
        # Patient info strip
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Patient",   parsed.get("patient_name", "N/A"))
        with col2:
            st.metric("Doctor",    parsed.get("doctor_name",  "N/A"))
        with col3:
            st.metric("Date",      parsed.get("prescription_date", "N/A"))
        with col4:
            st.metric("Follow Up", parsed.get("follow_up_date", "N/A"))

        st.divider()

        # Diagnosis
        diagnosis = parsed.get("diagnosis", "")
        if diagnosis and diagnosis != "Not specified":
            st.info(f"**Diagnosis:** {diagnosis}")

        # Drug interaction warnings
        interactions = parsed.get("drug_interactions", [])
        if interactions:
            st.error("### ⚠️ Drug Interaction Warnings")
            for interaction in interactions:
                meds = " + ".join(interaction.get("medicines", []))
                st.markdown(f"""
                <div style='background:#7B1A1A;border-left:4px solid #FF4444;
                padding:12px 16px;border-radius:8px;margin-bottom:8px;color:white;'>
                    <strong>{meds}</strong><br>
                    {interaction.get("description","")}<br>
                    <small><em>{interaction.get("action","")}</em></small>
                </div>
                """, unsafe_allow_html=True)

        # Red flags
        red_flags = parsed.get("red_flags", [])
        if red_flags:
            st.warning("### 🚩 Red Flags")
            for flag in red_flags:
                st.markdown(f"- {flag}")

        st.divider()

        # Language selector
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### Your Medicines — *{lang}*")
        with col2:
            if st.button("🔊 Listen to All", use_container_width=True):
                speak_full_prescription(
                    parsed.get("medicines", []), lang_code
                )

        medicines = parsed.get("medicines", [])

        # Translate if needed
        if lang != "English":
            from agents.translation_agent import translate_medicines
            with st.spinner(f"Translating to {lang}..."):
                medicines = translate_medicines(medicines, lang)

        if not medicines:
            st.warning("No medicines found in this prescription.")
        else:
            for i, med in enumerate(medicines):
                name    = med.get("name", "Medicine")
                dosage  = med.get("dosage", "")
                savings = med.get("generic_cost_saving", "")

                with st.expander(
                    f"💊 {name} — {dosage}",
                    expanded=(i == 0)
                ):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(f"**Frequency:** {med.get('frequency','N/A')}")
                        st.markdown(f"**Timing:** {med.get('timing','N/A')}")
                        st.markdown(f"**Duration:** {med.get('duration','N/A')}")
                        st.markdown(f"**Quantity:** {med.get('quantity','N/A')}")

                    with col2:
                        st.markdown(f"**Generic Name:** {med.get('generic_name','N/A')}")
                        st.markdown(f"**Drug Class:** {med.get('drug_class','N/A')}")
                        st.markdown(f"**Treats:** {med.get('what_it_treats','N/A')}")

                    with col3:
                        crush = "✅ Yes" if med.get("can_crush") else "❌ No"
                        fridge = "✅ Yes" if med.get("refrigeration_needed") else "❌ No"
                        st.markdown(f"**Can Crush:** {crush}")
                        st.markdown(f"**Refrigerate:** {fridge}")

                    st.markdown("---")
                    st.markdown(
                        f"**In simple words:** {med.get('simple_explanation','N/A')}"
                    )
                    st.markdown(
                        f"**Instructions:** {med.get('instructions','N/A')}"
                    )

                    if savings and savings != "Not specified":
                        st.success(f"💰 {savings}")

                    col1, col2 = st.columns(2)
                    with col1:
                        side_effects = med.get("side_effects", [])
                        if side_effects:
                            with st.expander("Side Effects"):
                                for effect in side_effects:
                                    st.markdown(f"- {effect}")
                    with col2:
                        food = med.get("food_interactions", [])
                        if food:
                            with st.expander("Food Interactions"):
                                for item in food:
                                    st.markdown(f"- {item}")

                    if st.button(
                        f"🔊 Listen",
                        key=f"voice_{i}",
                        use_container_width=True
                    ):
                        speak(
                            med.get("simple_explanation", ""),
                            lang_code
                        )

    # ════════════════════════════════════════════════════
    # TAB 2 — AI ASSISTANT
    # ════════════════════════════════════════════════════
    with tab2:
        st.markdown("### AI Medicine Assistant")
        st.markdown(
            "*Ask anything about your medicines — in any language*"
        )

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message("user"):
                st.write(msg["user"])
            with st.chat_message("assistant"):
                st.write(msg["assistant"])

        # Chat input
        user_input = st.chat_input(
            "Ask about your medicines..."
        )

        if user_input:
            with st.chat_message("user"):
                st.write(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = chat_with_assistant(
                        user_input,
                        parsed,
                        st.session_state.chat_history,
                        lang
                    )
                st.write(response)

            st.session_state.chat_history.append({
                "user":      user_input,
                "assistant": response
            })

        if st.session_state.chat_history:
            if st.button("Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()

    # ════════════════════════════════════════════════════
    # TAB 3 — NEARBY HELP
    # ════════════════════════════════════════════════════
    with tab3:
        st.markdown("### Nearby Hospitals & Pharmacies")

        # Get location
        lat, lng, city = get_user_location_from_ip()
        st.info(f"📍 Showing results near: **{city}**")

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "Find Nearby Hospitals",
                use_container_width=True
            ):
                with st.spinner("Finding hospitals..."):
                    hospitals = get_nearby_hospitals(lat, lng)

                if hospitals:
                    for h in hospitals[:5]:
                        open_status = (
                            "🟢 Open" if h.get("open_now") else
                            "🔴 Closed" if h.get("open_now") is False else
                            "⚪ Unknown"
                        )
                        st.markdown(f"""
                        <div style='background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);
                        border-radius:10px;padding:14px;margin-bottom:10px;'>
                            <strong style='color:#E2E8F0;'>{h["name"]}</strong><br>
                            <small style='color:#A0AEC0;'>{h["address"]}</small><br>
                            <small style='color:#A0AEC0;'>⭐ {h["rating"]} &nbsp;|&nbsp; {open_status}</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("No hospitals found nearby. Check your Places API key.")

        with col2:
            if st.button(
                "Find Nearby Pharmacies",
                use_container_width=True
            ):
                with st.spinner("Finding pharmacies..."):
                    pharmacies = get_nearby_pharmacies(lat, lng)

                if pharmacies:
                    for p in pharmacies[:5]:
                        open_status = (
                            "🟢 Open" if p.get("open_now") else
                            "🔴 Closed" if p.get("open_now") is False else
                            "⚪ Unknown"
                        )
                        st.markdown(f"""
                        <div style='background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);
                        border-radius:10px;padding:14px;margin-bottom:10px;'>
                            <strong style='color:#E2E8F0;'>{p["name"]}</strong><br>
                            <small style='color:#A0AEC0;'>{p["address"]}</small><br>
                            <small style='color:#A0AEC0;'>⭐ {p["rating"]} &nbsp;|&nbsp; {open_status}</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("No pharmacies found nearby.")

        # Specialist finder
        st.divider()
        st.markdown("### Find a Specialist")
        diagnosis = parsed.get("diagnosis", "").lower()
        suggested = None
        for condition, specialist in SPECIALTY_MAP.items():
            if condition in diagnosis:
                suggested = specialist
                break

        if suggested:
            st.info(f"Based on your diagnosis, you may need a **{suggested}**.")

        specialty = st.text_input(
            "Search specialist",
            value=suggested or "",
            placeholder="e.g. cardiologist, endocrinologist"
        )

        if st.button("Find Specialist Hospitals"):
            with st.spinner("Searching..."):
                from agents.pharmacy_agent import get_specialist_hospitals
                results = get_specialist_hospitals(lat, lng, specialty)
            if results:
                for h in results[:5]:
                    st.markdown(f"""
                    <div style='background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);
                    border-radius:10px;padding:14px;margin-bottom:10px;'>
                        <strong style='color:#E2E8F0;'>{h["name"]}</strong><br>
                        <small style='color:#A0AEC0;'>{h["address"]}</small><br>
                        <small style='color:#A0AEC0;'>⭐ {h["rating"]}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No results found.")

    # ════════════════════════════════════════════════════
    # TAB 4 — REFILL & SAVINGS
    # ════════════════════════════════════════════════════
    with tab4:
        st.markdown("### Refill Reminders & Generic Savings")

        medicines = parsed.get("medicines", [])

        # ── Show refill status cards ──────────────────────
        refill_statuses = show_refill_status(medicines)
        if refill_statuses:
            for s in refill_statuses:
                if s["status"] == "critical":
                    bg, border, icon = "rgba(234,67,53,0.15)", "#EA4335", "🔴"
                elif s["status"] == "warning":
                    bg, border, icon = "rgba(251,188,4,0.15)", "#FBBC04", "🟡"
                else:
                    bg, border, icon = "rgba(52,168,83,0.15)", "#34A853", "🟢"

                saving_text = f"<br><small style='color:#68D391;'>💰 {s['saving']}</small>" if s.get("saving") and s["saving"] != "Not specified" else ""
                st.markdown(f"""
                <div style='background:{bg};border-left:4px solid {border};
                border-radius:8px;padding:12px 16px;margin-bottom:8px;'>
                    {icon} <strong style='color:#E2E8F0;'>{s["name"]}</strong>
                    &nbsp;·&nbsp; <span style='color:#CBD5E0;'>{s["days_left"]} days left</span>
                    &nbsp;·&nbsp; <span style='color:#A0AEC0;font-size:12px;'>Runs out: {s["end_date"]}</span>
                    {saving_text}
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        # ── Send notifications (email only) ─────────────────
        st.markdown("### Send Alerts")
        notify_email = st.text_input(
            "📧 Email for alerts",
            value=st.session_state.get("alert_email", ""),
            placeholder="your@gmail.com",
            key="tab4_email"
        )

        if notify_email:
            st.session_state.alert_email = notify_email

        savings_meds = [
            m for m in medicines
            if m.get("generic_cost_saving")
            and m.get("generic_cost_saving") != "Not specified"
        ]

        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "💰 Send Savings Alert (Email)",
                use_container_width=True
            ):
                if not notify_email:
                    st.error("Enter an email address.")
                elif not savings_meds:
                    st.warning("No generic savings found in this prescription.")
                else:
                    with st.spinner("Sending..."):
                        results = send_generic_savings_alert(
                            savings_meds,
                            to_email=notify_email
                        )
                    if results.get("email"):
                        st.success("✅ Savings alert emailed! Check your inbox.")
                    else:
                        st.error("Failed to send. Check email credentials in .env")

        with col2:
            if st.button(
                "💊 Send Refill Reminder (Email)",
                use_container_width=True
            ):
                if not notify_email:
                    st.error("Enter an email address.")
                elif not medicines:
                    st.error("No medicines found.")
                else:
                    with st.spinner("Sending..."):
                        results = send_refill_reminder(
                            medicines[0].get("name", "Medicine"),
                            3,
                            to_email=notify_email
                        )
                    if results.get("email"):
                        st.success("✅ Refill reminder emailed!")
                    else:
                        st.error("Failed to send. Check email credentials in .env")

    # ════════════════════════════════════════════════════
    # TAB 5 — DOWNLOAD REPORT
    # ════════════════════════════════════════════════════
    with tab5:
        st.markdown("### Download Prescription Report")
        st.markdown(
            "Get a complete PDF summary of your prescription."
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Medicines", len(parsed.get("medicines", [])))
        with col2:
            st.metric(
                "Interactions",
                len(parsed.get("drug_interactions", []))
            )
        with col3:
            st.metric(
                "Red Flags",
                len(parsed.get("red_flags", []))
            )

        st.divider()

        if st.button(
            "Generate PDF Report",
            type="primary",
            use_container_width=True
        ):
            with st.spinner("Generating report..."):
                pdf_path = generate_report(
                    parsed,
                    st.session_state.get("username", "Patient")
                )

            if pdf_path:
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()

                st.download_button(
                    label="Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"MedSaathi_Report_{datetime.now().strftime('%d%m%Y')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("Report ready!")
            else:
                st.error("Could not generate report. Please try again.")