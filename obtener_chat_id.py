"""
obtener_chat_id.py  -  Ayuda a encontrar el chat_id del grupo
=============================================================
Requisitos previos:
  1) Ya tienes el TELEGRAM_BOT_TOKEN puesto en .env.
  2) Agregaste el bot al grupo.
  3) Enviaste al menos un mensaje en el grupo (ej: "hola").

Este script consulta getUpdates y te muestra los chats detectados,
con su chat_id (para grupos suele ser un numero NEGATIVO).
Copia ese numero a .env como TELEGRAM_CHAT_ID.
"""

import json
import sys
import urllib.request

from config import settings


def main() -> int:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        print("[ERROR] Falta TELEGRAM_BOT_TOKEN en .env. Ponlo primero.")
        return 1

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print("[ERROR] No se pudo consultar Telegram:", e)
        return 1

    if not data.get("ok"):
        print("[ERROR] Telegram respondio:", data.get("description", data))
        return 1

    updates = data.get("result", [])
    if not updates:
        print("No hay mensajes recientes. Envia un mensaje en el grupo y reintenta.")
        print("(Recuerda: el bot debe estar agregado al grupo.)")
        return 0

    vistos = {}
    for u in updates:
        msg = u.get("message") or u.get("channel_post") or {}
        chat = msg.get("chat") or {}
        if chat:
            vistos[chat.get("id")] = chat.get("title") or chat.get("username") or chat.get("type")

    print("Chats detectados (copia el chat_id del grupo a .env):\n")
    for chat_id, nombre in vistos.items():
        marca = "  <== probable grupo" if isinstance(chat_id, int) and chat_id < 0 else ""
        print(f"  chat_id = {chat_id}   ({nombre}){marca}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
