import streamlit as st
import json
from database.db import get_session
from database.models import Prescription, Medicine
from agents.report_agent import generate_report
from datetime import datetime

def show():
    st.markdown("## 📋 Prescription History")
    st.markdown("*All your past prescriptions in one place*")
    st.divider()

    user_id = st.session_state.get("user_id")
    db = get_session()

    prescriptions = db.query(Prescription).filter(
        Prescription.user_id == user_id
    ).order_by(Prescription.upload_date.desc()).all()

    if not prescriptions:
        st.info("No prescriptions uploaded yet.")
        if st.button("Upload First Prescription", type="primary"):
            st.session_state.page = "Upload Prescription"
            st.rerun()
        db.close()
        return

    # ── STATS ROW ─────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Prescriptions", len(prescriptions))
    with col2:
        active = sum(1 for p in prescriptions if p.is_active)
        st.metric("Active", active)
    with col3:
        avg_auth = sum(
            p.authenticity_score or 0 for p in prescriptions
        ) / len(prescriptions)
        st.metric("Avg Auth Score", f"{avg_auth:.1f}/10")

    st.divider()

    # ── SEARCH ────────────────────────────────────────────
    search = st.text_input(
        "Search prescriptions",
        placeholder="Search by doctor, medicine, or date..."
    )

    # ── PRESCRIPTION LIST ─────────────────────────────────
    for i, pres in enumerate(prescriptions):
        try:
            parsed = json.loads(pres.parsed_json)
        except:
            parsed = {}

        doctor    = parsed.get("doctor_name", "Unknown Doctor")
        hospital  = parsed.get("hospital_name", "")
        diagnosis = parsed.get("diagnosis", "")
        medicines = parsed.get("medicines", [])
        med_names = ", ".join(
            [m.get("name","") for m in medicines[:3]]
        )
        if len(medicines) > 3:
            med_names += f" +{len(medicines)-3} more"

        date_str = pres.upload_date.strftime("%d %b %Y")

        # Apply search filter
        search_text = (
            doctor + hospital + diagnosis +
            med_names + date_str
        ).lower()
        if search and search.lower() not in search_text:
            continue

        # Auth badge
        auth = pres.authenticity_score or 0
        if auth >= 8:
            auth_badge = f"✅ {auth}/10"
            badge_color = "rgba(52,168,83,0.2)"
        elif auth >= 5:
            auth_badge = f"⚠️ {auth}/10"
            badge_color = "rgba(251,188,4,0.2)"
        else:
            auth_badge = f"❌ {auth}/10"
            badge_color = "rgba(234,67,53,0.2)"

        with st.expander(
            f"📄 {date_str} — Dr. {doctor} | "
            f"{len(medicines)} medicines | Auth: {auth}/10",
            expanded=(i == 0)
        ):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Doctor:** {doctor}")
                st.markdown(f"**Hospital:** {hospital or 'N/A'}")
                st.markdown(
                    f"**Date:** "
                    f"{parsed.get('prescription_date','N/A')}"
                )
            with col2:
                st.markdown(f"**Patient:** {parsed.get('patient_name','N/A')}")
                st.markdown(f"**Diagnosis:** {diagnosis or 'N/A'}")
                st.markdown(
                    f"**Follow Up:** "
                    f"{parsed.get('follow_up_date','N/A')}"
                )
            with col3:
                st.markdown(
                    f"<div style='background:{badge_color};"
                    f"padding:8px 12px;border-radius:8px;"
                    f"text-align:center;font-weight:600;'>"
                    f"Auth: {auth_badge}</div>",
                    unsafe_allow_html=True
                )
                status = "🟢 Active" if pres.is_active else "⚫ Inactive"
                st.markdown(f"**Status:** {status}")

            # Medicines list
            if medicines:
                st.markdown("**Medicines:**")
                st.markdown(
                    f"<div style='background:rgba(255,255,255,0.07);"
                    f"padding:10px 14px;border-radius:8px;"
                    f"font-size:13px;color:#CBD5E0;'>"
                    f"{med_names}</div>",
                    unsafe_allow_html=True
                )

            # Drug interactions warning
            interactions = parsed.get("drug_interactions", [])
            if interactions:
                st.warning(
                    f"⚠️ {len(interactions)} drug interaction(s) detected"
                )

            # Red flags
            red_flags = parsed.get("red_flags", [])
            if red_flags:
                st.error(
                    f"🚩 {len(red_flags)} red flag(s) detected"
                )

            st.markdown("---")

            col1, col2, col3 = st.columns(3)

            # Load prescription
            with col1:
                if st.button(
                    "Load Prescription",
                    key=f"load_{i}",
                    use_container_width=True
                ):
                    st.session_state.current_prescription = parsed
                    st.session_state.prescription_id = pres.id
                    st.success("Prescription loaded! Go to Dashboard.")

            # Download PDF
            with col2:
                if st.button(
                    "Download PDF",
                    key=f"pdf_{i}",
                    use_container_width=True
                ):
                    with st.spinner("Generating..."):
                        pdf_path = generate_report(
                            parsed,
                            st.session_state.get("username","Patient")
                        )
                    if pdf_path:
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                        st.download_button(
                            "Download",
                            data=pdf_bytes,
                            file_name=f"MedSaathi_{date_str}.pdf",
                            mime="application/pdf",
                            key=f"dl_{i}",
                            use_container_width=True
                        )

            # Delete prescription
            with col3:
                if st.button(
                    "Delete",
                    key=f"del_{i}",
                    use_container_width=True,
                    type="secondary"
                ):
                    if st.session_state.get(f"confirm_del_{i}"):
                        db.delete(pres)
                        db.commit()
                        st.success("Deleted!")
                        st.rerun()
                    else:
                        st.session_state[f"confirm_del_{i}"] = True
                        st.warning("Click Delete again to confirm.")

    db.close()