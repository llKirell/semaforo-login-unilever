# ==================================================================
#  AUTO-RECUPERAR-SEMAFORO.ps1
#  Arranque autonomo del dashboard del Semaforo (modelado sobre el
#  AUTO-RECUPERAR-DASHBOARD.ps1 de Dinet, que si funciona).
#  Espera a Tailscale, garantiza el servidor PM2 del semaforo y aplica
#  el funnel en la ruta /semaforo. Deja log en temp\auto-start.
# ==================================================================

$ErrorActionPreference = 'Stop'

$proj    = 'C:\Users\ctrlreckcc\Desktop\erik proyectos\Semaforo Login'
$py      = Join-Path $proj '.venv\Scripts\python.exe'
$server  = Join-Path $proj 'servidor.py'
$pm2Exe  = 'C:\Users\ctrlreckcc\AppData\Roaming\npm\pm2.cmd'
$tailscaleExe = 'C:\Program Files\Tailscale\tailscale.exe'
$tailscaleIpnExe = 'C:\Program Files\Tailscale\tailscale-ipn.exe'
$healthUrl = 'http://127.0.0.1:4100/'   # el server pide login: 401 = arriba
$logDir  = Join-Path $proj 'temp\auto-start'
$logFile = Join-Path $logDir ("auto-semaforo-" + (Get-Date -Format 'yyyyMMdd') + ".log")

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
function Write-Log($m){ Add-Content -Path $logFile -Value ("[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m) }

function Test-Health {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 4
    return $r.StatusCode -eq 200
  } catch {
    try { return ($_.Exception.Response.StatusCode.value__ -eq 401) } catch { return $false }
  }
}

function Wait-Health($seconds){
  $deadline = (Get-Date).AddSeconds($seconds)
  while ((Get-Date) -lt $deadline) { if (Test-Health) { return $true }; Start-Sleep -Seconds 2 }
  return $false
}

function Ensure-TailscaleIpn {
  $ipn = Get-Process tailscale-ipn -ErrorAction SilentlyContinue
  if (-not $ipn -and (Test-Path $tailscaleIpnExe)) {
    Write-Log 'Iniciando tailscale-ipn.exe'
    Start-Process -FilePath $tailscaleIpnExe -WindowStyle Hidden | Out-Null
    Start-Sleep -Seconds 6
  }
}

function Wait-Tailscale($seconds){
  if (-not (Test-Path $tailscaleExe)) { return $false }
  $deadline = (Get-Date).AddSeconds($seconds)
  while ((Get-Date) -lt $deadline) {
    try {
      $out = (& $tailscaleExe status 2>&1 | Out-String).Trim()
      if ($LASTEXITCODE -eq 0 -and $out -and $out -notmatch 'NoState|starting|Logged out') { Write-Log 'Tailscale listo.'; return $true }
    } catch {}
    Start-Sleep -Seconds 5
  }
  return $false
}

function Ensure-Server {
  if (Test-Health) { Write-Log 'El semaforo ya responde en 127.0.0.1:4100.'; return $true }

  if (Test-Path $pm2Exe) {
    Write-Log 'Intentando reiniciar semaforo-dashboard con PM2.'
    try { & $pm2Exe restart semaforo-dashboard *> $null } catch {}
    if (Wait-Health 30) { Write-Log 'Recuperado con PM2 restart.'; return $true }

    Write-Log 'No existia o no respondio; creando con PM2 start.'
    try { & $pm2Exe start "$server" --name semaforo-dashboard --interpreter "$py" --cwd "$proj" *> $null } catch { Write-Log ('PM2 start excepcion: ' + $_.Exception.Message) }
    if (Wait-Health 40) {
      Write-Log 'Semaforo iniciado con PM2 start.'
      try { & $pm2Exe save *> $null; Write-Log 'PM2 save ok.' } catch {}
      return $true
    }
  }
  Write-Log 'No se pudo levantar el semaforo automaticamente.'
  return $false
}

function Ensure-Funnel {
  if (-not (Test-Path $tailscaleExe)) { return $false }
  Write-Log 'Aplicando funnel /semaforo -> 127.0.0.1:4100'
  try {
    & $tailscaleExe funnel --bg --set-path=/semaforo http://127.0.0.1:4100 *> $null
    if ($LASTEXITCODE -eq 0) { Write-Log 'Funnel /semaforo activo.'; return $true }
  } catch { Write-Log ('Funnel fallo: ' + $_.Exception.Message) }
  return $false
}

Write-Log '--- Inicio recuperacion Semaforo ---'
Start-Sleep -Seconds 20
Ensure-TailscaleIpn
$tsReady = Wait-Tailscale 120
$srvReady = Ensure-Server
if ($srvReady) {
  if ($tsReady) { Ensure-Funnel | Out-Null } else { Write-Log 'Se omite funnel: Tailscale no quedo listo.' }
} else {
  Write-Log 'Se omite funnel: el servidor no quedo listo.'
}
Write-Log '--- Fin recuperacion Semaforo ---'
