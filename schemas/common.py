"""Common/shared Pydantic schemas."""
from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "Vidur API"
    version: str = "2.0.0"
