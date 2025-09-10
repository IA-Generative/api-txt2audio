FROM nvidia/cuda:13.0.0-cudnn-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 1) Dépendances système (root)
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-venv python3-pip \
      git ffmpeg build-essential \
  && rm -rf /var/lib/apt/lists/*

# 2) Créer un utilisateur non-root
#    - UID/GID 1000 par défaut (modifiable via --build-arg si besoin)
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd -g ${APP_GID} appuser \
  && useradd -m -u ${APP_UID} -g ${APP_GID} -s /usr/sbin/nologin appuser

# 3) Préparer le venv et les répertoires
#    On crée le venv en root, puis on le donne à appuser.
RUN python3 -m venv /opt/venv && chown -R appuser:appuser /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# 4) Passer en appuser pour tout le reste (sécurité)
USER appuser
WORKDIR /app

# 5) Mettre à jour pip (dans le venv) et installer les deps Python
COPY --chown=appuser:appuser requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install -r /app/requirements.txt

# 6) Copier le code de l’app
COPY --chown=appuser:appuser app /app

EXPOSE 8080
# Uvicorn écoutera sur un port >1024 (OK pour non-root)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
