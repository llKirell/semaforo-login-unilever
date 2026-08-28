"""
src/processor/comparacion.py
----------------------------
Procesos P-011/P-012: comparar ejecuciones y calcular el avance.

Reglas:
  RN-009: ubicacion que estaba antes y ya no esta -> DESPEJADA.
  RN-010: ubicacion que no estaba y aparece        -> NUEVA.
  RN-011: las nuevas se cuentan aparte de las iniciales.

Avance (dos miradas, porque hoy son 3 ubicaciones fijas):
  - Por UBICACION (como el documento): despejadas_de_base / pendientes_iniciales.
  - Por REGISTROS (mas util): items despejados / items iniciales. Mide cuanto
    stock se saco de las ubicaciones durante el turno.
"""


def _mapa_registros(detalles: list[dict]) -> dict[str, int]:
    """{ubicacion: total_cajas} a partir de una lista de detalles."""
    return {d["ubicacion"]: (d.get("total_cajas") or 0) for d in detalles}


def comparar(actual: list[dict], anterior: dict | None, linea_base: dict | None) -> dict:
    """Calcula nuevas/despejadas vs la ejecucion anterior y avance vs linea base.

    'actual'      = lista de pendientes de esta corrida (procesar_login).
    'anterior'    = dict de ejecucion anterior con 'detalles' (o None).
    'linea_base'  = dict de la primera ejecucion del dia con 'detalles' (o None).
    """
    ubic_actual = {p["ubicacion"] for p in actual}
    reg_actual = {p["ubicacion"]: p["total_cajas"] for p in actual}
    total_reg_actual = sum(reg_actual.values())

    # --- vs ejecucion anterior: nuevas y despejadas (RN-009/010) ---
    if anterior:
        ubic_anterior = {d["ubicacion"] for d in anterior["detalles"]}
    else:
        ubic_anterior = set()
    nuevas = sorted(ubic_actual - ubic_anterior) if anterior else []
    despejadas = sorted(ubic_anterior - ubic_actual) if anterior else []

    # --- vs linea base: avance del turno (RN-012 avance) ---
    if linea_base:
        base_reg = _mapa_registros(linea_base["detalles"])
        ubic_base = set(base_reg)
        pendientes_iniciales = len(ubic_base)
        despejadas_de_base = len(ubic_base - ubic_actual)
        avance_ubic = round(despejadas_de_base / pendientes_iniciales * 100, 1) if pendientes_iniciales else 0.0

        registros_iniciales = sum(base_reg.values())
        # items despejados = reduccion neta de registros respecto a la base
        registros_despejados = max(0, registros_iniciales - total_reg_actual)
        avance_reg = round(registros_despejados / registros_iniciales * 100, 1) if registros_iniciales else 0.0
        es_linea_base = False
    else:
        # Esta corrida ES la linea base del dia.
        pendientes_iniciales = len(ubic_actual)
        despejadas_de_base = 0
        avance_ubic = 0.0
        registros_iniciales = total_reg_actual
        registros_despejados = 0
        avance_reg = 0.0
        es_linea_base = True

    return {
        "es_linea_base": es_linea_base,
        "nuevas": nuevas,
        "despejadas": despejadas,
        "total_nuevas": len(nuevas),
        "total_despejadas": len(despejadas),
        "pendientes_iniciales": pendientes_iniciales,
        "despejadas_de_base": despejadas_de_base,
        "porcentaje_avance_ubicaciones": avance_ubic,
        "registros_iniciales": registros_iniciales,
        "registros_actuales": total_reg_actual,
        "registros_despejados": registros_despejados,
        "porcentaje_avance_registros": avance_reg,
    }
