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


@pytest.mark.parametrize("texto, esperado", [
    # ordinal longe do livro
    ("segunda carta de paulo aos coríntios quatro um", "2 Coríntios 4:1"),
    ("primeira carta do apóstolo paulo a timóteo seis dez", "1 Timóteo 6:10"),
    ("segunda epístola do apóstolo paulo aos tessalonicenses três", "2 Tessalonicenses 3"),
    ("primeira carta de pedro cinco sete", "1 Pedro 5:7"),
    ("primeira epístola universal de pedro cinco sete", "1 Pedro 5:7"),
    ("primeira carta de joão um nove", "1 João 1:9"),
    ("primeira epístola de são joão um nove", "1 João 1:9"),
    ("segundo livro de samuel sete", "2 Samuel 7"),
    ("primeiro livro dos reis dezoito", "1 Reis 18"),
    ("segundo livro das crônicas sete catorze", "2 Crônicas 7:14"),
    ("primeiro reis dezoito", "1 Reis 18"),
    ("primeira samuel dezessete", "1 Samuel 17"),
    ("primeiro samuel dezessete", "1 Samuel 17"),
    ("segunda timóteo três dezesseis", "2 Timóteo 3:16"),
    ("segunda a timóteo três dezesseis", "2 Timóteo 3:16"),
    ("primeira tessalonicenses cinco dezessete", "1 Tessalonicenses 5:17"),
    ("primeira pedro dois nove", "1 Pedro 2:9"),
    ("segunda pedro três nove", "2 Pedro 3:9"),
    ("segunda de pedro três nove", "2 Pedro 3:9"),
    ("i coríntios treze", "1 Coríntios 13"),
    ("ii timóteo três", "2 Timóteo 3"),
    # nomes alternativos de livros
    ("carta aos romanos oito vinte e oito", "Romanos 8:28"),
    ("epístola aos hebreus onze um", "Hebreus 11:1"),
    ("carta de tiago um cinco", "Tiago 1:5"),
    ("evangelho de mateus cinco três", "Mateus 5:3"),
    ("evangelho segundo mateus cinco três", "Mateus 5:3"),
    ("evangelho de são lucas quinze", "Lucas 15"),
    ("ato dos apóstolos dois", "Atos 2"),
    ("o livro de atos dois quatro", "Atos 2:4"),
    ("cântico dos cânticos dois", "Cantares 2"),
    ("cantares de salomão dois", "Cantares 2"),
    ("cântico de salomão dois", "Cantares 2"),
    ("eclesiastes três um", "Eclesiastes 3:1"),
    ("provérbios de salomão três cinco", "Provérbios 3:5"),
    ("profeta isaías cinquenta e três", "Isaías 53"),
    ("livro do profeta isaías cinquenta e três", "Isaías 53"),
    ("profeta jeremias vinte e nove onze", "Jeremias 29:11"),
    ("salmista no salmo noventa e um", "Salmos 91"),
    ("salmo noventa e um", "Salmos 91"),
    ("o salmo de número vinte e três", "Salmos 23"),
    ("apocalipse de são joão três vinte", "Apocalipse 3:20"),
    ("revelação três vinte", "Apocalipse 3:20"),
    ("deuteronômio seis quatro", "Deuteronômio 6:4"),
    ("habacuque dois quatro", "Habacuque 2:4"),
    ("oséias seis seis", "Oseias 6:6"),
    ("miquéias seis oito", "Miqueias 6:8"),
    ("filemon seis", "Filemom 1:6"),
    ("filémon seis", "Filemom 1:6"),
    ("abdias quinze", "Obadias 1:15"),
    ("naum um sete", "Naum 1:7"),
    # formas de capítulo/versículo
    ("joão no capítulo três verso dezesseis", "João 3:16"),
    ("joão capítulo três a partir do versículo dezesseis", "João 3:16"),
    ("joão três a partir do dezesseis", "João 3:16"),
    ("joão três no versículo dezesseis", "João 3:16"),
    ("joão três verso dezesseis", "João 3:16"),
    ("joão três e dezesseis", "João 3:16"),
    ("joão três dois pontos dezesseis", "João 3:16"),
    ("joão capítulo terceiro", "João 3"),
    ("no terceiro capítulo de joão", "João 3"),
    ("no capítulo três de joão", "João 3"),
    ("joão três versículo dezesseis", "João 3:16"),
    ("joão três dezesseis em diante", "João 3:16"),
    ("romanos doze do um ao dois", "Romanos 12:1-2"),
    ("romanos doze um e dois", "Romanos 12:1"),
    ("romanos doze um a dois", "Romanos 12:1-2"),
    ("romanos doze versos um e dois", "Romanos 12:1"),
    ("salmo cento e dezenove cento e cinco", "Salmos 119:105"),
    ("salmos cento e cinquenta", "Salmos 150"),
    ("isaías quarenta trinta e um", "Isaías 40:31"),
    ("lucas quinze onze até trinta e dois", "Lucas 15:11-32"),
    ("lucas quinze onze ao trinta e dois", "Lucas 15:11-32"),
    ("versículo dezesseis de joão três", "João 3:16"),
    ("joão três ponto dezesseis", "João 3:16"),
    # o livro depois do capítulo ou do versículo
    ("versículo dezesseis do capítulo três de joão", "João 3:16"),
    ("capítulo três da primeira carta aos coríntios versículo quatro", "1 Coríntios 3:4"),
    ("capítulo quatro da carta aos romanos", "Romanos 4"),
    ("capítulo um de judas", "Judas 1"),
    ("revelação capítulo três", "Apocalipse 3"),
    ("evangelho segundo são joão três dezesseis", "João 3:16"),
    ("são joão três dezesseis", "João 3:16"),
    ("segundo paralipômenos sete catorze", "2 Crônicas 7:14"),
    ("III João 4", "3 João 1:4"),
])
def test_variacoes_de_fala(texto, esperado):
    assert str(ultima(texto)) == esperado


@pytest.mark.parametrize("texto", [
    "uma revelação três vezes maior",   # palavra comum só vale com capítulo e versículo
    "a revelação de deus dois mil anos",
    "o ato dois da peça",
    "a revelação de joão",
    "o apóstolo paulo disse a pedro três vezes",  # sem ordinal
    "versículo três de joão",           # o "três" é o versículo, não "3 João"
    "capítulo três e joão disse",
    "o terceiro dia",
    "esse é o ponto três",
])
def test_variacoes_ignoradas(texto):
    assert ultima(texto) is None


def test_capitulo_ordinal_e_versiculo_antes_do_capitulo_continuam_o_livro():
    falas = [(0, "romanos oito"), (10, "no quarto capítulo"),
             (20, "versículo dezesseis do capítulo três")]
    assert falar(*falas) == ["Romanos 8", "Romanos 4", "Romanos 3:16"]


def test_dois_pontos_corrige_o_parcial():
    d = Detector()
    assert str(d.ouvir("joão três dois", False, 0.0)) == "João 3:2"
    assert str(d.ouvir("joão três dois pontos dezesseis", False, 0.3)) == "João 3:16"


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
    assert {"paulo", "apóstolo", "terceiro", "pontos", "revelação", "abdias"} <= set(palavras)
    assert not any(p.isdigit() for p in palavras)
    assert "ii" not in palavras


def test_referencia_e_comparavel():
    assert Referencia(43, 3, 16) == Referencia(43, 3, 16)
