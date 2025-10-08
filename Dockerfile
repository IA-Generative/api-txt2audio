# =========================================================
# Dockerfile simple : apt -> torch -> requirements (venv)
# avec outils de build éphémères (purge ensuite)
# =========================================================
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/data/.cache/huggingface \
    TRANSFORMERS_CACHE=/data/.cache/huggingface/transformers \
    TOKENIZERS_PARALLELISM=false \
    PORT=8080 \
    # Evite les OOM pendant les builds C/C++ via pip
    CMAKE_BUILD_PARALLEL_LEVEL=1

# 1) apt (runtime + build éphémère)
ARG RUNTIME_APT="curl ca-certificates tzdata ffmpeg libsndfile1"
ARG BUILD_DEPS="build-essential cmake git pkg-config python3-dev"
RUN apt-get update \
 && apt-get install -y --no-install-recommends ${RUNTIME_APT} ${BUILD_DEPS} \
 && rm -rf /var/lib/apt/lists/*

# User non-root + venv
ARG USERNAME=appuser
ARG UID=10001
ARG GID=10001
RUN groupadd -g ${GID} -o ${USERNAME} || true \
 && useradd -m -u ${UID} -g ${GID} -o -s /bin/bash ${USERNAME}

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# 2) torch (pip "normal" – wheels CUDA si dispo pour ta plateforme)
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install torch torchvision torchaudio

# 3) requirements complet (sans flags spéciaux)
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# 🔻 Purge les deps de build pour rendre l'image slim
RUN apt-get purge -y ${BUILD_DEPS} \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

# App
COPY app.py /app/app.py
RUN mkdir -p /data/.cache/huggingface && chown -R ${USERNAME}:${USERNAME} /data
VOLUME ["/data"]

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD sh -c 'curl -fsS "http://127.0.0.1:${PORT:-8080}/healthz" || exit 1'

USER ${USERNAME}
ENTRYPOINT ["bash","-lc","exec uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
