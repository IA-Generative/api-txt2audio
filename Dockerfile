# =========================================================
# Etape 1 — Prépare les wheels (zéro build lourd en CI)
# =========================================================
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS wheels

# pip rapide, sans cache, et (par défaut) refuser les builds depuis la source
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_ONLY_BINARY=:all:

# (Optionnel) outils de build si une lib n'a vraiment pas de wheel précompilée.
# Laisse commenté pour minimiser la RAM utilisée en CI.
# RUN apt-get update && apt-get install -y --no-install-recommends \
#       build-essential gcc g++ pkg-config \
#    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp
COPY requirements.txt /tmp/requirements.txt

# Télécharge toutes les wheels nécessaires localement (pas d'installation ici)
RUN python -m pip install --upgrade pip wheel setuptools \
 && pip download -r /tmp/requirements.txt -d /wheels


# =========================================================
# Etape 2 — Runtime minimal
# =========================================================
FROM python:${PYTHON_VERSION}-slim AS runtime

# Env d'exécution (faible bruit, caches HF, perf CPU prévisible)
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
    PORT=8080

# Paquets système nécessaires à l'exécution (ajuste au besoin via ARG)
ARG RUNTIME_APT="curl ca-certificates tzdata ffmpeg libsndfile1"
RUN apt-get update \
 && apt-get install -y --no-install-recommends ${RUNTIME_APT} \
 && rm -rf /var/lib/apt/lists/*

# Utilisateur non-root minimal
ARG USERNAME=appuser
ARG UID=10001
ARG GID=10001
RUN groupadd -g ${GID} -o ${USERNAME} || true \
 && useradd -m -u ${UID} -g ${GID} -o -s /bin/bash ${USERNAME}

# Venv léger pour isoler les deps
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /app
RUN mkdir -p /data/.cache/huggingface && chown -R ${USERNAME}:${USERNAME} /data
VOLUME ["/data"]

# Installe depuis les wheels pré-téléchargées (zéro compilation, faible RAM)
COPY --from=wheels /wheels /wheels
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
 && pip install --no-index --find-links=/wheels -r /tmp/requirements.txt \
 && rm -rf /wheels /tmp/requirements.txt

# Votre application
COPY app.py /app/app.py

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD python - <<'PY' || exit 1
import sys, urllib.request, os
port=os.environ.get("PORT","8080")
try:
    urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=2)
except Exception:
    sys.exit(1)
PY

USER ${USERNAME}
ENTRYPOINT ["bash","-lc","exec uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
