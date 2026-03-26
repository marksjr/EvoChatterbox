# Publicar no GitHub

Checklist rapido para subir este projeto:

## Antes de publicar

- confirme que a aplicacao abre com `INICIAR.bat`
- confirme que o navegador abre a interface
- teste pelo menos uma geracao de audio
- confira se `.venv/`, `.cache/` e `output/` nao serao enviados

## Arquivos que devem ficar no repositorio

- `INICIAR.bat`
- `app.py`
- `requirements.txt`
- `README.md`
- `API.md`
- `PORTABLE_WINDOWS.md`
- `RELEASE_TEMPLATE.md`
- `postman_collection.json`
- `static/`

## Arquivos e pastas que nao devem ir

- `.venv/`
- `.cache/`
- `output/`
- `__pycache__/`
- logs temporarios

## Sugestao de nome do repositorio

- `chatterbox-tts-portable`
- `chatterbox-tts-windows`
- `audio-chatterbox-portable`

## Sugestao de descricao curta

`Portable Windows app for local audio generation with Evo Chatterbox, FastAPI and web UI.`

## Sugestao de topicos

- `tts`
- `text-to-speech`
- `python`
- `fastapi`
- `windows`
- `portable`
- `audio`
- `nvidia`

## Depois de publicar

- adicione screenshots da interface
- crie uma release com ZIP do projeto limpo
- explique no README que basta usar `INICIAR.bat`

