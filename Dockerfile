# =========================================================
# Dockerfile : apt -> torch -> requirements (venv) | sans pin torch
# =========================================================
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_PREFER_BINARY=1 \        # <-- favorise les wheels (évite build source)
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/data/.cache/huggingface \
    TRANSFORMERS_CACHE=/data/.cache/huggingface/transformers \
    TOKENIZERS_PARALLELISM=false \
    PORT=8080 \
    CMAKE_BUILD_PARALLEL_LEVEL=1 \
    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1

ARG RUNTIME_APT="curl ca-certificates tzdata ffmpeg libsndfile1"
ARG BUILD_DEPS="build-essential cmake git pkg-config python3-dev"
RUN apt-get update \
 && apt-get install -y --no-install-recommends ${RUNTIME_APT} ${BUILD_DEPS} \
 && rm -rf /var/lib/apt/lists/*

# user + venv
ARG USERNAME=appuser
ARG UID=10001
ARG GID=10001
RUN groupadd -g ${GID} -o ${USERNAME} || true \
 && useradd -m -u ${UID} -g ${GID} -o -s /bin/bash ${USERNAME}

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# 2) torch (pip normal, non épinglé)
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install torch torchvision torchaudio \
 && rm -rf /root/.cache/pip

# 3) requirements (sans flags spéciaux)
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt \
 && rm -rf /root/.cache/pip

# purge build deps
RUN apt-get purge -y ${BUILD_DEPS} \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

# app
COPY app.py /app/app.py
RUN mkdir -p /data/.cache/huggingface && chown -R ${USERNAME}:${USERNAME} /data
VOLUME ["/data"]

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD sh -c 'curl -fsS "http://127.0.0.1:${PORT:-8080}/healthz" || exit 1'

USER ${USERNAME}
ENTRYPOINT ["bash","-lc","exec uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
