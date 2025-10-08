# =========================================================
# Dockerfile minimal · build des wheels (sdist) si besoin · runtime slim
# =========================================================
ARG PYTHON_VERSION=3.12

# ---------- Étape 1 : wheels (avec toolchain pour construire les sdists) ----------
FROM python:${PYTHON_VERSION}-slim AS wheels

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_PREFER_BINARY=1

# Outils de build pour paquets Python/C++ (pyopenjtalk nécessite cmake + make + g++)
# On ajoute aussi libsndfile1-dev pour compiler contre libsndfile
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential cmake pkg-config ninja-build \
      libsndfile1-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp
COPY requirements.txt /tmp/requirements.txt

# 1) Upgrade pip toolchain
# 2) Construire des wheels pour TOUTES les deps (y compris celles livrées en sdist)
#    -> évite la compilation dans l'étape runtime
RUN python -m pip install --upgrade pip wheel setuptools \
 && pip wheel --prefer-binary -r /tmp/requirements.txt -w /wheels

# ---------- Étape 2 : runtime minimal ----------
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/data/.cache/huggingface \
    TRANSFORMERS_CACHE=/data/.cache/huggingface/transformers \
    HF_HUB_ENABLE_HF_TRANSFER=1 \
    TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    BATCH_SIZE=12 \
    MAX_WAIT_MS=12 \
    SENTENCE_MAX_QUEUE=48 \
    WORD_MAX_QUEUE=48 \
    SENTENCE_POLICY=reject_new \
    WORD_POLICY=drop_oldest \
    PORT=8080

# Paquets runtime (sans toolchain)
ARG RUNTIME_APT="curl ca-certificates tzdata ffmpeg libsndfile1"
RUN apt-get update \
 && apt-get install -y --no-install-recommends ${RUNTIME_APT} \
 && rm -rf /var/lib/apt/lists/*

# Utilisateur non-root
ARG USERNAME=appuser
ARG UID=10001
ARG GID=10001
RUN groupadd -g ${GID} -o ${USERNAME} || true \
 && useradd -m -u ${UID} -g ${GID} -o -s /bin/bash ${USERNAME}

# Venv d'exécution
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /app
RUN mkdir -p /data/.cache/huggingface && chown -R ${USERNAME}:${USERNAME} /data
VOLUME ["/data"]

# Install offline depuis les wheels construits
COPY --from=wheels /wheels /wheels
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
 && pip install --no-index --find-links=/wheels -r /tmp/requirements.txt \
 && rm -rf /wheels /tmp/requirements.txt

# Application
COPY app.py /app/app.py

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD sh -c 'curl -fsS "http://127.0.0.1:${PORT:-8080}/healthz" || exit 1'

USER ${USERNAME}
ENTRYPOINT ["bash","-lc","exec uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
