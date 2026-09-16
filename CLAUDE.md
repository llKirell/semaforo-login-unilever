# CLAUDE.md — Contexto técnico del proyecto Semáforo Login

> Este archivo lo lee Claude Code automáticamente. Resume la arquitectura,
> el modelo de datos, las decisiones y cómo modificar cosas comunes, para
> retomar el proyecto desde cualquier PC/sesión sin re-investigar.

## Qué es

Robot **solo de consulta** que monitorea ubicaciones con **LOGIN** pendiente de
la cuenta **UNILEVER** (CD HUACHIPA) en **W4W DINET**. Clasifica por antigüedad
(semáforo), publica un dashboard web y avisa por Telegram. **Corre 100% en la
nube (GitHub Actions + Pages), cada 2 horas.**

- Repo: `github.com/llKirell/semaforo-login-unilever` (público)
- Dashboard: https://llkirell.github.io/semaforo-login-unilever/

## Pipeline (cloud_run.py, el entrypoint de la nube)

```
iniciar_sesion(page)            # src/w4w/login.py — login UI en app.dinet.com.pe
fijar_contexto_unilever(ctx)    # src/w4w/context.py — 3 POST backend (HUACHIPA/UNILEVER)
consultar_saldo(ctx)            # src/w4w/saldo.py — POST a API InventarioSaldo -> JSON
filtrar_login(filas)            # src/processor/login.py — filtra ubicaciones LOG
agrupar_por_lote(filas)         # agrupa Ubic+Articulo+Lote, suma cajas, fecha más antigua
generar_dashboard(public/index.html)  # src/dashboard/generator.py
enviar_foto(...)                # src/telegram/ — imagen del reporte al grupo
```
`ejecutar.py` es la versión "para PC" (usa SQLite + comparación); `cloud_run.py`
es la de la nube (sin BD, snapshot puro). El dashboard NO necesita BD.

## Modelo de datos (respuesta de W4W)

- Endpoint saldo: `POST https://w4w.dinet.com.pe/AppWeb/Consultas/InventarioSaldo/Consultar`
  → JSON con `{ErrorCode, ErrorDescription, ListData}`. Payload = todos los
  filtros vacíos + `FlagConStock:true, FlagConReserva:false` (ver src/w4w/saldo.py).
- Cada fila de `ListData` = un registro de saldo (artículo-lote en una ubicación).
- **LOGIN es la UBICACION**, no un estado: `CodigoUbicacion` que contiene/empieza
  con las de la lista. Familias: `LOGIN`, `LOGIN.RC.NN`, `LOGI.RECEP`, `LOGI.ALMACEN`.
- Campos usados: `CodigoUbicacion`, `CodigoArticulo`, `DescripcionArticulo`,
  `LoteProveedor`, `CantidadFinalUMS` (cajas), `FechaUltimoMovimiento`,
  `UsuarioCreacion` (columna Usuario; `UsuarioModificacion` como respaldo).
- **Fechas** vienen como `/Date(ms_epoch_UTC)/`. Lima = UTC-5. Ver
  `parse_fecha_dinet` en src/processor/login.py. `FechaUltimoMovimiento` está
  presente ~100%; `FechaModificacion` suele venir vacía (no usar).
- **Definiciones:** LÍNEA = combinación única Ubic+Articulo+Lote. CAJAS = suma de
  `CantidadFinalUMS`. Antigüedad = días desde la fila más ANTIGUA del grupo.

## Reglas de negocio

- Ubicaciones monitoreadas: `config/ubicaciones.py` → `UBICACIONES_MONITOREADAS`
  + `MODO_COINCIDENCIA` ("exacto" o "prefijo"). Hoy: LOGIN, LOGI.RECEP, LOGI.ALMACEN.
- Semáforo (`clasificar_semaforo` en src/processor/login.py): 0-2 días=VERDE,
  3=AMARILLO, 4+=ROJO, sin fecha=OBSERVACION.
- Dashboard: 3 tarjetas (ROJO/AMARILLO/VERDE) con cajas+líneas+día más antiguo de
  cada color; tabla por línea/lote (columnas: Ubicación, Cód. Artículo,
  Artículo, Lote, Usuario, Cantidad, Fecha Últ. Mov., Días) con filtro por
  ubicación, buscador, orden y paginación con filas "Auto" (se ajustan a la
  altura de pantalla); botón Descargar Excel que exporta SOLO esas columnas
  mostradas (las líneas), no la data cruda (.xlsx embebido en base64).

## GOTCHAS críticos (no re-tropezar)

1. **W4W desde IPs de datacenter (GitHub Actions):** requiere user-agent Chrome
   realista + `add_init_script` anti-detección (webdriver=undefined, chrome,
   languages, plugins) + `--no-sandbox` + esperas robustas (networkidle,
   wait_for_selector 'input', timeout selectores 8000ms). Ver cloud_run.py y
   src/w4w/login.py. SIN esto, el login NO encuentra `#txtUsuario` y falla.
   W4W **no bloquea** las IPs de GitHub (confirmado); solo hay que "parecer" real.
2. **Selectores login reales:** usuario `#txtUsuario`, pass `#txtContrasenia`,
   botón `#btnIngresar`. Login solo pide usuario+password (NO hay campo Company).
3. **Consola Windows (cp1252)** rompe con emojis/acentos → `sys.stdout.reconfigure(encoding="utf-8")`.
4. **Excel:** se genera sin librerías (src/dashboard/xlsx.py, zip+XML inline
   strings) y se embebe como data-URI en el dashboard (descarga client-side).
5. **Credenciales:** en la nube van por GitHub Secrets (DINET_USER, DINET_PASS,
   TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID). settings.py lee de env (os.getenv);
   local usa `.env` (gitignored). `settings._requerido` acepta alias
   W4W_USERNAME/W4W_PASSWORD por compatibilidad.

## Recetas de modificación

- **Agregar/quitar ubicación:** editar `config/ubicaciones.py`. `git push`.
- **Cambiar umbrales del semáforo:** `clasificar_semaforo` en src/processor/login.py.
- **Cambiar diseño del dashboard:** `src/dashboard/generator.py` (plantilla HTML +
  CSS + JS al final del archivo; usa marcadores `@@KPIS@@`, `@@FILAS@@`, etc.).
- **Cambiar mensaje/imagen de Telegram:** src/telegram/report_image.py (imagen) y
  messages.py (caption, hoy no se usa; se envía solo la imagen).
- **Cambiar horario:** cron en `.github/workflows/actualizar.yml` (`0 */2 * * *`,
  UTC; horas impares Lima). Y/o la tarea PC `TriggerNube`.
- **Cambiar secretos:** repo → Settings → Secrets and variables → Actions.

## Cómo probar cambios

- **Rápido en la nube:** `git push`, luego dispara manual:
  `gh workflow run actualizar.yml --repo llKirell/semaforo-login-unilever`
  y revisa `gh run watch <id>` o la pestaña Actions. Éxito → dashboard y Pages
  se actualizan; Telegram se envía.
- **Local:** `python cloud_run.py` (necesita `.env` + venv + playwright). Genera
  `public/index.html`. Para solo ver el dashboard sin re-consultar W4W: hay data
  de ejemplo si existe `data/detalle_actual.json` y se corre
  `python dashboard.py` (versión PC) — pero lo canónico es cloud_run.py.

## Disparo cada 2h (estado actual)

El cron NATIVO de GitHub (`schedule` en el workflow) tarda en "enganchar" en
repos nuevos (self-hosted engancha al toque; GitHub-hosted no). **Puente
temporal:** tarea Windows `SemaforoLogin\TriggerNube` corre `disparar_nube.cmd`
(`gh workflow run`) cada 2h (horas impares, ancla 01:00) + `disparar_boot.cmd`
al iniciar sesión (desde carpeta Inicio, `semaforo_trigger_boot.vbs`). Cuando en
Actions aparezcan corridas con evento `schedule`, desactivar el puente:
`Disable-ScheduledTask -TaskName "TriggerNube" -TaskPath "\SemaforoLogin\"`.

## Legacy (versión "en PC", ya redundante pero en el repo)

`servidor.py` (sirve dashboard local con Basic Auth), `publicar.ps1`/`despublicar.ps1`
(Tailscale Funnel `/semaforo`), `AUTO-RECUPERAR-SEMAFORO.ps1` + `iniciar_pm2.cmd`
(arranque PM2), `ejecutar.py` (flujo con SQLite + comparación nuevas/despejadas/
avance), `instalar_tareas.ps1` (3 corridas/día). Se movió a la nube; esto queda
de referencia. Las tareas PC de `ejecutar.py` están DESACTIVADAS (para no duplicar
Telegram con la nube).
