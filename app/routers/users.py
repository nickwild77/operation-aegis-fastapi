"""User lookup endpoints."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from app.database import find_user_by_username
from app.dependencies import get_database
from app.schemas import UserResponse

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

UsernameQuery = Annotated[
    str,
    Query(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_.-]+$",
        description="Account username",
    ),
]

DatabaseConnection = Annotated[
    sqlite3.Connection,
    Depends(get_database),
]


@router.get(
    "",
    response_model=UserResponse,
)
def get_user(
    username: UsernameQuery,
    connection: DatabaseConnection,
) -> UserResponse:
    """Return one user using a parameterized query."""
    row = find_user_by_username(
        connection,
        username,
    )

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=row["id"],
        username=row["username"],
        role=row["role"],
    )
