# Base CUDA + cuDNN + Ubuntu 24.04
#FROM nvidia/cuda:13.0.0-cudnn-runtime-ubuntu24.04

# Dockerfile
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

# ---------- Stage 1: builder ----------
#FROM nvidia/cuda:13.0.0-cudnn-runtime-ubuntu24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VENV_PATH=/opt/venv

# Déps build uniquement pour ce stage
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      python3 python3-venv python3-pip \
      build-essential git ffmpeg ca-certificates curl; \
    rm -rf /var/lib/apt/lists/*

# Venv
RUN python3 -m venv "${VENV_PATH}"
ENV PATH="${VENV_PATH}/bin:${PATH}"

# Copier uniquement requirements pour profiter du cache
WORKDIR /tmp
COPY requirements.txt /tmp/requirements.txt

# Installer deps (builder seulement)
RUN set -eux; \
    python -m pip install --upgrade pip setuptools wheel; \
    # Si tu as des index privés/wheels CUDA, ajoute-les ici (ex: --extra-index-url)
    pip install -r /tmp/requirements.txt; \
    # Nettoyage venv (réduit quelques centaines de Mo)
    find "${VENV_PATH}" -type d -name "__pycache__" -exec rm -rf {} +; \
    find "${VENV_PATH}" -type f -name "*.pyc" -delete; \
    pip cache purge || true

# ---------- Stage 2: runtime ----------
#FROM nvidia/cuda:13.0.0-cudnn-runtime-ubuntu24.04

# Dockerfile
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VENV_PATH=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

# Déps runtime SEULEMENT
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      python3 python3-venv python3-pip \
      ffmpeg ca-certificates tzdata; \
    rm -rf /var/lib/apt/lists/*

# Utilisateur non-root idempotent
ARG APP_UID=1000
ARG APP_GID=1000
ARG USERNAME=appuser
RUN set -eux; \
    if getent group "${APP_GID}" >/dev/null; then \
      echo "Reusing GID ${APP_GID}"; \
    else \
      groupadd -g "${APP_GID}" "${USERNAME}"; \
    fi; \
    UID_TO_USE="${APP_UID}"; \
    if getent passwd "${APP_UID}" >/dev/null; then \
      echo "UID ${APP_UID} already exists, fallback 1001"; \
      UID_TO_USE=1001; \
    fi; \
    if getent passwd "${USERNAME}" >/dev/null; then \
      echo "User ${USERNAME} exists"; \
    else \
      useradd -m -u "${UID_TO_USE}" -g "${APP_GID}" -s /usr/sbin/nologin "${USERNAME}"; \
    fi

# Copier le venv depuis le builder (seulement le runtime Python)
COPY --from=builder --chown=${USERNAME}:${APP_GID} ${VENV_PATH} ${VENV_PATH}

# App
WORKDIR /app
COPY --chown=${USERNAME}:${APP_GID} app /app

USER ${USERNAME}
EXPOSE 8080

# Démarrage
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
