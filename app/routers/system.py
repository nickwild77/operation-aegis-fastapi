"""Public system endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas import HealthResponse, MessageResponse

router = APIRouter(tags=["system"])


@router.get(
    "/",
    response_model=MessageResponse,
)
async def index() -> MessageResponse:
    """Return a non-sensitive service greeting."""
    return MessageResponse(message="Operation Aegis API")


@router.get(
    "/health",
    response_model=HealthResponse,
)
async def health() -> HealthResponse:
    """Return the liveness status."""
    return HealthResponse(status="ok")
