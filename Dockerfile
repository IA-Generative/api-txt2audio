# =========================================================
# Dockerfile minimal · préfère les wheels · image finale slim
# =========================================================
# Étape 1 : télécharge les artefacts (wheels si dispo, sinon sdists)
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim AS wheels

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_PREFER_BINARY=1

WORKDIR /tmp
COPY requirements.txt /tmp/requirements.txt

# Télécharge toutes les deps dans /wheels (pas d'installation ici)
RUN python -m pip install --upgrade pip wheel setuptools \
 && pip download --prefer-binary -r /tmp/requirements.txt -d /wheels


# Étape 2 : runtime minimal
FROM python:${PYTHON_VERSION}-slim AS runtime

# ENV d'exécution
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

# Paquets système nécessaires à l'exécution (ajuste via ARG)
ARG RUNTIME_APT="curl ca-certificates tzdata ffmpeg libsndfile1"
RUN apt-get update \
 && apt-get install -y --no-install-recommends ${RUNTIME_APT} \
 && rm -rf /var/lib/apt/lists/*

# (Optionnel) Toolchain si certaines deps n'ont **que** un sdist nécessitant une build
# Laisse commenté tant que tout passe sans compilation lourde.
# ARG BUILD_DEPS="build-essential gcc g++ pkg-config python3-dev"
# RUN apt-get update \
#  && apt-get install -y --no-install-recommends ${BUILD_DEPS} \
#  && rm -rf /var/lib/apt/lists/*

# Utilisateur non-root
ARG USERNAME=appuser
ARG UID=10001
ARG GID=10001
RUN groupadd -g ${GID} -o ${USERNAME} || true \
 && useradd -m -u ${UID} -g ${GID} -o -s /bin/bash ${USERNAME}

# Venv (isole les deps)
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /app
RUN mkdir -p /data/.cache/huggingface && chown -R ${USERNAME}:${USERNAME} /data
VOLUME ["/data"]

# Installe hors-ligne depuis /wheels (wheels préférées, sinon sdist)
COPY --from=wheels /wheels /wheels
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
 && pip install --no-index --find-links=/wheels -r /tmp/requirements.txt \
 && rm -rf /wheels /tmp/requirements.txt

# Application
COPY app.py /app/app.py

EXPOSE 8080

# Healthcheck compatible Kaniko (pas de heredoc)
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD sh -c 'curl -fsS "http://127.0.0.1:${PORT:-8080}/healthz" || exit 1'

USER ${USERNAME}
ENTRYPOINT ["bash","-lc","exec uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
