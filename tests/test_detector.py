import pytest

from detector import Detector, Referencia, ler, vocabulario


def falar(*falas, janela=3.0):
    """Cada fala é (segundo, texto). Devolve as referências emitidas, como texto."""
    d = Detector(janela)
    saida = []
    for t, texto in falas:
        ref = d.ouvir(texto, True, t)
        if ref:
            saida.append(str(ref))
    return saida


def ultima(texto):
    d = Detector()
    return d.ouvir(texto, True, 0.0)


@pytest.mark.parametrize("texto, esperado", [
    ("joão três dezesseis", "João 3:16"),
    ("joão capítulo três versículo dezesseis", "João 3:16"),
    ("João 3:16", "João 3:16"),
    ("salmo vinte e três", "Salmos 23"),
    ("salmo cento e dezenove versículo cento e cinco", "Salmos 119:105"),
    ("salmos cem", "Salmos 100"),
    ("primeira aos coríntios treze", "1 Coríntios 13"),
    ("primeira carta aos coríntios capítulo treze", "1 Coríntios 13"),
    ("segundo livro de reis cinco", "2 Reis 5"),
    ("1 Coríntios 13:4", "1 Coríntios 13:4"),
    ("primeira de joão quatro oito", "1 João 4:8"),
    ("terceira joão quatro", "3 João 1:4"),
    ("evangelho segundo joão capítulo um", "João 1"),
    ("apocalipse de joão vinte e dois", "Apocalipse 22"),
    ("lamentações de jeremias três vinte e dois", "Lamentações 3:22"),
    ("atos dos apóstolos dois", "Atos 2"),
    ("judas cinco", "Judas 1:5"),
    ("judas versículo vinte e quatro", "Judas 1:24"),
    ("judas um cinco", "Judas 1:5"),
    ("filemom um seis", "Filemom 1:6"),
    ("romanos oito do vinte e oito ao trinta", "Romanos 8:28-30"),
    ("romanos oito versículos vinte e oito a trinta", "Romanos 8:28-30"),
    ("romanos oito vinte e oito até trinta", "Romanos 8:28-30"),
    ("mateus cinco três e quatro", "Mateus 5:3"),
    ("gênesis um um", "Gênesis 1:1"),
    ("jó trinta e oito", "Jó 38"),
])
def test_citacoes(texto, esperado):
    assert str(ultima(texto)) == esperado


@pytest.mark.parametrize("texto", [
    "joão",                       # livro sozinho não vale
    "joão quarenta e cinco",      # João não tem capítulo 45
    "salmo cento e cinquenta e um",
    "pedro três",                 # falta o ordinal
    "coríntios treze",
    "três dezesseis",             # número sem livro
    "joão disse a eles que três homens vieram",
    "jonas ficou três dias no ventre do peixe",
    "lucas era um médico",
    "atos um homem",
    "capítulo três versículo dezesseis",  # sem livro anterior
])
def test_ignorados(texto):
    assert ultima(texto) is None


def test_versiculo_inexistente_fica_no_capitulo():
    assert str(ultima("joão três noventa")) == "João 3"


def test_livro_sozinho_vale_com_gatilho():
    assert str(ultima("vamos ao evangelho de joão")) == "João"
    assert str(ultima("abram no livro de atos")) == "Atos"
    assert str(ultima("livro de salmos vinte e três")) == "Salmos 23"


def test_janela_entre_livro_e_numero():
    assert falar((0, "joão"), (2, "três")) == ["João 3"]
    assert falar((0, "joão"), (5, "três")) == []
    assert falar((0, "joão três"), (2, "dezesseis")) == ["João 3", "João 3:16"]
    assert falar((0, "joão três"), (9, "dezesseis")) == ["João 3"]
    assert falar((0, "joão"), (5, "três"), janela=6) == ["João 3"]


def test_continuacao_no_mesmo_livro():
    falas = [(0, "joão três dezesseis"), (60, "versículo dezessete"), (120, "capítulo quatro"),
             (121, "versículo dois")]
    assert falar(*falas) == ["João 3:16", "João 3:17", "João 4", "João 4:2"]


def test_nome_solto_nao_apaga_o_contexto():
    falas = [(0, "joão três dezesseis"), (30, "marcos disse"), (60, "versículo dezessete")]
    assert falar(*falas) == ["João 3:16", "João 3:17"]


def test_completa_so_quando_dita_em_sequencia():
    d = Detector()
    assert d.ouvir("joão três dezesseis", True, 0).completa
    assert not d.ouvir("versículo dezessete", True, 60).completa
    d = Detector()
    assert not d.ouvir("joão três", True, 0).completa


def test_ordinal_em_fala_separada():
    assert falar((0, "primeira aos"), (1, "coríntios treze")) == ["1 Coríntios 13"]


def test_numero_antes_de_livro_numerado_e_ordinal():
    assert str(ultima("joão três dois timóteo um sete")) == "2 Timóteo 1:7"
    assert str(ultima("mateus cinco 1 coríntios 13")) == "1 Coríntios 13"


def test_texto_parcial_revisado():
    d = Detector()
    assert str(d.ouvir("salmo vinte", False, 0.0)) == "Salmos 20"
    assert str(d.ouvir("salmo vinte e três", False, 0.3)) == "Salmos 23"
    assert d.ouvir("salmo vinte e três", False, 0.4) is None
    assert d.ouvir("salmo vinte e três", True, 0.5) is None


def test_parcial_desfeito_volta_sem_valer_como_citacao():
    d = Detector()
    assert d.ouvir("joão três dezesseis", True, 0).completa
    assert str(d.ouvir("marcos dois", False, 60)) == "Marcos 2"
    volta = d.ouvir("marcos disse", False, 60.2)
    assert str(volta) == "João 3:16" and not volta.completa


def test_versiculo_invalido_nao_troca_de_livro():
    assert falar((0, "joão três dezesseis"), (60, "judas versículo trinta")) == ["João 3:16"]


def test_repeticao_e_emitida_de_novo():
    assert falar((0, "joão três dezesseis"), (60, "joão três dezesseis")) == ["João 3:16"] * 2


def test_situar_leva_o_contexto_sem_emitir():
    d = Detector()
    assert str(d.ouvir("romanos oito vinte e oito", True, 0)) == "Romanos 8:28"
    d.situar(47, 4, 1)
    assert d.ouvir("e então irmãos", True, 60) is None
    volta = d.ouvir("versículo dois", True, 70)
    assert str(volta) == "2 Coríntios 4:2" and not volta.completa
    assert str(d.ouvir("capítulo cinco", True, 80)) == "2 Coríntios 5"


def test_situar_no_meio_da_fala_deixa_para_tras_o_que_ja_foi_dito():
    d = Detector()
    assert str(d.ouvir("romanos oito vinte e oito", False, 0)) == "Romanos 8:28"
    d.situar(47, 4, 1)
    assert d.ouvir("romanos oito vinte e oito como eu dizia", False, 1) is None
    fala = "romanos oito vinte e oito como eu dizia versículo três"
    assert str(d.ouvir(fala, True, 2)) == "2 Coríntios 4:3"
    assert str(d.ouvir("romanos oito um", True, 9)) == "Romanos 8:1"


def test_ler():
    assert str(ler("2 Coríntios 4:1")) == "2 Coríntios 4:1"
    assert str(ler("salmo 23")) == "Salmos 23"
    assert str(ler("Judas 5")) == "Judas 1:5"
    assert ler("joão") is None
    assert ler("") is None


def test_vocabulario():
    palavras = vocabulario()
    assert {"joão", "três", "capítulo", "versículo", "e", "primeira"} <= set(palavras)
    assert not any(p.isdigit() for p in palavras)


def test_referencia_e_comparavel():
    assert Referencia(43, 3, 16) == Referencia(43, 3, 16)
