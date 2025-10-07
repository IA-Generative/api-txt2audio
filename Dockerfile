# ===== base tags =====
# Même tag pour builder et runtime pour éviter les incohérences de CUDA/cuDNN
ARG PYTORCH_TAG=2.4.1-cuda12.4-cudnn9

# ===== builder =====
FROM pytorch/pytorch:${PYTORCH_TAG}-devel AS builder

# Optionnel: outils build SI tu actives JA/ZH qui compilent parfois
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential cmake pkg-config wget git \
#  && rm -rf /var/lib/apt/lists/*

# Crée un venv isolé (plus propre que le site-packages global)
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}" \
    PIP_NO_CACHE_DIR=1

# Copie du requirements en premier (layer cache friendly)
COPY requirements.txt /tmp/requirements.txt

# IMPORTANT :
# - torch est déjà dans l'image base -> ne PAS le réinstaller
# - Si ton requirements.txt contient torch, remplace par --no-deps ou enlève la ligne torch.
# - --prefer-binary pour éviter des builds source pénibles
RUN pip install --upgrade pip wheel setuptools \
 && pip install --prefer-binary -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

# ===== runtime =====
FROM pytorch/pytorch:${PYTORCH_TAG}-runtime AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility \
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

# ffmpeg pour mp3/opus/webm + libs de base
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg libsndfile1 curl ca-certificates tzdata \
      mecab libmecab2 mecab-ipadic-utf8 \
      libopenblas0 \
 && rm -rf /var/lib/apt/lists/*

# Utilisateur non-root
ARG USERNAME=appuser
ARG UID=10001
ARG GID=10001
RUN groupadd -g ${GID} -o ${USERNAME} || true \
 && useradd -m -u ${UID} -g ${GID} -o -s /bin/bash ${USERNAME}

# Copie du venv figé depuis le builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Dossiers appli & cache
WORKDIR /app
RUN mkdir -p /data/.cache/huggingface /app \
 && chown -R ${USERNAME}:${USERNAME} /data /app
VOLUME ["/data"]

# Code
COPY app.py /app/app.py
# (Facultatif) si tu ajoutes des assets, fais un chown:
# RUN chown -R ${USERNAME}:${USERNAME} /app

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT}/healthz" || exit 1

USER ${USERNAME}
ENTRYPOINT ["bash","-lc","exec uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
