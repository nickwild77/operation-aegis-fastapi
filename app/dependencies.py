"""Reusable FastAPI dependencies."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator

from fastapi import Request

from app.config import Settings


def get_request_settings(request: Request) -> Settings:
    """Return settings attached to the current application."""
    return request.app.state.settings


def get_database(
    request: Request,
) -> Iterator[sqlite3.Connection]:
    """Provide a short-lived SQLite connection for one request."""
    settings = get_request_settings(request)

    connection = sqlite3.connect(
        settings.database_path,
        check_same_thread=False,
    )
    connection.row_factory = sqlite3.Row

    try:
        yield connection
    finally:
        connection.close()
