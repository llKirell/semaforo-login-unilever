@echo off
REM ------------------------------------------------------------------
REM  Wrapper para el Programador de tareas de Windows (Fase 7).
REM  Corre ejecutar.py usando el entorno virtual y deja un log.
REM  %~dp0 = carpeta donde esta este .bat (funciona la llamen de donde
REM  la llamen), asi las rutas siempre son correctas.
REM ------------------------------------------------------------------
cd /d "%~dp0"
if not exist logs mkdir logs

echo ================================================================ >> "logs\ejecucion.log"
echo [%date% %time%] Iniciando ejecucion automatica >> "logs\ejecucion.log"

".venv\Scripts\python.exe" ejecutar.py >> "logs\ejecucion.log" 2>&1

echo [%date% %time%] Fin (codigo de salida %errorlevel%) >> "logs\ejecucion.log"
