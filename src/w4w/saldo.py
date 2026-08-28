"""
src/w4w/saldo.py
----------------
Procesos P-004/P-005/P-006: consultar el Inventario Saldo por API.

Endpoint confirmado:
    POST https://w4w.dinet.com.pe/AppWeb/Consultas/InventarioSaldo/Consultar
Devuelve JSON con claves { ErrorCode, ErrorDescription, ListData }.
Requiere que el login y el contexto (HUACHIPA/UNILEVER) ya esten fijados.
"""

from playwright.sync_api import BrowserContext

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


def consultar_saldo(context: BrowserContext) -> list[dict]:
    """Devuelve la lista de filas de saldo (ListData). Lanza error si falla."""
    print("  [P-005] Consultando Inventario Saldo por API...")
    r = context.request.post(ENDPOINT, data=PAYLOAD_TODO_CON_STOCK, timeout=180000)
    if not r.ok:
        raise RuntimeError(f"[P-006] El endpoint de saldo respondio HTTP {r.status}")

    data = r.json()
    # P-006: validar la respuesta.
    if not isinstance(data, dict) or "ListData" not in data:
        raise RuntimeError("[P-006] Respuesta inesperada: no contiene 'ListData'")
    if data.get("ErrorCode") not in (None, "", 0, "0"):
        raise RuntimeError(f"[P-006] W4W reporto error: {data.get('ErrorDescription')}")

    filas = data["ListData"] or []
    print(f"  [P-006] Saldo recibido: {len(filas)} filas totales.")
    return filas
