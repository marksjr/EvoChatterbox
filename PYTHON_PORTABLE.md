# Python Portable

Este projeto aceita um `Python portable` sem alterar o backend de geracao.

## Objetivo

Permitir que o launcher [INICIAR.bat](./INICIAR.bat) funcione mesmo em maquinas sem Python instalado no sistema.

## Como o launcher procura o Python

Ordem de busca:

1. `python\python.exe`
2. `runtime\python.exe`
3. `python` instalado no Windows

## Estrutura recomendada

Dentro da pasta do projeto:

```text
audio_Chatterbox/
  INICIAR.bat
  app.py
  requirements.txt
  static/
  python/
    python.exe
    python311.dll
    DLLs/
    Lib/
    Scripts/
    ...
```

## Caminho minimo esperado

O caminho principal que precisa existir e:

`python\python.exe`

Se esse arquivo existir, o launcher tentara usar esse Python antes do Python instalado no sistema.

## Melhor pratica

Use uma distribuicao portable baseada em Python 3.11.

Evite misturar:

- Python 3.10 em uma release
- Python 3.11 em outra

Manter a mesma versao reduz risco de incompatibilidade com dependencias.

## O que nao muda

Adicionar Python portable nao altera:

- a qualidade do audio
- a logica de geracao
- a deteccao de GPU/CPU
- a API FastAPI

Isso apenas muda de onde o launcher pega o executavel do Python.

## O que continua sendo criado localmente

Mesmo com Python portable, o sistema ainda cria:

- `.venv/`
- `.cache/`
- `output/`

Ou seja: o Python portable serve como bootstrap para criar e usar o ambiente local do projeto.

## Fluxo recomendado para release

1. Prepare a pasta do projeto limpa.
2. Copie um Python portable 3.11 para `python\`.
3. Nao inclua `.venv/`, `.cache/` e `output/`.
4. Comprima a pasta em ZIP.
5. Publique esse ZIP no GitHub Releases.

## Resumo

Para suportar Python portable, basta garantir:

- pasta `python/`
- arquivo `python/python.exe`

O restante do projeto ja esta preparado para isso.
