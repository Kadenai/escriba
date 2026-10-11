"""Envia versículos ao API Server do Holyrics pela rede local."""

import json
import urllib.parse
import urllib.request

# O Holyrics está na rede local: o proxy do Windows, se houver, não entra no caminho.
_DIRETO = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def chamar(host, porta, token, acao, dados):
    url = f"http://{host}:{porta}/api/{acao}?token={urllib.parse.quote(token)}"
    pedido = urllib.request.Request(url, json.dumps(dados).encode(),
                                    {"Content-Type": "application/json"})
    with _DIRETO.open(pedido, timeout=3) as resposta:
        corpo = json.load(resposta)
    if corpo.get("status") != "ok":
        raise RuntimeError(corpo.get("error", corpo))


def _id(livro, capitulo, versiculo):
    return f"{livro:02d}{capitulo or 1:03d}{versiculo or 1:03d}"


def selecionar(host, porta, token, livro, capitulo=None, versiculo=None):
    """Deixa o versículo selecionado na janela da Bíblia, sem projetar."""
    chamar(host, porta, token, "SelectVerse", {"id": _id(livro, capitulo, versiculo)})


def projetar(host, porta, token, livro, capitulo, versiculo, fim=None):
    ids = [_id(livro, capitulo, v) for v in range(versiculo, (fim or versiculo) + 1)]
    chamar(host, porta, token, "ShowVerse", {"ids": ids})
