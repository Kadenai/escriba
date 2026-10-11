@echo off
rem Remove o Escriba. As configuracoes em %APPDATA%\Escriba ficam guardadas.
setlocal
set "DESTINO=%~dp0"
set "DESTINO=%DESTINO:~0,-1%"
rem So age se estiver dentro da pasta de instalacao: a pasta inteira e apagada no fim.
if not exist "%DESTINO%\_internal\modelos" exit /b 1

taskkill /im "Escriba.exe" /f >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "foreach ($pasta in 'Desktop', 'Programs', 'Startup') { Remove-Item (Join-Path ([Environment]::GetFolderPath($pasta)) 'Escriba.lnk') -ErrorAction SilentlyContinue }"
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\Escriba" /f >nul 2>&1

rem Um arquivo em uso nao se apaga: outro cmd espera este terminar e remove a pasta.
cd /d "%TEMP%"
start "" /min cmd /c "ping -n 3 127.0.0.1 >nul & rmdir /s /q "%DESTINO%""
