@echo off
rem Gera dist\Escriba\ (executavel + modelos). Copie a pasta inteira para o PC do culto.
.venv\Scripts\python -m PyInstaller --noconfirm --windowed --name "Escriba" ^
  --icon logo\escriba.ico --add-data "logo\escriba.ico;logo" ^
  --add-data "modelos;modelos" --collect-all vosk --collect-all sherpa_onnx --collect-all winrt app.py
