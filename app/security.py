"""Authentication dependencies."""

from __future__ import annotations

from hmac import compare_digest
from typing import Annotated

from fastapi import HTTPException, Request, Security, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="AegisBearerAuth",
    description=("Static demonstration bearer token supplied through API_TOKEN."),
)


def require_api_token(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Security(bearer_scheme),
    ],
) -> None:
    """Require a valid bearer token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expected_token = request.app.state.settings.api_token.get_secret_value()
    supplied_token = credentials.credentials

    if not compare_digest(supplied_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
