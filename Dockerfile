FROM python:3.11-slim AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    HF_HOME=/data/.cache/huggingface \
    TRANSFORMERS_CACHE=/data/.cache/huggingface/transformers \
    HF_HUB_ENABLE_HF_TRANSFER=1 \
    PORT=8080 \
    TZ=UTC \
    LANG=C.UTF-8 \
    # >>> important pour pyopenjtalk (CMake >=3.25 casse la compat <3.5)
    CMAKE_ARGS="-DCMAKE_POLICY_VERSION_MINIMUM=3.5"

# OS deps: audio, JP/CN + toolchain (pyopenjtalk/langdetect)
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc g++ make cmake pkg-config swig \
      git curl ca-certificates tzdata \
      ffmpeg libsndfile1 \
      mecab libmecab-dev mecab-ipadic-utf8 \
      libhtsengine-dev htsengine-api \
      libopenblas-dev \
      python3-dev \
      cython3 \
  && rm -rf /var/lib/apt/lists/*

# User non-root
ARG USERNAME=appuser
ARG UID=10001
ARG GID=10001
RUN groupadd -g ${GID} -o ${USERNAME} || true \
 && useradd -m -u ${UID} -g ${GID} -o -s /bin/bash ${USERNAME}

WORKDIR /app
RUN mkdir -p /data/.cache/huggingface /app \
 && chown -R ${USERNAME}:${USERNAME} /data /app

# Deps Python (wheels partout, sauf langdetect et pyopenjtalk)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip wheel setuptools \
 && pip install --prefer-binary \
      --only-binary=:all: \
      --no-binary=langdetect,pyopenjtalk \
      -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

# Code
COPY app.py /app/app.py

# Healthcheck sans heredoc (Kaniko-friendly)
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT}/healthz" || exit 1

USER ${USERNAME}
ENTRYPOINT ["sh","-c","exec uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
