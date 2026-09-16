"""Pydantic schemas for authentication endpoints."""
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    preferred_language: str = Field(default="English")


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    preferred_language: str


class UserOut(BaseModel):
    id: int
    username: str
    preferred_language: str
    wake_time: str

    class Config:
        from_attributes = True
