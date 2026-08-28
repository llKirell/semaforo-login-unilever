"""
analizar_login.py  -  FASE 2: procesamiento de pendientes LOGIN
===============================================================
Flujo completo por API (sin Excel, sin clics):
    Login -> Contexto UNILEVER -> Consultar Saldo -> Filtrar/Agrupar LOGIN
    -> Antiguedad + Semaforo -> Resumen

Genera pendientes_login.json con el detalle por ubicacion.
"""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from config import settings
from src.w4w.login import iniciar_sesion
from src.w4w.context import fijar_contexto_unilever
from src.w4w.saldo import consultar_saldo
from src.processor.login import procesar_login, resumen_semaforo

SALIDA = Path(__file__).resolve().parent / "pendientes_login.json"


def main() -> int:
    print("=" * 60)
    print("FASE 2 - Analisis de pendientes LOGIN (UNILEVER)")
    print("=" * 60)

    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        contexto = navegador.new_context()
        page = contexto.new_page()

        try:
            print("\n[1] Login")
            iniciar_sesion(page)

            print("\n[2] Contexto HUACHIPA/UNILEVER")
            fijar_contexto_unilever(contexto)

            print("\n[3] Consultar saldo")
            filas = consultar_saldo(contexto)

            print("\n[4] Procesar LOGIN")
            pendientes = procesar_login(filas)
            conteo = resumen_semaforo(pendientes)

            print("\n" + "=" * 60)
            print("RESUMEN - Ubicaciones LOGIN pendientes:", len(pendientes))
            print(f"  VERDE: {conteo['VERDE']}  AMARILLO: {conteo['AMARILLO']}  "
                  f"ROJO: {conteo['ROJO']}  OBSERVACION: {conteo['OBSERVACION']}")
            print("=" * 60)
            print(f"\n{'UBICACION':<16}{'REGISTROS':>10}{'DIAS':>6}  {'SEMAFORO':<11}{'DESDE':<12}")
            print("-" * 58)
            for r in pendientes[:15]:
                antig = "-" if r["antiguedad_dias"] is None else str(r["antiguedad_dias"])
                print(f"{r['ubicacion']:<16}{r['num_registros']:>10}{antig:>6}  "
                      f"{r['estado_semaforo']:<11}{str(r['fecha_mas_antigua'] or '-'):<12}")
            if len(pendientes) > 15:
                print(f"... y {len(pendientes) - 15} ubicaciones mas (ver {SALIDA.name})")

            SALIDA.write_text(json.dumps(pendientes, ensure_ascii=False, indent=2), encoding="utf-8")
            print("\n[OK] Detalle guardado en:", SALIDA.name)
            return 0

        except Exception as e:
            print("\n[ERROR]", e)
            return 1
        finally:
            contexto.close()
            navegador.close()


if __name__ == "__main__":
    sys.exit(main())
