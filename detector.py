"""Acha referências bíblicas no texto que o motor de fala vai entregando."""

import copy
import re
import unicodedata
from dataclasses import dataclass

from biblia import FRACOS, LIVROS, NOMES, NUMERADOS, SUFIXOS, VERSICULOS

UNIDADES = {"um": 1, "dois": 2, "três": 3, "quatro": 4, "cinco": 5, "seis": 6, "sete": 7,
            "oito": 8, "nove": 9}
DEZ_A_19 = {"dez": 10, "onze": 11, "doze": 12, "treze": 13, "catorze": 14, "quatorze": 14,
            "quinze": 15, "dezesseis": 16, "dezessete": 17, "dezoito": 18, "dezenove": 19,
            "dezasseis": 16, "dezassete": 17, "dezanove": 19}
DEZENAS = {"vinte": 20, "trinta": 30, "quarenta": 40, "cinquenta": 50, "sessenta": 60,
           "setenta": 70, "oitenta": 80, "noventa": 90}
ORDINAIS = {"primeiro": 1, "primeira": 1, "segundo": 2, "segunda": 2, "terceiro": 3,
            "terceira": 3, "um": 1, "dois": 2, "três": 3, "1": 1, "2": 2, "3": 3}
ROMANOS = {"i": 1, "ii": 2, "iii": 3}  # só no texto escrito ("II Timóteo"), nunca na fala
# Ordinais de capítulo e versículo, só valem junto da marca ("capítulo terceiro", "terceiro capítulo").
ORD_UNIDADES = {"primeiro": 1, "segundo": 2, "terceiro": 3, "quarto": 4, "quinto": 5, "sexto": 6,
                "sétimo": 7, "oitavo": 8, "nono": 9}
ORD_DEZENAS = {"décimo": 10, "vigésimo": 20, "trigésimo": 30, "quadragésimo": 40,
               "quinquagésimo": 50, "sexagésimo": 60, "septuagésimo": 70, "setuagésimo": 70,
               "octogésimo": 80, "nonagésimo": 90}
CAPITULO = ("capítulo", "capítulos")
VERSICULO = ("versículo", "versículos", "verso", "versos")
# Ditas pouco antes do livro, valem o livro sozinho ("evangelho de João").
GATILHOS = ("livro", "evangelho", "carta", "epístola", "abra", "abram", "abramos", "abrir")
# Podem ficar entre o ordinal e o livro ("segunda carta do apóstolo Paulo aos Coríntios").
CONECTIVOS = ("de", "do", "dos", "da", "das", "a", "o", "as", "ao", "aos", "livro", "carta",
              "epístola", "paulo", "apóstolo", "são", "universal")
ATE = ("a", "ao", "até")
# Ditas entre o capítulo e o versículo sem contar como palavra de fora ("três dois pontos dezesseis").
PONTES = ("dois pontos", "ponto", "a partir do", "a partir de", "a partir da")

FOLGA = 1  # palavras de fora toleradas entre o capítulo e o versículo ("três e dezesseis")
DISTANCIA = 6  # palavras toleradas entre o ordinal e o livro, e entre "capítulo três" e o livro


def normalizar(texto):
    """Minúsculas sem acento, separando palavras e algarismos ("João 3:16" -> joao, 3, 16)."""
    sem_acento = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
    return re.findall(r"[a-z]+|\d+", sem_acento)


def _n(palavras):
    if isinstance(palavras, dict):
        return {normalizar(p)[0]: v for p, v in palavras.items()}
    return {normalizar(p)[0] for p in palavras}


_UNIDADES, _DEZENAS = _n(UNIDADES), _n(DEZENAS)
_ATE_19 = {**_UNIDADES, **_n(DEZ_A_19)}
_ORDINAIS, _LIVROS, _NUMERADOS = {**_n(ORDINAIS), **ROMANOS}, _n(LIVROS), _n(NUMERADOS)
_FRACOS, _ORD_UNIDADES, _ORD_DEZENAS = _n(FRACOS), _n(ORD_UNIDADES), _n(ORD_DEZENAS)
_PONTES = [normalizar(p) for p in PONTES]
_CAPITULO, _VERSICULO, _GATILHOS, _ATE = _n(CAPITULO), _n(VERSICULO), _n(GATILHOS), _n(ATE)
_CONECTIVOS = _n(CONECTIVOS) | {"unk"}  # "[unk]" é o que o Vosk põe no lugar de palavra de fora
_SUFIXOS = {livro: [normalizar(s) for s in sufixos] for livro, sufixos in SUFIXOS.items()}


def vocabulario():
    """Toda palavra que o detector entende, com acento, para restringir o motor de fala."""
    palavras = {"e", "cem", "cento", "centésimo"}
    for grupo in (UNIDADES, DEZ_A_19, DEZENAS, ORDINAIS, ORD_UNIDADES, ORD_DEZENAS, LIVROS,
                  FRACOS, NUMERADOS, CAPITULO, VERSICULO, GATILHOS, CONECTIVOS, ATE):
        palavras.update(p for p in grupo if not p.isdigit())
    for frase in PONTES + tuple(s for sufixos in SUFIXOS.values() for s in sufixos):
        palavras.update(frase.split())
    return sorted(palavras)


@dataclass(frozen=True)
class Referencia:
    livro: int
    capitulo: int | None = None
    versiculo: int | None = None
    fim: int | None = None  # último versículo, quando foi dito um intervalo
    completa: bool = False  # livro, capítulo e versículo ditos em sequência

    def __str__(self):
        return rotulo(self.livro, self.capitulo, self.versiculo, self.fim)


def rotulo(livro, capitulo=None, versiculo=None, fim=None):
    texto = NOMES[livro - 1]
    if capitulo:
        texto += f" {capitulo}"
        if versiculo:
            texto += f":{versiculo}" + (f"-{fim}" if fim else "")
    return texto


@dataclass
class _Estado:
    livro: int | None = None
    cap: int | None = None
    vers: int | None = None
    fim: int | None = None
    cadeia: bool = False     # capítulo e versículo vieram em sequência com o livro
    espera: str = ""         # o que um número solto seria agora: "vers", "fim" ou nada
    t_num: float = 0.0       # quando o último número foi aceito
    cand: int | None = None  # livro ouvido, ainda sem capítulo
    t_cand: float = 0.0
    soltos: int = 0          # palavras de fora desde o último livro ou número aceito
    ate: bool = False        # ouviu "a"/"até" logo depois do versículo
    serie: int = 0           # sobe a cada citação aceita, para distinguir repetições


def _ate_99(toks, i):
    if i >= len(toks):
        return None
    if toks[i] in _DEZENAS:
        if toks[i + 1:i + 2] == ["e"] and toks[i + 2:i + 3] and toks[i + 2] in _UNIDADES:
            return _DEZENAS[toks[i]] + _UNIDADES[toks[i + 2]], i + 3
        return _DEZENAS[toks[i]], i + 1
    if toks[i] in _ATE_19:
        return _ATE_19[toks[i]], i + 1
    return None


def _numero(toks, i):
    """(valor, índice seguinte) se toks[i] começa um número, por extenso ou em algarismos."""
    if i >= len(toks):
        return None
    if toks[i].isdigit():
        return int(toks[i]), i + 1
    if toks[i] == "cem":
        return 100, i + 1
    if toks[i] == "cento":
        resto = _ate_99(toks, i + 2 if toks[i + 1:i + 2] == ["e"] else i + 1)
        return (100 + resto[0], resto[1]) if resto else (100, i + 1)
    return _ate_99(toks, i)


def _numero_ordinal(toks, i):
    """(valor, índice seguinte) se toks[i] começa um ordinal de capítulo ("terceiro", "vigésimo")."""
    v, j = 0, i
    if toks[j:j + 1] == ["centesimo"]:
        v, j = 100, j + 1
    if j < len(toks) and toks[j] in _ORD_DEZENAS:
        v, j = v + _ORD_DEZENAS[toks[j]], j + 1
    if j < len(toks) and toks[j] in _ORD_UNIDADES:
        v, j = v + _ORD_UNIDADES[toks[j]], j + 1
    return (v, j) if j > i else None


def _marca(toks, i):
    """("capítulo"/"versículo", valor, início e fim do número) para "capítulo três",
    "capítulo terceiro" ou "terceiro capítulo"; None se não houver número marcado em toks[i]."""
    if toks[i] in _CAPITULO or toks[i] in _VERSICULO:
        j = i + 2 if toks[i + 1:i + 2] in (["o"], ["do"], ["de"]) else i + 1
        num = _numero(toks, j) or _numero_ordinal(toks, j)
        return (toks[i] in _CAPITULO, num[0], j, num[1]) if num else None
    num = _numero_ordinal(toks, i)
    if num and num[1] < len(toks) and (toks[num[1]] in _CAPITULO or toks[num[1]] in _VERSICULO):
        return toks[num[1]] in _CAPITULO, num[0], i, num[1] + 1
    return None


def _ponte(toks, i):
    """Índice depois de "dois pontos", "a partir do"... se começarem em toks[i]."""
    for ponte in _PONTES:
        if toks[i:i + len(ponte)] == ponte:
            return i + len(ponte)
    return None


def _ordinal(toks, i, usados):
    """Ordinal dito antes do livro em toks[i]; 0 se não houver."""
    j = i - 1
    while j >= 0 and toks[j] in _CONECTIVOS and i - j <= DISTANCIA:
        j -= 1
    if j < 0 or j in usados:
        return 0
    if toks[j] == "segundo" and toks[j - 1:j] == ["evangelho"]:  # "evangelho segundo João"
        return 0
    return _ORDINAIS.get(toks[j], 0)


def _e_ordinal(toks, num):
    """O número é o ordinal do livro seguinte ("um Coríntios"), não capítulo nem versículo."""
    seguinte = toks[num[1]] if num[1] < len(toks) else ""
    return num[0] <= 3 and 0 not in _NUMERADOS.get(seguinte, {0: 0})


def _livro(toks, i, usados):
    """(livro, quantos tokens ocupa) se toks[i] é o nome de um livro."""
    if toks[i] in _NUMERADOS:
        livro = _NUMERADOS[toks[i]].get(_ordinal(toks, i, usados))
    else:
        livro = _LIVROS.get(toks[i]) or _FRACOS.get(toks[i])
    if not livro:
        return None
    for sufixo in _SUFIXOS.get(livro, ()):
        if toks[i + 1:i + 1 + len(sufixo)] == sufixo:
            return livro, 1 + len(sufixo)
    if toks[i] in _FRACOS:
        num = _numero(toks, i + 1)
        if not (toks[i + 1:i + 2] and toks[i + 1] in _CAPITULO or num and _numero(toks, num[1])):
            return None
    return livro, 1


def _adiante(toks, i, usados):
    """(livro, índice seguinte) se um livro vem logo depois, como em "capítulo três de João"."""
    k = i
    while k < len(toks) and k - i < DISTANCIA:
        achado = _livro(toks, k, usados)
        if achado:
            return achado[0], k + achado[1]
        if toks[k] not in _CONECTIVOS and toks[k] not in _GATILHOS and toks[k] not in _ORDINAIS:
            return None
        k += 1
    return None


class Detector:
    def __init__(self, janela=3.0):
        self.janela = janela  # segundos entre o livro e o capítulo, e entre este e o versículo
        self._base = _Estado()  # estado ao fim da fala anterior
        self._cauda = []        # últimos tokens da fala anterior, para o ordinal e o gatilho
        self._tempos = []       # quando cada token da fala atual apareceu
        self._pulo = 0          # tokens da fala atual ditos antes de situar()
        self._ultima = None

    def situar(self, livro, cap, vers=None):
        """Leva o contexto a um texto sem que ele seja dito: "versículo 2" passa a ser dele."""
        self._base = _Estado(livro, cap, vers, serie=self._base.serie)
        self._cauda = []
        self._pulo = len(self._tempos)
        self._ultima = livro, cap, vers, None, self._base.serie

    def ouvir(self, texto, final, agora):
        """Recebe o texto acumulado da fala atual. Devolve a Referencia quando há citação nova."""
        toks = normalizar(texto)
        del self._tempos[len(toks):]
        self._tempos += [agora] * (len(toks) - len(self._tempos))
        todos = [tok for tok, _ in self._cauda] + toks
        tempos = [t for _, t in self._cauda] + self._tempos
        # O motor revisa o texto parcial, então a fala é sempre relida do começo.
        e = copy.copy(self._base)
        usados = set()
        i = len(self._cauda) + min(self._pulo, len(toks))
        while i < len(todos):
            i = self._passo(e, todos, tempos, i, usados)
        nova = e.serie != self._base.serie  # e não só a volta de um parcial revisado
        if final:
            self._base = e
            self._cauda = [("" if k in usados else todos[k], tempos[k])
                           for k in range(max(0, len(todos) - 4), len(todos))]
            self._tempos = []
            self._pulo = 0
        if e.livro is None:
            return None
        atual = e.livro, e.cap, e.vers, e.fim, e.serie
        if atual == self._ultima:
            return None
        self._ultima = atual
        return Referencia(e.livro, e.cap, e.vers, e.fim, nova and e.cadeia and e.vers is not None)

    def _passo(self, e, toks, tempos, i, usados):
        tok, t = toks[i], tempos[i]
        achado = _livro(toks, i, usados)
        if achado:
            e.cand, e.t_cand, e.soltos, e.ate, e.espera = achado[0], t, 0, False, ""
            if any(toks[k] in _GATILHOS and t - tempos[k] <= self.janela
                   for k in range(max(0, i - 4), i)):
                e.livro, e.cap, e.vers, e.fim, e.cadeia = achado[0], None, None, None, True
                e.serie += 1
            return i + achado[1]
        ponte = _ponte(toks, i)
        if ponte:
            return ponte
        marca = _marca(toks, i)
        if marca:
            return self._marcado(e, toks, tempos, marca, usados)
        if tok in _CAPITULO or tok in _VERSICULO:
            return i + 1
        num = _numero(toks, i)
        # "Lucas era um médico": "um" só vale como capítulo se vier outro número depois
        seguinte = toks[i + 1] if i + 1 < len(toks) else ""
        artigo = tok == "um" and not (_numero(toks, i + 1) or seguinte in _VERSICULO)
        if num and not _e_ordinal(toks, num) and self._solto(e, num[0], t, artigo):
            usados.update(range(i, num[1]))
            return num[1]
        if tok in _ATE and e.espera == "fim" and e.soltos == 0:
            e.ate = True
            return i + 1
        e.soltos += 1
        e.ate = False
        return num[1] if num else i + 1

    def _marcado(self, e, toks, tempos, marca, usados):
        """ "capítulo três", com o livro antes ou depois ("capítulo três de João",
        "versículo dezesseis de João três", "versículo dezesseis do capítulo três de João")."""
        e_cap, v, ini, fim = marca
        t = tempos[ini]
        usados.update(range(ini, fim))
        if e_cap:
            adiante = _adiante(toks, fim, usados)
            if not adiante:
                self._capitulo(e, v, t, True)
                return fim
            livro, fim = adiante
            if 1 <= v <= len(VERSICULOS[livro - 1]):
                self._fixar(e, livro, v, None, t)
            return fim
        cap = None
        j = fim + 1 if toks[fim:fim + 1] in (["do"], ["de"], ["no"]) else fim
        seguinte = _marca(toks, j) if j < len(toks) else None
        if seguinte and seguinte[0]:  # "versículo dezesseis do capítulo três"
            cap, fim = seguinte[1], seguinte[3]
            usados.update(range(seguinte[2], fim))
        adiante = _adiante(toks, fim, usados)
        if adiante:
            livro, fim = adiante
            if cap is None:
                num = _numero(toks, fim)
                if num:
                    cap, fim = num[0], num[1]
                    usados.update(range(adiante[1], fim))
                elif len(VERSICULOS[livro - 1]) == 1:
                    cap = 1
            if cap is None:  # o capítulo ainda não veio: fica o livro
                e.cand, e.t_cand, e.soltos, e.ate, e.espera = livro, t, 0, False, ""
                return fim
        elif cap is not None and e.livro is not None:
            livro = e.livro
        else:
            self._versiculo(e, v, t, True)
            return fim
        capitulos = VERSICULOS[livro - 1]
        if 1 <= cap <= len(capitulos) and 1 <= v <= capitulos[cap - 1]:
            self._fixar(e, livro, cap, v, t)
        return fim

    def _fixar(self, e, livro, cap, vers, t):
        """Citação dita de uma vez, com o livro depois do capítulo ou do versículo."""
        e.livro, e.cap, e.vers, e.fim, e.cadeia = livro, cap, vers, None, True
        e.espera = "fim" if vers else "vers"
        e.cand, e.t_num, e.soltos, e.ate = None, t, 0, False
        e.serie += 1

    def _solto(self, e, v, t, artigo):
        """Número dito sem "capítulo" nem "versículo": vale pelo que veio logo antes."""
        # Colado ao livro: "Jonas ficou três dias" não é Jonas 3.
        if e.cand is not None and t - e.t_cand <= self.janela and e.soltos == 0 and not artigo:
            return self._capitulo(e, v, t, False)
        if t - e.t_num > self.janela:
            return False
        if e.espera == "vers" and e.soltos <= FOLGA:
            return self._versiculo(e, v, t, False)
        if (e.espera == "fim" and not e.ate and e.soltos <= FOLGA and e.vers == 1
                and len(VERSICULOS[e.livro - 1]) == 1):  # "Judas um cinco": o "um" era o capítulo
            return self._versiculo(e, v, t, False)
        if e.espera == "fim" and e.ate and e.vers < v <= VERSICULOS[e.livro - 1][e.cap - 1]:
            e.fim, e.espera, e.t_num, e.ate = v, "", t, False
            e.serie += 1
            return True
        return False

    def _capitulo(self, e, v, t, marcado):
        novo = e.cand is not None and t - e.t_cand <= self.janela
        livro = e.cand if novo else e.livro if marcado else None  # "capítulo 4" continua o livro
        if livro is None:
            return False
        capitulos = VERSICULOS[livro - 1]
        if novo and not marcado and len(capitulos) == 1:  # livro de um capítulo: é o versículo
            if not 1 <= v <= capitulos[0]:
                return False
            e.livro, e.cap, e.vers, e.fim, e.cadeia, e.espera = livro, 1, v, None, True, "fim"
        elif 1 <= v <= len(capitulos):
            e.livro, e.cap, e.vers, e.fim, e.cadeia, e.espera = livro, v, None, None, novo, "vers"
        else:
            return False
        e.cand, e.t_num, e.soltos, e.ate = None, t, 0, False
        e.serie += 1
        return True

    def _versiculo(self, e, v, t, marcado):
        unico = (marcado and e.cand is not None and t - e.t_cand <= self.janela
                 and len(VERSICULOS[e.cand - 1]) == 1)  # "Judas versículo 5"
        livro, cap = (e.cand, 1) if unico else (e.livro, e.cap)
        if cap is None or not 1 <= v <= VERSICULOS[livro - 1][cap - 1]:
            return False
        if unico:
            e.livro, e.cap, e.cadeia, e.cand, e.t_num = livro, 1, True, None, t
        e.cadeia = e.cadeia and t - e.t_num <= self.janela
        e.vers, e.fim, e.espera, e.t_num, e.soltos, e.ate = v, None, "fim", t, 0, False
        e.serie += 1
        return True


def ler(texto):
    """A referência escrita em texto ("2 Coríntios 4:1"), ou None se não houver."""
    return Detector().ouvir(texto, True, 0.0)
