"""
servidor.py  -  Sirve SOLO el dashboard por HTTP local, con Basic Auth
======================================================================
Pensado para exponerse por Tailscale Funnel. Por seguridad:
  - Escucha SOLO en 127.0.0.1 (Tailscale hace el proxy).
  - Sirve UNICAMENTE el dashboard.html (nunca la carpeta del proyecto,
    para no exponer .env, la base de datos ni el codigo).
  - Exige usuario y contrasena (Basic Auth). Si no hay credenciales
    configuradas en .env, NO arranca (evita quedar abierto al publico).
  - Regenera el dashboard en cada visita, asi siempre muestra lo ultimo.

Variables en .env:
    DASHBOARD_USER, DASHBOARD_PASS   (obligatorias)
    DASHBOARD_PORT                   (opcional, por defecto 4100)
"""

import base64
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from config import settings  # carga el .env
from src.dashboard.generator import generar_dashboard

BASE_DIR = Path(__file__).resolve().parent
DASHBOARD = BASE_DIR / "dashboard.html"

USER = os.getenv("DASHBOARD_USER", "").strip()
PASS = os.getenv("DASHBOARD_PASS", "").strip()
PORT = int(os.getenv("DASHBOARD_PORT", "4100"))


class Handler(BaseHTTPRequestHandler):
    def _pide_login(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Semaforo Login"')
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Autenticacion requerida".encode("utf-8"))

    def _autorizado(self) -> bool:
        cab = self.headers.get("Authorization", "")
        if not cab.startswith("Basic "):
            return False
        try:
            usr, pwd = base64.b64decode(cab[6:]).decode("utf-8").split(":", 1)
        except Exception:
            return False
        return usr == USER and pwd == PASS

    def do_GET(self):
        if not self._autorizado():
            return self._pide_login()
        # Solo servimos el dashboard (cualquier otra ruta -> 404)
        if self.path not in ("/", "/index.html", "/dashboard.html"):
            self.send_response(404)
            self.end_headers()
            return
        try:
            generar_dashboard(DASHBOARD)  # siempre lo ultimo
            html = DASHBOARD.read_bytes()
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, *args):
        pass  # silencioso (no ensuciar logs con cada request)


def main() -> int:
    if not USER or not PASS:
        print("[ERROR] Falta DASHBOARD_USER / DASHBOARD_PASS en .env. "
              "No arranco sin credenciales (evito exponer datos sin proteccion).")
        return 1
    servidor = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[OK] Dashboard sirviendo en http://127.0.0.1:{PORT} (solo local, con Basic Auth)")
    print("     Exponer con Tailscale Funnel para acceso del equipo.")
    servidor.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
