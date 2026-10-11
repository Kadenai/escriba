"""Acha referências bíblicas no texto que o motor de fala vai entregando."""

import copy
import re
import unicodedata
from dataclasses import dataclass

from biblia import LIVROS, NOMES, NUMERADOS, SUFIXOS, VERSICULOS

UNIDADES = {"um": 1, "dois": 2, "três": 3, "quatro": 4, "cinco": 5, "seis": 6, "sete": 7,
            "oito": 8, "nove": 9}
DEZ_A_19 = {"dez": 10, "onze": 11, "doze": 12, "treze": 13, "catorze": 14, "quatorze": 14,
            "quinze": 15, "dezesseis": 16, "dezessete": 17, "dezoito": 18, "dezenove": 19,
            "dezasseis": 16, "dezassete": 17, "dezanove": 19}
DEZENAS = {"vinte": 20, "trinta": 30, "quarenta": 40, "cinquenta": 50, "sessenta": 60,
           "setenta": 70, "oitenta": 80, "noventa": 90}
ORDINAIS = {"primeiro": 1, "primeira": 1, "segundo": 2, "segunda": 2, "terceiro": 3,
            "terceira": 3, "um": 1, "dois": 2, "três": 3, "1": 1, "2": 2, "3": 3}
CAPITULO = ("capítulo", "capítulos")
VERSICULO = ("versículo", "versículos", "verso", "versos")
# Ditas pouco antes do livro, valem o livro sozinho ("evangelho de João").
GATILHOS = ("livro", "evangelho", "carta", "epístola", "abra", "abram", "abramos", "abrir")
# Podem ficar entre o ordinal e o livro ("primeira carta aos Coríntios").
CONECTIVOS = ("de", "do", "dos", "da", "a", "o", "ao", "aos", "livro", "carta", "epístola")
ATE = ("a", "ao", "até")

FOLGA = 1  # palavras de fora toleradas entre o capítulo e o versículo ("três e dezesseis")


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
_ORDINAIS, _LIVROS, _NUMERADOS = _n(ORDINAIS), _n(LIVROS), _n(NUMERADOS)
_CAPITULO, _VERSICULO, _GATILHOS, _ATE = _n(CAPITULO), _n(VERSICULO), _n(GATILHOS), _n(ATE)
_CONECTIVOS = _n(CONECTIVOS) | {"unk"}  # "[unk]" é o que o Vosk põe no lugar de palavra de fora
_SUFIXOS = {livro: [normalizar(s) for s in sufixos] for livro, sufixos in SUFIXOS.items()}


def vocabulario():
    """Toda palavra que o detector entende, com acento, para restringir o motor de fala."""
    palavras = {"e", "cem", "cento"}
    for grupo in (UNIDADES, DEZ_A_19, DEZENAS, ORDINAIS, LIVROS, NUMERADOS, CAPITULO, VERSICULO,
                  GATILHOS, CONECTIVOS, ATE):
        palavras.update(p for p in grupo if not p.isdigit())
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


def _ordinal(toks, i, usados):
    """Ordinal dito antes do livro em toks[i]; 0 se não houver."""
    j = i - 1
    while j >= 0 and toks[j] in _CONECTIVOS and i - j <= 3:
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
        livro = _LIVROS.get(toks[i])
    if not livro:
        return None
    for sufixo in _SUFIXOS.get(livro, ()):
        if toks[i + 1:i + 1 + len(sufixo)] == sufixo:
            return livro, 1 + len(sufixo)
    return livro, 1


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
        if tok in _CAPITULO or tok in _VERSICULO:
            j = i + 2 if toks[i + 1:i + 2] in (["o"], ["do"], ["de"]) else i + 1
            num = _numero(toks, j)
            if num:
                aceitar = self._capitulo if tok in _CAPITULO else self._versiculo
                if aceitar(e, num[0], tempos[j], True):
                    usados.update(range(j, num[1]))
                return num[1]
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
