# Evo Chatterbox API

REST API built with FastAPI for text-to-speech generation.

## Base URL

```
http://127.0.0.1:8000
```

Start the server by running `start.bat`.

## Auto-generated Documentation

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints

### `GET /`

Returns the web interface (HTML).

### `GET /health`

Health check endpoint.

Response:

```json
{
  "status": "ok"
}
```

### `GET /config`

Returns application configuration, active device, supported languages, and UI metadata.

Response example:

```json
{
  "device": "cuda",
  "device_mode": "auto",
  "cuda_available": true,
  "gpu_name": "NVIDIA GeForce RTX 3070",
  "cpu_name": "Intel64 Family 6",
  "default_language": "en",
  "languages": [
    { "id": "en", "label": "English", "backend": "standard" },
    { "id": "pt", "label": "Portuguese", "backend": "multilingual" }
  ],
  "quality_modes": [
    { "id": "ultra", "label": "High stability" },
    { "id": "max", "label": "Balanced stability" },
    { "id": "fast", "label": "Direct processing" }
  ],
  "audio_prompt_max_mb": 15
}
```

### `POST /generate`

Generates a `.wav` audio file from text.

Content type: `multipart/form-data`

#### Parameters

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `text` | string | Yes | — | Text to convert to speech |
| `language_id` | string | No | `en` | Language code (`en`, `pt`, `es`, `fr`, `de`, `ja`, etc.) |
| `quality_mode` | string | No | `max` | Processing strategy: `ultra`, `max`, `fast` |
| `exaggeration` | float | No | `0.5` | Expressive intensity (0.0 to 1.0) |
| `cfg_weight` | float | No | `0.5` | Generation adherence control (0.0 to 1.0) |
| `temperature` | float | No | `0.8` | Generation variation (0.1 to 2.0) |
| `audio_prompt` | file | No | — | Optional voice reference file (`.wav`, `.mp3`, `.flac`, `.m4a`, `.ogg`, max 15 MB) |

#### Response

- `200 OK` — returns `audio/wav` file
- `400 Bad Request` — invalid parameters
- `413 Payload Too Large` — audio prompt exceeds size limit

#### Response Headers

| Header | Description |
|--------|-------------|
| `X-Character-Count` | Number of characters processed |
| `X-Language-Id` | Language used |
| `X-Backend` | Backend used (`standard` or `multilingual`) |
| `X-Device` | Device used (`cuda` or `cpu`) |
| `X-Quality-Mode` | Quality mode applied |
| `X-Output-Filename` | Generated filename |
| `X-Request-Id` | Unique request identifier |

## Examples

### cURL

```bash
curl -X POST "http://127.0.0.1:8000/generate" \
  -F "text=Hello, this is a voice test." \
  -F "language_id=en" \
  -F "quality_mode=max" \
  -F "exaggeration=0.5" \
  -F "cfg_weight=0.5" \
  -F "temperature=0.8" \
  --output chatterbox.wav
```

### PowerShell

```powershell
$form = @{
  text = "Hello, this is a voice test."
  language_id = "en"
  quality_mode = "max"
  exaggeration = "0.5"
  cfg_weight = "0.5"
  temperature = "0.8"
}

Invoke-RestMethod -Uri "http://127.0.0.1:8000/generate" -Method Post -Form $form -OutFile "chatterbox.wav"
```

### Python

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/generate",
    files={},
    data={
        "text": "Hello, this is a voice test.",
        "language_id": "en",
        "quality_mode": "max",
        "exaggeration": "0.5",
        "cfg_weight": "0.5",
        "temperature": "0.8",
    },
)

with open("chatterbox.wav", "wb") as f:
    f.write(response.content)

print(response.headers.get("X-Backend"))
print(response.headers.get("X-Device"))
```

### With Voice Reference

```bash
curl -X POST "http://127.0.0.1:8000/generate" \
  -F "text=Clone this voice." \
  -F "language_id=en" \
  -F "quality_mode=max" \
  -F "audio_prompt=@reference.wav" \
  --output chatterbox.wav
```

## Notes

- `en` (English) uses the standard backend; all other languages use the multilingual backend
- First use of a backend may take longer due to model download and loading
- `quality_mode` controls text chunking strategy — it does not change the model
- Each request generates a unique temporary file to avoid conflicts between simultaneous requests
- If an NVIDIA GPU is available, the API uses CUDA automatically

## Postman

A ready-to-use collection is available at [postman_collection.json](./postman_collection.json).

Included requests:
- Health
- Config
- Generate EN
- Generate PT
- Generate With Voice Prompt

To import:
1. Open Postman
2. Click **Import**
3. Select `docs/postman_collection.json`
4. Adjust the `base_url` variable if needed

