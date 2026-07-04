# Phase 0 Evidence

## Repository

- Repository: operation-aegis-fastapi
- Baseline tag: baseline-vulnerable
- Baseline commit: b3f2da21405bfe046d09b45597f8e3416e7a24eb
- Working branch: docs/phase-0-baseline

## Local environment

- Git: git version 2.39.5 (Apple Git-154)
- Python: Python 3.12.13
- Docker: Docker version 29.4.0, build 9d7ad9f

## Verification results

- Python dependencies installed successfully.
- Existing unit tests executed.
- Docker image built as `operation-aegis:baseline`.
- Container started on localhost port 8080.
- Root endpoint returned HTTP 200.
- OpenAPI specification was available.
- SQL injection behavior was reproduced locally.
- Arbitrary file-read behavior was reproduced locally.
- Hardcoded-token authentication was reproduced locally.
- Unhandled exception behavior was reproduced locally.
- Unrestricted upload behavior was reproduced locally.

## Safety note

All verification was performed against a local disposable Docker container.
The intentionally vulnerable application was not exposed to the public network.
