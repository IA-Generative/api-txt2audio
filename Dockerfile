# ===== builder =====
FROM pytorch/pytorch:2.4.1-cuda12.4-cudnn9-devel AS builder
# (éventuels outils build, compilation, caches…)

# ===== runtime =====
FROM pytorch/pytorch:2.4.1-cuda12.4-cudnn9-runtime AS runtime
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

RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg libsndfile1 curl ca-certificates tzdata \
 && rm -rf /var/lib/apt/lists/*

ARG USERNAME=appuser
ARG UID=10001
ARG GID=10001
RUN groupadd -g ${GID} -o ${USERNAME} || true \
 && useradd -m -u ${UID} -g ${GID} -o -s /bin/bash ${USERNAME}

WORKDIR /app
RUN mkdir -p /data/.cache/huggingface && chown -R ${USERNAME}:${USERNAME} /data
VOLUME ["/data"]

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip wheel setuptools \
 && pip install -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

COPY app.py /app/app.py

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT}/healthz" || exit 1

USER ${USERNAME}
ENTRYPOINT ["bash","-lc","exec uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
