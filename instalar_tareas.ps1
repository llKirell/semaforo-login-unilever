# ==================================================================
#  instalar_tareas.ps1  -  Registra las 4 tareas programadas (Fase 7)
# ==================================================================
#  Horarios:
#    Lun-Vie : 09:00 (inicio), 13:00 (mediodia), 17:00 (cierre)
#    Sabado  : 11:30
#
#  Las tareas corren SOLO cuando el usuario ha iniciado sesion
#  (no requiere guardar contrasena). Ejecuta este script una vez.
# ==================================================================

$ErrorActionPreference = "Stop"
$bat = Join-Path $PSScriptRoot "ejecutar_tarea.bat"
$tr = "`"$bat`""              # ruta entre comillas para /TR
$folder = "SemaforoLogin"

Write-Host "Registrando tareas que ejecutan:" $bat

schtasks /Create /F /TN "$folder\Inicio_0900" /TR $tr /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 09:00
schtasks /Create /F /TN "$folder\Medio_1300"  /TR $tr /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 13:00
schtasks /Create /F /TN "$folder\Cierre_1700" /TR $tr /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 17:00
schtasks /Create /F /TN "$folder\Sabado_1130" /TR $tr /SC WEEKLY /D SAT /ST 11:30

Write-Host ""
Write-Host "Tareas creadas. Para verlas:  schtasks /Query /TN SemaforoLogin /FO LIST"
