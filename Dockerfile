FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Installer uniquement ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg \
  && rm -rf /var/lib/apt/lists/*

# Créer l’utilisateur non-root
ARG USERNAME=appuser
ARG UID=10001
ARG GID=10001
RUN groupadd -g ${GID} -o ${USERNAME} || true \
 && useradd -m -u ${UID} -g ${GID} -o -s /bin/bash ${USERNAME}

WORKDIR /app
COPY requirements.txt /app/requirements.txt

# Installer les dépendances Python sans pinning, avec les dernières versions
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# Copier le code
COPY app.py /app/app.py

# Exposer le port
EXPOSE 8080

# Healthcheck simple
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT}/healthz" || exit 1

USER ${USERNAME}
ENTRYPOINT ["sh", "-c", "exec uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
