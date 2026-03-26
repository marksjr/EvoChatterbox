# Portable Windows

Este projeto foi preparado para funcionar como uma pasta portatil no Windows.

## O que significa aqui

- voce pode clonar ou baixar o projeto em qualquer pasta
- os modelos e caches ficam dentro da propria pasta do projeto
- o launcher principal e `INICIAR.bat`
- o launcher aceita Python instalado ou Python portable local
- se houver GPU NVIDIA compativel, o sistema tenta usar `CUDA`
- se nao houver GPU, o sistema continua em `CPU`

## Como distribuir no GitHub

Publique estes arquivos e pastas:

- `app.py`
- `static/`
- `requirements.txt`
- `INICIAR.bat`
- `README.md`
- `API.md`
- `postman_collection.json`

Nao publique:

- `.venv/`
- `.cache/`
- `output/`

## Como iniciar no Windows

Opcao mais simples:

`INICIAR.bat`

Esse launcher:

1. cria o ambiente virtual se necessario
2. instala dependencias
3. detecta GPU NVIDIA com `nvidia-smi`
4. instala `PyTorch CUDA` somente quando fizer sentido
5. sobe o servidor local
6. abre a interface no navegador

## Requisitos no Windows

- Python 3.10 ou 3.11 instalado no `PATH`
  ou um Python portable em `python\python.exe`
- Internet no primeiro uso para baixar dependencias e modelos
- GPU NVIDIA opcional para acelerar a geracao

## Ordem de deteccao do Python

O launcher tenta nesta ordem:

1. `python\python.exe`
2. `runtime\python.exe`
3. `python` instalado no sistema

## Override manual do dispositivo

Por padrao, o backend usa:

- `cuda` se estiver disponivel
- `cpu` caso contrario

Tambem e possivel forcar o comportamento pela variavel:

`CHATTERBOX_DEVICE=auto|cpu|cuda`

Exemplo em PowerShell:

```powershell
$env:CHATTERBOX_DEVICE="cpu"
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

## Caches locais

Os dados portateis ficam em:

- `.cache/huggingface`
- `.cache/multilingual`
- `.cache/pkuseg`
