@echo off
REM ------------------------------------------------------------------
REM  disparar_boot.cmd  -  Dispara UNA corrida en la nube al prender la PC
REM  (se lanza desde la carpeta Inicio de Windows). Espera 90s a que la
REM  red y gh esten listos, luego llama al disparador normal.
REM ------------------------------------------------------------------
timeout /t 90 /nobreak >nul
call "%~dp0disparar_nube.cmd"
