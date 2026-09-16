"""
firebase_config.py — Initialize Firebase Admin SDK once at startup.
Uses the service account JSON file.
"""
import os
import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth

_initialized = False

def get_firebase_app():
    global _initialized
    if not _initialized:
        sa_path = os.path.join(os.path.dirname(__file__), "firebase-service-account.json")
        cred = credentials.Certificate(sa_path)
        firebase_admin.initialize_app(cred)
        _initialized = True
    return firebase_admin.get_app()


def get_firestore():
    get_firebase_app()
    return firestore.client()


def verify_firebase_token(id_token: str) -> dict:
    """
    Verify a Firebase ID token from the frontend.
    Returns the decoded token payload (uid, email, name, etc.)
    Raises ValueError on failure.
    """
    get_firebase_app()
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        return decoded
    except Exception as e:
        raise ValueError(f"Invalid Firebase token: {e}")
