"""Lê a passagem digitada pelo operador ("genesis 2 3", "Rm 8:28-30", "1Co 13").

Independente do detector da fala: não usa o estado dele, as janelas de tempo nem as regras
para a fala comum. Só os dados dos livros vêm do mesmo lugar.
"""

import re
import unicodedata
from dataclasses import dataclass

from biblia import ABREVIATURAS, FRACOS, LIVROS, NOMES, NUMERADOS, SUFIXOS, VERSICULOS

ORDINAIS = {"1": 1, "2": 2, "3": 3, "i": 1, "ii": 2, "iii": 3, "primeiro": 1, "primeira": 1,
            "segundo": 2, "segunda": 2, "terceiro": 3, "terceira": 3}
INTERVALO = {"-", "–", "a", "ao", "até", "ate"}


def _sem_acento(palavra):
    return unicodedata.normalize("NFKD", palavra).encode("ascii", "ignore").decode()


_LIVROS = {_sem_acento(nome): livro for nome, livro in {**LIVROS, **FRACOS}.items()}
_LIVROS.update({_sem_acento(nome.split()[-1].lower()): livro
                for livro, nome in enumerate(NOMES, 1) if not nome[0].isdigit()})
_NUMERADOS = {_sem_acento(nome): livros for nome, livros in NUMERADOS.items()}
# Nomes de mais de uma palavra: a primeira basta, o resto é ignorado ("Cântico dos Cânticos").
_COMPLEMENTOS = {_sem_acento(p) for sufixos in SUFIXOS.values() for s in sufixos for p in s.split()}


@dataclass(frozen=True)
class Passagem:
    livro: int
    capitulo: int | None = None
    versiculo: int | None = None
    fim: int | None = None

    def __str__(self):
        texto = NOMES[self.livro - 1]
        if self.capitulo:
            texto += f" {self.capitulo}"
            if self.versiculo:
                texto += f":{self.versiculo}" + (f"-{self.fim}" if self.fim else "")
        return texto


def _livro(palavra, ordinal):
    """O livro que a palavra (minúscula, com acento) nomeia, dado o ordinal antes dela."""
    chave = (str(ordinal) if ordinal else "") + palavra
    if chave in ABREVIATURAS:  # com acento: "jó" é Jó, "jo" é João
        return ABREVIATURAS[chave]
    simples = _sem_acento(palavra)
    if simples not in _NUMERADOS and simples not in _LIVROS and len(simples) >= 3:
        # O começo do nome, se for de um livro só: "ecl", "apoc", "rom"; "fil" não.
        nomes = {n for n in list(_NUMERADOS) + list(_LIVROS) if n.startswith(simples)}
        livros = {_NUMERADOS[n].get(ordinal or 0) if n in _NUMERADOS else _LIVROS[n] for n in nomes}
        if len(nomes) == 1 or len(livros) == 1 and None not in livros:
            simples = min(nomes)
    if simples in _NUMERADOS:
        return _NUMERADOS[simples].get(ordinal or 0)
    return None if ordinal else _LIVROS.get(simples)


def interpretar(texto):
    """A Passagem digitada, ou None se não der para entender ou se ela não existir."""
    texto = texto.lower().replace("º", "").replace("ª", "")
    livro = ordinal = None
    numeros, intervalo, antes = [], False, 0  # antes: palavras vistas antes do livro
    for tok in re.findall(r"[^\W\d_]+|\d+|[-–]", texto):
        if livro is None:
            if tok in ORDINAIS and antes == 0 and ordinal is None:
                ordinal = ORDINAIS[tok]  # só no começo: "evangelho segundo João" é João
            elif tok.isdigit():
                return None  # número antes do livro que não é o ordinal
            else:
                livro = _livro(tok, ordinal)
                antes += 1
        elif tok.isdigit():
            if len(numeros) == 2 and not intervalo:
                break  # "Rm 8:28, 30": versículos soltos, fica o primeiro
            numeros.append(int(tok))
            if len(numeros) == 3:
                break
        elif tok in INTERVALO and len(numeros) == 2:
            intervalo = True
    if livro is None:
        return None
    return _validar(livro, numeros)


def _validar(livro, numeros):
    capitulos = VERSICULOS[livro - 1]
    if len(capitulos) == 1 and len(numeros) == 1:  # "Judas 5": o capítulo é o único
        numeros = [1] + numeros
    cap, vers, fim = (numeros + [None] * 3)[:3]
    if cap is not None and not 1 <= cap <= len(capitulos):
        return None
    if vers is not None and not 1 <= vers <= capitulos[cap - 1]:
        return None
    if fim is not None and not vers < fim <= capitulos[cap - 1]:
        fim = None
    return Passagem(livro, cap, vers, fim)
