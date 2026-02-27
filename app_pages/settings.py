import streamlit as st
import bcrypt
from database.db import get_session
from database.models import User
from utils.constants import LANGUAGES

def show():
    st.markdown("## ⚙️ Settings")
    st.markdown("*Manage your account and preferences*")
    st.divider()

    user_id = st.session_state.get("user_id")
    db = get_session()
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        st.error("User not found.")
        db.close()
        return

    # ── TABS ─────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs([
        "Profile",
        "Preferences",
        "Change Password"
    ])

    # ════════════════════════════════════════════════════
    # TAB 1 — PROFILE
    # ════════════════════════════════════════════════════
    with tab1:
        st.markdown("### Your Profile")

        st.markdown(f"""
        <div style='background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);
        border-radius:12px;padding:24px;margin-bottom:20px;'>
            <h3 style='margin:0 0 4px 0;color:#E2E8F0;'>
                {user.username}
            </h3>
            <p style='margin:0;color:#A0AEC0;font-size:14px;'>
                Member since {user.created_at.strftime("%d %B %Y")
                if user.created_at else "N/A"}
            </p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Preferred Language",
                user.preferred_language or "English"
            )
        with col2:
            st.metric(
                "Wake Time",
                user.wake_time or "07:00"
            )

        st.divider()

        # Update profile form
        st.markdown("### Update Profile")
        with st.form("update_profile"):
            new_email = st.text_input(
                "Email Address",
                placeholder="your@gmail.com"
            )
            new_phone = st.text_input(
                "Phone Number",
                placeholder="+91xxxxxxxxxx"
            )
            new_wake = st.time_input(
                "Wake Time",
                help="Used for scheduling reminders"
            )
            new_lang = st.selectbox(
                "Preferred Language",
                list(LANGUAGES.keys()),
                index=list(LANGUAGES.keys()).index(
                    user.preferred_language or "English"
                )
            )

            save = st.form_submit_button(
                "Save Changes",
                use_container_width=True
            )

            if save:
                user.preferred_language = new_lang
                user.wake_time = str(new_wake)
                db.commit()
                st.session_state.language = new_lang
                st.success("Profile updated!")

    # ════════════════════════════════════════════════════
    # TAB 2 — PREFERENCES
    # ════════════════════════════════════════════════════
    with tab2:
        st.markdown("### App Preferences")

        st.markdown("#### Notification Preferences")
        col1, col2 = st.columns(2)
        with col1:
            email_notif = st.toggle(
                "Email Notifications",
                value=True
            )
            sms_notif = st.toggle(
                "SMS Notifications",
                value=True
            )
        with col2:
            refill_notif = st.toggle(
                "Refill Reminders",
                value=True
            )
            savings_notif = st.toggle(
                "Generic Savings Alerts",
                value=True
            )

        st.divider()

        st.markdown("#### Display Preferences")
        col1, col2 = st.columns(2)
        with col1:
            show_side_effects = st.toggle(
                "Show Side Effects",
                value=True
            )
            show_food = st.toggle(
                "Show Food Interactions",
                value=True
            )
        with col2:
            show_savings = st.toggle(
                "Show Generic Savings",
                value=True
            )
            auto_translate = st.toggle(
                "Auto Translate",
                value=True
            )

        st.divider()

        st.markdown("#### Language")
        selected_lang = st.selectbox(
            "Display Language",
            list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(
                st.session_state.get("language","English")
            )
        )

        if st.button(
            "Save Preferences",
            use_container_width=True
        ):
            st.session_state.language = selected_lang
            st.success("Preferences saved!")

        st.divider()

        # App info
        st.markdown("#### About Vidur")
        st.markdown(f"""
        <div style='background:rgba(255,255,255,0.07);border-radius:10px;
        padding:16px;font-size:13px;color:#A0AEC0;'>
            <strong style='color:#E2E8F0;'>Version:</strong> 1.0.0 &nbsp;|&nbsp;
            <strong style='color:#E2E8F0;'>Build:</strong> Hackathon 2025<br><br>
            Vidur is not a substitute for professional
            medical advice. Always consult your doctor.
        </div>
        """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════
    # TAB 3 — CHANGE PASSWORD
    # ════════════════════════════════════════════════════
    with tab3:
        st.markdown("### Change Password")

        with st.form("change_password"):
            current_pw = st.text_input(
                "Current Password",
                type="password",
                placeholder="Enter current password"
            )
            new_pw = st.text_input(
                "New Password",
                type="password",
                placeholder="Enter new password"
            )
            confirm_pw = st.text_input(
                "Confirm New Password",
                type="password",
                placeholder="Confirm new password"
            )

            change = st.form_submit_button(
                "Change Password",
                use_container_width=True
            )

            if change:
                if not current_pw or not new_pw or not confirm_pw:
                    st.error("Please fill in all fields.")
                elif new_pw != confirm_pw:
                    st.error("New passwords do not match.")
                elif len(new_pw) < 6:
                    st.error(
                        "Password must be at least 6 characters."
                    )
                elif not bcrypt.checkpw(
                    current_pw.encode("utf-8"),
                    user.password_hash.encode("utf-8")
                ):
                    st.error("Current password is incorrect.")
                else:
                    new_hash = bcrypt.hashpw(
                        new_pw.encode("utf-8"),
                        bcrypt.gensalt()
                    ).decode("utf-8")
                    user.password_hash = new_hash
                    db.commit()
                    st.success("Password changed successfully!")

        st.divider()

        # Danger zone
        st.markdown("### Danger Zone")
        st.error(
            "Deleting your account will remove all your "
            "prescriptions and data permanently."
        )
        if st.button(
            "Delete My Account",
            type="secondary",
            use_container_width=True
        ):
            if st.session_state.get("confirm_delete_account"):
                db.delete(user)
                db.commit()
                st.session_state.logged_in = False
                st.session_state.user_id = None
                st.session_state.username = None
                st.success("Account deleted.")
                st.rerun()
            else:
                st.session_state.confirm_delete_account = True
                st.warning("Click again to confirm deletion.")

    db.close()