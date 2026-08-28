"""
cloud_run.py  -  Entrypoint para GitHub Actions (ejecucion en la nube)
=====================================================================
Corre en el runner de GitHub cada 2 horas:
  Login -> Contexto UNILEVER -> Saldo -> Filtrar LOGIN
  -> Genera el dashboard en public/index.html (para GitHub Pages)
  -> (opcional) Envia la imagen a Telegram si hay credenciales

Las credenciales salen de variables de entorno (GitHub Secrets):
  DINET_USER, DINET_PASS  (obligatorias)
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID  (opcionales)

No usa base de datos: el dashboard es un snapshot del estado actual.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from playwright.sync_api import sync_playwright

from src.w4w.login import iniciar_sesion
from src.w4w.context import fijar_contexto_unilever
from src.w4w.saldo import consultar_saldo
from src.processor.login import filtrar_login, procesar_login, resumen_semaforo
from src.dashboard.generator import generar_dashboard

BASE = Path(__file__).resolve().parent
DETALLE = BASE / "data" / "detalle_actual.json"
PUBLIC = BASE / "public"


def _enviar_telegram(filas: list[dict]) -> None:
    """Envia la imagen del reporte si hay credenciales de Telegram. No es critico."""
    if not (os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")):
        print("[Telegram] Sin credenciales; se omite el envio.")
        return
    try:
        from src.telegram.report_image import generar_imagen
        from src.telegram.bot import enviar_foto

        pend = procesar_login(filas)
        resumen = {
            "tipo_ejecucion": "cloud",
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "hora": datetime.now().strftime("%H:%M"),
        }
        img = BASE / "reporte.png"
        generar_imagen(pend, resumen, {"es_linea_base": True}, img)
        ok, detalle = enviar_foto(img)
        print("[Telegram]", "enviado" if ok else f"fallo: {detalle}")
    except Exception as e:
        print("[Telegram] error (no critico):", e)


def main() -> int:
    print("=" * 60)
    print("CLOUD RUN - Semaforo Login |", datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 60)

    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        contexto = navegador.new_context()
        page = contexto.new_page()
        try:
            print("[1] Login"); iniciar_sesion(page)
            print("[2] Contexto UNILEVER"); fijar_contexto_unilever(contexto)
            print("[3] Saldo"); filas = consultar_saldo(contexto)
        finally:
            contexto.close()
            navegador.close()

    login = filtrar_login(filas)
    conteo = resumen_semaforo(procesar_login(filas))
    print(f"[4] Filas LOGIN: {len(login)} | semaforo: {conteo}")

    DETALLE.parent.mkdir(parents=True, exist_ok=True)
    DETALLE.write_text(json.dumps(login, ensure_ascii=False), encoding="utf-8")

    PUBLIC.mkdir(parents=True, exist_ok=True)
    generar_dashboard(PUBLIC / "index.html")
    print("[5] Dashboard generado en public/index.html")

    _enviar_telegram(filas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
