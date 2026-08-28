"""
config/settings.py
-------------------
Punto UNICO de configuracion. Credenciales desde .env (nunca en codigo).

Los endpoints y codigos NO son inventados: fueron confirmados leyendo el
robot ya probado en dms-unilever-cloudflare-spa (w4w-legacy-bridge). Por eso
podemos fijar el contexto HUACHIPA/UNILEVER por backend (3 POST) en vez de
hacer clic en los <select>.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _requerido(*claves: str) -> str:
    """Devuelve el valor de la primera variable que exista entre las claves dadas.

    Acepta alias para ser retrocompatible: DINET_USER es el nombre oficial,
    pero un .env antiguo con W4W_USERNAME tambien funciona.
    """
    for clave in claves:
        valor = os.getenv(clave, "").strip()
        if valor:
            return valor
    nombres = " / ".join(claves)
    raise RuntimeError(
        f"Falta la variable '{claves[0]}' (o su alias {nombres}) en el archivo .env. "
        f"Copia .env.example a .env y complétala."
    )


# --- Credenciales (DINET_USER/DINET_PASS; alias antiguos W4W_USERNAME/W4W_PASSWORD) ---
DINET_USER = _requerido("DINET_USER", "W4W_USERNAME")
DINET_PASS = _requerido("DINET_PASS", "W4W_PASSWORD")

# --- Contexto operativo (HUACHIPA / UNILEVER) ---
SYSTEM_CODE = "W4WWEB"
DISTRIBUTION_CENTER_CODE = "HU"
DISTRIBUTION_CENTER = "HUACHIPA"
ACCOUNT_CODE = "I1002"
ACCOUNT = "UNILEVER"

# --- URLs de navegacion ---
URL_LOGIN = "https://app.dinet.com.pe/"
URL_W4W_APPWEB = "https://w4w.dinet.com.pe/AppWeb"
URL_INVENTARIO_SALDO = "https://w4w.dinet.com.pe/AppWeb/Consultas/InventarioSaldo/"

# --- Endpoints de backend confirmados (para fijar contexto por API) ---
URL_REDIRECT_SYSTEM = "https://app.dinet.com.pe/Home/RedirectSystem"
URL_LISTAR_CUENTAS = "https://w4w.dinet.com.pe/AppWeb/IngresoSistema/ListarCuentas"
URL_ASSIGNMENT_CREDENTIALS = "https://w4w.dinet.com.pe/AppWeb/IngresoSistema/AssignmentCredentials"

# --- Telegram (opcional: el sistema funciona sin esto) ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# --- Endpoint de Inventario Saldo: AUN POR CONFIRMAR ---
# El script de descubrimiento lo detectara espiando la red. Cuando lo
# tengamos, lo fijamos aqui (probable patron: .../InventarioSaldo/Consultar).
URL_INVENTARIO_SALDO_CONSULTAR = os.getenv("W4W_SALDO_ENDPOINT", "").strip()
