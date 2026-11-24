"""Gravação e limpeza automática de transcrições temporárias."""

from datetime import date, datetime
from pathlib import Path

DIAS_RETENCAO = 7
PREFIXO = "Transcrição "
SUFIXO = ".txt"


def registrar_fala(pasta: Path, inicio: datetime, texto: str) -> Path:
    """Acrescenta a fala, com a hora em que começou, ao arquivo do dia."""
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"{PREFIXO}{inicio:%Y-%m-%d}{SUFIXO}"
    with open(caminho, "a", encoding="utf-8") as arquivo:
        arquivo.write(f"[{inicio:%H:%M:%S}] {texto}\n")
    return caminho


def limpar_antigas(pasta: Path, dias: int = DIAS_RETENCAO, hoje: date | None = None) -> int:
    """Remove arquivos de transcrição mais antigos que `dias` dias. Retorna quantos apagou."""
    if not pasta.exists():
        return 0
    referencia = hoje or date.today()
    removidos = 0
    for arquivo in pasta.iterdir():
        if not (arquivo.is_file() and arquivo.name.startswith(PREFIXO) and arquivo.name.endswith(SUFIXO)):
            continue
        trecho_data = arquivo.name[len(PREFIXO):-len(SUFIXO)]
        try:
            data_arquivo = date.fromisoformat(trecho_data)
        except ValueError:
            continue
        if (referencia - data_arquivo).days >= dias:
            try:
                arquivo.unlink()
                removidos += 1
            except OSError:
                pass
    return removidos
