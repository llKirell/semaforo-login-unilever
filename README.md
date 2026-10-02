# 🚦 Semáforo Login — Monitoreo LOGIN Unilever (W4W DINET)

Automatización **solo de consulta** que monitorea las ubicaciones con **LOGIN**
pendiente de la cuenta **UNILEVER** (CD HUACHIPA) en W4W DINET, las clasifica
con un semáforo por antigüedad, publica un **dashboard web** y envía un
**reporte a Telegram** — todo **automático cada 2 horas**.

- 🌐 **Dashboard (en vivo):** https://llkirell.github.io/semaforo-login-unilever/
- ☁️ **Corre en la nube** (GitHub Actions) — no depende de ninguna PC para verse.

---

## 🧭 Cómo funciona (arquitectura)

```
GitHub Actions (cada 2h)
  → Login a W4W (Playwright, sin descargar Excel)
  → Fija contexto HUACHIPA/UNILEVER por API (3 POST)
  → Consulta Inventario Saldo (API JSON)
  → Filtra ubicaciones LOGIN, agrupa por lote, calcula antigüedad + semáforo
  → Genera public/index.html  → GitHub Pages (dashboard público)
  → Envía imagen del reporte a Telegram
```

El "disparo" cada 2 horas hoy viene de una tarea en la PC (`disparar_nube.cmd`
vía `gh workflow run`) como **puente**, hasta que el cron nativo de GitHub
(`schedule` en el workflow) enganche solo. Ver más abajo.

**Reglas de negocio clave:**
- Ubicaciones monitoreadas: se definen en `config/ubicaciones.py` (lista
  editable: LOGIN, LOGI.*, varias X1.* y LOGIN.RC.*). Editable sin tocar la lógica.
- Antigüedad = días desde la fila más antigua de `FechaUltimoMovimiento`.
- Semáforo: 0-2 días = 🟢 | 3 = 🟡 | 4+ = 🔴 | sin fecha = OBSERVACIÓN.
- **Líneas** = combinaciones únicas Ubicación+Artículo+Lote. **Cajas** = suma de
  `CantidadFinalUMS`.

---

## 🔑 Secretos (en GitHub, no en el código)

En el repo → **Settings → Secrets and variables → Actions**:

| Secret | Qué es |
|---|---|
| `DINET_USER` | Usuario de DINET (login de app.dinet.com.pe) |
| `DINET_PASS` | Contraseña de DINET |
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram |
| `TELEGRAM_CHAT_ID` | ID del grupo de Telegram |

---

## ✏️ Modificar el proyecto desde CUALQUIER PC

Todo el código está en este repo. Para cambiar algo:

```bash
git clone https://github.com/llKirell/semaforo-login-unilever
cd semaforo-login-unilever
# editar lo que quieras...
git add -A
git commit -m "mi cambio"
git push
```
En la próxima corrida, la nube usa el código nuevo. (También puedes editar
archivos directo en github.com.)

## 💻 Correr el proyecto LOCALMENTE (opcional)

Solo si quieres probarlo en tu PC:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
copy .env.example .env      # y rellena DINET_USER, DINET_PASS, TELEGRAM_*
python cloud_run.py         # genera public/index.html y envía Telegram
```

---

## ⏰ Programación (cada 2 horas, horas impares)

- **Nube:** el workflow tiene `schedule: cron "0 */2 * * *"` (horas impares
  en Lima). En repos nuevos GitHub tarda en "engancharlo".
- **Puente (PC):** tarea de Windows `SemaforoLogin\TriggerNube` que corre
  `disparar_nube.cmd` cada 2h (horas impares) + `disparar_boot.cmd` al prender
  la PC. Cuando el cron nativo enganche (aparecerán corridas con evento
  `schedule` en Actions), desactivar el puente:
  ```powershell
  Disable-ScheduledTask -TaskName "TriggerNube" -TaskPath "\SemaforoLogin\"
  ```

---

## 📁 Archivos principales

| Archivo | Rol |
|---|---|
| `.github/workflows/actualizar.yml` | Workflow de GitHub Actions (cron + deploy Pages) |
| `cloud_run.py` | Entrypoint cloud: login → saldo → dashboard → Telegram |
| `config/settings.py` | Credenciales (.env / env) + endpoints W4W |
| `config/ubicaciones.py` | **Lista editable** de ubicaciones a monitorear |
| `src/w4w/` | Login, contexto y consulta de saldo (W4W) |
| `src/processor/login.py` | Filtro LOGIN, agrupación por lote, antigüedad, semáforo |
| `src/dashboard/generator.py` | Genera el dashboard HTML (tarjetas, tabla, filtros, Excel) |
| `src/dashboard/xlsx.py` | Escritor .xlsx sin librerías (para el botón Descargar Excel) |
| `src/telegram/` | Imagen del reporte + envío al grupo |
| `disparar_nube.cmd` / `disparar_boot.cmd` | Puente en la PC que dispara la nube |

> Los scripts de la versión "en PC" (`servidor.py`, `publicar.ps1`,
> `AUTO-RECUPERAR-SEMAFORO.ps1`, tareas, etc.) quedan para referencia, pero la
> operación actual es 100% en la nube.
