"""
dashboard.py  -  Genera y ABRE el dashboard en el navegador
===========================================================
Uso:
    python dashboard.py          (genera dashboard.html y lo abre)

El HTML es autocontenido (no necesita servidor). Se puede volver a
abrir cuando quieras haciendo doble clic en dashboard.html.
"""

import sys
import webbrowser
from pathlib import Path

from src.dashboard.generator import generar_dashboard

SALIDA = Path(__file__).resolve().parent / "dashboard.html"


def main() -> int:
    ruta = generar_dashboard(SALIDA)
    print("[OK] Dashboard generado:", ruta)
    webbrowser.open(ruta.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
