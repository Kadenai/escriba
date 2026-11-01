<img src="logo/escriba.png" width="96" alt="Escriba">

# Escriba

Ouve o preletor pelo microfone, reconhece o livro, o capítulo e o versículo citados e deixa a
passagem pronta no [Holyrics](https://holyrics.com.br), sem ninguém precisar digitar.

- Roda em Windows 10/11 e envia para o Holyrics pela rede local (Windows ou Mac), via API Server.
- Reconhecimento de fala no próprio computador, sem internet, com três motores à escolha:
  sherpa-onnx (padrão), Vosk e o do Windows.
- Modos: só o livro, livro e capítulo, livro/capítulo/versículo, ou já projetando.
- Volta sozinho ao texto principal do sermão depois de outra citação.
- Grava a transcrição do que foi dito, com a hora de cada frase.

O uso está descrito no manual, gerado por `manual/manual.py`.

## Rodar a partir do código

Precisa de Python 3.11 no Windows.

```bat
py -3.11 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

Os modelos de fala não cabem no git. Baixe `modelos.zip` na
[página de releases](../../releases) e extraia dentro da pasta `modelos/`, de modo que existam
`modelos/vosk-pt/` e `modelos/sherpa-pt/`. A origem e a licença de cada um estão em
[modelos/ORIGEM.txt](modelos/ORIGEM.txt).

```bat
.venv\Scripts\python app.py
```

## Testes

```bat
.venv\Scripts\python -m pytest -q
```

## Gerar o instalador

```bat
.\empacotar.bat
py -3.11 instalador\montar.py
py -3.11 manual\manual.py
```

O primeiro comando gera `dist\Escriba\` com o PyInstaller; o segundo, `dist\Instalar Escriba.exe`
com o IExpress do Windows; o terceiro, o manual em PDF (precisa do `reportlab`).

### Publicar uma versão nos releases

Não precisa de Windows: troque o número em `VERSAO` (por exemplo, `1.2.0`), escreva as notas em
`.github/notas/v1.2.0.md` e envie. O GitHub Actions monta o instalador e o manual numa máquina
Windows e publica o release `v1.2.0` com os dois arquivos. Se esse release já existir, nada acontece.

## Arquivos

| Arquivo | O que faz |
| --- | --- |
| `app.py` | Janela, configuração e envio ao Holyrics |
| `detector.py` | Acha as referências bíblicas no texto reconhecido |
| `digitado.py` | Lê a passagem digitada na janela, separado da fala |
| `biblia.py` | Nomes dos livros e número de versículos por capítulo |
| `motores.py` | Os três motores de fala |
| `holyrics.py` | Chamadas ao API Server do Holyrics |
