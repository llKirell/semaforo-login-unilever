"""
main.py  -  Orquestador de la FASE 1
====================================
Flujo estable validado (sin descarga de Excel, todo por sesion autenticada):

    Login (UI)  ->  Fijar contexto HUACHIPA/UNILEVER (backend)  ->  Inventario Saldo

La consulta del saldo por API se cablea DESPUES de confirmar el endpoint
con descubrir_endpoint_saldo.py. headless=False para ver cada paso.
"""

import sys

from playwright.sync_api import sync_playwright

from config import settings
from src.w4w.login import iniciar_sesion
from src.w4w.context import fijar_contexto_unilever


def main() -> int:
    print("=" * 60)
    print("FASE 1 - Semaforo Login | Navegacion W4W (solo consulta)")
    print("Cuenta:", settings.ACCOUNT, "| CD:", settings.DISTRIBUTION_CENTER)
    print("=" * 60)

    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=False, slow_mo=300)
        contexto = navegador.new_context(accept_downloads=True)
        page = contexto.new_page()

        try:
            print("\n[ETAPA 1/3] Autenticacion")
            iniciar_sesion(page)

            print("\n[ETAPA 2/3] Fijar contexto HUACHIPA/UNILEVER")
            fijar_contexto_unilever(contexto)

            print("\n[ETAPA 3/3] Abriendo Inventario Saldo")
            page.goto(settings.URL_INVENTARIO_SALDO, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)

            page.screenshot(path="validacion_fase1.png", full_page=True)
            print("\n[OK] Captura guardada: validacion_fase1.png")

            print("\n" + "=" * 60)
            print("RESULTADO: llegamos a", page.url)
            print("Debe verse el Inventario Saldo de UNILEVER.")
            print("=" * 60)

            input("\n>> Presiona ENTER para cerrar el navegador...")
            return 0

        except Exception as e:
            print("\n[ERROR] La automatizacion se detuvo:", e)
            input(">> ENTER para cerrar (el navegador queda abierto para inspeccionar)...")
            return 1
        finally:
            contexto.close()
            navegador.close()


if __name__ == "__main__":
    sys.exit(main())
