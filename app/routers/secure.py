"""Protected demonstration endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Security

from app.schemas import SecureDataResponse
from app.security import require_api_token

router = APIRouter(tags=["secure"])


@router.get(
    "/secure-data",
    response_model=SecureDataResponse,
)
def secure_data(
    _: Annotated[
        None,
        Security(require_api_token),
    ],
) -> SecureDataResponse:
    """Return data only after token validation."""
    return SecureDataResponse(data="Sensitive Data")
