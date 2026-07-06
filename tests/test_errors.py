"""Tests for safe internal-error responses."""

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_unhandled_exception_response_is_generic(
    app: FastAPI,
) -> None:
    sensitive_message = "database-password=do-not-return"

    @app.get("/test-only-error")
    def raise_test_error() -> None:
        raise RuntimeError(sensitive_message)

    with TestClient(
        app,
        raise_server_exceptions=False,
    ) as client:
        response = client.get("/test-only-error")

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert sensitive_message not in response.text
