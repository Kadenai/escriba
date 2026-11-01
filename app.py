"""Escriba: ouve o microfone e deixa pronto no Holyrics o versículo que o preletor citou."""

import ctypes
import json
import os
import queue
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, ttk

import sounddevice as sd

import holyrics
from detector import Detector, ler, rotulo
from motores import MOTORES

CONFIG = Path(os.environ["APPDATA"]) / "Escriba" / "config.json"
ICONE = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "logo" / "escriba.ico"
PADRAO = {"motor": "sherpa-onnx", "microfone": "", "modo": "lcv", "confirmar": False,
          "espera": 4, "janela": 3, "principal": "", "retorno": 60, "pasta": "",
          "host": "", "porta": 8091, "token": "", "transcricao": True}
# Só no config.json, sem opção na janela: "transcricao": false desliga e esconde a transcrição.
MODOS = (("off", "Desativado"), ("l", "Só o livro"), ("lc", "Livro e capítulo"),
         ("lcv", "Livro, capítulo e versículo"),
         ("projeta", "Livro, capítulo e versículo, e já projeta"))
EXEMPLO_DIGITADO = "ex.: Rm 8:28-30, 1Co 13, Salmo 23"
ASSENTAR = 1000  # ms antes de projetar, para "vinte" não ir à tela antes de "vinte e um"
TENTAR_DE_NOVO = 5000  # ms até religar o motor depois de uma falha
ADIAR = 500  # ms entre uma olhada e outra enquanto a volta espera o preletor terminar a frase
ADIAR_MAX = 15000  # ms que a volta espera, no máximo, por uma frase que não termina


def microfones():
    """Nome -> índice das entradas de áudio do Windows."""
    entradas = {}
    for i in sd.query_hostapis(sd.default.hostapi)["devices"]:
        dispositivo = sd.query_devices(i)
        if dispositivo["max_input_channels"] > 0:
            entradas[dispositivo["name"]] = i
    return entradas


class App:
    def __init__(self, raiz):
        self.raiz = raiz
        try:
            salvo = json.loads(CONFIG.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            salvo = {}
        self.entradas = microfones()
        if not salvo.get("microfone"):  # primeira vez: o padrão do Windows vem no topo da lista
            salvo["microfone"] = next(iter(self.entradas), "")
        self.v = {chave: (tk.BooleanVar if isinstance(padrao, bool) else tk.StringVar)(
            value=salvo.get(chave, padrao)) for chave, padrao in PADRAO.items()}
        self.estado = tk.StringVar()
        self.ouvido = tk.StringVar()
        self.envio = tk.StringVar()
        self.lido = tk.StringVar()  # como o texto principal foi entendido
        self.digitado = tk.StringVar()  # passagem digitada para enviar na mão
        self.entendido = tk.StringVar(value=EXEMPLO_DIGITADO)
        self.fila = queue.Queue()  # o que chega das outras threads: (motor, tipo, dados...)
        self.envios = queue.Queue()  # pedidos ao Holyrics, despachados em ordem por uma thread
        threading.Thread(target=self._despachar, daemon=True).start()
        self.motor = None
        self.tentativa = None  # temporizador para religar o motor depois de uma falha
        self.alvo = None      # último (livro, capítulo, versículo, fim, projetar) tratado
        self.pendente = None  # temporizador do aviso ou da projeção
        self.aviso = None
        self.principal = None  # (livro, capítulo, versículo) aonde voltar depois de outra citação
        self.volta = None      # temporizador dessa volta
        self.inicio = None     # quando começou a fala em curso, para a transcrição
        self._montar()
        for chave, variavel in self.v.items():
            variavel.trace_add("write", self._salvar)
        for chave in ("motor", "microfone"):
            self.v[chave].trace_add("write", self._reiniciar)
        self.v["modo"].trace_add("write", self._mudar_modo)
        self.v["principal"].trace_add("write", self._mudar_principal)
        self.v["janela"].trace_add(
            "write", lambda *_: setattr(self.detector, "janela", self._inteiro("janela")))
        raiz.protocol("WM_DELETE_WINDOW", self._sair)
        self._salvar()  # completa o config.json com as opções novas, como "transcricao"
        self._reiniciar()
        self._mudar_principal()
        self._tique()

    def _montar(self):
        quadro = ttk.Frame(self.raiz, padding=12)
        quadro.grid()
        ttk.Label(quadro, text="Motor de fala").grid(row=0, column=0, sticky="w")
        ttk.Combobox(quadro, textvariable=self.v["motor"], values=list(MOTORES), state="readonly",
                     width=40).grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Label(quadro, text="Microfone").grid(row=1, column=0, sticky="w")
        self.caixa_microfone = ttk.Combobox(quadro, textvariable=self.v["microfone"],
                                            values=list(self.entradas), width=40)
        self.caixa_microfone.grid(row=1, column=1, sticky="ew", pady=2)

        modos = ttk.LabelFrame(quadro, text="O que deixar pronto no Holyrics", padding=8)
        modos.grid(row=2, column=0, columnspan=2, sticky="ew", pady=8)
        for valor, texto in MODOS:
            ttk.Radiobutton(modos, text=texto, value=valor, variable=self.v["modo"]).pack(anchor="w")

        linha = ttk.Frame(quadro)
        linha.grid(row=3, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(linha, text="Pedir confirmação antes de enviar; descartar após",
                        variable=self.v["confirmar"]).pack(side="left")
        ttk.Spinbox(linha, from_=1, to=30, width=3, textvariable=self.v["espera"]).pack(side="left")
        ttk.Label(linha, text=" s").pack(side="left")
        linha = ttk.Frame(quadro)
        linha.grid(row=4, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Label(linha, text="Tempo máximo entre o livro e o capítulo: ").pack(side="left")
        ttk.Spinbox(linha, from_=1, to=15, width=3, textvariable=self.v["janela"]).pack(side="left")
        ttk.Label(linha, text=" s").pack(side="left")

        principal = ttk.LabelFrame(quadro, text="Texto principal do sermão", padding=8)
        principal.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        linha = ttk.Frame(principal)
        linha.pack(anchor="w")
        ttk.Entry(linha, textvariable=self.v["principal"], width=24).pack(side="left")
        ttk.Label(linha, textvariable=self.lido).pack(side="left", padx=8)
        linha = ttk.Frame(principal)
        linha.pack(anchor="w", pady=(4, 0))
        ttk.Label(linha, text="Voltar a ele ").pack(side="left")
        ttk.Spinbox(linha, from_=5, to=900, width=4, textvariable=self.v["retorno"]).pack(side="left")
        ttk.Label(linha, text=" s depois de outra citação").pack(side="left")

        manual = ttk.LabelFrame(quadro, text="Enviar uma passagem", padding=8)
        manual.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        linha = ttk.Frame(manual)
        linha.pack(anchor="w")
        campo = ttk.Entry(linha, textvariable=self.digitado, width=24)
        campo.pack(side="left")
        campo.bind("<Return>", lambda _: self._enviar_digitado(False))
        ttk.Button(linha, text="Selecionar (Enter)",
                   command=lambda: self._enviar_digitado(False)).pack(side="left", padx=(8, 0))
        ttk.Button(linha, text="Projetar",
                   command=lambda: self._enviar_digitado(True)).pack(side="left", padx=(4, 0))
        ttk.Label(manual, textvariable=self.entendido).pack(anchor="w", pady=(4, 0))
        self.digitado.trace_add("write", self._ler_digitado)

        if self.v["transcricao"].get():
            linha = ttk.Frame(quadro)
            linha.grid(row=7, column=0, columnspan=2, sticky="w", pady=(8, 0))
            ttk.Label(linha, text="Salvar a transcrição em ").pack(side="left")
            ttk.Entry(linha, textvariable=self.v["pasta"], width=30).pack(side="left")
            ttk.Button(linha, text="Escolher…", command=self._escolher_pasta).pack(
                side="left", padx=(4, 0))

        rede = ttk.LabelFrame(quadro, text="Holyrics (API Server)", padding=8)
        rede.grid(row=8, column=0, columnspan=2, sticky="ew", pady=8)
        for coluna, (texto, chave, largura) in enumerate((("IP", "host", 15), ("Porta", "porta", 6),
                                                          ("Token", "token", 18))):
            ttk.Label(rede, text=texto).grid(row=0, column=2 * coluna, padx=(0, 4))
            ttk.Entry(rede, textvariable=self.v[chave], width=largura).grid(
                row=0, column=2 * coluna + 1, padx=(0, 10))

        for linha, variavel in enumerate((self.estado, self.ouvido, self.envio), start=9):
            ttk.Label(quadro, textvariable=variavel, width=58).grid(row=linha, column=0,
                                                                    columnspan=2, sticky="w")

    def _inteiro(self, chave):
        try:
            return max(1, int(self.v[chave].get()))
        except ValueError:
            return PADRAO[chave]

    def _salvar(self, *_):
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps({chave: v.get() for chave, v in self.v.items()}, indent=2,
                                     ensure_ascii=False), encoding="utf-8")

    def _escolher_pasta(self):
        pasta = filedialog.askdirectory(initialdir=self.v["pasta"].get() or None)
        if pasta:
            self.v["pasta"].set(os.path.normpath(pasta))

    def _mudar_principal(self, *_):
        texto = self.v["principal"].get().strip()
        ref = ler(texto)
        self.principal = (ref.livro, ref.capitulo, ref.versiculo) if ref and ref.capitulo else None
        if self.principal:
            self.detector.situar(*self.principal)
            self.lido.set(f"→ {rotulo(*self.principal)}")
        else:
            self.lido.set("não entendi" if texto else "ex.: 2 Coríntios 4:1")

    def _ler_digitado(self, *_):
        texto = self.digitado.get().strip()
        ref = ler(texto)
        self.entendido.set(f"→ {ref}" if ref else "não entendi" if texto else EXEMPLO_DIGITADO)

    def _enviar_digitado(self, projetar):
        """Envia a passagem digitada, inteira, como foi escrita: o modo não a corta. Funciona
        mesmo com o aplicativo desativado. Passa a valer como a última citação ouvida."""
        ref = ler(self.digitado.get())
        if not ref:
            self.entendido.set("não entendi")
            return
        versiculo = ref.versiculo or (1 if projetar else None)
        self._cancelar()
        if ref.capitulo:
            self.detector.situar(ref.livro, ref.capitulo, versiculo)  # "versículo 29" continua
        self._marcar_volta(ref)
        self.alvo = (ref.livro, ref.capitulo, versiculo, ref.fim if projetar else None, projetar)
        self._enviar(self.alvo, " (digitado)")

    def _recorte(self, capitulo, versiculo):
        """O capítulo e o versículo que o modo escolhido deixa passar."""
        modo = self.v["modo"].get()
        return capitulo if modo != "l" else None, versiculo if modo in ("lcv", "projeta") else None

    def _mudar_modo(self, *_):
        ligado = self.motor is not None or self.tentativa is not None
        if ligado != (self.v["modo"].get() != "off"):
            self._reiniciar()
        self._cancelar()
        self.alvo = None

    def _reiniciar(self, *_):
        if self.tentativa:
            self.raiz.after_cancel(self.tentativa)
            self.tentativa = None
        parado = True
        if self.motor:
            self.motor.parar()
            self.motor.join(3)
            parado = not self.motor.is_alive()
            self.motor = None
        self._cancelar()
        self.alvo = None
        self.inicio = None  # a frase em curso morreu com o motor
        self.detector = Detector(self._inteiro("janela"))
        if self.principal:
            self.detector.situar(*self.principal)
        if parado:  # o PortAudio só enxerga dispositivos ligados depois se for reiniciado
            sd._terminate()
            sd._initialize()
            self.entradas = microfones()
        nome = self.v["motor"].get()
        # O reconhecimento do Windows só ouve o microfone padrão do sistema.
        self.caixa_microfone.configure(values=list(self.entradas),
                                       state="disabled" if nome == "Windows" else "readonly")
        if self.v["modo"].get() == "off":
            self.estado.set("Desativado")
            return
        microfone = self.v["microfone"].get()  # vazio = o padrão do Windows
        if nome != "Windows" and microfone and microfone not in self.entradas:
            self._falhou(f"microfone “{microfone}” não encontrado")
            return
        self.estado.set(f"Carregando {nome}…")
        fila = self.fila
        self.motor = motor = MOTORES[nome](
            self.entradas.get(microfone),
            lambda texto, final: fila.put((motor, "ouvido", texto, final, time.monotonic())),
            lambda erro: fila.put((motor, "falha", erro)))
        motor.start()

    def _falhou(self, erro):
        self.estado.set(f"Erro: {erro}. Tentando de novo…")
        self.tentativa = self.raiz.after(TENTAR_DE_NOVO, self._reiniciar)

    def _tique(self):
        try:
            while True:
                motor, tipo, *dados = self.fila.get_nowait()
                if tipo == "envio":
                    self.envio.set(dados[0])
                    if dados[1] == self.alvo:  # falhou: a mesma citação, repetida, tenta de novo
                        self.alvo = None
                elif motor is not self.motor:
                    continue  # sobra de um motor já trocado
                elif tipo == "falha":
                    self._falhou(dados[0])
                else:
                    self._ouvido(*dados)
        except queue.Empty:
            pass
        finally:  # um erro ao tratar uma fala não pode parar o laço
            self.raiz.after(50, self._tique)
        if self.motor and self.motor.pronto.is_set() and self.estado.get().startswith("Carregando"):
            self.estado.set(f"Ouvindo ({self.v['motor'].get()})")

    def _ouvido(self, texto, final, quando):
        if texto:
            self.ouvido.set(f"Ouvido: {texto[-60:]}")
            self.inicio = self.inicio or datetime.now()
        if final:
            if texto:
                self._transcrever(texto)
            self.inicio = None
        ref = self.detector.ouvir(texto, final, quando)
        if not ref:
            return
        self._marcar_volta(ref)
        projetar = self.v["modo"].get() == "projeta" and ref.completa
        alvo = (ref.livro, *self._recorte(ref.capitulo, ref.versiculo),
                ref.fim if projetar else None, projetar)
        if alvo == self.alvo:
            return
        self._cancelar()
        self.alvo = alvo
        if self.v["confirmar"].get():
            self._perguntar(alvo)
        elif projetar:
            self.pendente = self.raiz.after(ASSENTAR, self._enviar, alvo)
        else:
            self._enviar(alvo)

    def _transcrever(self, texto):
        """Acrescenta a fala, com a hora em que começou, ao arquivo do dia."""
        pasta = self.v["pasta"].get().strip()
        if not pasta or not self.v["transcricao"].get():
            return
        try:
            with open(Path(pasta) / f"Transcrição {self.inicio:%Y-%m-%d}.txt", "a",
                      encoding="utf-8") as arquivo:
                arquivo.write(f"[{self.inicio:%H:%M:%S}] {texto}\n")
        except OSError as erro:
            self.envio.set(f"Transcrição não gravada: {erro}")

    def _marcar_volta(self, ref):
        """Citação dentro do texto principal o faz avançar; fora dele, arma a volta."""
        if self.volta:
            self.raiz.after_cancel(self.volta)
            self.volta = None
        if not self.principal:
            return
        if (ref.livro, ref.capitulo) == self.principal[:2]:
            self.principal = ref.livro, ref.capitulo, ref.versiculo or self.principal[2]
            self.lido.set(f"→ {rotulo(*self.principal)}")
        else:
            self.volta = self.raiz.after(self._inteiro("retorno") * 1000, self._voltar)

    def _voltar(self, esperou=0):
        self.volta = None
        if not self.principal or self.v["modo"].get() == "off":
            return
        # O preletor no meio de uma frase, ou uma citação a caminho do Holyrics (esperando para
        # projetar ou no aviso de confirmação): o que ele está dizendo prevalece. A volta espera
        # a pausa; se a frase trouxer outra citação, a contagem recomeça do zero.
        if (self.inicio or self.pendente) and esperou < ADIAR_MAX:
            self.volta = self.raiz.after(ADIAR, self._voltar, esperou + ADIAR)
            return
        self.detector.situar(*self.principal)
        self._cancelar()
        self.alvo = (self.principal[0], *self._recorte(*self.principal[1:]), None, False)
        self._enviar(self.alvo, " (texto principal)")

    def _enviar(self, alvo, nota=""):
        self.pendente = None
        livro, capitulo, versiculo, fim, projetar = alvo
        texto = rotulo(livro, capitulo, versiculo, fim) + nota
        destino = self.v["host"].get().strip(), self._inteiro("porta"), self.v["token"].get().strip()
        if not destino[0]:
            self.envio.set(f"{texto}: falta o IP do Holyrics")
            self.alvo = None
            return
        self.envios.put((destino, alvo, texto))

    def _despachar(self):
        """Envia um pedido por vez, em ordem. Se acumularem, só o mais recente interessa."""
        while True:
            pedido = self.envios.get()
            while not self.envios.empty():
                pedido = self.envios.get()
            destino, alvo, texto = pedido
            livro, capitulo, versiculo, fim, projetar = alvo
            try:
                if projetar:
                    holyrics.projetar(*destino, livro, capitulo, versiculo, fim)
                else:
                    holyrics.selecionar(*destino, livro, capitulo, versiculo)
                resultado, falhou = f"{'Projetado' if projetar else 'Selecionado'}: {texto}", None
            except Exception as erro:
                resultado, falhou = f"Falhou ({texto}): {erro}", alvo
            self.fila.put((None, "envio", resultado, falhou))

    def _perguntar(self, alvo):
        self.aviso = aviso = tk.Toplevel(self.raiz)
        aviso.overrideredirect(True)
        aviso.attributes("-topmost", True)
        quadro = ttk.Frame(aviso, padding=12, relief="solid", borderwidth=1)
        quadro.pack()
        ttk.Label(quadro, text=rotulo(*alvo[:4]), font=("Segoe UI", 16, "bold")).pack()
        ttk.Label(quadro, text="Projetar no Holyrics?" if alvo[4] else "Selecionar no Holyrics?").pack()
        botoes = ttk.Frame(quadro)
        botoes.pack(pady=(8, 0))
        ttk.Button(botoes, text="Enviar (Enter)",
                   command=lambda: self._responder(alvo)).pack(side="left", padx=4)
        ttk.Button(botoes, text="Descartar (Esc)", command=self._responder).pack(side="left", padx=4)
        aviso.bind("<Return>", lambda _: self._responder(alvo))
        aviso.bind("<Escape>", lambda _: self._responder())
        aviso.update_idletasks()
        aviso.geometry(f"+{aviso.winfo_screenwidth() - aviso.winfo_reqwidth() - 24}"
                       f"+{aviso.winfo_screenheight() - aviso.winfo_reqheight() - 72}")
        aviso.focus_force()
        self.pendente = self.raiz.after(self._inteiro("espera") * 1000, self._responder)

    def _responder(self, alvo=None):
        """Fecha o aviso. Com alvo, envia; sem, descarta."""
        self._cancelar()
        if alvo:
            self._enviar(alvo)
        else:
            self.alvo = None  # a mesma citação, dita de novo, volta a perguntar

    def _cancelar(self):
        if self.pendente:
            self.raiz.after_cancel(self.pendente)
            self.pendente = None
        if self.aviso:
            self.aviso.destroy()
            self.aviso = None

    def _sair(self):
        if self.motor:
            self.motor.parar()
        self.raiz.destroy()


def main():
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # sem isso a janela fica borrada
    raiz = tk.Tk()
    raiz.title("Escriba")
    raiz.iconbitmap(default=ICONE)
    raiz.resizable(False, False)
    App(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
