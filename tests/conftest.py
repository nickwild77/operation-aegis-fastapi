"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from app.factory import create_app


@pytest.fixture
def settings(tmp_path) -> Settings:
    """Return isolated settings for each test."""
    return Settings(
        app_env="test",
        api_token="t" * 32,
        database_path=tmp_path / "aegis-test.db",
        upload_directory=tmp_path / "uploads",
        max_upload_size_bytes=128,
        docs_enabled=False,
    )


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    """Create one isolated application instance."""
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """Run the application lifespan around each test."""
    with TestClient(
        app,
        raise_server_exceptions=False,
    ) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(
    settings: Settings,
) -> dict[str, str]:
    """Return a valid bearer-token header."""
    return {"Authorization": (f"Bearer {settings.api_token.get_secret_value()}")}
