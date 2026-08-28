# ==================================================================
#  validar.ps1  -  Revisa de un golpe que todo este funcionando
# ==================================================================
#  Ejecutalo despues de prender la PC para confirmar que todo levanto.
# ==================================================================

Set-Location $PSScriptRoot
$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
Write-Host "======== Validacion Semaforo Login ========" -ForegroundColor Cyan

# 1) Servidor en PM2
$pmpid = (pm2 pid semaforo-dashboard 2>$null | Select-Object -First 1)
if ($pmpid -and $pmpid -ne "0") { Write-Host "[OK ] Servidor PM2 online (pid $pmpid)" -ForegroundColor Green }
else { Write-Host "[X  ] Servidor NO esta en PM2  ->  corre:  .\publicar.ps1" -ForegroundColor Red }

# 2) El servidor responde en local (401 = arriba y pidiendo login)
try {
    Invoke-WebRequest -Uri "http://127.0.0.1:4100/" -UseBasicParsing -TimeoutSec 8 | Out-Null
    Write-Host "[OK ] Servidor responde en :4100" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 401) { Write-Host "[OK ] Servidor responde en :4100 (pide login)" -ForegroundColor Green }
    else { Write-Host "[X  ] Servidor no responde en :4100" -ForegroundColor Red }
}

# 3) Funnel de Tailscale con la ruta /semaforo
if ((tailscale funnel status 2>$null | Out-String) -match "/semaforo") { Write-Host "[OK ] Tailscale Funnel /semaforo activo" -ForegroundColor Green }
else { Write-Host "[X  ] Funnel /semaforo no activo  ->  corre:  .\publicar.ps1" -ForegroundColor Red }

# 4) Ultima corrida registrada
& $py -c "from src.database.db import get_conn; c=get_conn(); r=c.execute('SELECT fecha,hora,tipo_ejecucion,estado,total_cajas,total_lineas FROM ejecucion ORDER BY id DESC LIMIT 1').fetchone(); print('[OK ] Ultima corrida: {} {} ({}) estado={} | {} cjs / {} lineas'.format(r['fecha'],r['hora'],r['tipo_ejecucion'],r['estado'],r['total_cajas'],r['total_lineas'])) if r else print('[!  ] Aun no hay corridas registradas')"

# 5) Tareas programadas
Write-Host ""
Write-Host "Proximas corridas programadas:" -ForegroundColor Cyan
schtasks /Query /TN "SemaforoLogin\Inicio_0900" /FO LIST /V 2>$null | Select-String "Hora pr" | ForEach-Object { $_.ToString().Trim() }
schtasks /Query /TN "SemaforoLogin\Medio_1300"  /FO LIST /V 2>$null | Select-String "Hora pr" | ForEach-Object { $_.ToString().Trim() }
schtasks /Query /TN "SemaforoLogin\Cierre_1700" /FO LIST /V 2>$null | Select-String "Hora pr" | ForEach-Object { $_.ToString().Trim() }

Write-Host ""
Write-Host "URL:  https://cpu663.tail644cd7.ts.net/semaforo" -ForegroundColor Yellow
