from datetime import date, datetime

from transcricao import limpar_antigas, registrar_fala


def test_registrar_fala_cria_arquivo_do_dia(tmp_path):
    inicio = datetime(2026, 11, 24, 20, 15, 3)
    caminho = registrar_fala(tmp_path, inicio, "João 3:16")

    assert caminho == tmp_path / "Transcrição 2026-11-24.txt"
    assert caminho.read_text(encoding="utf-8") == "[20:15:03] João 3:16\n"


def test_limpar_antigas_remove_arquivos_com_7_dias_ou_mais(tmp_path):
    hoje = date(2026, 11, 24)
    manter_hoje = tmp_path / "Transcrição 2026-11-24.txt"
    manter_6_dias = tmp_path / "Transcrição 2026-11-18.txt"
    remover_7_dias = tmp_path / "Transcrição 2026-11-17.txt"
    remover_10_dias = tmp_path / "Transcrição 2026-11-14.txt"
    outro_arquivo = tmp_path / "notas.txt"

    for arquivo in (manter_hoje, manter_6_dias, remover_7_dias, remover_10_dias, outro_arquivo):
        arquivo.write_text("conteudo", encoding="utf-8")

    removidos = limpar_antigas(tmp_path, dias=7, hoje=hoje)

    assert removidos == 2
    assert manter_hoje.exists()
    assert manter_6_dias.exists()
    assert not remover_7_dias.exists()
    assert not remover_10_dias.exists()
    assert outro_arquivo.exists()
