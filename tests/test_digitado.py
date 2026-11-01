import pytest

from digitado import Passagem, interpretar


@pytest.mark.parametrize("texto, esperado", [
    ("genesis 2 3", "Gênesis 2:3"),
    ("Gênesis 2:3", "Gênesis 2:3"),
    ("GENESIS 2.3", "Gênesis 2:3"),
    ("Gn 2,3", "Gênesis 2:3"),
    ("salmo 23", "Salmos 23"),
    ("salmos 119 105", "Salmos 119:105"),
    ("Rm 8:28", "Romanos 8:28"),
    ("Rm 8:28-30", "Romanos 8:28-30"),
    ("romanos 8 28 a 30", "Romanos 8:28-30"),
    ("Rm 8:28, 30", "Romanos 8:28"),            # versículos soltos: fica o primeiro
    ("1Co 13", "1 Coríntios 13"),
    ("1 Co 13:4", "1 Coríntios 13:4"),
    ("1ª Coríntios 13", "1 Coríntios 13"),
    ("primeira coríntios 13", "1 Coríntios 13"),
    ("I Coríntios 13", "1 Coríntios 13"),
    ("II Timóteo 3 16", "2 Timóteo 3:16"),
    ("2Tm 3.16", "2 Timóteo 3:16"),
    ("Jo 3:16", "João 3:16"),                   # sem acento é João
    ("Jó 38", "Jó 38"),                         # com acento é Jó
    ("joão 3 16", "João 3:16"),
    ("1 joão 4 8", "1 João 4:8"),
    ("3Jo 4", "3 João 1:4"),
    ("Judas 5", "Judas 1:5"),                   # livro de um capítulo só
    ("Judas 1:5", "Judas 1:5"),
    ("Cântico dos Cânticos 2", "Cantares 2"),
    ("Atos dos Apóstolos 2 4", "Atos 2:4"),
    ("Apocalipse de João 3 20", "Apocalipse 3:20"),
    ("evangelho segundo joão 3", "João 3"),     # "segundo" no meio não é ordinal
    ("Evangelho de Lucas 15", "Lucas 15"),
    ("2 cronicas 7 14", "2 Crônicas 7:14"),
    ("ecl 3", "Eclesiastes 3"),                 # começo do nome
    ("apoc 22", "Apocalipse 22"),
    ("1 cor 13", "1 Coríntios 13"),
    ("filip 4 13", "Filipenses 4:13"),
    ("romanos", "Romanos"),
])
def test_interpretar(texto, esperado):
    assert str(interpretar(texto)) == esperado


@pytest.mark.parametrize("texto", [
    "",
    "xyz",
    "coríntios 13",       # falta o ordinal
    "1 romanos 8",        # ordinal num livro sem número
    "fil 4 13",           # Filipenses ou Filemom
    "João 45",            # João tem 21 capítulos
    "joão 3 99",
    "4 joão 3",
])
def test_nao_entende(texto):
    assert interpretar(texto) is None


def test_intervalo_invalido_fica_no_versiculo():
    assert interpretar("Rm 8:28-20") == Passagem(45, 8, 28)
