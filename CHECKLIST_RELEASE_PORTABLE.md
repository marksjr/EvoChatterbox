# Checklist Release Portable

## Preparacao

- remover `.venv/`
- remover `.cache/`
- remover `output/`
- remover `__pycache__/`

## Arquivos obrigatorios

- `INICIAR.bat`
- `app.py`
- `requirements.txt`
- `README.md`
- `API.md`
- `PORTABLE_WINDOWS.md`
- `PYTHON_PORTABLE.md`
- `postman_collection.json`
- `static/`

## Python portable

- copiar Python 3.11 portable para `python/`
- confirmar existencia de `python/python.exe`

## Teste

- extrair em pasta nova
- executar `INICIAR.bat`
- aguardar abrir no navegador
- testar geracao de audio

## Empacotamento

- criar ZIP da pasta limpa
- nome sugerido: `chatterbox-tts-portable-windows.zip`

## Publicacao

- subir o codigo no GitHub
- anexar o ZIP no GitHub Releases
- usar o texto base de `RELEASE_TEMPLATE.md`
