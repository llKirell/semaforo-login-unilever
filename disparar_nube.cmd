@echo off
REM ------------------------------------------------------------------
REM  disparar_nube.cmd  -  Dispara el workflow en la nube (GitHub)
REM  Puente cada 2h hasta que el cron NATIVO de GitHub enganche solo.
REM  Usa gh (ya autenticado). El trabajo pesado corre en la nube.
REM ------------------------------------------------------------------
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] Disparando workflow en la nube... >> "%~dp0logs\trigger.log"
"C:\Program Files\GitHub CLI\gh.exe" workflow run actualizar.yml --repo llKirell/semaforo-login-unilever >> "%~dp0logs\trigger.log" 2>&1
echo [%date% %time%] Fin (codigo %errorlevel%) >> "%~dp0logs\trigger.log"
