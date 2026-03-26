# Evo Chatterbox Portable

Aplicacao local para gerar audio com interface web, `FastAPI` e suporte a GPU NVIDIA quando disponivel.

![Evo Chatterbox UI](docs/assets/evo-chatterbox-ui.png)

## Visao geral

O projeto foi preparado para usuarios que querem abrir, clicar e gerar audio, sem configurar servidor manualmente.

O launcher principal e [INICIAR.bat](./INICIAR.bat). Ele:

- detecta um `Python portable` local, se existir
- usa o Python instalado no Windows, se necessario
- cria o ambiente `.venv`
- instala dependencias
- detecta GPU NVIDIA
- ativa `CUDA` quando possivel
- abre a interface automaticamente no navegador

## Recursos

- interface web local
- suporte a texto para fala
- selecao de idioma
- suporte ao modelo padrao e ao modelo multilingual
- upload opcional de audio de referencia
- presets de emocao
- contagem de caracteres
- cronometro de geracao
- tema dark
- API `FastAPI` com `/docs` e `/redoc`

## Requisitos

### Opcao 1: Python instalado

Instale `Python 3.11` no Windows e marque `Add Python to PATH`:

- Site oficial: https://www.python.org/downloads/windows/

### Opcao 2: Python portable

Se preferir uma distribuicao mais portatil, coloque um Python em:

- `python\python.exe`

Guia completo:

- [PYTHON_PORTABLE.md](./PYTHON_PORTABLE.md)

## Como instalar e usar

1. Baixe ou clone este projeto.
2. Garanta uma destas opcoes:
   - Python 3.11 instalado no Windows
   - ou um Python portable em `python\python.exe`
3. De duplo clique em [INICIAR.bat](./INICIAR.bat).
4. Aguarde a configuracao inicial.
5. O navegador sera aberto automaticamente.

Se quiser encerrar o sistema depois, feche a janela `Evo Chatterbox Server`.

## GPU e CPU

- Se existir GPU NVIDIA compativel, o sistema tenta usar `CUDA`.
- Se nao existir GPU, ele continua funcionando em `CPU`.
- A deteccao automatica nao muda a qualidade do audio de forma relevante; ela melhora principalmente a velocidade.

Override manual:

- `CHATTERBOX_DEVICE=auto`
- `CHATTERBOX_DEVICE=cpu`
- `CHATTERBOX_DEVICE=cuda`

## Estrutura principal

- Launcher principal: [INICIAR.bat](./INICIAR.bat)
- Backend: [app.py](./app.py)
- Interface: [static/index.html](./static/index.html)
- API: [API.md](./API.md)
- Guia portable Windows: [PORTABLE_WINDOWS.md](./PORTABLE_WINDOWS.md)
- Guia de Python portable: [PYTHON_PORTABLE.md](./PYTHON_PORTABLE.md)
- Postman: [postman_collection.json](./postman_collection.json)

## Documentacao da API

Quando o servidor estiver rodando localmente:

- App: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Guia completo:

- [API.md](./API.md)

## Publicacao no GitHub

Arquivos auxiliares para publicacao:

- Checklist: [PUBLISH_GITHUB.md](./PUBLISH_GITHUB.md)
- Release notes: [RELEASE_TEMPLATE.md](./RELEASE_TEMPLATE.md)
- Checklist de release portable: [CHECKLIST_RELEASE_PORTABLE.md](./CHECKLIST_RELEASE_PORTABLE.md)

## Observacoes

- O primeiro uso pode demorar porque o sistema baixa dependencias e modelos.
- Todos os caches ficam dentro da pasta do projeto.
- Para usuarios finais, o melhor caminho costuma ser:
  - repositorio GitHub sem Python embutido
  - release ZIP com Python portable embutido
