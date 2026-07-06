"""Security regression tests for user lookup."""

from fastapi.testclient import TestClient


def test_get_existing_user(
    client: TestClient,
) -> None:
    response = client.get(
        "/users",
        params={"username": "alice"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "username": "alice",
        "role": "customer",
    }


def test_get_unknown_user(
    client: TestClient,
) -> None:
    response = client.get(
        "/users",
        params={"username": "charlie"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_sql_injection_payload_is_rejected(
    client: TestClient,
) -> None:
    payload = "admin' OR '1'='1"

    response = client.get(
        "/users",
        params={"username": payload},
    )

    assert response.status_code == 422

    # Database remains accessible after the attack payload.
    valid_response = client.get(
        "/users",
        params={"username": "alice"},
    )

    assert valid_response.status_code == 200
