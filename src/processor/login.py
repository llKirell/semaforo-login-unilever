"""
src/processor/login.py
----------------------
Procesos P-007 a P-010: filtrar LOGIN, extraer, calcular antiguedad y semaforo.

Decisiones de negocio (confirmadas con el usuario, 2026-08-21):
  - Unidad de analisis = UBICACION (CodigoUbicacion que empieza con 'LOGIN').
  - Antiguedad de una ubicacion = dias desde su fila MAS ANTIGUA de
    FechaUltimoMovimiento (el item que mas lleva quieto ahi).

Reglas de semaforo (RN-003/4/5/6):
  0-2 dias = VERDE | 3 = AMARILLO | 4+ = ROJO | sin fecha valida = OBSERVACION
"""

import re
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from config.ubicaciones import UBICACIONES_MONITOREADAS, MODO_COINCIDENCIA

# Lima no usa horario de verano: UTC-5 fijo.
_TZ_LIMA = timezone(timedelta(hours=-5))
_RE_DINET_DATE = re.compile(r"/Date\((\d+)\)/")


def parse_fecha_dinet(valor) -> datetime | None:
    """Convierte '/Date(ms)/' (epoch UTC) a datetime en hora de Lima.

    Devuelve None si el valor es vacio o no tiene el formato esperado
    (asi respetamos RN-006: no inventamos fechas).
    """
    if not valor:
        return None
    m = _RE_DINET_DATE.search(str(valor))
    if not m:
        return None
    epoch_utc = datetime.fromtimestamp(int(m.group(1)) / 1000, tz=timezone.utc)
    return epoch_utc.astimezone(_TZ_LIMA)


def es_ubicacion_monitoreada(codigo_ubicacion: str) -> bool:
    """True si la ubicacion esta en la lista editable config/ubicaciones.py.

    En modo "prefijo", cada entrada es una FAMILIA: "LOGIN" abarca "LOGIN"
    y cualquier "LOGIN.<algo>". En modo "exacto", solo coincide el codigo
    identico. Asi puedes agregar ubicaciones nuevas sin tocar la logica.
    """
    codigo = str(codigo_ubicacion or "").upper().strip()
    for patron in UBICACIONES_MONITOREADAS:
        p = str(patron).upper().strip()
        if not p:
            continue
        if MODO_COINCIDENCIA == "exacto":
            if codigo == p:
                return True
        else:  # "prefijo": codigo exacto o sub-ubicacion con punto
            if codigo == p or codigo.startswith(p + "."):
                return True
    return False


def es_ubicacion_login(fila: dict) -> bool:
    """Compatibilidad: aplica el filtro de ubicaciones monitoreadas a una fila."""
    return es_ubicacion_monitoreada(fila.get("CodigoUbicacion", ""))


def clasificar_semaforo(antiguedad_dias: int | None) -> str:
    """Aplica RN-003/4/5/6."""
    if antiguedad_dias is None:
        return "OBSERVACION"
    if antiguedad_dias <= 2:
        return "VERDE"
    if antiguedad_dias == 3:
        return "AMARILLO"
    return "ROJO"


def procesar_login(filas: list[dict], ahora: datetime | None = None) -> list[dict]:
    """Agrupa las filas LOGIN por ubicacion y calcula antiguedad + semaforo.

    Devuelve una lista de dicts, uno por ubicacion, ordenada de mas
    antigua a mas nueva (las mas urgentes primero).
    """
    ahora = ahora or datetime.now(tz=_TZ_LIMA)

    # P-007/P-008: filtrar LOGIN y agrupar por ubicacion.
    grupos: dict[str, list[dict]] = defaultdict(list)
    for fila in filas:
        if es_ubicacion_login(fila):
            grupos[fila["CodigoUbicacion"]].append(fila)

    resultado = []
    for ubicacion, items in grupos.items():
        # P-009: fecha mas antigua entre las filas de la ubicacion.
        fechas = [parse_fecha_dinet(i.get("FechaUltimoMovimiento")) for i in items]
        fechas_validas = [f for f in fechas if f is not None]

        if fechas_validas:
            mas_antigua = min(fechas_validas)
            antiguedad = (ahora.date() - mas_antigua.date()).days
            observacion = ""
        else:
            # RN-006: sin fecha valida -> no calculamos antiguedad.
            mas_antigua = None
            antiguedad = None
            observacion = "Ninguna fila tiene FechaUltimoMovimiento valida"

        total_cajas = sum((i.get("CantidadFinalUMS") or 0) for i in items)
        # lineas = combinaciones distintas de articulo + lote en esta ubicacion
        lineas = {(i.get("CodigoArticulo"), i.get("LoteProveedor")) for i in items}

        resultado.append(
            {
                "ubicacion": ubicacion,
                "num_lineas": len(lineas),
                "total_cajas": total_cajas,
                "fecha_mas_antigua": mas_antigua.strftime("%Y-%m-%d") if mas_antigua else None,
                "antiguedad_dias": antiguedad,
                "estado_semaforo": clasificar_semaforo(antiguedad),  # P-010
                "observacion": observacion,
            }
        )

    # Orden: OBSERVACION primero, luego por antiguedad desc (mas viejo arriba).
    resultado.sort(key=lambda r: (r["antiguedad_dias"] is not None, -(r["antiguedad_dias"] or 0)))
    return resultado


def filtrar_login(filas: list[dict]) -> list[dict]:
    """Devuelve solo las filas crudas que pertenecen a ubicaciones monitoreadas."""
    return [f for f in filas if es_ubicacion_login(f)]


def agrupar_por_lote(filas_login: list[dict], ahora: datetime | None = None) -> list[dict]:
    """Agrupa filas LOGIN por Ubicacion+Articulo+Lote (para la tabla del dashboard).

    Suma las cajas (CantidadFinalUMS) y toma la fecha MAS ANTIGUA de cada grupo.
    """
    ahora = ahora or datetime.now(tz=_TZ_LIMA)

    def _usuario(fila: dict) -> str:
        # UsuarioCreacion (quien lo puso) suele estar; UsuarioModificacion como respaldo.
        return (str(fila.get("UsuarioCreacion") or "").strip()
                or str(fila.get("UsuarioModificacion") or "").strip())

    grupos: dict[tuple, dict] = {}
    for f in filas_login:
        key = (f.get("CodigoUbicacion"), f.get("CodigoArticulo"), f.get("LoteProveedor"))
        g = grupos.get(key)
        if g is None:
            g = grupos[key] = {
                "ubicacion": f.get("CodigoUbicacion"),
                "cod_articulo": f.get("CodigoArticulo"),
                "articulo": f.get("DescripcionArticulo"),
                "lote": f.get("LoteProveedor"),
                "cajas": 0,
                "fecha": None,
                "usuario": _usuario(f),   # respaldo si no hay fecha; se pisa con el de la fila mas antigua
            }
        g["cajas"] += (f.get("CantidadFinalUMS") or 0)
        dt = parse_fecha_dinet(f.get("FechaUltimoMovimiento"))
        if dt and (g["fecha"] is None or dt < g["fecha"]):
            g["fecha"] = dt
            g["usuario"] = _usuario(f)   # usuario de la fila mas antigua

    lineas = []
    for g in grupos.values():
        if g["fecha"]:
            dias = (ahora.date() - g["fecha"].date()).days
        else:
            dias = None
        lineas.append(
            {
                "ubicacion": g["ubicacion"],
                "cod_articulo": g["cod_articulo"],
                "articulo": g["articulo"],
                "lote": g["lote"],
                "usuario": g["usuario"],
                "cajas": g["cajas"],
                "fecha_mas_antigua": g["fecha"].strftime("%d/%m/%Y") if g["fecha"] else None,
                "antiguedad_dias": dias,
                "estado_semaforo": clasificar_semaforo(dias),
            }
        )
    lineas.sort(key=lambda r: (r["antiguedad_dias"] is not None, -(r["antiguedad_dias"] or 0)))
    return lineas


def resumen_semaforo(pendientes: list[dict]) -> dict[str, int]:
    """Cuenta cuantas ubicaciones hay en cada color (para el resumen/Telegram)."""
    conteo = {"VERDE": 0, "AMARILLO": 0, "ROJO": 0, "OBSERVACION": 0}
    for p in pendientes:
        conteo[p["estado_semaforo"]] += 1
    return conteo
