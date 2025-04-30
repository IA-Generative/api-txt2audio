from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import list_repo_files, hf_hub_download
from kokoro import KPipeline
import torch
import struct
import numpy as np
import subprocess
from langdetect import detect  # Ajout pour la détection de langue

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = None
current_voice = None
current_language_code = None  # On garde aussi la langue détectée

# Mapping langdetect ➔ code de ta liste
LANGUAGE_CODE_MAPPING = {
    'en': 'a',  # 🇺🇸 American English par défaut
    'fr': 'f',  # 🇫🇷 French
    'es': 's',  # 🇪🇸 Spanish
    'it': 'i',  # 🇮🇹 Italian
    'pt': 'b',  # 🇧🇷 Brazilian Portuguese
    'hi': 'h',  # 🇮🇳 Hindi
    'ja': 'j',  # 🇯🇵 Japanese
    'zh-cn': 'm',  # 🇨🇳 Mandarin
    'zh-tw': 'm',  # 🇨🇳 Mandarin
    'en-gb': 'b',  # 🇬🇧 British English
}

# Chargement des fichiers de voix disponibles
files = list_repo_files("hexgrad/Kokoro-82M", repo_type="model")
voices = [f.split("/")[-1].replace(".pt", "") for f in files if f.startswith("voices/")]

# Construction du lookup { nom: (voix complète, code langue) }
voice_lookup = {}
for voice in voices:
    underscore_index = voice.find("_")
    if underscore_index == -1:
        continue
    name = voice[underscore_index + 1:].lower()
    language_code = voice[0]
    voice_lookup[name] = (voice, language_code)

# Jetons valides
ALLOWED_TOKENS = {
    "token_client_a",
    "token_client_b",
    "token_admin_123",
}

def select_voice(requested: str) -> (str, str):
    requested = requested.lower().strip()
    if requested in voice_lookup:
        return voice_lookup[requested]
    for name, (voice_name, language_code) in voice_lookup.items():
        if requested in name:
            return voice_name, language_code
    return "ff_siwis", "f"

def detect_language(text: str) -> str:
    try:
        detected_lang = detect(text)
        print(f"🌍 Langue détectée: {detected_lang}")
    except Exception as e:
        print(f"❌ Erreur détection langue: {e}")
        detected_lang = 'en'
    return LANGUAGE_CODE_MAPPING.get(detected_lang, 'a')

def setup_pipeline_for_voice(voice_name: str, override_language: str):
    global pipeline, current_voice, current_language_code

    # Si même voix et même langue détectée, ne rien faire
    if current_voice == voice_name and current_language_code == override_language:
        return

    # Télécharger le fichier modèle
    try:
        local_path = hf_hub_download(
            repo_id="hexgrad/Kokoro-82M",
            repo_type="model",
            filename=f"voices/{voice_name}.pt",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download voice model: {e}")

    # Créer le pipeline avec la langue détectée (override)
    try:
        p = KPipeline(lang_code=override_language)
        p.load_voice(local_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize voice pipeline: {e}")

    assert p is not None, "Pipeline creation returned None"

    pipeline = p
    current_voice = voice_name
    current_language_code = override_language

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
    response_format = body.get("response_format", "wav").lower()

    voice_full, _ = select_voice(requested_voice)
    detected_language_code = detect_language(text)

    try:
        setup_pipeline_for_voice(voice_full, detected_language_code)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Unexpected setup error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error during pipeline setup.")

    if pipeline is None:
        raise HTTPException(status_code=500, detail="Pipeline initialization failed.")

    generator = pipeline(text, voice=voice_full)

    if response_format == "opus":
        def generate_opus():
            wav_data = make_wav_header()
            for _, _, audio in generator:
                if isinstance(audio, torch.Tensor):
                    audio_np = audio.cpu().numpy()
                else:
                    audio_np = audio
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
            if isinstance(audio, torch.Tensor):
                audio_np = audio.cpu().numpy()
            else:
                audio_np = audio
            pcm = (audio_np * 32767).astype(np.int16).tobytes()
            yield pcm

    return StreamingResponse(chunks(), media_type="audio/wav")
