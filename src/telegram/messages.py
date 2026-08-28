"""
src/telegram/messages.py
------------------------
Proceso P-015: construir el texto del resumen para Telegram.

Telegram es RESUMEN Y ALERTA (el detalle fino va en la base/dashboard).
Usa HTML simple (<b>) que Telegram soporta.
"""

_EMOJI = {"VERDE": "🟢", "AMARILLO": "🟡", "ROJO": "🔴", "OBSERVACION": "⚪"}


def construir_caption(resumen: dict, comp: dict) -> str:
    """Texto corto que acompaña la imagen del reporte (el detalle va en la imagen)."""
    return (
        f"🚦 <b>UNILEVER — LOGIN</b> · {resumen['fecha']} {resumen['hora']}\n"
        f"Pendientes: {resumen['total_login']} ubicaciones · {resumen['total_registros']} ítems  "
        f"({_EMOJI['ROJO']}{resumen['total_rojo']} {_EMOJI['AMARILLO']}{resumen['total_amarillo']} "
        f"{_EMOJI['VERDE']}{resumen['total_verde']})"
    )


def construir_resumen(resumen: dict, comp: dict, pendientes: list[dict]) -> str:
    """Arma el mensaje del turno a partir del resumen, la comparacion y el detalle."""
    lineas = []
    lineas.append("🚦 <b>UNILEVER — Seguimiento LOGIN</b>")
    lineas.append(f"Turno: <b>{resumen['tipo_ejecucion'].upper()}</b> · "
                  f"{resumen['fecha']} {resumen['hora']}")
    lineas.append("")
    lineas.append(f"Ubicaciones pendientes: <b>{resumen['total_login']}</b>")
    lineas.append(f"Ítems totales: <b>{resumen['total_registros']}</b>")
    lineas.append(
        f"{_EMOJI['VERDE']} {resumen['total_verde']}   "
        f"{_EMOJI['AMARILLO']} {resumen['total_amarillo']}   "
        f"{_EMOJI['ROJO']} {resumen['total_rojo']}   "
        f"{_EMOJI['OBSERVACION']} {resumen['total_observacion']}"
    )

    if comp["es_linea_base"]:
        lineas.append("")
        lineas.append("<i>Línea base del día (sin comparación previa).</i>")
    else:
        lineas.append("")
        lineas.append(f"Ítems inicio del día: {comp['registros_iniciales']} → "
                      f"ahora: {comp['registros_actuales']}")
        lineas.append(f"Ítems despejados hoy: <b>{comp['registros_despejados']}</b>")
        lineas.append(f"Avance del turno: <b>{comp['porcentaje_avance_registros']}%</b>")
        if comp["total_nuevas"] or comp["total_despejadas"]:
            lineas.append(f"(Ubicaciones nuevas: {comp['total_nuevas']} · "
                          f"despejadas: {comp['total_despejadas']})")

    lineas.append("")
    lineas.append("<b>Detalle:</b>")
    for p in pendientes:
        emoji = _EMOJI.get(p["estado_semaforo"], "⚪")
        dias = "-" if p["antiguedad_dias"] is None else f"{p['antiguedad_dias']} días"
        lineas.append(f"{emoji} {p['ubicacion']} — {p['num_registros']} ítems — {dias}")

    return "\n".join(lineas)
