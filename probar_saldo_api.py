"""
probar_saldo_api.py  -  Prueba directa del endpoint de Inventario Saldo
=======================================================================
Ya conocemos el endpoint (descubierto):
    POST https://w4w.dinet.com.pe/AppWeb/Consultas/InventarioSaldo/Consultar

Este script hace login + fija contexto + llama DIRECTO al endpoint con el
payload real y guarda la respuesta JSON completa y bien leida en
saldo_respuesta.json. Objetivo: conocer la ESTRUCTURA (nombres de campos)
para luego extraer ubicacion / login / ultima modificacion.

No hace clics ni espia la red: consulta por API, como sera el robot final.
"""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from config import settings
from src.w4w.login import iniciar_sesion
from src.w4w.context import fijar_contexto_unilever

ENDPOINT = "https://w4w.dinet.com.pe/AppWeb/Consultas/InventarioSaldo/Consultar"
SALIDA = Path(__file__).resolve().parent / "saldo_respuesta.json"

# Payload real capturado: todos los filtros vacios + solo con stock.
PAYLOAD = {
    "CodigoUbicacion": "",
    "CodigoSeccion": "",
    "CodigoLPN": "",
    "CodigoLineaArticulo": "",
    "CodigoClaseArticulo": None,
    "CodigoSubClaseArticulo": None,
    "CodigoArticulo": "",
    "DescripcionArticulo": "",
    "LoteProveedor": "",
    "CodigoEstadoMercaderia": "",
    "CodigoUM": "",
    "FlagConStock": True,
    "FlagConReserva": False,
}


def main() -> int:
    print("=" * 60)
    print("PRUEBA DIRECTA - Inventario Saldo API (UNILEVER)")
    print("=" * 60)

    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)  # ya no hace falta ver el navegador
        contexto = navegador.new_context()
        page = contexto.new_page()

        try:
            print("\n[1] Login")
            iniciar_sesion(page)

            print("\n[2] Fijar contexto HUACHIPA/UNILEVER")
            fijar_contexto_unilever(contexto)

            print("\n[3] Llamando al endpoint de saldo...")
            r = contexto.request.post(ENDPOINT, data=PAYLOAD, timeout=180000)
            print("    HTTP", r.status, "| ct:", r.headers.get("content-type", "")[:40])

            if not r.ok:
                print("[ERROR] El endpoint no respondio OK:", r.status)
                print(r.text()[:500])
                return 1

            data = r.json()

            # Detectar donde vienen las filas (patron DINET: ListData/Rows/Data)
            if isinstance(data, dict):
                filas = data.get("ListData") or data.get("Rows") or data.get("Data") or []
                claves_top = list(data.keys())
            else:
                filas = data
                claves_top = ["(respuesta es lista directa)"]

            print("\n[4] Analisis de la respuesta")
            print("    Claves de nivel superior:", claves_top)
            print("    Total de filas:", len(filas))
            if filas:
                print("    Campos de una fila:", list(filas[0].keys()))
                print("\n    --- Primera fila de ejemplo ---")
                print(json.dumps(filas[0], ensure_ascii=False, indent=2)[:1200])

            # Guardar respuesta completa para analizarla con calma
            SALIDA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print("\n[OK] Respuesta completa guardada en:", SALIDA.name)
            return 0

        except Exception as e:
            print("\n[ERROR]", e)
            return 1
        finally:
            contexto.close()
            navegador.close()


if __name__ == "__main__":
    sys.exit(main())
