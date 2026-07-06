"""Restricted file upload and download endpoints."""

from __future__ import annotations

import codecs
import json
import logging
import re
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from anyio import Path as AsyncPath
from anyio import open_file
from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Request,
    Security,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse

from app.config import Settings
from app.schemas import UploadResponse
from app.security import require_api_token

logger = logging.getLogger(__name__)

CHUNK_SIZE = 64 * 1024

FILE_ID_PATTERN = re.compile(r"^[a-f0-9]{32}\.(txt|csv|json)$")

CONTENT_TYPE_BY_EXTENSION = {
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".json": "application/json",
}

router = APIRouter(
    prefix="/files",
    tags=["files"],
    dependencies=[
        Security(require_api_token),
    ],
)


def resolve_upload_path(
    upload_directory: Path,
    file_id: str,
) -> Path:
    """Resolve a file identifier inside the upload root."""
    root = upload_directory.resolve()
    candidate = (root / file_id).resolve()

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        ) from exc

    return candidate


def validate_upload_metadata(
    file: UploadFile,
    settings: Settings,
) -> tuple[str, str]:
    """Validate extension and declared content type."""
    original_name = Path(file.filename or "").name

    if not original_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A filename is required",
        )

    extension = Path(original_name).suffix.lower()

    if extension not in settings.allowed_upload_extensions:
        raise HTTPException(
            status_code=(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE),
            detail="Unsupported file extension",
        )

    content_type = (file.content_type or "").lower()

    if content_type not in settings.allowed_upload_content_types:
        raise HTTPException(
            status_code=(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE),
            detail="Unsupported content type",
        )

    expected_content_type = CONTENT_TYPE_BY_EXTENSION.get(extension)

    if expected_content_type != content_type:
        raise HTTPException(
            status_code=(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE),
            detail=("File extension and content type do not match"),
        )

    return extension, content_type


async def validate_saved_json(
    destination: Path,
) -> None:
    """Require syntactically valid UTF-8 JSON."""
    try:
        async with await open_file(
            destination,
            mode="r",
            encoding="utf-8",
        ) as uploaded_file:
            content = await uploaded_file.read()

        json.loads(content)

    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise HTTPException(
            status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail="Uploaded JSON is invalid",
        ) from exc


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    request: Request,
    file: Annotated[
        UploadFile,
        File(description=("UTF-8 text, CSV, or JSON file")),
    ],
) -> UploadResponse:
    """Store a bounded upload using a random identifier."""
    settings: Settings = request.app.state.settings

    extension, content_type = validate_upload_metadata(
        file,
        settings,
    )

    await AsyncPath(settings.upload_directory).mkdir(
        parents=True,
        exist_ok=True,
    )

    # Never use a client-controlled filename for storage.
    file_id = f"{uuid4().hex}{extension}"

    destination = resolve_upload_path(
        settings.upload_directory,
        file_id,
    )

    size = 0
    decoder = codecs.getincrementaldecoder("utf-8")("strict")

    try:
        async with await open_file(
            destination,
            mode="xb",
        ) as output:
            while chunk := await file.read(CHUNK_SIZE):
                size += len(chunk)

                if size > settings.max_upload_size_bytes:
                    raise HTTPException(
                        status_code=(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE),
                        detail="Uploaded file is too large",
                    )

                try:
                    decoder.decode(chunk)
                except UnicodeDecodeError as exc:
                    raise HTTPException(
                        status_code=(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE),
                        detail=("Uploaded file must contain valid UTF-8 text"),
                    ) from exc

                await output.write(chunk)

            try:
                decoder.decode(b"", final=True)
            except UnicodeDecodeError as exc:
                raise HTTPException(
                    status_code=(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE),
                    detail=("Uploaded file must contain valid UTF-8 text"),
                ) from exc

        if size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )

        if extension == ".json":
            await validate_saved_json(destination)

    except HTTPException:
        await remove_file_if_exists(destination)
        raise

    except OSError as exc:
        await remove_file_if_exists(destination)

        logger.error(
            "Unable to store uploaded file",
            exc_info=(
                type(exc),
                exc,
                exc.__traceback__,
            ),
        )

        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail="Unable to store file",
        ) from exc

    finally:
        await file.close()

    return UploadResponse(
        file_id=file_id,
        size_bytes=size,
        content_type=content_type,
    )


async def remove_file_if_exists(
    destination: Path,
) -> None:
    """Remove a partially written file."""
    try:
        await AsyncPath(destination).unlink(missing_ok=True)
    except OSError:
        logger.exception(
            "Unable to remove incomplete upload: %s",
            destination.name,
        )


@router.get(
    "/{file_id}",
    response_class=FileResponse,
)
def download_file(
    request: Request,
    file_id: str,
) -> FileResponse:
    """Return a file selected by server-generated ID."""
    if not FILE_ID_PATTERN.fullmatch(file_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    settings: Settings = request.app.state.settings

    destination = resolve_upload_path(
        settings.upload_directory,
        file_id,
    )

    if not destination.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    return FileResponse(
        path=destination,
        media_type=CONTENT_TYPE_BY_EXTENSION[destination.suffix],
        filename=file_id,
    )
