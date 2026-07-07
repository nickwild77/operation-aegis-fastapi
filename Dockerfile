# syntax=docker/dockerfile:1.7

# Base image pinned by tag and digest.
ARG PYTHON_IMAGE="python:3.12-slim-bookworm@sha256:8a7e7cc04fd3e2bd787f7f24e22d5d119aa590d429b50c95dfe12b3abe52f48b"

FROM ${PYTHON_IMAGE} AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv

WORKDIR /build

RUN python -m venv "${VIRTUAL_ENV}"

ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    --require-hashes \
    --requirement requirements.txt


FROM ${PYTHON_IMAGE} AS runtime

ARG APP_UID=10001
ARG APP_GID=10001

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    APP_ENV=production \
    DATABASE_PATH=/data/aegis.db \
    UPLOAD_DIRECTORY=/uploads

WORKDIR /app

RUN groupadd \
        --gid "${APP_GID}" \
        appgroup \
    && useradd \
        --uid "${APP_UID}" \
        --gid "${APP_GID}" \
        --no-create-home \
        --shell /usr/sbin/nologin \
        appuser \
    && mkdir \
        --parents \
        /data \
        /uploads \
    && chown \
        --recursive \
        "${APP_UID}:${APP_GID}" \
        /app \
        /data \
        /uploads

COPY --from=builder \
    --chown=${APP_UID}:${APP_GID} \
    /opt/venv \
    /opt/venv

COPY --chown=${APP_UID}:${APP_GID} \
    app \
    ./app

USER ${APP_UID}:${APP_GID}

EXPOSE 8080

HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=10s \
    --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3)"]

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--no-server-header"]
