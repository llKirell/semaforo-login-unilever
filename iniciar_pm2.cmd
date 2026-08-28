@echo off
REM ------------------------------------------------------------------
REM  iniciar_pm2.cmd  -  Arranque autonomo del dashboard del semaforo
REM  Se ejecuta al iniciar sesion (desde la carpeta Inicio de Windows).
REM
REM  NO usa "pm2 resurrect" a proposito: ese metodo se atasca si el
REM  daemon quedo corrupto por otros procesos (dinet). En su lugar
REM  garantiza el semaforo directamente: lo reinicia si existe, o lo
REM  crea si no. Asi arranca sin importar el estado del daemon.
REM ------------------------------------------------------------------

set "PROY=C:\Users\ctrlreckcc\Desktop\erik proyectos\Semaforo Login"
set "PM2=%APPDATA%\npm\pm2.cmd"

REM Espera a que el sistema, la red y Tailscale terminen de arrancar.
timeout /t 90 /nobreak >nul

cd /d "%PROY%"

REM Si el proceso ya existe, reiniciarlo (toma el codigo mas reciente).
call "%PM2%" restart semaforo-dashboard
REM Si no existia (errorlevel 1), crearlo desde cero.
if errorlevel 1 call "%PM2%" start "%PROY%\servidor.py" --name semaforo-dashboard --interpreter "%PROY%\.venv\Scripts\python.exe"
