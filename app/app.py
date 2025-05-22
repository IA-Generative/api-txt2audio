import functools
import re
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

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LANGUAGE_CODE_MAPPING = {
    'en': 'a',   # 🇺🇸 American English par défaut
    'fr': 'f',   # 🇫🇷 French
    'es': 'e',   # 🇪🇸 Spanish
    'it': 'i',   # 🇮🇹 Italian
    'pt': 'p',   # 🇧🇷 Brazilian Portuguese
    'hi': 'h',   # 🇮🇳 Hindi
    'ja': 'j',   # 🇯🇵 Japanese
    'zh-cn': 'z',# 🇨🇳 Mandarin
    'zh-tw': 'z',# 🇨🇳 Mandarin
    'en-gb': 'b',# 🇬🇧 British English
}

# --- Chargement et parsing des voix du repo HuggingFace ---
files = list_repo_files("hexgrad/Kokoro-82M", repo_type="model")
voices = [f.split("/")[-1].replace(".pt", "") for f in files if f.startswith("voices/")]

voice_db = []
for voice in voices:
    # Pattern : 2 lettres + '_' + nom
    m = re.match(r"([a-z])([mf])_(.+)", voice)
    if not m:
        continue
    lang, gender, name = m.groups()
    voice_db.append({
        "full": voice,         # nom complet (ex: ff_siwis)
        "lang": lang,          # code langue (ex: f)
        "gender": gender,      # m/f
        "name": name.lower()   # nom de la voix, en minuscule
    })

ALLOWED_TOKENS = {
    "token_client_a",
    "token_client_b",
    "token_admin_123",
}

def detect_language(text: str) -> str:
    try:
        detected_lang = detect(text)
        print(f"🌍 Langue détectée: {detected_lang}")
    except Exception as e:
        print(f"❌ Erreur détection langue: {e}")
        detected_lang = 'en'
    return LANGUAGE_CODE_MAPPING.get(detected_lang, 'a')

def select_voice(requested: str, detected_language_code: str, requested_gender: str = None):
    requested = (requested or "").lower().strip()
    requested_gender = (requested_gender or "").lower().strip()
    if requested_gender and requested_gender not in ("m", "f"):
        requested_gender = None

    # 1. Recherche stricte : nom + langue + genre
    candidates = [
        v for v in voice_db
        if v["name"] == requested and v["lang"] == detected_language_code and (not requested_gender or v["gender"] == requested_gender)
    ]
    if candidates:
        print(f"✅ Voix exacte trouvée (nom+langue+genre): {candidates[0]['full']}")
        return candidates[0]['full'], candidates[0]['lang']

    # 2. Nom + langue (genre ignoré)
    candidates = [
        v for v in voice_db
        if v["name"] == requested and v["lang"] == detected_language_code
    ]
    if candidates:
        print(f"✅ Voix trouvée (nom+langue): {candidates[0]['full']}")
        return candidates[0]['full'], candidates[0]['lang']

    # 3. Langue + genre demandé (voix générique)
    if requested_gender:
        candidates = [
            v for v in voice_db
            if v["lang"] == detected_language_code and v["gender"] == requested_gender
        ]
        if candidates:
            print(f"🟡 Fallback voix générique (langue+genre): {candidates[0]['full']}")
            return candidates[0]['full'], candidates[0]['lang']

    # 4. N'importe quelle voix dans la langue concernée
    candidates = [
        v for v in voice_db
        if v["lang"] == detected_language_code
    ]
    if candidates:
        print(f"🟡 Fallback voix générique (langue): {candidates[0]['full']}")
        return candidates[0]['full'], candidates[0]['lang']

    # 5. Si aucune voix pour cette langue, on prend la première voix dispo dans la base
    if voice_db:
        print(f"🔴 Fallback ultime : première voix du voice_db ({voice_db[0]['full']})")
        return voice_db[0]['full'], voice_db[0]['lang']

    # 6. Aucune voix du tout
    print("❌ Aucune voix trouvée")
    return "ff_siwis", "f"

@functools.lru_cache(maxsize=8)
def get_pipeline(voice_name: str, override_language: str):
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
        raise RuntimeError(f"Failed to setup pipeline: {e}")

def make_wav_header(num_channels=1, sample_rate=24000, bits_per_sample=16):
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    hdr = b'RIFF' + struct.pack('<I', 0xFFFFFFFF) + b'WAVE'
    hdr += (b'fmt ' + struct.pack('<IHHIIHH',
               16, 1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample))
    hdr += b'data' + struct.pack('<I', 0xFFFFFFFF)
    return hdr

@app.post("/v1/audio/speech")
async def speech(
    request: Request,
    authorization: str = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
    token = authorization.split(" ", 1)[1]
    if token not in ALLOWED_TOKENS:
        raise HTTPException(status_code=403, detail="Forbidden")
    body = await request.json()
    text = body.get("input", "")
    requested_voice = body.get("voice", "")
    requested_gender = body.get("gender", None)
    response_format = body.get("response_format", "wav").lower()
    detected_language_code = detect_language(text)

    voice_full, used_language_code = select_voice(requested_voice, detected_language_code, requested_gender)
    try:
        pipeline = get_pipeline(voice_full, used_language_code)
    except Exception as e:
        print(f"❌ Pipeline setup error: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")

    generator = pipeline(text, voice=voice_full)

    if response_format == "opus":
        def generate_opus():
            wav_data = make_wav_header()
            for _, _, audio in generator:
                audio_np = audio.cpu().numpy() if isinstance(audio, torch.Tensor) else audio
                pcm = (audio_np * 32767).astype(np.int16).tobytes()
                wav_data += pcm
            process = subprocess.Popen(
                ["ffmpeg", "-f", "wav", "-i", "pipe:0", "-f", "ogg", "-acodec", "libopus", "-ar", "24000", "pipe:1"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            out, err = process.communicate(wav_data)
            if process.returncode != 0:
                print("❌ FFmpeg error:", err.decode())
                raise HTTPException(status_code=500, detail="Audio encoding failed")
            yield out
        return StreamingResponse(generate_opus(), media_type="audio/ogg")

    def chunks():
        yield make_wav_header()
        for _, _, audio in generator:
            audio_np = audio.cpu().numpy() if isinstance(audio, torch.Tensor) else audio
            pcm = (audio_np * 32767).astype(np.int16).tobytes()
            yield pcm
    return StreamingResponse(chunks(), media_type="audio/wav")
