"""Tests for bearer-token authentication."""

from fastapi.testclient import TestClient

from app.config import Settings


def test_missing_token_is_rejected(
    client: TestClient,
) -> None:
    response = client.get("/secure-data")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_wrong_token_is_rejected(
    client: TestClient,
) -> None:
    response = client.get(
        "/secure-data",
        headers={"Authorization": (f"Bearer {'x' * 32}")},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_query_string_token_is_ignored(
    client: TestClient,
    settings: Settings,
) -> None:
    response = client.get(
        "/secure-data",
        params={"token": (settings.api_token.get_secret_value())},
    )

    assert response.status_code == 401


def test_valid_bearer_token_is_accepted(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get(
        "/secure-data",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {"data": "Sensitive Data"}
