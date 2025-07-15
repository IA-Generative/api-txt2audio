import functools
import re
import os
import threading
import time
import logging
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import list_repo_files, hf_hub_download
from kokoro import KPipeline
import torch
import struct
import numpy as np
import subprocess
from langdetect import detect
#, DetectorFactory
#DetectorFactory.seed = 0  # pour des résultats déterministes
from typing import Optional, Tuple, Generator

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger("kokoro_tts")

# --- FASTAPI SETUP ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LANGUAGE MAPPING ---
LANGUAGE_CODE_MAPPING = {
    'en': 'a',
    'fr': 'f',
    'es': 'e',
    'it': 'i',
    'pt': 'p',
    'hi': 'h',
    'ja': 'j',
    'zh-cn': 'z',
    'zh-tw': 'z',
    'en-gb': 'b',
    'bg': 'a',   # bulgare, à adapter selon les voix disponibles
    # Ajoute d'autres codes si besoin
}

# --- VOICES DB INIT ---
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

# --- TOKENS ---
ALLOWED_TOKENS = set(os.getenv("TTS_ALLOWED_TOKENS", "token_client_a,token_client_b,token_admin_123").split(","))

# --- UTILS ---
#NBSP_RE = re.compile(r'[\u00A0\u202F]')         # espace insécable & fine insécable
#PAD_PUNCT_RE = re.compile(r'\s+([?!:;…])')      # espaces avant ? ! : ; …

#def normalize_punctuation(txt: str) -> str:
#    """
#    - remplace les espaces faibles/non-brisisus par un espace simple
#    - supprime l’espace avant ? ! : ; … (règle anglaise requise par Kokoro)
#    """
#    txt = NBSP_RE.sub(' ', txt)
#    return PAD_PUNCT_RE.sub(r'\1', txt)

def detect_language(text: str) -> str:
    try:
        detected_lang = detect(text)
        logger.info(f"🌍 Langue détectée: {detected_lang}")
    except Exception as e:
        logger.warning(f"❌ Erreur détection langue: {e}")
        detected_lang = 'en'
    return LANGUAGE_CODE_MAPPING.get(detected_lang, 'a')

def clean_text(text: str) -> str:
    return ' '.join([line.strip() for line in text.splitlines() if line.strip()])

def select_voice(requested: str, detected_language_code: str, requested_gender: Optional[str] = None) -> Tuple[str, str]:
    requested = (requested or "").lower().strip()
    requested_gender = (requested_gender or "").lower().strip()
    if requested_gender and requested_gender not in ("m", "f"):
        requested_gender = None

    candidates = [
        v for v in voice_db
        if v["name"] == requested and v["lang"] == detected_language_code and (not requested_gender or v["gender"] == requested_gender)
    ]
    if candidates:
        logger.info(f"✅ Voix exacte trouvée (nom+langue+genre): {candidates[0]['full']}")
        return candidates[0]['full'], candidates[0]['lang']

    candidates = [
        v for v in voice_db
        if v["name"] == requested and v["lang"] == detected_language_code
    ]
    if candidates:
        logger.info(f"✅ Voix trouvée (nom+langue): {candidates[0]['full']}")
        return candidates[0]['full'], candidates[0]['lang']

    if requested_gender:
        candidates = [
            v for v in voice_db
            if v["lang"] == detected_language_code and v["gender"] == requested_gender
        ]
        if candidates:
            logger.info(f"🟡 Fallback voix générique (langue+genre): {candidates[0]['full']}")
            return candidates[0]['full'], candidates[0]['lang']

    candidates = [
        v for v in voice_db
        if v["lang"] == detected_language_code
    ]
    if candidates:
        logger.info(f"🟡 Fallback voix générique (langue): {candidates[0]['full']}")
        return candidates[0]['full'], candidates[0]['lang']

    if voice_db:
        logger.warning(f"🔴 Fallback ultime : première voix du voice_db ({voice_db[0]['full']})")
        return voice_db[0]['full'], voice_db[0]['lang']

    logger.error("❌ Aucune voix trouvée")
    return "af_heart", "a"

@functools.lru_cache(maxsize=8)
def get_pipeline(voice_name: str, override_language: str) -> KPipeline:
    try:
        local_path = hf_hub_download(
            repo_id="hexgrad/Kokoro-82M",
            repo_type="model",
            filename=f"voices/{voice_name}.pt",
        )
        p = KPipeline(lang_code=override_language)
        p.load_voice(local_path)
        return p
    except Exception as e:
        logger.error(f"Failed to setup pipeline: {e}")
        raise RuntimeError(f"Failed to setup pipeline: {e}")

def make_wav_header(num_channels=1, sample_rate=24000, bits_per_sample=16) -> bytes:
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    hdr = b'RIFF' + struct.pack('<I', 0xFFFFFFFF) + b'WAVE'
    hdr += (b'fmt ' + struct.pack('<IHHIIHH',
               16, 1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample))
    hdr += b'data' + struct.pack('<I', 0xFFFFFFFF)
    return hdr

def count_words(text):
    # Compte uniquement les séquences de lettres/nombres (mots)
    return len(re.findall(r'\b\w+\b', text, flags=re.UNICODE))

def split_by_language_blocks(text: str, min_words: int = 5):
    # 1. Découpe en phrases avec ponctuation forte conservée
    raw_sentences = re.findall(r'.*?[\.!?;:…]+(?:\s+|$)|.+$', text, flags=re.DOTALL)
    raw_sentences = [s.strip() for s in raw_sentences if s.strip()]

    # 2. Fusionner jusqu'à avoir au moins `min_words` mots
    prepared_sentences = []
    buffer = ""
    word_count = 0
    for sentence in raw_sentences:
        buffer = (buffer + " " + sentence).strip()
        word_count = count_words(buffer)
        if word_count >= min_words:
            prepared_sentences.append(buffer)
            buffer = ""
            word_count = 0
    if buffer:
        # Essayer de rattacher à la dernière phrase si c'est trop court
        if prepared_sentences and count_words(buffer) < min_words:
            prepared_sentences[-1] += " " + buffer
        else:
            prepared_sentences.append(buffer)

    # 3. Détection langue & 4. Fusion des blocs consécutifs de même langue
    blocks = []
    last_lang = None
    current_block = []
    for chunk in prepared_sentences:
        try:
            lang = detect(chunk)
        except Exception:
            lang = "unknown"
        if last_lang is None or lang == last_lang:
            current_block.append(chunk)
        else:
            blocks.append((" ".join(current_block), last_lang))
            current_block = [chunk]
        last_lang = lang
    if current_block:
        blocks.append((" ".join(current_block), last_lang))

    return blocks

def stream_ffmpeg(generator: Generator, ffmpeg_cmd, media_type="audio/mpeg", timeout_sec=20):
    """Stream PCM à ffmpeg et yield l'audio encodé, protège contre les blocages."""
    def iter_pcm():
        yield make_wav_header()
        for i, (_, _, audio) in enumerate(generator):
            logger.info(f"Chunk audio {i} généré.")
            audio_np = audio.cpu().numpy() if isinstance(audio, torch.Tensor) else audio
            pcm = (audio_np * 32767).astype(np.int16).tobytes()
            yield pcm

    ffmpeg = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=10**7,
    )

    def feed():
        try:
            for chunk in iter_pcm():
                ffmpeg.stdin.write(chunk)
                ffmpeg.stdin.flush()
            ffmpeg.stdin.close()
        except Exception as e:
            logger.error(f"Erreur feed FFmpeg: {e}")
            try:
                ffmpeg.stdin.close()
            except Exception:
                pass

    t = threading.Thread(target=feed, daemon=True)
    t.start()

    last_chunk = time.time()
    try:
        while True:
            data = ffmpeg.stdout.read(4096)
            if data:
                last_chunk = time.time()
                yield data
            elif not t.is_alive():
                break
            elif time.time() - last_chunk > timeout_sec:
                ffmpeg.kill()
                logger.error("Timeout: génération audio bloquée.")
                raise HTTPException(status_code=500, detail="Timeout sur génération audio (texte trop complexe ?).")
            else:
                time.sleep(0.1)
        ffmpeg.wait()
        if ffmpeg.returncode != 0:
            stderr = ffmpeg.stderr.read().decode()
            logger.error(f"FFmpeg error: {stderr}")
            raise HTTPException(status_code=500, detail=f"Erreur encodage ({media_type}): {stderr}")
    finally:
        try:
            ffmpeg.stdout.close()
            ffmpeg.stderr.close()
        except Exception:
            pass

@app.post("/v1/audio/speech")
async def speech(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    # --- Auth ---
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
    token = authorization.split(" ", 1)[1]
    if token not in ALLOWED_TOKENS:
        raise HTTPException(status_code=403, detail="Forbidden")

    # --- Request parsing ---
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    raw_text = body.get("input", "")
    #text = raw_text
    #text = normalize_punctuation(raw_text)
    #logger.info(f"text: {text.encode('unicode_escape').decode()}")
#f"text: {text}")
#.strip()
    text = clean_text(raw_text)
    if not text:
        raise HTTPException(status_code=400, detail="Texte d'entrée vide")

    requested_voice = body.get("voice", "")
    requested_gender = body.get("gender", None)
    response_format = body.get("response_format", "opus").lower()

    # --- Découpage multilingue par blocs de même langue ---
    blocks = split_by_language_blocks(text)

    def multilang_generator():
        for segment, lang in blocks:
            logger.info(f"Synthèse bloc: '{segment[:30]}...' (langue: {lang})")
            detected_language_code = LANGUAGE_CODE_MAPPING.get(lang, 'a')
            voice_full, used_language_code = select_voice(requested_voice, detected_language_code, requested_gender)
            try:
                pipeline = get_pipeline(voice_full, used_language_code)
                for out in pipeline(segment, voice=voice_full):
                    yield out
            except Exception as e:
                logger.error(f"Erreur TTS pour le bloc '{segment[:30]}': {e}")
                continue

    if response_format == "mp3":
        ffmpeg_cmd = [
            "ffmpeg", "-f", "wav", "-i", "pipe:0",
            "-codec:a", "libmp3lame", "-ar", "24000", "-b:a", "128k", "-f", "mp3", "pipe:1"
        ]
        return StreamingResponse(
            stream_ffmpeg(multilang_generator(), ffmpeg_cmd, "audio/mpeg"),
            media_type="audio/mpeg"
        )
    elif response_format == "opus":
        ffmpeg_cmd = [
            "ffmpeg", "-f", "wav", "-i", "pipe:0",
            "-acodec", "libopus", "-ar", "24000", "-f", "ogg", "pipe:1"
        ]
        return StreamingResponse(
            stream_ffmpeg(multilang_generator(), ffmpeg_cmd, "audio/ogg"),
            media_type="audio/ogg"
        )
    elif response_format == "webm":
        ffmpeg_cmd = [
            "ffmpeg", "-f", "wav", "-i", "pipe:0",
            "-acodec", "libopus", "-ar", "24000", "-f", "webm", "pipe:1"
        ]
        return StreamingResponse(
            stream_ffmpeg(multilang_generator(), ffmpeg_cmd, "audio/webm"),
            media_type="audio/webm"
        )
    else:  # WAV brut
        def wav_chunks():
            yield make_wav_header()
            for _, _, audio in multilang_generator():
                audio_np = audio.cpu().numpy() if isinstance(audio, torch.Tensor) else audio
                pcm = (audio_np * 32767).astype(np.int16).tobytes()
                yield pcm
        return StreamingResponse(wav_chunks(), media_type="audio/wav")
