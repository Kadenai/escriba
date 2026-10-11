"""Monta dist/Instalar Escriba.exe a partir de dist/Escriba (rode empacotar.bat antes).

O instalador é um pacote autoextraível do IExpress, que já vem no Windows: leva o app
compactado, instalar.cmd e desinstalar.cmd, e roda instalar.cmd depois de extrair.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

AQUI = Path(__file__).parent
DIST = AQUI.parent / "dist"
SAIDA = DIST / "Instalar Escriba.exe"

# Com o ponto: o cmd pode estar proibido de procurar scripts na pasta atual. E o mesmo comando
# vale para a instalação silenciosa (/Q): sem ele, o IExpress em português trava nesse modo.
COMANDO = r"cmd /c .\instalar.cmd"

SED = """[Version]
Class=IEXPRESS
SEDVersion=3
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=0
HideExtractAnimation=0
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=%InstallPrompt%
DisplayLicense=%DisplayLicense%
FinishMessage=%FinishMessage%
TargetName=%TargetName%
FriendlyName=%FriendlyName%
AppLaunched=%AppLaunched%
PostInstallCmd=%PostInstallCmd%
AdminQuietInstCmd=%AdminQuietInstCmd%
UserQuietInstCmd=%UserQuietInstCmd%
SourceFiles=SourceFiles
[Strings]
InstallPrompt=Instalar o Escriba neste computador?
FinishMessage=Escriba instalado. Use o atalho criado no desktop ou no menu Iniciar.
TargetName={saida}
FriendlyName=Escriba
AppLaunched={comando}
PostInstallCmd=<None>
AdminQuietInstCmd={comando}
UserQuietInstCmd={comando}
DisplayLicense=
FILE0="Escriba.zip"
FILE1="instalar.cmd"
FILE2="desinstalar.cmd"
[SourceFiles]
SourceFiles0={pasta}\\
[SourceFiles0]
%FILE0%=
%FILE1%=
%FILE2%=
"""

with tempfile.TemporaryDirectory() as pasta:
    pasta = Path(pasta)
    shutil.make_archive(str(pasta / "Escriba"), "zip", DIST / "Escriba")
    for nome in ("instalar.cmd", "desinstalar.cmd"):
        shutil.copy(AQUI / nome, pasta)
    sed = pasta / "instalador.sed"
    # Sem acentos nos textos: o IExpress os grava na página de código de quem monta.
    sed.write_text(SED.format(saida=SAIDA, pasta=pasta, comando=COMANDO), encoding="ascii")
    SAIDA.unlink(missing_ok=True)
    subprocess.run(["iexpress", "/N", "/Q", str(sed)], check=True)
if not SAIDA.exists():
    raise SystemExit("O IExpress não gerou o instalador.")
print(f"{SAIDA} ({SAIDA.stat().st_size / 2**20:.0f} MB)")
