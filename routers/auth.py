"""
routers/auth.py — Firebase-backed authentication.
Verifies Firebase ID tokens from the frontend.
User profiles stored in Firestore (collection: 'users').
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from firebase_config import verify_firebase_token, get_firestore

router = APIRouter(prefix="/auth", tags=["Authentication"])
_bearer = HTTPBearer(auto_error=False)


# ── Dependency: get current Firebase user ─────────────────────────────────────
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> dict:
    """
    Verify Firebase ID token from Authorization: Bearer <token>.
    Returns the decoded Firebase token payload.
    """
    try:
        return verify_firebase_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[dict]:
    """Returns the Firebase user or None (guest access allowed)."""
    if not credentials:
        return None
    try:
        return verify_firebase_token(credentials.credentials)
    except Exception:
        return None


# ── Profile endpoints ──────────────────────────────────────────────────────────

@router.post("/profile", status_code=200)
def upsert_profile(
    preferred_language: str = "English",
    current_user: dict = Depends(get_current_user),
):
    """
    Create or update the user's profile in Firestore.
    Called after Google/Email sign-in to store preferences.
    """
    db = get_firestore()
    uid = current_user["uid"]
    ref = db.collection("users").document(uid)
    doc = ref.get()

    data = {
        "uid": uid,
        "email": current_user.get("email", ""),
        "name": current_user.get("name", current_user.get("email", "User")),
        "preferred_language": preferred_language,
    }

    if doc.exists:
        ref.update({"preferred_language": preferred_language})
    else:
        ref.set(data)

    return {"message": "Profile saved", "user": data}


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    """Return current authenticated user's Firebase profile."""
    db = get_firestore()
    uid = current_user["uid"]
    doc = db.collection("users").document(uid).get()

    profile = doc.to_dict() if doc.exists else {}
    return {
        "uid": uid,
        "email": current_user.get("email", ""),
        "name": current_user.get("name", ""),
        "preferred_language": profile.get("preferred_language", "English"),
    }


@router.patch("/me")
def update_profile(
    preferred_language: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Update profile settings in Firestore."""
    db = get_firestore()
    uid = current_user["uid"]
    updates = {}
    if preferred_language:
        updates["preferred_language"] = preferred_language
    if updates:
        db.collection("users").document(uid).set(updates, merge=True)
    return {"message": "Profile updated", "success": True}
