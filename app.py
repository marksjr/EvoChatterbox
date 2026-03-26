from __future__ import annotations

import os
import platform
import re
import shutil
import tempfile
from pathlib import Path
from threading import Lock

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = BASE_DIR / "output"
CACHE_DIR = BASE_DIR / ".cache"
MULTILINGUAL_DIR = CACHE_DIR / "multilingual"
PKUSEG_DIR = CACHE_DIR / "pkuseg"
OUTPUT_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
MULTILINGUAL_DIR.mkdir(exist_ok=True)
PKUSEG_DIR.mkdir(exist_ok=True)

os.environ.setdefault("HF_HOME", str(CACHE_DIR / "huggingface"))
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(CACHE_DIR / "huggingface" / "hub"))
os.environ.setdefault("PKUSEG_HOME", str(PKUSEG_DIR))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import torch
import torchaudio as ta
from chatterbox.models.s3gen import S3GEN_SR
from chatterbox.mtl_tts import ChatterboxMultilingualTTS, SUPPORTED_LANGUAGES
from chatterbox.tts import ChatterboxTTS
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from huggingface_hub import snapshot_download

app = FastAPI(title="Evo Chatterbox")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_tts_model = None
_tts_model_lock = Lock()
_multilingual_model = None
_multilingual_model_lock = Lock()
MAX_CHUNK_CHARS = 220
ULTRA_CHUNK_CHARS = 140
CHUNK_SILENCE_MS = 140
ULTRA_CHUNK_SILENCE_MS = 220


def resolve_device() -> str:
    requested_device = os.getenv("CHATTERBOX_DEVICE", "auto").strip().lower()
    if requested_device == "cpu":
        return "cpu"
    if requested_device == "cuda":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def get_runtime_info() -> dict[str, str | bool | None]:
    active_device = resolve_device()
    return {
        "device": active_device,
        "device_mode": os.getenv("CHATTERBOX_DEVICE", "auto").strip().lower() or "auto",
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "cpu_name": platform.processor() or None,
    }


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_text_for_quality(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    text = normalize_text(text)
    if len(text) <= max_chars:
        return [text]

    parts = re.split(r"(?<=[\.\!\?;:。！？])\s+", text)
    chunks: list[str] = []
    current = ""

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if len(part) > max_chars:
            words = part.split(" ")
            long_current = ""
            for word in words:
                candidate = f"{long_current} {word}".strip()
                if len(candidate) > max_chars and long_current:
                    chunks.append(long_current)
                    long_current = word
                else:
                    long_current = candidate
            if long_current:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.append(long_current)
            continue

        candidate = f"{current} {part}".strip()
        if len(candidate) > max_chars and current:
            chunks.append(current)
            current = part
        else:
            current = candidate

    if current:
        chunks.append(current)

    return chunks or [text]


def generate_chunked_audio(
    model: object,
    backend: str,
    text: str,
    language_id: str,
    generate_kwargs: dict,
    max_chunk_chars: int = MAX_CHUNK_CHARS,
    silence_ms: int = CHUNK_SILENCE_MS,
) -> torch.Tensor:
    chunks = split_text_for_quality(text, max_chars=max_chunk_chars)
    silence_samples = int((silence_ms / 1000) * S3GEN_SR)
    silence = torch.zeros((1, silence_samples), dtype=torch.float32)
    rendered: list[torch.Tensor] = []

    for index, chunk in enumerate(chunks):
        if backend == "multilingual":
            wav = model.generate(chunk, language_id=language_id, **generate_kwargs)
        else:
            wav = model.generate(chunk, **generate_kwargs)

        if wav.dim() == 1:
            wav = wav.unsqueeze(0)
        rendered.append(wav.cpu())
        if index < len(chunks) - 1:
            rendered.append(silence)

    return torch.cat(rendered, dim=1) if len(rendered) > 1 else rendered[0]


def get_tts_model() -> ChatterboxTTS:
    global _tts_model

    if _tts_model is None:
        with _tts_model_lock:
            if _tts_model is None:
                _tts_model = ChatterboxTTS.from_pretrained(device=resolve_device())
    return _tts_model


def get_multilingual_model() -> ChatterboxMultilingualTTS:
    global _multilingual_model

    if _multilingual_model is None:
        with _multilingual_model_lock:
            if _multilingual_model is None:
                ckpt_dir = Path(
                    snapshot_download(
                        repo_id="ResembleAI/chatterbox",
                        repo_type="model",
                        revision="main",
                        allow_patterns=[
                            "ve.pt",
                            "t3_mtl23ls_v2.safetensors",
                            "s3gen.pt",
                            "grapheme_mtl_merged_expanded_v1.json",
                            "conds.pt",
                            "Cangjie5_TC.json",
                        ],
                        local_dir=MULTILINGUAL_DIR,
                        token=os.getenv("HF_TOKEN"),
                    )
                )
                _multilingual_model = ChatterboxMultilingualTTS.from_local(ckpt_dir, resolve_device())
    return _multilingual_model


def resolve_generation_backend(language_id: str) -> tuple[object, str]:
    language_id = language_id.strip().lower() or "en"

    if language_id == "en":
        return get_tts_model(), "standard"

    if language_id not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail="Idioma nao suportado.")

    return get_multilingual_model(), "multilingual"


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config")
def config() -> JSONResponse:
    languages = [{"id": "en", "label": "English", "backend": "standard"}]
    languages.extend(
        {"id": language_id, "label": label, "backend": "multilingual"}
        for language_id, label in sorted(SUPPORTED_LANGUAGES.items())
        if language_id != "en"
    )
    runtime_info = get_runtime_info()
    return JSONResponse(
        {
            **runtime_info,
            "default_language": "en",
            "languages": languages,
        }
    )


@app.post("/generate")
async def generate_audio(
    text: str = Form(...),
    language_id: str = Form("en"),
    quality_mode: str = Form("max"),
    exaggeration: float = Form(0.5),
    cfg_weight: float = Form(0.5),
    temperature: float = Form(0.8),
    audio_prompt: UploadFile | None = File(default=None),
) -> FileResponse:
    text = normalize_text(text)
    if not text:
        raise HTTPException(status_code=400, detail="Texto vazio.")

    model, backend = resolve_generation_backend(language_id)
    temp_dir = Path(tempfile.mkdtemp(prefix="chatterbox_", dir=BASE_DIR))
    prompt_path: Path | None = None

    try:
        if audio_prompt and audio_prompt.filename:
            suffix = Path(audio_prompt.filename).suffix or ".wav"
            prompt_path = temp_dir / f"prompt{suffix}"
            with prompt_path.open("wb") as buffer:
                shutil.copyfileobj(audio_prompt.file, buffer)

        generate_kwargs = {
            "audio_prompt_path": str(prompt_path) if prompt_path else None,
            "exaggeration": exaggeration,
            "cfg_weight": cfg_weight,
            "temperature": temperature,
        }

        if quality_mode == "ultra":
            wav = generate_chunked_audio(
                model,
                backend,
                text,
                language_id,
                generate_kwargs,
                max_chunk_chars=ULTRA_CHUNK_CHARS,
                silence_ms=ULTRA_CHUNK_SILENCE_MS,
            )
        elif quality_mode == "max":
            wav = generate_chunked_audio(model, backend, text, language_id, generate_kwargs)
        else:
            if backend == "multilingual":
                wav = model.generate(text, language_id=language_id, **generate_kwargs)
            else:
                wav = model.generate(text, **generate_kwargs)

        output_path = OUTPUT_DIR / "latest.wav"
        ta.save(str(output_path), wav.cpu(), model.sr)

        headers = {
            "X-Character-Count": str(len(text)),
            "X-Language-Id": language_id,
            "X-Backend": backend,
            "X-Device": resolve_device(),
            "X-Quality-Mode": quality_mode,
        }
        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename="chatterbox.wav",
            headers=headers,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Falha na geracao: {exc}") from exc
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

