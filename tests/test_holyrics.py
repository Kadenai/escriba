import holyrics


def test_projetar_envia_input_ids(monkeypatch):
    chamadas = []

    def fake_chamar(host, porta, token, acao, dados):
        chamadas.append((host, porta, token, acao, dados))

    monkeypatch.setattr(holyrics, "chamar", fake_chamar)
    holyrics.projetar("127.0.0.1", 8091, "tok", 43, 3, 16)

    assert chamadas == [
        ("127.0.0.1", 8091, "tok", "ShowVerse", {"input": {"ids": ["43003016"]}})
    ]


def test_projetar_intervalo_envia_todos_ids(monkeypatch):
    chamadas = []

    def fake_chamar(host, porta, token, acao, dados):
        chamadas.append((acao, dados))

    monkeypatch.setattr(holyrics, "chamar", fake_chamar)
    holyrics.projetar("127.0.0.1", 8091, "tok", 19, 23, 1, 3)

    assert chamadas == [
        ("ShowVerse", {"input": {"ids": ["19023001", "19023002", "19023003"]}})
    ]


def test_selecionar_envia_id(monkeypatch):
    chamadas = []

    def fake_chamar(host, porta, token, acao, dados):
        chamadas.append((acao, dados))

    monkeypatch.setattr(holyrics, "chamar", fake_chamar)
    holyrics.selecionar("127.0.0.1", 8091, "tok", 43, 3, 16)

    assert chamadas == [("SelectVerse", {"id": "43003016"})]
