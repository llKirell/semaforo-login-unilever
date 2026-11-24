"""
src/w4w/saldo.py
----------------
Procesos P-004/P-005/P-006: consultar el Inventario Saldo por API.

Endpoint confirmado:
    POST https://w4w.dinet.com.pe/AppWeb/Consultas/InventarioSaldo/Consultar
Devuelve JSON con claves { ErrorCode, ErrorDescription, ListData }.
Requiere que el login y el contexto (HUACHIPA/UNILEVER) ya esten fijados.
"""

import time

from playwright.sync_api import BrowserContext, Error as PlaywrightError

from config import settings


ENDPOINT = (
    settings.URL_INVENTARIO_SALDO_CONSULTAR
    or "https://w4w.dinet.com.pe/AppWeb/Consultas/InventarioSaldo/Consultar"
)

# Filtros del payload: todo vacio + solo con stock (capturado de la web real).
PAYLOAD_TODO_CON_STOCK = {
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

MAX_INTENTOS_SALDO = 3
ESPERA_REINTENTO_SEGUNDOS = 5


def consultar_saldo(context: BrowserContext) -> list[dict]:
    """Consulta el saldo y reintenta solo errores transitorios de conexión/Oracle."""
    for intento in range(1, MAX_INTENTOS_SALDO + 1):
        print(
            f"  [P-005] Consultando Inventario Saldo por API "
            f"(intento {intento}/{MAX_INTENTOS_SALDO})..."
        )

        try:
            r = context.request.post(
                ENDPOINT,
                data=PAYLOAD_TODO_CON_STOCK,
                timeout=180000,
            )
        except PlaywrightError as exc:
            if intento == MAX_INTENTOS_SALDO:
                raise RuntimeError(
                    f"[P-006] Fallo de conexión al consultar saldo tras "
                    f"{MAX_INTENTOS_SALDO} intentos: {exc}"
                ) from exc

            espera = ESPERA_REINTENTO_SEGUNDOS * intento
            print(
                f"  [P-005] Error transitorio de conexión: {exc}. "
                f"Reintento en {espera}s."
            )
            time.sleep(espera)
            continue

        if not r.ok:
            raise RuntimeError(
                f"[P-006] El endpoint de saldo respondio HTTP {r.status}"
            )

        data = r.json()
        if not isinstance(data, dict) or "ListData" not in data:
            raise RuntimeError(
                "[P-006] Respuesta inesperada: no contiene 'ListData'"
            )

        error_code = data.get("ErrorCode")
        if error_code not in (None, "", 0, "0"):
            descripcion = str(data.get("ErrorDescription") or "")
            if "ORA-12570" in descripcion.upper() and intento < MAX_INTENTOS_SALDO:
                espera = ESPERA_REINTENTO_SEGUNDOS * intento
                print(
                    f"  [P-005] W4W devolvio ORA-12570. "
                    f"Reintento en {espera}s."
                )
                time.sleep(espera)
                continue

            raise RuntimeError(f"[P-006] W4W reporto error: {descripcion}")

        filas = data["ListData"] or []
        print(f"  [P-006] Saldo recibido: {len(filas)} filas totales.")
        return filas

    raise RuntimeError(
        f"[P-006] No se obtuvo saldo tras {MAX_INTENTOS_SALDO} intentos."
    )
