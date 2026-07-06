"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.database import initialize_database
from app.exception_handlers import (
    unhandled_exception_handler,
)
from app.middleware import SecurityHeadersMiddleware
from app.routers import files, secure, system, users


def create_app(
    settings: Settings | None = None,
) -> FastAPI:
    """Create an application with testable configuration."""
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(
        _: FastAPI,
    ) -> AsyncIterator[None]:
        resolved_settings.upload_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        initialize_database(resolved_settings.database_path)

        yield

    docs_url = "/docs" if resolved_settings.docs_enabled else None

    redoc_url = "/redoc" if resolved_settings.docs_enabled else None

    app = FastAPI(
        title=resolved_settings.app_name,
        version="0.2.0",
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.state.settings = resolved_settings

    app.add_middleware(
        SecurityHeadersMiddleware,
        app_env=resolved_settings.app_env,
    )

    app.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )

    app.include_router(system.router)
    app.include_router(users.router)
    app.include_router(files.router)
    app.include_router(secure.router)

    return app
