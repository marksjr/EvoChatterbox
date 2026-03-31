# Evo Chatterbox

Local text-to-speech application with a web interface, FastAPI backend, multilingual voice generation, optional reference-audio cloning, and automatic NVIDIA GPU acceleration.

![Evo Chatterbox UI](docs/assets/evo-chatterbox-ui.png)

## Overview

Evo Chatterbox is built to run locally with a simple Windows workflow:

- `install.bat`: one-time setup
- `start.bat`: daily launcher
- `http://127.0.0.1:8000`: main interface
- `http://127.0.0.1:8000/docs`: FastAPI Swagger UI
- `http://127.0.0.1:8000/static/doc.html`: full HTML documentation

The application keeps inference local. Text and reference audio are processed on your machine.

## Features

- Local web interface
- English standard backend plus multilingual backend for supported non-English languages
- Multiple supported languages including English, Portuguese, Spanish, French, German, Japanese, Arabic, Dutch, Danish, Norwegian, and more
- 23 emotion presets
- Three quality modes: `ultra`, `max`, `fast`
- Optional reference audio for voice cloning / timbre matching
- Runtime metrics in the UI
- Automatic CUDA usage when an NVIDIA GPU is available
- REST API with Swagger UI and HTML docs
- CPU fallback when no GPU is available

## Quick Start

1. Clone or download the repository.
2. Run `install.bat` once.
3. Run `start.bat`.
4. Open `http://127.0.0.1:8000`.

## Requirements

- Windows 10 or Windows 11
- Internet connection on first install
- No preinstalled Python required: `install.bat` downloads portable Python 3.11 automatically with `curl` when Python is missing
- Optional NVIDIA GPU for faster generation

## API and Docs

Available when the server is running:

- Web app: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- HTML docs: `http://127.0.0.1:8000/static/doc.html`

Additional files:

- API reference: `docs/API.md`
- Postman collection: `docs/postman_collection.json`

## Quality Modes

| Mode | Behavior | Best for |
| --- | --- | --- |
| `ultra` | Smaller chunks and longer pauses | Long text, multilingual stability |
| `max` | Balanced chunking and pacing | General use |
| `fast` | Single-pass generation | Short text, fastest turnaround |

## Reference Audio

Reference audio is optional.

Supported formats:
- `.wav`
- `.mp3`
- `.flac`
- `.m4a`
- `.ogg`

Current upload limit:
- `15 MB`

Without reference audio, the model uses its built-in fallback voice.

## Portuguese Notes

The backend supports:
- `pt`
- `pt-BR`
- `pt-PT`

Important:
- `pt-BR` and `pt-PT` are guided aliases for the same internal multilingual `pt` model.
- They improve UI/API clarity.
- They do not create separate native accent models by themselves.
- Without reference audio, accent fallback still depends on the base model voice.

## Project Structure

Core product files:

```text
app.py
install.bat
start.bat
requirements.txt
docs/API.md
README.md
docs/postman_collection.json
static/
  index.html
  app.js
  styles.css
  doc.html
docs/
  assets/
tests/
  test_app.py
```

Generated runtime folders:

```text
.cache/       # model downloads and runtime cache
.venv/        # local Python environment
output/       # temporary/generated audio output
__pycache__/  # Python cache
```

Folders that are not part of the Evo Chatterbox product itself:

```text
.agent/       # AI agent assets, prompt catalogs, skills, auxiliary tooling
.claude/      # AI assistant workspace metadata
```

These folders are not required to run the application and should not be treated as part of the shipped product.

## GitHub Repository Scope

The GitHub repository should contain the application source and documentation, not local AI-agent workspaces or generated runtime caches.

Ignored from version control:
- `.venv/`
- `.cache/`
- `output/`
- `.agent/`
- `.claude/`

## Running Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Notes

- First run may download several gigabytes of model data into `.cache/`.
- English typically runs faster than multilingual generation.
- CUDA affects speed, not core output quality.
- Each generation request returns a WAV file and temporary output is cleaned up automatically.



