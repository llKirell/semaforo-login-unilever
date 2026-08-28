# ==================================================================
#  desinstalar_tareas.ps1  -  Elimina las tareas programadas (Fase 7)
# ==================================================================
$folder = "SemaforoLogin"
foreach ($t in @("Inicio_0900", "Medio_1300", "Cierre_1700", "Sabado_1130")) {
    schtasks /Delete /F /TN "$folder\$t"
}
Write-Host "Tareas de SemaforoLogin eliminadas."
