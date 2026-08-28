# ==================================================================
#  autonomia.ps1  -  Deja el sistema 100% autonomo al prender la PC
# ==================================================================
#  1) Crea una tarea "Al iniciar sesion" que revive PM2 (todos los
#     dashboards) 45s despues de entrar.
#  2) Marca las 4 corridas programadas para que se ejecuten aunque
#     la PC se prenda despues de la hora (StartWhenAvailable).
#  3) Guarda la lista actual de PM2.
# ==================================================================

$ErrorActionPreference = "Continue"
$cmd = Join-Path $PSScriptRoot "iniciar_pm2.cmd"

Write-Host "1) Instalando lanzador en la carpeta Inicio (revive PM2 al entrar, sin admin)..."
$startup = [Environment]::GetFolderPath('Startup')
$vbs = Join-Path $startup "semaforo_pm2_startup.vbs"
$contenido = @"
' Lanzador de arranque (carpeta Inicio de Windows) - sin ventana visible.
Set sh = CreateObject("WScript.Shell")
sh.Run "cmd /c ""$cmd""", 0, False
"@
Set-Content -Path $vbs -Value $contenido -Encoding ASCII
Write-Host "   OK: $vbs"

Write-Host "2) Marcando las corridas para ejecutarse aunque se pierda la hora..."
foreach ($t in @("Inicio_0900","Medio_1300","Cierre_1700","Sabado_1130")) {
    try {
        $st = Get-ScheduledTask -TaskName $t -TaskPath "\SemaforoLogin\" -ErrorAction Stop
        $st.Settings.StartWhenAvailable = $true
        Set-ScheduledTask -TaskName $t -TaskPath "\SemaforoLogin\" -Settings $st.Settings | Out-Null
        Write-Host "   OK: $t (se ejecutara si se perdio la hora)."
    } catch {
        Write-Host "   (aviso) No pude ajustar $t : $($_.Exception.Message)"
    }
}

Write-Host "3) Guardando lista de PM2..."
try { pm2 save | Out-Null; Write-Host "   OK: pm2 save." } catch { Write-Host "   (aviso) pm2 save fallo." }

Write-Host ""
Write-Host "LISTO. Al prender la PC e iniciar sesion, en ~45s se levantan los dashboards,"
Write-Host "y las corridas de las 09:00/13:00/17:00 (sab 11:30) corren solas (o al arrancar si se perdio la hora)."
