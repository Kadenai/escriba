"""Motores de fala. Cada um chama ao_ouvir(texto acumulado da fala atual, final?)."""

import asyncio
import json
import os
import sys
import tempfile
import threading
from pathlib import Path

from detector import vocabulario

# As bibliotecas de fala abrem arquivos pela página de código do Windows e se perdem se a pasta
# do app tiver acento. Por isso os motores entram em MODELOS e usam caminhos relativos.
MODELOS = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "modelos"
TAXA = 16000
BLOCO = TAXA // 10  # 100 ms de áudio por leitura


class _Motor(threading.Thread):
    def __init__(self, microfone, ao_ouvir, ao_falhar):
        super().__init__(daemon=True)
        self.microfone = microfone  # índice do dispositivo; None = padrão do Windows
        self.ao_ouvir = ao_ouvir
        self.ao_falhar = ao_falhar
        self._parar = threading.Event()
        self.pronto = threading.Event()  # já está ouvindo

    def parar(self):
        self._parar.set()

    def run(self):
        try:
            self._ouvir()
        except Exception as erro:
            self.ao_falhar(erro)


class _MotorComMicrofone(_Motor):
    """Motores que recebem o áudio do microfone escolhido."""

    def _ouvir(self):
        import sounddevice as sd
        anterior = None
        # O microfone abre antes do modelo: se ele faltar, a falha vem na hora, sem carga à toa.
        with sd.RawInputStream(samplerate=TAXA, blocksize=BLOCO, device=self.microfone,
                               dtype="int16", channels=1) as entrada:
            self.carregar()
            self.pronto.set()
            while not self._parar.is_set():
                atual = self.reconhecer(bytes(entrada.read(BLOCO)[0]))
                if atual != anterior and (atual[0] or atual[1]):
                    self.ao_ouvir(*atual)
                anterior = atual


class MotorVosk(_MotorComMicrofone):
    def carregar(self):
        import vosk
        vosk.SetLogLevel(-1)
        os.chdir(MODELOS)
        # Sem vocabulário restrito: com ele, a fala comum era forçada a virar nome de livro.
        self._rec = vosk.KaldiRecognizer(vosk.Model("vosk-pt"), TAXA)

    def reconhecer(self, pcm):
        if self._rec.AcceptWaveform(pcm):
            return json.loads(self._rec.Result())["text"], True
        return json.loads(self._rec.PartialResult())["partial"], False


class MotorSherpa(_MotorComMicrofone):
    def carregar(self):
        import sherpa_onnx
        os.chdir(MODELOS)
        self._rec = sherpa_onnx.OnlineRecognizer.from_transducer(
            tokens="sherpa-pt/tokens.txt", encoder="sherpa-pt/encoder.onnx",
            decoder="sherpa-pt/decoder.onnx", joiner="sherpa-pt/joiner.onnx",
            # Uma thread: com mais, elas ficam girando à espera de áudio e gastam um núcleo à toa.
            num_threads=1, enable_endpoint_detection=True)
        self._fala = self._rec.create_stream()

    def reconhecer(self, pcm):
        import numpy as np
        amostras = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768
        self._fala.accept_waveform(TAXA, amostras)
        while self._rec.is_ready(self._fala):
            self._rec.decode_stream(self._fala)
        texto = self._rec.get_result(self._fala)
        final = self._rec.is_endpoint(self._fala)
        if final:
            self._rec.reset(self._fala)
        return texto, final


class MotorWindows(_Motor):
    """Reconhecimento do próprio Windows. Usa sempre o microfone padrão do sistema."""

    IDIOMA = "pt-BR"

    def _ouvir(self):
        asyncio.run(self._sessao())

    async def _sessao(self):
        from winrt.windows.globalization import Language
        from winrt.windows.media.speechrecognition import (
            SpeechRecognitionConfidence, SpeechRecognitionGrammarFileConstraint,
            SpeechRecognitionResultStatus, SpeechRecognizer)
        from winrt.windows.storage import StorageFile

        try:
            rec = SpeechRecognizer(Language(self.IDIOMA))
        except OSError as erro:
            raise RuntimeError("Instale a fala em português (Brasil) no Windows.") from erro
        caminho = Path(tempfile.gettempdir()) / "escriba.grxml"
        caminho.write_text(self.gramatica(), encoding="utf-8")
        arquivo = await StorageFile.get_file_from_path_async(str(caminho))
        rec.constraints.append(SpeechRecognitionGrammarFileConstraint(arquivo))
        compilada = await rec.compile_constraints_async()
        if compilada.status != SpeechRecognitionResultStatus.SUCCESS:
            raise RuntimeError(f"O Windows recusou a gramática ({compilada.status.name}).")

        def resultado(_, evento):
            if evento.result.confidence != SpeechRecognitionConfidence.REJECTED:
                self.ao_ouvir(evento.result.text, True)

        encerrou = asyncio.Event()
        laco = asyncio.get_running_loop()
        sessao = rec.continuous_recognition_session
        sessao.add_result_generated(resultado)
        sessao.add_completed(lambda *_: laco.call_soon_threadsafe(encerrou.set))
        while not self._parar.is_set():  # o Windows encerra a sessão no silêncio; reabre
            encerrou.clear()
            await sessao.start_async()
            self.pronto.set()
            while not self._parar.is_set() and not encerrou.is_set():
                await asyncio.sleep(0.1)
        if not encerrou.is_set():
            await sessao.stop_async()

    def gramatica(self):
        itens = "".join(f"<item>{p}</item>" for p in vocabulario())
        return ('<?xml version="1.0" encoding="UTF-8"?>'
                f'<grammar version="1.0" xml:lang="{self.IDIOMA}" root="fala" '
                'xmlns="http://www.w3.org/2001/06/grammar"><rule id="fala" scope="public">'
                f'<item repeat="1-12"><one-of>{itens}'
                '<item><ruleref special="GARBAGE"/></item></one-of></item></rule></grammar>')


MOTORES = {"sherpa-onnx": MotorSherpa, "Vosk": MotorVosk, "Windows": MotorWindows}
