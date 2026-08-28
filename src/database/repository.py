"""
src/database/repository.py
--------------------------
Guardado y consulta del historico (P-013).

Reglas respetadas:
  RN-014: nunca sobrescribimos; cada ejecucion es un INSERT nuevo.
  RN-008: la 'linea base' es la primera ejecucion VALIDA del dia.
  Para nuevas/despejadas usamos la ultima ejecucion VALIDA anterior.
Una ejecucion FALLIDA se guarda para dejar rastro, pero NO se considera
'valida' para comparaciones (asi no contamina el historico).
"""

from datetime import datetime

from .db import get_conn

_ESTADOS_VALIDOS = ("OK", "PARCIAL")


def guardar_ejecucion(resumen: dict, pendientes: list[dict]) -> int:
    """Inserta una ejecucion + su detalle. Devuelve el id de la ejecucion."""
    ahora = datetime.now()
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO ejecucion
               (fecha, hora, tipo_ejecucion, estado, total_login, total_lineas, total_cajas,
                total_verde, total_amarillo, total_rojo, total_observacion,
                total_nuevas, total_despejadas, porcentaje_avance, fecha_creacion)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                resumen["fecha"], resumen["hora"], resumen["tipo_ejecucion"], resumen["estado"],
                resumen["total_login"], resumen["total_lineas"], resumen["total_cajas"],
                resumen["total_verde"], resumen["total_amarillo"], resumen["total_rojo"],
                resumen["total_observacion"], resumen["total_nuevas"], resumen["total_despejadas"],
                resumen["porcentaje_avance"], ahora.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        ejecucion_id = cur.lastrowid
        conn.executemany(
            """INSERT INTO detalle_login
               (ejecucion_id, ubicacion, num_lineas, total_cajas, ultima_modificacion,
                antiguedad_dias, estado_semaforo, observacion)
               VALUES (?,?,?,?,?,?,?,?)""",
            [
                (
                    ejecucion_id, p["ubicacion"], p["num_lineas"], p["total_cajas"],
                    p["fecha_mas_antigua"], p["antiguedad_dias"], p["estado_semaforo"], p["observacion"],
                )
                for p in pendientes
            ],
        )
    return ejecucion_id


def registrar_error(ejecucion_id, tipo_error: str, modulo: str, descripcion: str) -> None:
    """Guarda un error (P-017)."""
    ahora = datetime.now()
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO error_ejecucion
               (ejecucion_id, tipo_error, modulo, descripcion, fecha, hora)
               VALUES (?,?,?,?,?,?)""",
            (ejecucion_id, tipo_error, modulo, descripcion,
             ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S")),
        )


def actualizar_estado(ejecucion_id: int, estado: str) -> None:
    """Cambia el estado de una ejecucion (ej: OK -> PARCIAL si fallo Telegram)."""
    with get_conn() as conn:
        conn.execute("UPDATE ejecucion SET estado = ? WHERE id = ?", (estado, ejecucion_id))


def _detalles_de(conn, ejecucion_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM detalle_login WHERE ejecucion_id = ?", (ejecucion_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def obtener_linea_base_del_dia(fecha: str) -> dict | None:
    """Primera ejecucion VALIDA del dia (RN-008), con su detalle. None si no hay."""
    with get_conn() as conn:
        row = conn.execute(
            f"""SELECT * FROM ejecucion
                WHERE fecha = ? AND estado IN {_ESTADOS_VALIDOS}
                ORDER BY id ASC LIMIT 1""",
            (fecha,),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["detalles"] = _detalles_de(conn, row["id"])
        return d


def obtener_ultima_ejecucion_valida() -> dict | None:
    """Ultima ejecucion VALIDA (cualquier fecha), con su detalle. None si no hay."""
    with get_conn() as conn:
        row = conn.execute(
            f"""SELECT * FROM ejecucion
                WHERE estado IN {_ESTADOS_VALIDOS}
                ORDER BY id DESC LIMIT 1"""
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["detalles"] = _detalles_de(conn, row["id"])
        return d
