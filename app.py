# app.py — FastAPI TTS (Kokoro-82M) · multilang blocks + ffmpeg streaming + auth unifiée
# Dépendances: fastapi, uvicorn, langdetect, huggingface_hub, kokoro, torch, numpy

import os, re, time, json, struct, functools, threading, subprocess, logging
from typing import Optional, Tuple, Generator, Dict, List
import numpy as np
import torch
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from huggingface_hub import list_repo_files, hf_hub_download
from langdetect import detect
from kokoro import KPipeline

# =========================
# Logging
# =========================
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("kokoro_tts")

# =========================
# FastAPI & CORS
# =========================
app = FastAPI(title="tts-kokoro")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Constantes audio & service
# =========================
SAMPLE_RATE_TTS = 24000
CHANNELS = 1
BITS = 16

# =========================
# Auth helpers (API_TOKENS)
# =========================
def load_auth_tokens_env(var_name: str = "API_TOKENS") -> set[str]:
    v = os.getenv(var_name, "").strip()
    if not v:
        return set()  # vide => on refuse par défaut
    tokens = {t for t in v.replace(",", " ").split() if t}
    return tokens if tokens else set()

API_TOKENS = load_auth_tokens_env("API_TOKENS")  # {'*'} pour laisser ouvert, sinon liste
def require_bearer(authorization: Optional[str], allowed: set[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"error": {"type": "auth_missing", "message": "Missing or malformed Authorization header"}})
    token = authorization.split(" ", 1)[1].strip()
    if allowed != {"*"} and token not in allowed:
        raise HTTPException(status_code=403, detail={"error": {"type": "auth_forbidden", "message": "Forbidden"}})
    return token

# =========================
# Rate limit simple (sliding window)
# =========================
from collections import defaultdict, deque
WINDOW_S = float(os.getenv("RATE_WINDOW_S", "2"))
MAX_REQ = int(os.getenv("RATE_MAX_REQ", "6"))
TOK_REQS: Dict[str, deque] = defaultdict(deque)

def check_rate(token: str):
    now = time.time()
    q = TOK_REQS[token]
    while q and now - q[0] > WINDOW_S:
        q.popleft()
    if len(q) >= MAX_REQ:
        raise HTTPException(status_code=429, detail={"error": {"type": "rate_limit", "message": "Too many requests"}}, headers={"Retry-After": "1"})
    q.append(now)

# =========================
# Modèle Pydantic d'entrée
# =========================
class SpeechRequest(BaseModel):
    input: str
    voice: Optional[str] = None
    gender: Optional[str] = None   # "m" | "f"
    response_format: str = "opus"  # opus | mp3 | webm | wav

    @field_validator("gender")
    @classmethod
    def _v_gender(cls, v):
        if v is None: return None
        v = v.lower().strip()
        if v not in ("m", "f"):
            raise ValueError("gender must be 'm' or 'f'")
        return v

    @field_validator("response_format")
    @classmethod
    def _v_rf(cls, v):
        v = (v or "").lower().strip()
        if v not in ("opus", "mp3", "webm", "wav"):
            raise ValueError("response_format must be one of opus|mp3|webm|wav")
        return v

# =========================
# Langues / voix
# =========================
LANGUAGE_CODE_MAPPING = {
    "en": "a",
    "fr": "f",
    "es": "e",
    "it": "i",
    "pt": "p",
    "hi": "h",
    "ja": "j",
    "zh-cn": "z",
    "zh-tw": "z",
    "en-gb": "b",
    "bg": "a",  # pas de voix bg native -> fallback anglais
}

# Récupère la DB de voix Kokoro-82M sur HF
def build_voice_db() -> List[Dict[str, str]]:
    files = list_repo_files("hexgrad/Kokoro-82M", repo_type="model")
    voices = [f.split("/")[-1].replace(".pt", "") for f in files if f.startswith("voices/")]
    voice_db = []
    for voice in voices:
        m = re.match(r"([a-z])([mf])_(.+)", voice)
        if not m:
            continue
        lang, gender, name = m.groups()
        voice_db.append({
            "full": voice,
            "lang": lang,
            "gender": gender,
            "name": name.lower()
        })
    voice_db.sort(key=lambda v: (v["lang"], v["gender"], v["name"]))
    return voice_db

voice_db = build_voice_db()
startup_ts = time.time()

# =========================
# Utilitaires texte/langue
# =========================
def clean_text(text: str) -> str:
    return " ".join([line.strip() for line in text.splitlines() if line.strip()])

def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))

def split_by_language_blocks(text: str, min_words: int = 5):
    # 1) Découpe en phrases avec ponctuation forte conservée
    raw_sentences = re.findall(r".*?[\.!?;:…]+(?:\s+|$)|.+$", text, flags=re.DOTALL)
    raw_sentences = [s.strip() for s in raw_sentences if s.strip()]
    # 2) Fusionner jusqu'à min_words
    prepared, buf = [], ""
    for s in raw_sentences:
        buf = (buf + " " + s).strip()
        if count_words(buf) >= min_words:
            prepared.append(buf)
            buf = ""
    if buf:
        if prepared and count_words(buf) < min_words:
            prepared[-1] += " " + buf
        else:
            prepared.append(buf)
    # 3) Détection & fusion par langue
    blocks, last_lang, cur = [], None, []
    for chunk in prepared:
        try:
            lang = detect(chunk)
        except Exception:
            lang = "unknown"
        if last_lang is None or lang == last_lang:
            cur.append(chunk)
        else:
            blocks.append((" ".join(cur), last_lang))
            cur = [chunk]
        last_lang = lang
    if cur:
        blocks.append((" ".join(cur), last_lang))
    return blocks

# =========================
# Kokoro pipeline caching + locks
# =========================
@functools.lru_cache(maxsize=8)
def _download_voice(voice_name: str) -> str:
    return hf_hub_download(
        repo_id="hexgrad/Kokoro-82M",
        repo_type="model",
        filename=f"voices/{voice_name}.pt",
    )

@functools.lru_cache(maxsize=8)
def _get_pipeline(lang_code: str) -> KPipeline:
    # Instancier un pipeline par langue (plus stable)
    return KPipeline(lang_code=lang_code)

_voice_locks: Dict[str, threading.Lock] = {}
def _lock_for(voice: str) -> threading.Lock:
    if voice not in _voice_locks:
        _voice_locks[voice] = threading.Lock()
    return _voice_locks[voice]

def select_voice(requested: str, detected_language_code: str, requested_gender: Optional[str]) -> Tuple[str, str]:
    req = (requested or "").lower().strip()
    g = (requested_gender or "").lower().strip() if requested_gender else None
    if g and g not in ("m", "f"):
        g = None
    # 1) nom+lang+genre
    cand = [v for v in voice_db if v["name"] == req and v["lang"] == detected_language_code and (not g or v["gender"] == g)]
    if cand: return cand[0]["full"], cand[0]["lang"]
    # 2) nom+lang
    cand = [v for v in voice_db if v["name"] == req and v["lang"] == detected_language_code]
    if cand: return cand[0]["full"], cand[0]["lang"]
    # 3) lang+genre
    if g:
        cand = [v for v in voice_db if v["lang"] == detected_language_code and v["gender"] == g]
        if cand: return cand[0]["full"], cand[0]["lang"]
    # 4) lang
    cand = [v for v in voice_db if v["lang"] == detected_language_code]
    if cand: return cand[0]["full"], cand[0]["lang"]
    # 5) tout
    if voice_db:
        return voice_db[0]["full"], voice_db[0]["lang"]
    # Ultime
    return "af_heart", "a"

def make_wav_header(num_channels=CHANNELS, sample_rate=SAMPLE_RATE_TTS, bits_per_sample=BITS) -> bytes:
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    hdr = b"RIFF" + struct.pack("<I", 0xFFFFFFFF) + b"WAVE"
    hdr += b"fmt " + struct.pack("<IHHIIHH", 16, 1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample)
    hdr += b"data" + struct.pack("<I", 0xFFFFFFFF)
    return hdr

# =========================
# FFmpeg streaming (robuste)
# =========================
def stream_ffmpeg(generator: Generator, ffmpeg_cmd: List[str], media_type: str, timeout_sec: float = 20.0):
    def iter_pcm():
        yield make_wav_header()
        for i, (_, _, audio) in enumerate(generator):
            log.info(f"Chunk audio {i} généré")
            audio_np = audio.cpu().numpy() if isinstance(audio, torch.Tensor) else audio
            pcm = (audio_np * 32767).astype(np.int16).tobytes()
            yield pcm

    ffmpeg = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=10**7,
        close_fds=True,
    )

    def feeder():
        try:
            for chunk in iter_pcm():
                ffmpeg.stdin.write(chunk)
                ffmpeg.stdin.flush()
            try:
                ffmpeg.stdin.close()
            except Exception:
                pass
        except Exception as e:
            log.error(f"Erreur feed FFmpeg: {e}")
            try:
                ffmpeg.stdin.close()
            except Exception:
                pass

    t = threading.Thread(target=feeder, daemon=True)
    t.start()

    last = time.time()
    try:
        while True:
            data = ffmpeg.stdout.read(4096)
            if data:
                last = time.time()
                yield data
            elif not t.is_alive():
                break
            elif time.time() - last > timeout_sec:
                ffmpeg.kill()
                log.error("Timeout: génération audio bloquée.")
                raise HTTPException(status_code=500, detail={"error": {"type": "tts_timeout", "message": "Timeout audio generation"}})
            else:
                time.sleep(0.05)
        ffmpeg.wait()
        if ffmpeg.returncode != 0:
            stderr = ffmpeg.stderr.read().decode(errors="ignore")
            log.error(f"FFmpeg error: {stderr}")
            raise HTTPException(status_code=500, detail={"error": {"type": "ffmpeg_error", "message": stderr}})
    finally:
        try:
            ffmpeg.stdout.close(); ffmpeg.stderr.close()
        except Exception:
            pass

# =========================
# Endpoints santé
# =========================
@app.get("/healthz")
async def healthz():
    return {
        "uptime_s": int(time.time() - startup_ts),
        "voices_count": len(voice_db),
        "pipeline_cache": _get_pipeline.cache_info()._asdict(),
        "voice_cache": _download_voice.cache_info()._asdict(),
    }

@app.get("/readyz")
async def readyz():
    try:
        v0_full = voice_db[0]["full"] if voice_db else "af_heart"
        v0_lang = voice_db[0]["lang"] if voice_db else "a"
        # warm minimal
        _download_voice(v0_full)
        _get_pipeline(v0_lang)
        return {"ready": True}
    except Exception as e:
        return {"ready": False, "error": str(e)}

# =========================
# Endpoint principal TTS
# =========================
@app.post("/v1/audio/speech")
async def speech(request: Request, authorization: Optional[str] = Header(None)):
    # Auth + rate limit
    token = require_bearer(authorization, API_TOKENS if API_TOKENS else set())  # refuse si set() vide
    check_rate(token)

    # Parse
    try:
        payload = await request.json()
        data = SpeechRequest(**payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": {"type": "bad_request", "message": f"Invalid JSON: {e}"}})

    text = clean_text(data.input or "")
    if not text:
        raise HTTPException(status_code=400, detail={"error": {"type": "bad_request", "message": "Empty input text"}})

    # Découpage multilingue
    blocks = split_by_language_blocks(text)
    # Générateur multi-blocs
    def multilang_generator():
        for segment, lang in blocks:
            detected_lang = lang or "unknown"
            lang_code = LANGUAGE_CODE_MAPPING.get(detected_lang, "a")
            voice_full, used_lang_code = select_voice(data.voice or "", lang_code, data.gender)
            try:
                # DL voix + pipeline par langue
                voice_path = _download_voice(voice_full)
                pipeline = _get_pipeline(used_lang_code)
                # Load voice (kokoro permet de charger une voix; protégé par verrou par voix)
                with _lock_for(voice_full):
                    pipeline.load_voice(voice_path)
                    for out in pipeline(segment, voice=voice_full):
                        yield out
            except Exception as e:
                log.error(f"Erreur TTS bloc '{segment[:40]}…' : {e}")
                continue

    # Choix ffmpeg et media type
    rf = data.response_format
    if rf == "mp3":
        ffmpeg_cmd = [
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-f", "wav", "-i", "pipe:0", "-vn",
            "-ac", "1", "-ar", str(SAMPLE_RATE_TTS),
            "-codec:a", "libmp3lame", "-b:a", "128k",
            "-f", "mp3", "pipe:1"
        ]
        return StreamingResponse(stream_ffmpeg(multilang_generator(), ffmpeg_cmd, "audio/mpeg"), media_type="audio/mpeg")
    elif rf == "opus":
        ffmpeg_cmd = [
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-f", "wav", "-i", "pipe:0", "-vn",
            "-ac", "1", "-ar", str(SAMPLE_RATE_TTS),
            "-acodec", "libopus",
            "-f", "ogg", "pipe:1"
        ]
        return StreamingResponse(stream_ffmpeg(multilang_generator(), ffmpeg_cmd, "audio/ogg"), media_type="audio/ogg")
    elif rf == "webm":
        ffmpeg_cmd = [
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-f", "wav", "-i", "pipe:0", "-vn",
            "-ac", "1", "-ar", str(SAMPLE_RATE_TTS),
            "-acodec", "libopus",
            "-f", "webm", "pipe:1"
        ]
        return StreamingResponse(stream_ffmpeg(multilang_generator(), ffmpeg_cmd, "audio/webm"), media_type="audio/webm")
    else:  # wav streamable
        def wav_chunks():
            yield make_wav_header()
            for _, _, audio in multilang_generator():
                audio_np = audio.cpu().numpy() if isinstance(audio, torch.Tensor) else audio
                pcm = (audio_np * 32767).astype(np.int16).tobytes()
                yield pcm
        return StreamingResponse(wav_chunks(), media_type="audio/wav")

# =========================
# Main dev
# =========================
if __name__ == "__main__":
    import uvicorn
    # Prod: 1 worker (GPU/CPU batching interne), timeout keep-alive court si proxy
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
