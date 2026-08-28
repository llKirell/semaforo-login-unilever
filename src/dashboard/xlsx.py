"""
src/dashboard/xlsx.py
---------------------
Generador MINIMO de archivos .xlsx (Excel real) sin librerias externas.

Un .xlsx es un ZIP con varios XML. Aqui armamos lo minimo indispensable
para una hoja con encabezados + filas. Los textos van como "inline string"
(no usamos tabla de strings compartidos, para simplificar) y los numeros
como celda numerica. Devuelve los bytes del archivo.
"""

import io
import zipfile
from datetime import datetime, timezone, timedelta

_TZ = timezone(timedelta(hours=-5))


def _esc(t: str) -> str:
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _col(idx: int) -> str:
    """0 -> A, 1 -> B, ... 26 -> AA."""
    s = ""
    idx += 1
    while idx:
        idx, r = divmod(idx - 1, 26)
        s = chr(65 + r) + s
    return s


def _celda(ref: str, valor) -> str:
    if isinstance(valor, bool):
        valor = "SI" if valor else "NO"
    if isinstance(valor, (int, float)):
        return f'<c r="{ref}"><v>{valor}</v></c>'
    return f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{_esc(valor)}</t></is></c>'


def build_xlsx(headers: list[str], filas: list[list], hoja: str = "Detalle") -> bytes:
    """Construye un .xlsx con encabezados + filas. Devuelve bytes."""
    filas_xml = []
    # fila 1: encabezados
    celdas = "".join(_celda(f"{_col(c)}1", h) for c, h in enumerate(headers))
    filas_xml.append(f'<row r="1">{celdas}</row>')
    # datos
    for i, fila in enumerate(filas, start=2):
        celdas = "".join(_celda(f"{_col(c)}{i}", v) for c, v in enumerate(fila))
        filas_xml.append(f'<row r="{i}">{celdas}</row>')

    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(filas_xml)}</sheetData></worksheet>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{_esc(hoja)[:31]}" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    wb_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '</Relationships>'
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return buf.getvalue()


def convertir_fecha_dinet(valor):
    """Convierte '/Date(ms)/' a texto dd/mm/YYYY HH:MM (hora Lima). Si no aplica, devuelve el valor tal cual."""
    import re
    if not isinstance(valor, str):
        return valor
    m = re.search(r"/Date\((\d+)\)/", valor)
    if not m:
        return valor
    dt = datetime.fromtimestamp(int(m.group(1)) / 1000, tz=timezone.utc).astimezone(_TZ)
    return dt.strftime("%d/%m/%Y %H:%M")
