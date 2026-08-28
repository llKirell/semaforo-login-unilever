"""
src/telegram/bot.py
-------------------
Proceso P-016: enviar un mensaje al grupo de Telegram.

Usa solo la libreria estandar (urllib), sin dependencias nuevas.
NUNCA imprime el token. Devuelve (ok, detalle) para que quien llama
decida que hacer si falla (RN-012: un fallo de Telegram no invalida
los datos ya procesados).
"""

import json
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from config import settings

_API = "https://api.telegram.org/bot{token}/{metodo}"


def enviar_mensaje(texto: str, timeout: int = 20) -> tuple[bool, str]:
    """Envia 'texto' al chat configurado. Devuelve (ok, detalle)."""
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        return False, "Falta TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en .env"

    url = _API.format(token=token, metodo="sendMessage")
    data = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": texto,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if body.get("ok"):
            return True, "enviado"
        return False, f"Telegram respondio ok=false: {body.get('description', body)}"
    except Exception as e:
        return False, f"Error de red al enviar Telegram: {e}"


def enviar_foto(ruta_imagen, caption: str = "", timeout: int = 60) -> tuple[bool, str]:
    """Envia una imagen (PNG) con un texto opcional. Devuelve (ok, detalle)."""
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        return False, "Falta TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en .env"

    ruta = Path(ruta_imagen)
    if not ruta.exists():
        return False, f"No existe la imagen: {ruta}"

    url = _API.format(token=token, metodo="sendPhoto")
    boundary = "----semaforo" + uuid.uuid4().hex

    def _campo(nombre: str, valor: str) -> bytes:
        return (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{nombre}"\r\n\r\n{valor}\r\n'
        ).encode("utf-8")

    cuerpo = b""
    cuerpo += _campo("chat_id", str(chat_id))
    if caption:
        cuerpo += _campo("caption", caption)
        cuerpo += _campo("parse_mode", "HTML")
    cuerpo += (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="photo"; filename="reporte.png"\r\n'
        "Content-Type: image/png\r\n\r\n"
    ).encode("utf-8")
    cuerpo += ruta.read_bytes() + b"\r\n"
    cuerpo += f"--{boundary}--\r\n".encode("utf-8")

    try:
        req = urllib.request.Request(url, data=cuerpo)
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if body.get("ok"):
            return True, "enviado"
        return False, f"Telegram respondio ok=false: {body.get('description', body)}"
    except Exception as e:
        return False, f"Error de red al enviar foto: {e}"
