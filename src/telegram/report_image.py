"""
src/telegram/report_image.py
----------------------------
Genera la IMAGEN del reporte (PNG) que se envia por Telegram.

Tecnica: construimos una tabla en HTML con el diseño solicitado
(UBI. | ITEMS | SEMAFORO, con los dias debajo del semaforo) y le
tomamos una captura con Playwright/Chromium (ya instalado). Asi no
necesitamos librerias de imagen adicionales.
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

# Colores del semaforo
_COLOR = {
    "ROJO": "#e23b3b",
    "AMARILLO": "#f2c200",
    "VERDE": "#2ca02c",
    "OBSERVACION": "#9aa0a6",
}


def construir_html(pendientes: list[dict], resumen: dict, comp: dict) -> str:
    """Arma el HTML del reporte con el diseño de la tabla."""
    filas = ""
    for p in pendientes:
        color = _COLOR.get(p["estado_semaforo"], "#9aa0a6")
        dias = "-" if p["antiguedad_dias"] is None else f"{p['antiguedad_dias']} días"
        filas += f"""
        <tr>
          <td class="ubi">{p['ubicacion']}</td>
          <td class="items">{p['total_cajas']}</td>
          <td class="items">{p['num_lineas']}</td>
          <td class="dias"><span class="chip" style="background:{color}">{dias}</span></td>
        </tr>"""

    return f"""<!doctype html><html><head><meta charset="utf-8">
    <style>
      * {{ box-sizing: border-box; margin: 0; }}
      body {{ background: #ffffff; font-family: 'Segoe UI', Arial, sans-serif; }}
      #card {{ width: 620px; padding: 22px 24px; background: #ffffff; }}
      .titulo {{ font-size: 20px; font-weight: 700; color: #1b1b1b; }}
      .sub {{ font-size: 13px; color: #666; margin-top: 2px; margin-bottom: 16px; }}
      table {{ width: 100%; border-collapse: collapse; }}
      thead th {{ font-size: 13px; color: #333; text-transform: uppercase;
                  padding: 8px 10px; border-bottom: 2px solid #ddd; text-align: left; }}
      th.c-items, td.items {{ text-align: center; width: 70px; }}
      th.c-sem, td.dias {{ text-align: center; width: 150px; }}
      .barra {{ display: flex; height: 10px; width: 130px; margin: 4px auto 2px;
                border-radius: 3px; overflow: hidden; }}
      .barra span {{ flex: 1; }}
      .b-r {{ background: #e23b3b; }} .b-y {{ background: #f2c200; }} .b-g {{ background: #2ca02c; }}
      tbody td {{ padding: 10px; border-bottom: 1px solid #eee; font-size: 15px; color: #1b1b1b; }}
      td.ubi {{ font-weight: 600; }}
      td.items {{ font-weight: 600; }}
      .chip {{ display: inline-block; padding: 4px 12px; border-radius: 12px;
               color: #fff; font-weight: 600; font-size: 13px; }}
    </style></head>
    <body><div id="card">
      <div class="titulo">🚦 UNILEVER — Seguimiento LOGIN</div>
      <div class="sub">{resumen['fecha']} {resumen['hora']}</div>
      <table>
        <thead><tr>
          <th class="c-ubi">Ubicación</th>
          <th class="c-items">Cjs</th>
          <th class="c-items">Líneas</th>
          <th class="c-sem">
            <div class="barra"><span class="b-r"></span><span class="b-y"></span><span class="b-g"></span></div>
            Semáforo · Días
          </th>
        </tr></thead>
        <tbody>{filas}</tbody>
      </table>
    </div></body></html>"""


def generar_imagen(pendientes: list[dict], resumen: dict, comp: dict, salida: Path) -> Path:
    """Renderiza el HTML y guarda la captura PNG en 'salida'. Devuelve la ruta."""
    html = construir_html(pendientes, resumen, comp)
    salida = Path(salida)
    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        contexto = navegador.new_context(device_scale_factor=2)  # nitidez x2
        page = contexto.new_page()
        page.set_content(html, wait_until="networkidle")
        page.locator("#card").screenshot(path=str(salida))
        navegador.close()
    return salida
