# ==================================================================
#  publicar.ps1  -  Pone el dashboard online (PM2 + Tailscale Funnel)
# ==================================================================
#  Requisitos: DASHBOARD_USER y DASHBOARD_PASS ya definidos en .env.
#  Expone en:  https://cpu663.tail644cd7.ts.net/semaforo
#  NO toca la ruta "/" existente (dashboard Dinet en puerto 4000).
# ==================================================================

$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$srv = Join-Path $PSScriptRoot "servidor.py"

Write-Host "1) Arrancando el servidor bajo PM2..."
# Si ya existia, lo borramos (ignorando el aviso si no existe todavia).
try { pm2 delete semaforo-dashboard | Out-Null } catch {}
pm2 start "$srv" --name semaforo-dashboard --interpreter "$py"
try { pm2 save | Out-Null } catch {}

Write-Host "2) Exponiendo la ruta /semaforo con Tailscale Funnel..."
tailscale funnel --bg --set-path=/semaforo http://127.0.0.1:4100

Write-Host ""
Write-Host "LISTO. Dashboard online en:  https://cpu663.tail644cd7.ts.net/semaforo"
Write-Host "Entra con el usuario/clave de DASHBOARD_USER / DASHBOARD_PASS."
