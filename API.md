# API Evo Chatterbox

Esta API foi criada com `FastAPI`.

## Base URL

Quando o servidor estiver rodando localmente:

`http://127.0.0.1:8000`

Forma mais simples de iniciar no Windows:

`INICIAR.bat`

## Documentacao automatica

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints

### `GET /`

Retorna a interface HTML do gerador de audio.

### `GET /health`

Verifica se a API esta no ar.

Exemplo de resposta:

```json
{
  "status": "ok"
}
```

### `GET /config`

Retorna configuracao da aplicacao, dispositivo ativo, idiomas suportados e metadados da UI.

Exemplo:

```json
{
  "device": "cuda",
  "default_language": "en",
  "audio_prompt_max_mb": 15,
  "quality_modes": [
    {
      "id": "ultra",
      "label": "Estabilidade alta"
    },
    {
      "id": "max",
      "label": "Estabilidade equilibrada"
    },
    {
      "id": "fast",
      "label": "Processamento direto"
    }
  ],
  "languages": [
    {
      "id": "en",
      "label": "English",
      "backend": "standard"
    },
    {
      "id": "pt",
      "label": "Portuguese",
      "backend": "multilingual"
    }
  ]
}
```

### `POST /generate`

Gera um arquivo de audio `.wav` a partir de texto.

Tipo de envio:

`multipart/form-data`

Campos:

- `text`:
  Texto a converter em voz.
- `language_id`:
  Idioma. Ex.: `en`, `pt`, `es`, `fr`, `de`, `ja`.
- `quality_mode`:
  Estrategia de processamento do texto.
  Valores aceitos: `ultra`, `max`, `fast`.
- `exaggeration`:
  Intensidade expressiva. Intervalo aceito: `0.0` a `1.0`.
- `cfg_weight`:
  Controle de aderencia da geracao. Intervalo aceito: `0.0` a `1.0`.
- `temperature`:
  Variacao da geracao. Intervalo aceito: `0.1` a `2.0`.
- `audio_prompt`:
  Arquivo opcional de referencia de voz.
  Formatos aceitos: `.wav`, `.mp3`, `.flac`, `.m4a`, `.ogg`.
  Tamanho maximo: `15 MB`.

Resposta:

- `200 OK` com `audio/wav`
- `400 Bad Request` para campos invalidos
- `413 Payload Too Large` para `audio_prompt` acima do limite

Headers uteis:

- `X-Character-Count`
- `X-Language-Id`
- `X-Backend`
- `X-Device`
- `X-Quality-Mode`
- `X-Output-Filename`

## Exemplo com cURL

```bash
curl -X POST "http://127.0.0.1:8000/generate" ^
  -F "text=Ola, este e um teste de voz." ^
  -F "language_id=pt" ^
  -F "quality_mode=max" ^
  -F "exaggeration=0.5" ^
  -F "cfg_weight=0.5" ^
  -F "temperature=0.8" ^
  --output chatterbox.wav
```

## Exemplo com PowerShell

```powershell
$form = @{
  text = "Ola, este e um teste de voz."
  language_id = "pt"
  quality_mode = "max"
  exaggeration = "0.5"
  cfg_weight = "0.5"
  temperature = "0.8"
}

Invoke-RestMethod -Uri "http://127.0.0.1:8000/generate" -Method Post -Form $form -OutFile "chatterbox.wav"
```

## Exemplo com Python

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/generate",
    files={},
    data={
        "text": "Ola, este e um teste de voz.",
        "language_id": "pt",
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
print(response.headers.get("X-Output-Filename"))
```

## Observacoes

- `en` usa o backend padrao.
- Demais idiomas usam o backend `multilingual`.
- O primeiro uso pode demorar por causa do carregamento dos modelos.
- `quality_mode` melhora principalmente estabilidade em textos longos; nao troca o modelo.
- Cada requisicao gera um arquivo temporario proprio no servidor para evitar conflito entre requisicoes simultaneas.
- Se houver GPU NVIDIA disponivel, a API tenta usar `CUDA` automaticamente.

## Postman

Existe uma colecao pronta em:

[postman_collection.json](./postman_collection.json)

Ela inclui:

- `Health`
- `Config`
- `Generate EN`
- `Generate PT`
- `Generate With Voice Prompt`

Como importar:

1. Abra o Postman.
2. Clique em `Import`.
3. Selecione o arquivo `postman_collection.json`.
4. Ajuste a variavel `base_url` se necessario.
5. Para teste com voz de referencia, preencha `reference_audio_path`.
