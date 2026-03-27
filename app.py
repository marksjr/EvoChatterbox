from __future__ import annotations

import logging
import os
import platform
import re
import shutil
import tempfile
import time
from pathlib import Path
from threading import Lock
from uuid import uuid4

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
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from huggingface_hub import snapshot_download
from starlette.background import BackgroundTask

app = FastAPI(title="Evo Chatterbox")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

logging.basicConfig(
    level=os.getenv("CHATTERBOX_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("evo_chatterbox")

_tts_model = None
_tts_model_lock = Lock()
_multilingual_model = None
_multilingual_model_lock = Lock()
MAX_CHUNK_CHARS = 220
ULTRA_CHUNK_CHARS = 140
CHUNK_SILENCE_MS = 140
ULTRA_CHUNK_SILENCE_MS = 220
DEFAULT_QUALITY_MODE = "max"
VALID_QUALITY_MODES = {"ultra", "max", "fast"}
ALLOWED_AUDIO_PROMPT_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}
MAX_AUDIO_PROMPT_BYTES = 15 * 1024 * 1024
MAX_EXAGGERATION = 1.0
MAX_CFG_WEIGHT = 1.0
MIN_TEMPERATURE = 0.1
MAX_TEMPERATURE = 2.0


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

    parts = re.split(r"(?<=[\.\!\?;:\u3002\uff01\uff1f])\s+", text)
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


def validate_quality_mode(quality_mode: str) -> str:
    normalized_mode = quality_mode.strip().lower() or DEFAULT_QUALITY_MODE
    if normalized_mode not in VALID_QUALITY_MODES:
        allowed_modes = ", ".join(sorted(VALID_QUALITY_MODES))
        raise HTTPException(status_code=400, detail=f"Modo de estabilidade invalido. Use: {allowed_modes}.")
    return normalized_mode


def validate_generation_controls(exaggeration: float, cfg_weight: float, temperature: float) -> None:
    if not 0.0 <= exaggeration <= MAX_EXAGGERATION:
        raise HTTPException(status_code=400, detail="Exaggeration deve ficar entre 0.0 e 1.0.")
    if not 0.0 <= cfg_weight <= MAX_CFG_WEIGHT:
        raise HTTPException(status_code=400, detail="CFG Weight deve ficar entre 0.0 e 1.0.")
    if not MIN_TEMPERATURE <= temperature <= MAX_TEMPERATURE:
        raise HTTPException(status_code=400, detail="Temperature deve ficar entre 0.1 e 2.0.")


def validate_audio_prompt(audio_prompt: UploadFile | None) -> str | None:
    if audio_prompt is None or not audio_prompt.filename:
        return None

    suffix = Path(audio_prompt.filename).suffix.lower()
    if suffix not in ALLOWED_AUDIO_PROMPT_EXTENSIONS:
        allowed_extensions = ", ".join(sorted(ALLOWED_AUDIO_PROMPT_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"Audio de referencia invalido. Use um destes formatos: {allowed_extensions}.",
        )
    return suffix


def save_upload_with_limit(upload: UploadFile, destination: Path, max_bytes: int = MAX_AUDIO_PROMPT_BYTES) -> None:
    written_bytes = 0
    with destination.open("wb") as buffer:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            written_bytes += len(chunk)
            if written_bytes > max_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"Audio de referencia excede o limite de {max_bytes // (1024 * 1024)} MB.",
                )
            buffer.write(chunk)


def build_output_path() -> Path:
    return OUTPUT_DIR / f"chatterbox_{uuid4().hex}.wav"


def remove_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.warning("Nao foi possivel remover arquivo temporario: %s", path)


@app.middleware("http")
async def add_request_logging(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or uuid4().hex[:12]
    request.state.request_id = request_id
    started = time.perf_counter()
    response = None

    try:
        response = await call_next(request)
        return response
    finally:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        status_code = response.status_code if response is not None else 500
        logger.info(
            "request_id=%s method=%s path=%s status=%s elapsed_ms=%s",
            request_id,
            request.method,
            request.url.path,
            status_code,
            elapsed_ms,
        )
        if response is not None:
            response.headers["X-Request-Id"] = request_id


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
            "quality_modes": [
                {"id": "ultra", "label": "Estabilidade alta"},
                {"id": "max", "label": "Estabilidade equilibrada"},
                {"id": "fast", "label": "Processamento direto"},
            ],
            "audio_prompt_max_mb": MAX_AUDIO_PROMPT_BYTES // (1024 * 1024),
        }
    )


@app.post("/generate")
async def generate_audio(
    request: Request,
    text: str = Form(...),
    language_id: str = Form("en"),
    quality_mode: str = Form(DEFAULT_QUALITY_MODE),
    exaggeration: float = Form(0.5),
    cfg_weight: float = Form(0.5),
    temperature: float = Form(0.8),
    audio_prompt: UploadFile | None = File(default=None),
) -> FileResponse:
    text = normalize_text(text)
    if not text:
        raise HTTPException(status_code=400, detail="Texto vazio.")

    quality_mode = validate_quality_mode(quality_mode)
    validate_generation_controls(exaggeration, cfg_weight, temperature)
    language_id = language_id.strip().lower() or "en"
    prompt_suffix = validate_audio_prompt(audio_prompt)
    model, backend = resolve_generation_backend(language_id)
    temp_dir = Path(tempfile.mkdtemp(prefix="chatterbox_", dir=BASE_DIR))
    prompt_path: Path | None = None
    output_path = build_output_path()
    request_id = getattr(request.state, "request_id", "unknown")

    try:
        if audio_prompt and prompt_suffix:
            prompt_path = temp_dir / f"prompt{prompt_suffix}"
            save_upload_with_limit(audio_prompt, prompt_path)

        generate_kwargs = {
            "exaggeration": exaggeration,
            "cfg_weight": cfg_weight,
            "temperature": temperature,
        }
        if prompt_path:
            generate_kwargs["audio_prompt_path"] = str(prompt_path)

        logger.info(
            "request_id=%s action=generate_start chars=%s language=%s backend=%s quality_mode=%s device=%s audio_prompt=%s",
            request_id,
            len(text),
            language_id,
            backend,
            quality_mode,
            resolve_device(),
            bool(prompt_path),
        )

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

        ta.save(str(output_path), wav.cpu(), model.sr)

        headers = {
            "X-Character-Count": str(len(text)),
            "X-Language-Id": language_id,
            "X-Backend": backend,
            "X-Device": resolve_device(),
            "X-Quality-Mode": quality_mode,
            "X-Output-Filename": output_path.name,
            "X-Request-Id": request_id,
        }
        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename=output_path.name,
            headers=headers,
            background=BackgroundTask(remove_file, output_path),
        )
    except HTTPException:
        remove_file(output_path)
        raise
    except Exception as exc:
        remove_file(output_path)
        logger.exception("request_id=%s action=generate_failure", request_id)
        raise HTTPException(status_code=500, detail="Falha interna na geracao do audio.") from exc
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
