import streamlit as st
from database.db import get_session
from database.models import User
import bcrypt

def show():
    # ── HEADER ───────────────────────────────────────────
    st.markdown("""
    <div style='text-align: center; padding: 40px 0 20px 0;'>
        <h1 style='font-size: 52px; color: #4DA6FF; letter-spacing: -1px;'>Vidur</h1>
        <p style='font-size: 20px; color: #CBD5E0;'>
            Your Family Health Companion
        </p>
        <p style='font-size: 16px; color: #90A4AE; font-style: italic;'>
            From prescription to last tablet — in your language, for your family.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── STATS ROW ─────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Patients Served", "500M+", "in India daily")
    with col2:
        st.metric("Languages", "7+", "Indian languages")
    with col3:
        st.metric("Generic Savings", "80%", "average savings")
    with col4:
        st.metric("Accuracy", "90%+", "OCR accuracy")

    st.divider()

    # ── LOGIN / SIGNUP TABS ───────────────────────────────
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    # ── LOGIN TAB ─────────────────────────────────────────
    with tab1:
        st.markdown("### Welcome Back!")

        with st.form("login_form"):
            username = st.text_input(
                "Username",
                placeholder="Enter your username"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password"
            )
            submit = st.form_submit_button(
                "Login",
                use_container_width=True
            )

        if submit:
            if not username or not password:
                st.error("Please fill in all fields.")
            else:
                db = get_session()
                user = db.query(User).filter(
                    User.username == username
                ).first()
                db.close()

                if user and bcrypt.checkpw(
                    password.encode('utf-8'),
                    user.password_hash.encode('utf-8')
                ):
                    st.session_state.logged_in = True
                    st.session_state.user_id = user.id
                    st.session_state.username = user.username
                    st.session_state.language = user.preferred_language
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Wrong username or password.")

    # ── SIGNUP TAB ────────────────────────────────────────
    with tab2:
        st.markdown("### Create Account")

        with st.form("signup_form"):
            new_username = st.text_input(
                "Username",
                placeholder="Choose a username"
            )
            new_password = st.text_input(
                "Password",
                type="password",
                placeholder="Choose a password"
            )
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Confirm your password"
            )
            email = st.text_input(
                "Email",
                placeholder="Your email for notifications"
            )
            phone = st.text_input(
                "Phone Number",
                placeholder="+91xxxxxxxxxx"
            )
            language = st.selectbox(
                "Preferred Language",
                ["English", "Hindi", "Telugu",
                 "Tamil", "Bengali", "Kannada", "Marathi"]
            )
            wake_time = st.time_input("Your Wake Time")

            signup = st.form_submit_button(
                "Create Account",
                use_container_width=True
            )

        if signup:
            if not new_username or not new_password or not confirm_password:
                st.error("Please fill in all fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                db = get_session()
                existing = db.query(User).filter(
                    User.username == new_username
                ).first()

                if existing:
                    st.error("Username already taken.")
                    db.close()
                else:
                    hashed = bcrypt.hashpw(
                        new_password.encode('utf-8'),
                        bcrypt.gensalt()
                    ).decode('utf-8')

                    new_user = User(
                        username=new_username,
                        password_hash=hashed,
                        preferred_language=language,
                        wake_time=str(wake_time),
                    )
                    db.add(new_user)
                    db.commit()
                    db.refresh(new_user)
                    db.close()

                    st.success("Account created! Please login.")

    st.divider()

    # ── FEATURES SECTION ─────────────────────────────────
    st.markdown(
        "<h3 style='text-align:center'>What Vidur Does</h3>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**Reads Your Prescription**\nUploads any photo or PDF and explains every medicine in simple words.")
        st.info("**7 Indian Languages**\nGet explanations in Hindi, Telugu, Tamil, Bengali, Kannada and Marathi.")
        st.info("**Voice Output**\nListen to medicine explanations in your language.")
    with col2:
        st.success("**AI Doctor Assistant**\nAsk any medicine question in your language and get instant answers.")
        st.success("**Save on Medicines**\nFind cheaper generic alternatives and get alerts on savings.")
        st.success("**Refill Reminders**\nGet notified before your medicines run out.")
    with col3:
        st.warning("**Find Hospitals**\nLocate nearby specialists and Ayushman Bharat hospitals.")
        st.warning("**Family Care**\nManage prescriptions for your entire family.")
        st.warning("**Download Reports**\nGet a complete PDF summary of your prescription.")

    # ── DISCLAIMER ────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center; color:#90A4AE;
    font-size:12px; margin-top:30px;'>
        Vidur is not a substitute for professional
        medical advice. Always consult your doctor.
    </div>
    """, unsafe_allow_html=True)