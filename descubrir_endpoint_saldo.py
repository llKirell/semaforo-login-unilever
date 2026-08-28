"""
descubrir_endpoint_saldo.py  -  Herramienta de DESCUBRIMIENTO (una sola vez)
===========================================================================
Detecta el endpoint real de Inventario Saldo y su payload espiando la red.
No requiere presionar ENTER: guarda el reporte AUTOMATICAMENTE cada vez que
captura una peticion, y espera un tiempo fijo mientras tu haces clic en
"Consultar". Se cierra solo al terminar la ventana de espera.

Que hace:
  1) Login (P-002)  ->  cookies activas.
  2) Fija contexto HUACHIPA/UNILEVER por backend (P-003).
  3) Espia todas las peticiones POST a w4w.dinet.com.pe y las guarda al
     instante en descubrimiento_saldo.json.
  4) Abre Inventario Saldo y espera ~150s: TU presionas "Consultar".
  5) Cierra e imprime el resumen de endpoints candidatos.
"""

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from config import settings
from src.w4w.login import iniciar_sesion
from src.w4w.context import fijar_contexto_unilever

REPORTE = Path(__file__).resolve().parent / "descubrimiento_saldo.json"
SEGUNDOS_ESPERA = 150  # ventana para que hagas clic en "Consultar"


def main() -> int:
    print("=" * 64)
    print("DESCUBRIMIENTO de endpoint de Inventario Saldo (UNILEVER)")
    print("=" * 64)

    capturas: list[dict] = []

    def guardar():
        """Escribe el reporte al disco en cada captura (no espera ENTER)."""
        try:
            REPORTE.write_text(json.dumps(capturas, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=False, slow_mo=200)
        contexto = navegador.new_context(accept_downloads=True)
        page = contexto.new_page()

        def on_response(response):
            try:
                req = response.request
                url = response.url
                if req.method != "POST" or "w4w.dinet.com.pe" not in url:
                    return
                ct = (response.headers or {}).get("content-type", "")
                registro = {
                    "url": url,
                    "metodo": req.method,
                    "status": response.status,
                    "content_type": ct,
                    "payload_enviado": req.post_data,
                    "muestra_respuesta": "",
                }
                if "json" in ct.lower():
                    try:
                        registro["muestra_respuesta"] = response.text()[:2000]
                    except Exception as ex:
                        registro["muestra_respuesta"] = f"(no se pudo leer body: {ex})"
                capturas.append(registro)
                guardar()  # <-- guardado inmediato
                marca = "  <== CANDIDATO" if any(
                    k in url.lower() for k in ("saldo", "inventario", "consultar")
                ) else ""
                print(f"  [RED] POST {response.status} {url}{marca}")
            except Exception:
                pass

        contexto.on("response", on_response)

        try:
            print("\n[ETAPA 1] Login")
            iniciar_sesion(page)

            print("\n[ETAPA 2] Fijar contexto HUACHIPA/UNILEVER")
            fijar_contexto_unilever(contexto)

            print("\n[ETAPA 3] Abriendo Inventario Saldo:", settings.URL_INVENTARIO_SALDO)
            page.goto(settings.URL_INVENTARIO_SALDO, wait_until="domcontentloaded")

            print("\n" + "-" * 64)
            print("AHORA, en el navegador que se abrio:")
            print("  1. Presiona el boton 'Consultar' / 'Buscar' del saldo.")
            print("  2. Espera a que carguen los datos.")
            print(f"  (Tienes {SEGUNDOS_ESPERA}s; NO necesitas tocar esta consola)")
            print("-" * 64)

            # Espera automatica con avisos; el guardado ya es inmediato.
            for restante in range(SEGUNDOS_ESPERA, 0, -10):
                print(f"  ...esperando ({restante}s) - capturas hasta ahora: {len(capturas)}")
                time.sleep(10)

        except Exception as e:
            print("\n[ERROR] Se detuvo antes de completar:", e)
        finally:
            guardar()
            print("\n" + "=" * 64)
            print("RESUMEN DE ENDPOINTS POST CAPTURADOS")
            print("=" * 64)
            if not capturas:
                print("No se capturo ningun POST a w4w. ¿Presionaste 'Consultar' a tiempo?")
            else:
                for i, c in enumerate(capturas, 1):
                    es_cand = any(k in c["url"].lower() for k in ("saldo", "inventario", "consultar"))
                    print(f"\n[{i}]{' *** PROBABLE ***' if es_cand else ''}")
                    print("  URL     :", c["url"])
                    print("  status  :", c["status"], "| ct:", c["content_type"][:40])
                    print("  payload :", (c["payload_enviado"] or "")[:300])
                    if c["muestra_respuesta"]:
                        print("  resp    :", c["muestra_respuesta"][:300])
            print("\n[OK] Reporte guardado en:", REPORTE.name)
            contexto.close()
            navegador.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
