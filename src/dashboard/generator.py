"""
src/dashboard/generator.py
--------------------------
Proceso P-014: genera el dashboard como un HTML autocontenido.

Lee la data CRUDA de la ultima corrida (data/detalle_actual.json), la
agrupa por lote para la tabla, calcula los KPIs y embebe:
  - la tabla (con filtro por ubicacion, buscador y orden por columna),
  - un boton de descarga a Excel (.xlsx) con la DATA COMPLETA cruda de
    W4W (todas las columnas y filas) de las ubicaciones asignadas.
No necesita servidor: es un solo archivo que se abre en el navegador.
"""

import base64
import html
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from src.processor.login import agrupar_por_lote
from src.dashboard.xlsx import build_xlsx, convertir_fecha_dinet

BASE_DIR = Path(__file__).resolve().parents[2]
DETALLE_CRUDO = BASE_DIR / "data" / "detalle_actual.json"

_COLOR = {"ROJO": "#e23b3b", "AMARILLO": "#e0a800", "VERDE": "#2ca02c", "OBSERVACION": "#9aa0a6"}
_KPI_BG = {"cjs": "#2aa9e0", "lineas": "#6aa84f", "rojo": "#c0398f", "antiguo": "#16a2a2"}


def _excel_datauri(lineas: list[dict]) -> tuple[str, int]:
    """Construye el .xlsx con SOLO las columnas que se muestran en el dashboard
    (por linea/lote). Devuelve (dataURI, n_filas)."""
    if not lineas:
        return "", 0
    headers = ["Ubicacion", "Cod. Articulo", "Articulo", "Lote Proveedor",
               "Usuario", "Cantidad (cajas)", "Fecha Ult. Mov.", "Dias", "Semaforo"]
    filas = []
    for l in lineas:
        filas.append([
            l["ubicacion"],
            l["cod_articulo"] or "",
            l["articulo"] or "",
            l["lote"] or "",
            l.get("usuario") or "",
            l["cajas"],
            l["fecha_mas_antigua"] or "",
            l["antiguedad_dias"] if l["antiguedad_dias"] is not None else "",
            l["estado_semaforo"],
        ])
    xlsx = build_xlsx(headers, filas, hoja="LOGIN")
    b64 = base64.b64encode(xlsx).decode("ascii")
    uri = "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64," + b64
    return uri, len(filas)


def _card_semaforo(estado, emoji, bg, texto, lineas):
    """Tarjeta de un color del semaforo: cajas, lineas y dia mas antiguo de ese grupo."""
    grp = [l for l in lineas if l["estado_semaforo"] == estado]
    cajas = sum(l["cajas"] for l in grp)
    n_lin = len(grp)
    dd = [l["antiguedad_dias"] for l in grp if l["antiguedad_dias"] is not None]
    d_max = f"{max(dd)}d" if dd else "—"
    return (
        f'<div class="kpi" style="background:{bg};color:{texto}">'
        f'<div class="kt">{emoji} {estado}</div>'
        f'<div class="kstats">'
        f'<div><span class="n">{cajas}</span><span class="l">cajas</span></div>'
        f'<div><span class="n">{n_lin}</span><span class="l">líneas</span></div>'
        f'<div><span class="n">{d_max}</span><span class="l">+ antiguo</span></div>'
        f'</div></div>'
    )


def generar_dashboard(salida: Path) -> Path:
    salida = Path(salida)
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not DETALLE_CRUDO.exists():
        salida.write_text(
            "<h1>Semáforo Login</h1><p>Aún no hay datos. Corre "
            "<code>python ejecutar.py</code> primero.</p>", encoding="utf-8")
        return salida

    crudas = json.loads(DETALLE_CRUDO.read_text(encoding="utf-8"))
    lineas = agrupar_por_lote(crudas)

    total_cajas = sum(l["cajas"] for l in lineas)
    total_lineas = len(lineas)
    peor = {}
    for l in lineas:
        d = l["antiguedad_dias"]
        if d is not None:
            peor[l["ubicacion"]] = max(peor.get(l["ubicacion"], 0), d)
    en_rojo = sum(1 for d in peor.values() if d >= 4)
    max_dias = max((l["antiguedad_dias"] or 0) for l in lineas) if lineas else 0

    kpis = (_card_semaforo("ROJO", "🔴", "#e23b3b", "#fff", lineas)
            + _card_semaforo("AMARILLO", "🟡", "#e0a800", "#3a2f00", lineas)
            + _card_semaforo("VERDE", "🟢", "#2ca02c", "#fff", lineas))

    # chips de ubicaciones presentes
    ubics = sorted({l["ubicacion"] for l in lineas})
    chips = "".join(f'<span class="fchip on" data-ubic="{html.escape(u)}">{html.escape(u)}</span>' for u in ubics)

    # filas de la tabla
    tr = ""
    for i, l in enumerate(lineas):
        color = _COLOR.get(l["estado_semaforo"], "#9aa0a6")
        dias_txt = "-" if l["antiguedad_dias"] is None else f"{l['antiguedad_dias']}d"
        usuario = str(l.get("usuario") or "").strip()
        buscar = f"{l['cod_articulo']} {l['articulo']} {l['lote']} {usuario}".lower()
        tr += (
            f'<tr data-ubic="{html.escape(str(l["ubicacion"]))}" data-buscar="{html.escape(buscar)}" '
            f'data-cajas="{l["cajas"]}" data-dias="{l["antiguedad_dias"] if l["antiguedad_dias"] is not None else -1}">'
            f'<td class="b">{html.escape(str(l["ubicacion"]))}</td>'
            f'<td class="mono">{html.escape(str(l["cod_articulo"] or ""))}</td>'
            f'<td>{html.escape(str(l["articulo"] or ""))}</td>'
            f'<td class="mono">{html.escape(str(l["lote"] or ""))}</td>'
            f'<td class="mono">{html.escape(usuario or "-")}</td>'
            f'<td class="c b">{l["cajas"]}</td>'
            f'<td class="c">{html.escape(str(l["fecha_mas_antigua"] or "-"))}</td>'
            f'<td class="c"><span class="chip" style="background:{color}">{dias_txt}</span></td></tr>'
        )

    excel_uri, nfilas = _excel_datauri(lineas)
    excel_name = f"login_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    excel_btn = (
        f'<a class="btnxls" download="{excel_name}" href="{excel_uri}">⬇ Descargar Excel '
        f'({nfilas} líneas)</a>'
    ) if excel_uri else '<span class="muted">Sin datos para exportar</span>'

    tpl = _PLANTILLA
    for k, v in {
        "@@ACTUALIZADO@@": ahora,
        "@@KPIS@@": kpis,
        "@@CHIPS@@": chips,
        "@@FILAS@@": tr,
        "@@NLINEAS@@": str(total_lineas),
        "@@EXCEL@@": excel_btn,
    }.items():
        tpl = tpl.replace(k, v)

    salida.write_text(tpl, encoding="utf-8")
    return salida


_PLANTILLA = """<!doctype html><html lang=es><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Semáforo Login — Dashboard</title>
<style>
 *{box-sizing:border-box;margin:0}
 /* zoom 0.8 = vista tipo 80% (mas compacta, entra mas en pantalla) */
 body{background:#eef1f4;font-family:'Segoe UI',Arial,sans-serif;color:#1b1b1b;zoom:.8;display:flex;min-height:100vh}
 .sidebar{width:54px;background:#141b2d;display:flex;flex-direction:column;align-items:center;padding:12px 0;gap:6px;flex:none}
 .sblogo{font-size:22px;margin-bottom:10px}
 .sbtn{width:40px;height:40px;border:none;border-radius:10px;background:transparent;color:#9aa7bd;font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center}
 .sbtn:hover{background:#1f2a40;color:#fff}
 .sbtn.active{background:rgba(74,163,255,.18);color:#4aa3ff}
 .main{flex:1;min-width:0}
 .cfgbody{padding:18px 20px;font-size:14px;line-height:1.5}
 .step{display:flex;gap:12px;margin:14px 0;align-items:flex-start}
 .stepn{flex:none;width:26px;height:26px;border-radius:50%;background:#1f3a5f;color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center;font-size:13px}
 .btncfg{display:inline-block;margin-top:8px;background:#1f6feb;color:#fff;text-decoration:none;padding:9px 16px;border-radius:8px;font-weight:600;font-size:13px}
 .btncfg:hover{background:#1559c9}
 .btncfg.alt{background:#1d6f42}
 .btncfg.alt:hover{background:#175a36}
 code{background:#eef1f4;padding:1px 5px;border-radius:4px;font-size:12px;color:#c0398f}
 .wrap{max-width:100%;margin:0;padding:20px 26px 40px}
 h1{font-size:22px} .sub{color:#777;font-size:13px;margin:2px 0 18px}
 .kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:22px}
 .kpi{border-radius:12px;padding:14px 18px;box-shadow:0 2px 6px rgba(0,0,0,.15)}
 .kt{font-size:14px;font-weight:800;letter-spacing:.04em;margin-bottom:12px}
 .kstats{display:flex;justify-content:space-between;gap:8px}
 .kstats>div{display:flex;flex-direction:column;align-items:center;flex:1}
 .kstats .n{font-size:26px;font-weight:800;line-height:1}
 .kstats .l{font-size:10px;opacity:.92;margin-top:4px;text-transform:uppercase;letter-spacing:.03em}
 .panel{background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08)}
 .ptop{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;border-bottom:1px solid #eee;gap:12px;flex-wrap:wrap}
 .ptop h2{font-size:15px}
 .controls{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
 .flabel{font-size:12px;color:#777}
 .fchip{font-size:12px;padding:5px 11px;border-radius:16px;border:1.5px solid #cfd6dd;color:#555;background:#fff;cursor:pointer;user-select:none}
 .fchip.on{background:#eaf4ff;border-color:#2aa9e0;color:#1466a0;font-weight:600}
 .fchip.on::before{content:'\\2713 '}
 .search{font-size:12px;padding:6px 10px;border:1px solid #cfd6dd;border-radius:8px;width:170px}
 .tablewrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
 table{width:100%;border-collapse:collapse;font-size:13px}
 .tablewrap table{min-width:880px}
 thead th{background:#1f3a5f;color:#fff;text-align:left;padding:10px;font-size:11px;text-transform:uppercase;white-space:nowrap;cursor:pointer;user-select:none}
 thead th .ar{font-size:8px;opacity:.5;margin-left:3px}
 td{padding:9px 10px;border-bottom:1px solid #eef0f2}
 td.c,th.c{text-align:center} td.b{font-weight:600} td.mono{font-family:Consolas,monospace;font-size:12px;color:#555}
 .chip{display:inline-block;color:#fff;font-weight:700;font-size:11px;padding:3px 9px;border-radius:10px}
 .pfoot{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;color:#777;font-size:12px;border-top:1px solid #eee;gap:12px;flex-wrap:wrap}
 .fl,.fr{display:flex;align-items:center;gap:10px}
 .pp select{font-size:12px;padding:3px 6px;border:1px solid #cfd6dd;border-radius:6px}
 .pager{display:flex;align-items:center;gap:4px}
 .pager button{border:1px solid #cfd6dd;background:#fff;color:#333;border-radius:6px;padding:4px 9px;font-size:12px;cursor:pointer}
 .pager button:disabled{opacity:.4;cursor:default}
 .pager .cur{font-weight:600;color:#1466a0;padding:0 6px}
 .btnxls{background:#1d6f42;color:#fff;text-decoration:none;padding:9px 16px;border-radius:8px;font-weight:600;font-size:13px}
 .btnxls:hover{background:#175a36}
 .muted{color:#999}
 @media(max-width:760px){
   body{zoom:1}
   .wrap{padding:14px 10px 30px}
   h1{font-size:19px}
   .kpis{grid-template-columns:1fr;gap:10px}
   .ptop{flex-direction:column;align-items:flex-start}
   .controls{width:100%}
   .search{flex:1;min-width:120px}
   .pfoot{flex-direction:column;align-items:stretch}
   .pager{flex-wrap:wrap;justify-content:center}
   .btnxls{text-align:center}
 }
</style></head><body>
<nav class=sidebar>
  <div class=sblogo>🚦</div>
  <button class="sbtn active" data-view=dashboard title="Dashboard">📊</button>
  <button class=sbtn data-view=config title="Configuración">⚙️</button>
</nav>
<div class=main>
<div class=wrap id=view-dashboard>
 <h1>🚦 Semáforo Login — UNILEVER</h1>
 <div class=sub>Actualizado: @@ACTUALIZADO@@ · Centro HUACHIPA</div>
 <div class=kpis>@@KPIS@@</div>
 <div class=panel>
   <div class=ptop>
     <h2>Detalle de pendientes LOGIN (por línea/lote)</h2>
     <div class=controls>
       <span class=flabel>Ubicaciones:</span>
       @@CHIPS@@
       <input class=search id=q placeholder="Buscar artículo/lote...">
     </div>
   </div>
   <div class=tablewrap><table id=tabla><thead><tr>
     <th data-k=ubic data-t=s>Ubicación<span class=ar>&#9650;&#9660;</span></th>
     <th data-k=cod data-t=s>Cód. Artículo<span class=ar>&#9650;&#9660;</span></th>
     <th data-k=art data-t=s>Artículo<span class=ar>&#9650;&#9660;</span></th>
     <th data-k=lote data-t=s>Lote Proveedor<span class=ar>&#9650;&#9660;</span></th>
     <th data-k=usuario data-t=s>Usuario<span class=ar>&#9650;&#9660;</span></th>
     <th class=c data-k=cajas data-t=n>Cantidad<span class=ar>&#9650;&#9660;</span></th>
     <th class=c data-k=fecha data-t=s>Fecha Últ. Mov.<span class=ar>&#9650;&#9660;</span></th>
     <th class=c data-k=dias data-t=n>Días<span class=ar>&#9650;&#9660;</span></th>
   </tr></thead><tbody>@@FILAS@@</tbody></table></div>
   <div class=pfoot>
     <div class=fl>
       <span id=conteo></span>
       <label class=pp>Filas:
         <select id=perPage>
           <option value=auto selected>Auto</option><option>10</option><option>12</option><option>15</option><option>20</option><option>25</option><option>50</option>
         </select>
       </label>
     </div>
     <div class=pager id=pager></div>
     <div class=fr>@@EXCEL@@</div>
   </div>
 </div>
</div>
<div class=wrap id=view-config style="display:none">
 <h1>⚙️ Configuración</h1>
 <div class=sub>Opciones del sistema — Semáforo Login</div>
 <div class=panel style="max-width:760px">
   <div class=ptop><h2>🔑 Credenciales DINET</h2></div>
   <div class=cfgbody>
     <p>Cuando la contraseña de DINET <b>cambie o caduque</b>, el dashboard deja de actualizarse. Para reactivarlo, sigue estos 2 pasos:</p>
     <div class=step><div class=stepn>1</div><div>
       <b>Cambiar la contraseña</b><br>
       <span class=muted>Abre los Secrets de GitHub y edita <code>DINET_PASS</code> (y <code>DINET_USER</code> si también cambió). Pega el valor nuevo y presiona <b>Update secret</b>.</span><br>
       <a class=btncfg href="https://github.com/llKirell/semaforo-login-unilever/settings/secrets/actions" target=_blank rel=noopener>✏️ Cambiar contraseña (GitHub Secrets)</a>
     </div></div>
     <div class=step><div class=stepn>2</div><div>
       <b>Re-ejecutar ahora</b><br>
       <span class=muted>Dispara el proceso para que tome la clave nueva: botón <b>“Run workflow”</b>.</span><br>
       <a class="btncfg alt" href="https://github.com/llKirell/semaforo-login-unilever/actions/workflows/actualizar.yml" target=_blank rel=noopener>▶️ Re-ejecutar ahora (GitHub Actions)</a>
     </div></div>
     <p class=muted style="margin-top:14px">En ~2 minutos el dashboard vuelve a actualizarse. 🔒 Solo tú (dueño del repo, con tu sesión de GitHub) puedes hacer estos cambios.</p>
   </div>
 </div>
</div>
</div>
<script>
 var tbody=document.querySelector('#tabla tbody');
 var filasAll=Array.prototype.slice.call(tbody.querySelectorAll('tr'));
 var idx={ubic:0,cod:1,art:2,lote:3,usuario:4,cajas:5,fecha:6,dias:7};
 var st={col:null,dir:1,page:1,per:10,auto:true,q:''};

 // Calcula cuantas filas caben en la altura visible del monitor.
 function calcPer(){
   var fr=tbody.querySelector('tr');
   var rowH=fr?fr.getBoundingClientRect().height:36; if(rowH<10)rowH=36;
   var top=tbody.getBoundingClientRect().top;
   var pf=document.querySelector('.pfoot');
   var footH=pf?pf.getBoundingClientRect().height:44;
   var avail=window.innerHeight-top-footH-16;
   return Math.max(5,Math.floor(avail/rowH));
 }

 function activas(){var s={};document.querySelectorAll('.fchip').forEach(function(c){if(c.classList.contains('on'))s[c.dataset.ubic]=1});return s;}
 function filtradas(){
   var s=activas(), q=st.q;
   return filasAll.filter(function(tr){
     return s[tr.dataset.ubic] && (q==='' || tr.dataset.buscar.indexOf(q)>=0);
   });
 }
 function ordenar(list){
   if(!st.col) return list;
   var k=st.col, d=st.dir;
   return list.slice().sort(function(a,b){
     var va,vb;
     if(k==='cajas'){va=+a.dataset.cajas;vb=+b.dataset.cajas;}
     else if(k==='dias'){va=+a.dataset.dias;vb=+b.dataset.dias;}
     else{va=a.children[idx[k]].textContent.trim().toLowerCase();vb=b.children[idx[k]].textContent.trim().toLowerCase();}
     if(va<vb)return -1*d; if(va>vb)return 1*d; return 0;
   });
 }
 function boton(txt,pg,dis,cur){
   var b=document.createElement('button'); b.textContent=txt;
   if(cur){b.className='cur';b.disabled=true;} if(dis)b.disabled=true;
   if(!dis&&!cur)b.addEventListener('click',function(){st.page=pg;render();});
   return b;
 }
 function pager(pages){
   var p=document.getElementById('pager'); p.innerHTML='';
   if(pages<=1){return;}
   p.appendChild(boton('« Primera',1,st.page===1));
   p.appendChild(boton('‹ Ant',st.page-1,st.page===1));
   // ventana de paginas alrededor de la actual
   var ini=Math.max(1,st.page-2), fin=Math.min(pages,ini+4); ini=Math.max(1,fin-4);
   for(var i=ini;i<=fin;i++){ p.appendChild(boton(String(i),i,false,i===st.page)); }
   p.appendChild(boton('Sig ›',st.page+1,st.page===pages));
   p.appendChild(boton('Última »',pages,st.page===pages));
 }
 function render(){
   if(st.auto){ st.per=calcPer(); }
   var flt=ordenar(filtradas());
   var pages=Math.max(1,Math.ceil(flt.length/st.per));
   if(st.page>pages)st.page=pages; if(st.page<1)st.page=1;
   var start=(st.page-1)*st.per, end=start+st.per;
   filasAll.forEach(function(r){r.style.display='none';});
   flt.slice(start,end).forEach(function(r){tbody.appendChild(r);r.style.display='';});
   var desde=flt.length?start+1:0, hasta=Math.min(end,flt.length);
   document.getElementById('conteo').textContent='Mostrando '+desde+'-'+hasta+' de '+flt.length+' líneas';
   pager(pages);
 }
 document.querySelectorAll('.fchip').forEach(function(c){c.addEventListener('click',function(){c.classList.toggle('on');st.page=1;render();});});
 document.getElementById('q').addEventListener('input',function(e){st.q=(e.target.value||'').toLowerCase();st.page=1;render();});
 document.getElementById('perPage').addEventListener('change',function(e){
   var v=e.target.value;
   if(v==='auto'){st.auto=true;}else{st.auto=false;st.per=+v;}
   st.page=1;render();
 });
 var rz; window.addEventListener('resize',function(){ if(st.auto && document.getElementById('view-dashboard').style.display!=='none'){ clearTimeout(rz); rz=setTimeout(render,150); } });
 document.querySelectorAll('thead th').forEach(function(th){th.addEventListener('click',function(){
   var k=th.dataset.k; if(st.col===k){st.dir=-st.dir;}else{st.col=k;st.dir=1;} st.page=1; render();
 });});
 render();

 // --- Sidebar: cambiar entre Dashboard y Configuracion ---
 (function(){
   var vDash=document.getElementById('view-dashboard'), vCfg=document.getElementById('view-config');
   document.querySelectorAll('.sbtn').forEach(function(btn){
     btn.addEventListener('click',function(){
       document.querySelectorAll('.sbtn').forEach(function(b){b.classList.remove('active');});
       btn.classList.add('active');
       if(btn.dataset.view==='config'){ vDash.style.display='none'; vCfg.style.display=''; }
       else { vCfg.style.display='none'; vDash.style.display=''; render(); }
     });
   });
 })();
</script>
</body></html>"""
