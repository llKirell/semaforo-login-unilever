"""
ejecutar.py  -  FASE 4: ejecucion completa con historico y comparacion
======================================================================
Este es el comando PRINCIPAL del sistema. Hace:
    Login -> Contexto -> Saldo -> LOGIN -> Semaforo
    -> Compara con la ejecucion anterior y la linea base del dia
    -> Guarda todo en la base SQLite (data/semaforo.db)
    -> Imprime el resumen del turno (nuevas / despejadas / avance)

Uso:
    python ejecutar.py                 (detecta el tipo por la hora)
    python ejecutar.py inicio          (fuerza tipo: inicio/mediodia/cierre/manual)

Reglas: una corrida FALLIDA se registra pero NO contamina el historico
valido (RN-013/014).
"""

import json
import sys
from datetime import datetime

# Blindaje: la consola de Windows (cp1252) puede fallar con acentos/emoji.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from playwright.sync_api import sync_playwright

from src.w4w.login import iniciar_sesion
from src.w4w.context import fijar_contexto_unilever
from src.w4w.saldo import consultar_saldo
from src.processor.login import procesar_login, resumen_semaforo, filtrar_login
from src.processor.comparacion import comparar
from src.database.db import init_db
from src.database import repository
from pathlib import Path
from src.telegram.bot import enviar_foto
from src.telegram.report_image import generar_imagen

DETALLE_CRUDO = Path(__file__).resolve().parent / "data" / "detalle_actual.json"

REPORTE_IMG = Path(__file__).resolve().parent / "reporte_login.png"


def _tipo_por_hora() -> str:
    h = datetime.now().hour
    if h < 11:
        return "inicio"
    if h < 16:
        return "mediodia"
    return "cierre"


def main() -> int:
    tipo = sys.argv[1].lower() if len(sys.argv) > 1 else _tipo_por_hora()
    ahora = datetime.now()
    fecha = ahora.strftime("%Y-%m-%d")

    print("=" * 60)
    print(f"EJECUCION {tipo.upper()} | {fecha} {ahora.strftime('%H:%M:%S')}")
    print("=" * 60)

    init_db()

    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        contexto = navegador.new_context()
        page = contexto.new_page()
        try:
            print("\n[1] Login");                iniciar_sesion(page)
            print("\n[2] Contexto UNILEVER");     fijar_contexto_unilever(contexto)
            print("\n[3] Consultar saldo");       filas = consultar_saldo(contexto)
        except Exception as e:
            # RN-013: fallo de W4W/descarga -> no generamos datos falsos.
            print("\n[ERROR] Fallo la obtencion de datos:", e)
            repository.registrar_error(None, "W4W", "ejecutar", str(e))
            return 1
        finally:
            contexto.close()
            navegador.close()

    print("\n[4] Procesar y comparar")
    pendientes = procesar_login(filas)
    conteo = resumen_semaforo(pendientes)

    # Guardar la DATA CRUDA de las ubicaciones asignadas (para el dashboard y el Excel)
    filas_login = filtrar_login(filas)
    DETALLE_CRUDO.parent.mkdir(parents=True, exist_ok=True)
    DETALLE_CRUDO.write_text(json.dumps(filas_login, ensure_ascii=False), encoding="utf-8")

    # Comparacion ANTES de guardar (para no compararnos con nosotros mismos)
    anterior = repository.obtener_ultima_ejecucion_valida()
    linea_base = repository.obtener_linea_base_del_dia(fecha)
    comp = comparar(pendientes, anterior, linea_base)

    total_cajas = sum(p["total_cajas"] for p in pendientes)
    total_lineas = sum(p["num_lineas"] for p in pendientes)
    resumen = {
        "fecha": fecha,
        "hora": ahora.strftime("%H:%M:%S"),
        "tipo_ejecucion": tipo,
        "estado": "OK",
        "total_login": len(pendientes),
        "total_lineas": total_lineas,
        "total_cajas": total_cajas,
        "total_verde": conteo["VERDE"],
        "total_amarillo": conteo["AMARILLO"],
        "total_rojo": conteo["ROJO"],
        "total_observacion": conteo["OBSERVACION"],
        "total_nuevas": comp["total_nuevas"],
        "total_despejadas": comp["total_despejadas"],
        "porcentaje_avance": comp["porcentaje_avance_registros"],
    }

    ejecucion_id = repository.guardar_ejecucion(resumen, pendientes)  # P-013

    # --- Salida en pantalla ---
    print("\n" + "=" * 60)
    print(f"RESUMEN DEL TURNO  (ejecucion #{ejecucion_id}, tipo {tipo})")
    print("=" * 60)
    print(f"  Ubicaciones LOGIN pendientes : {len(pendientes)}")
    print(f"  Total cajas / lineas         : {total_cajas} cjs / {total_lineas} lineas")
    print(f"  Semaforo -> VERDE:{conteo['VERDE']}  AMARILLO:{conteo['AMARILLO']}  "
          f"ROJO:{conteo['ROJO']}  OBSERVACION:{conteo['OBSERVACION']}")
    if comp["es_linea_base"]:
        print("  (Esta es la LINEA BASE del dia: sin comparacion previa aun)")
    else:
        print(f"  Cajas al inicio del dia: {comp['registros_iniciales']}  ->  ahora: {comp['registros_actuales']}")
        print(f"  Cajas despejadas hoy   : {comp['registros_despejados']}")
        print(f"  AVANCE del turno       : {comp['porcentaje_avance_registros']}%  (por cajas)")

    print(f"\n{'UBICACION':<16}{'CJS':>7}{'LINEAS':>8}{'DIAS':>6}  {'SEMAFORO':<11}{'DESDE':<12}")
    print("-" * 62)
    for r in pendientes:
        antig = "-" if r["antiguedad_dias"] is None else str(r["antiguedad_dias"])
        print(f"{r['ubicacion']:<16}{r['total_cajas']:>7}{r['num_lineas']:>8}{antig:>6}  "
              f"{r['estado_semaforo']:<11}{str(r['fecha_mas_antigua'] or '-'):<12}")

    print(f"\n[OK] Ejecucion #{ejecucion_id} guardada en data/semaforo.db")

    # --- P-016: enviar a Telegram (RN-012 / CASO D: fallo no pierde datos) ---
    print("\n[5] Telegram")
    try:
        generar_imagen(pendientes, resumen, comp, REPORTE_IMG)
    except Exception as e:
        print("  [P-016] No se pudo generar la imagen:", e)
    ok, detalle = enviar_foto(REPORTE_IMG)  # solo la imagen, sin texto
    if ok:
        print("  [P-016] Reporte (imagen) enviado al grupo.")
    else:
        print("  [P-016] No se envio a Telegram:", detalle)
        repository.registrar_error(ejecucion_id, "TELEGRAM", "ejecutar", detalle)
        repository.actualizar_estado(ejecucion_id, "PARCIAL")
        print("  [P-016] Ejecucion marcada como PARCIAL (los datos SI se guardaron).")

    # --- P-014: refrescar el dashboard (no critico) ---
    try:
        from src.dashboard.generator import generar_dashboard
        generar_dashboard(Path(__file__).resolve().parent / "dashboard.html")
        print("  [P-014] Dashboard actualizado (dashboard.html)")
    except Exception as e:
        print("  [P-014] No se pudo actualizar el dashboard:", e)

    return 0


if __name__ == "__main__":
    sys.exit(main())
