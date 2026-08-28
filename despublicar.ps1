# ==================================================================
#  despublicar.ps1  -  Quita el dashboard de internet
# ==================================================================
#  Detiene el servidor PM2 y elimina SOLO la ruta /semaforo del Funnel
#  (la ruta "/" del dashboard Dinet queda intacta).
# ==================================================================

Write-Host "Quitando la ruta /semaforo del Funnel..."
tailscale funnel --set-path=/semaforo off 2>$null

Write-Host "Deteniendo el servidor PM2..."
pm2 delete semaforo-dashboard 2>$null
pm2 save 2>$null | Out-Null

Write-Host "Listo. El dashboard ya no esta online (la ruta / de Dinet sigue igual)."
