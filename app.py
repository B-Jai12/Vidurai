import streamlit as st
from dotenv import load_dotenv
from database.db import init_db

load_dotenv()

init_db()

st.set_page_config(
    page_title="Vidur — Your Family Health Companion",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* ── Global dark-theme helpers ──────────────────────────── */
    .medicine-card {
        background: rgba(255,255,255,0.07);
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #4DA6FF;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }

    /* Alert variants — translucent so they work on dark OR light bg */
    .alert-success {
        background: rgba(52,168,83,0.15);
        border-left: 4px solid #34A853;
        padding: 12px 16px;
        border-radius: 8px;
        color: #86EFAC;
    }
    .alert-warning {
        background: rgba(251,188,4,0.12);
        border-left: 4px solid #FBBC04;
        padding: 12px 16px;
        border-radius: 8px;
        color: #FDE68A;
    }
    .alert-danger {
        background: rgba(234,67,53,0.15);
        border-left: 4px solid #EA4335;
        padding: 12px 16px;
        border-radius: 8px;
        color: #FCA5A5;
    }

    /* Streamlit button polish */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }

    /* Hide Streamlit chrome */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }

    .disclaimer {
        font-size: 11px;
        color: #718096;
        text-align: center;
        padding: 8px;
        border-top: 1px solid rgba(255,255,255,0.1);
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "language" not in st.session_state:
    st.session_state.language = "English"
if "current_prescription" not in st.session_state:
    st.session_state.current_prescription = None

if not st.session_state.logged_in:
    from app_pages.home import show
    show()
else:
    with st.sidebar:
        st.markdown("## Vidur")
        st.markdown(f"*Welcome, {st.session_state.username}!*")
        st.divider()

        page = st.radio(
            "Navigate",
            [
                "Upload Prescription",
                "Dashboard",
                "Caregiver Mode",
                "History",
                "Settings"
            ],
            index=st.session_state.get("nav_page", 0),
            label_visibility="collapsed"
        )
        st.session_state.nav_page = [
            "Upload Prescription", "Dashboard", "Caregiver Mode", "History", "Settings"
        ].index(page)

        st.divider()

        from utils.constants import LANGUAGES
        selected_lang = st.selectbox(
            "Language",
            list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(
                st.session_state.language
            )
        )
        st.session_state.language = selected_lang

        st.divider()

        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()

        st.markdown(
            '<div class="disclaimer">Vidur is not a substitute for professional medical advice.</div>',
            unsafe_allow_html=True
        )

    if page == "Upload Prescription":
        from app_pages.upload import show
        show()
    elif page == "Dashboard":
        from app_pages.dashboard import show
        show()
    elif page == "Caregiver Mode":
        from app_pages.caregiver import show
        show()
    elif page == "History":
        from app_pages.history import show
        show()
    elif page == "Settings":
        from app_pages.settings import show
        show()