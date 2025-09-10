# Base CUDA + cuDNN + Ubuntu 24.04
#FROM nvidia/cuda:13.0.0-cudnn-runtime-ubuntu24.04

# Dockerfile
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

# ---- Environnement ----
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}"

# ---- Dépendances système (root) ----
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        python3 python3-venv python3-pip \
        git ffmpeg build-essential ca-certificates curl; \
    rm -rf /var/lib/apt/lists/*

# ---- Utilisateur non-root idempotent ----
ARG APP_UID=1000
ARG APP_GID=1000
ARG USERNAME=appuser

RUN set -eux; \
    # Groupe : si GID existe, on le réutilise; sinon on crée ${USERNAME}
    if getent group "${APP_GID}" >/dev/null; then \
        echo "GID ${APP_GID} existe déjà ($(getent group ${APP_GID} | cut -d: -f1))."; \
    else \
        groupadd -g "${APP_GID}" "${USERNAME}"; \
    fi; \
    # UID : si déjà pris, fallback 1001
    UID_TO_USE="${APP_UID}"; \
    if getent passwd "${APP_UID}" >/dev/null; then \
        echo "UID ${APP_UID} existe déjà ($(getent passwd ${APP_UID} | cut -d: -f1)), fallback 1001."; \
        UID_TO_USE=1001; \
    fi; \
    # Créer l'utilisateur si absent
    if getent passwd "${USERNAME}" >/dev/null; then \
        echo "Utilisateur ${USERNAME} existe déjà."; \
    else \
        useradd -m -u "${UID_TO_USE}" -g "${APP_GID}" -s /usr/sbin/nologin "${USERNAME}"; \
    fi

# ---- Python venv (créé en root, possédé par appuser) ----
RUN set -eux; \
    python3 -m venv /opt/venv; \
    chown -R ${USERNAME}:${APP_GID} /opt/venv

# ---- Passage en utilisateur non-root ----
USER ${USERNAME}
WORKDIR /app

# ---- Dépendances Python ----
# Astuce: copier seulement requirements.txt d'abord pour tirer parti du cache Docker
COPY --chown=${USERNAME}:${APP_GID} requirements.txt /app/requirements.txt

# Mettre à jour pip dans le venv (PEP 668 safe car venv), puis installer deps
RUN set -eux; \
    python -m pip install --upgrade pip setuptools wheel; \
    pip install -r /app/requirements.txt

# ---- Application ----
COPY --chown=${USERNAME}:${APP_GID} app /app

EXPOSE 8080

# ---- Démarrage ----
# Uvicorn en non-root (port >1024), logs flushés
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
