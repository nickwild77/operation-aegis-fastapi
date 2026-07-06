"""Security regression tests for file handling."""

from fastapi.testclient import TestClient

from app.config import Settings


def test_upload_and_download_text_file(
    client: TestClient,
    auth_headers: dict[str, str],
    settings: Settings,
) -> None:
    upload_response = client.post(
        "/files/upload",
        headers=auth_headers,
        files={
            "file": (
                "report.txt",
                b"Operation Aegis report\n",
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 201

    body = upload_response.json()

    assert body["size_bytes"] == 23
    assert body["content_type"] == "text/plain"

    stored_path = settings.upload_directory / body["file_id"]

    assert stored_path.is_file()
    assert stored_path.parent == settings.upload_directory

    download_response = client.get(
        f"/files/{body['file_id']}",
        headers=auth_headers,
    )

    assert download_response.status_code == 200
    assert download_response.content == b"Operation Aegis report\n"


def test_upload_requires_authentication(
    client: TestClient,
) -> None:
    response = client.post(
        "/files/upload",
        files={
            "file": (
                "report.txt",
                b"hello",
                "text/plain",
            )
        },
    )

    assert response.status_code == 401


def test_path_like_filename_cannot_control_storage(
    client: TestClient,
    auth_headers: dict[str, str],
    settings: Settings,
) -> None:
    response = client.post(
        "/files/upload",
        headers=auth_headers,
        files={
            "file": (
                "../../outside.txt",
                b"safe content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 201

    file_id = response.json()["file_id"]

    assert (settings.upload_directory / file_id).is_file()

    assert not (settings.upload_directory.parent / "outside.txt").exists()


def test_unsupported_extension_is_rejected(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/files/upload",
        headers=auth_headers,
        files={
            "file": (
                "payload.exe",
                b"MZ",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415


def test_mismatched_content_type_is_rejected(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/files/upload",
        headers=auth_headers,
        files={
            "file": (
                "report.txt",
                b"hello",
                "application/json",
            )
        },
    )

    assert response.status_code == 415


def test_oversized_file_is_rejected_and_deleted(
    client: TestClient,
    auth_headers: dict[str, str],
    settings: Settings,
) -> None:
    response = client.post(
        "/files/upload",
        headers=auth_headers,
        files={
            "file": (
                "large.txt",
                b"a" * (settings.max_upload_size_bytes + 1),
                "text/plain",
            )
        },
    )

    assert response.status_code == 413
    assert list(settings.upload_directory.iterdir()) == []


def test_non_utf8_file_is_rejected(
    client: TestClient,
    auth_headers: dict[str, str],
    settings: Settings,
) -> None:
    response = client.post(
        "/files/upload",
        headers=auth_headers,
        files={
            "file": (
                "binary.txt",
                b"\xff\xfe\x00\x00",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415
    assert list(settings.upload_directory.iterdir()) == []


def test_invalid_json_is_rejected(
    client: TestClient,
    auth_headers: dict[str, str],
    settings: Settings,
) -> None:
    response = client.post(
        "/files/upload",
        headers=auth_headers,
        files={
            "file": (
                "broken.json",
                b'{"missing":',
                "application/json",
            )
        },
    )

    assert response.status_code == 422
    assert list(settings.upload_directory.iterdir()) == []


def test_invalid_file_identifier_is_rejected(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get(
        "/files/not-a-valid-file-id",
        headers=auth_headers,
    )

    assert response.status_code == 404
