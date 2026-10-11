@echo off
rem Instala o Escriba: copia os arquivos, cria os atalhos e registra a desinstalacao.
rem Roda de dentro do instalador, ao lado de "Escriba.zip" e de desinstalar.cmd.
setlocal
title Escriba
echo Instalando o Escriba. Aguarde, leva cerca de um minuto...
taskkill /im "Escriba.exe" /f >nul 2>&1

rem Ate outubro de 2026 o app se chamava Bible Crawler: tira a instalacao antiga e herda a
rem configuracao dela (microfone, IP e token do Holyrics). Se ela abria junto com o
rem Windows, o Escriba passa a abrir tambem.
set "PASTAS='Desktop', 'Programs'"
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Bible Crawler.lnk" set "PASTAS=%PASTAS%, 'Startup'"
for %%P in ("C:\Bible Crawler" "%LOCALAPPDATA%\Programs\Bible Crawler") do if exist "%%~P\desinstalar.cmd" cmd /c ""%%~P\desinstalar.cmd""
if not exist "%APPDATA%\Escriba\config.json" if exist "%APPDATA%\Bible Crawler\config.json" (
  mkdir "%APPDATA%\Escriba" 2>nul
  copy /y "%APPDATA%\Bible Crawler\config.json" "%APPDATA%\Escriba\" >nul
)

rem Pasta curta e sem acento; se nao der para criar, cai na pasta de programas do usuario.
call :preparar "C:\Escriba" || call :preparar "%LOCALAPPDATA%\Programs\Escriba" || goto falha

set "TAR=%SystemRoot%\Sysnative\tar.exe"
if not exist "%TAR%" set "TAR=%SystemRoot%\System32\tar.exe"
"%TAR%" -xf "%~dp0Escriba.zip" -C "%DESTINO%" || goto falha
copy /y "%~dp0desinstalar.cmd" "%DESTINO%\" >nul || goto falha

powershell -NoProfile -ExecutionPolicy Bypass -Command "$w = New-Object -ComObject WScript.Shell; foreach ($pasta in %PASTAS%) { $a = $w.CreateShortcut((Join-Path ([Environment]::GetFolderPath($pasta)) 'Escriba.lnk')); $a.TargetPath = Join-Path $env:DESTINO 'Escriba.exe'; $a.WorkingDirectory = $env:DESTINO; $a.Save() }"

set "CHAVE=HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\Escriba"
reg add "%CHAVE%" /v DisplayName /d "Escriba" /f >nul
reg add "%CHAVE%" /v DisplayIcon /d "%DESTINO%\Escriba.exe" /f >nul
reg add "%CHAVE%" /v InstallLocation /d "%DESTINO%" /f >nul
reg add "%CHAVE%" /v UninstallString /d "\"%DESTINO%\desinstalar.cmd\"" /f >nul
reg add "%CHAVE%" /v NoModify /t REG_DWORD /d 1 /f >nul
reg add "%CHAVE%" /v NoRepair /t REG_DWORD /d 1 /f >nul

rem Com /d: aberto a partir daqui, o app prenderia a pasta temporaria do instalador.
start "" /d "%DESTINO%" "%DESTINO%\Escriba.exe"
exit /b 0

:preparar
rem So apaga a pasta se ela for uma instalacao anterior do Escriba.
if exist "%~1\_internal\modelos" rmdir /s /q "%~1"
mkdir "%~1" 2>nul
if not exist "%~1\" exit /b 1
set "DESTINO=%~1"
exit /b 0

:falha
echo.
echo A instalacao falhou. Feche o Escriba, se estiver aberto, e tente de novo.
pause
exit /b 1
