"""Pure ASGI middleware for HTTP security headers."""

from __future__ import annotations

from typing import Literal

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

DOCS_PATHS = {
    "/docs",
    "/redoc",
    "/openapi.json",
}


class SecurityHeadersMiddleware:
    """Add security headers without BaseHTTPMiddleware or call_next."""

    def __init__(
        self,
        app: ASGIApp,
        app_env: Literal[
            "development",
            "test",
            "production",
        ],
    ) -> None:
        self.app = app
        self.app_env = app_env

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """Process one ASGI request."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(
            message: Message,
        ) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)

                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "no-referrer"
                headers["Permissions-Policy"] = "camera=(), geolocation=(), microphone=()"
                headers["Cross-Origin-Resource-Policy"] = "same-origin"
                headers["Cache-Control"] = "no-store"

                path = scope.get("path", "")

                if path not in DOCS_PATHS:
                    headers["Content-Security-Policy"] = (
                        "default-src 'none'; "
                        "base-uri 'none'; "
                        "frame-ancestors 'none'; "
                        "form-action 'none'"
                    )

                scheme = scope.get("scheme", "http")

                if scheme == "https" and self.app_env == "production":
                    headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

            await send(message)

        await self.app(
            scope,
            receive,
            send_with_security_headers,
        )
