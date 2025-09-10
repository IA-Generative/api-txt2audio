# ========= Stage 1: build venv with deps =========
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS venv

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VENV_PATH=/opt/venv

# Build deps only in this stage
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      build-essential git ffmpeg ca-certificates curl; \
    rm -rf /var/lib/apt/lists/*

# Create venv and install Python deps
RUN python -m venv "${VENV_PATH}"
ENV PATH="${VENV_PATH}/bin:${PATH}"

WORKDIR /tmp
COPY requirements.txt /tmp/requirements.txt

RUN set -eux; \
    python -m pip install --upgrade pip setuptools wheel; \
    pip install -r /tmp/requirements.txt; \
    # Clean venv caches
    find "${VENV_PATH}" -type d -name "__pycache__" -exec rm -rf {} +; \
    find "${VENV_PATH}" -type f -name "*.pyc" -delete; \
    pip cache purge || true

# ========= Stage 2: slim runtime =========
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VENV_PATH=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

# Runtime deps only
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      ffmpeg ca-certificates tzdata; \
    rm -rf /var/lib/apt/lists/*

# Non-root user (idempotent)
ARG APP_UID=1000
ARG APP_GID=1000
ARG USERNAME=appuser
RUN set -eux; \
    if getent group "${APP_GID}" >/dev/null; then \
      echo "Reusing existing GID ${APP_GID}"; \
    else \
      groupadd -g "${APP_GID}" "${USERNAME}"; \
    fi; \
    UID_TO_USE="${APP_UID}"; \
    if getent passwd "${APP_UID}" >/dev/null; then \
      echo "UID ${APP_UID} already exists, fallback to 1001"; \
      UID_TO_USE=1001; \
    fi; \
    if getent passwd "${USERNAME}" >/dev/null; then \
      echo "User ${USERNAME} already exists"; \
    else \
      useradd -m -u "${UID_TO_USE}" -g "${APP_GID}" -s /usr/sbin/nologin "${USERNAME}"; \
    fi

# Copy venv from the venv stage  ✅ (note --from=venv, pas "builder")
COPY --from=venv --chown=${USERNAME}:${APP_GID} ${VENV_PATH} ${VENV_PATH}

# App
WORKDIR /app
COPY --chown=${USERNAME}:${APP_GID} app /app

USER ${USERNAME}
EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
