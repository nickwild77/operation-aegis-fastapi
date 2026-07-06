"""Response schemas exposed by the API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Simple text response."""

    message: str


class HealthResponse(BaseModel):
    """Health endpoint response."""

    status: Literal["ok"]


class UserResponse(BaseModel):
    """Safe public user representation."""

    id: int
    username: str
    role: str


class SecureDataResponse(BaseModel):
    """Protected demonstration payload."""

    data: str


class UploadResponse(BaseModel):
    """Metadata returned after a successful upload."""

    file_id: str = Field(pattern=r"^[a-f0-9]{32}\.(txt|csv|json)$")
    size_bytes: int = Field(ge=1)
    content_type: str
