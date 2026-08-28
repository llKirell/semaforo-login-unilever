"""
src/w4w/login.py
----------------
Proceso P-002: autenticar en AppDinet.

Selectores REALES confirmados desde el robot ya probado (w4w-legacy-bridge):
    usuario     -> #txtUsuario
    contrasena  -> #txtContrasenia
    boton       -> #btnIngresar
El login solo pide usuario + contrasena (no hay campo "Company").
Mantenemos pequeños fallbacks por si DINET cambia una version.
"""

from playwright.sync_api import Page

from config import settings


def _primer_selector(page: Page, selectores: list[str], descripcion: str, timeout: int = 4000) -> str:
    """Devuelve el primer selector que aparezca visible; error claro si ninguno."""
    for sel in selectores:
        try:
            page.wait_for_selector(sel, timeout=timeout)
            return sel
        except Exception:
            continue
    raise RuntimeError(f"[LOGIN] No pude ubicar: {descripcion}. Revisa la pantalla de login.")


def iniciar_sesion(page: Page) -> None:
    """Abre AppDinet y autentica. Deja la sesion (cookies) lista para la API."""
    print("  [P-002] Abriendo AppDinet:", settings.URL_LOGIN)
    page.goto(settings.URL_LOGIN, wait_until="domcontentloaded")
    page.wait_for_timeout(1500)

    user_sel = _primer_selector(
        page,
        ["#txtUsuario", "input[name='txtUsuario']", "input[id*='usuario' i]", "input[type='text']"],
        "campo Usuario",
    )
    pass_sel = _primer_selector(
        page,
        ["#txtContrasenia", "input[name='txtContrasenia']", "input[type='password']"],
        "campo Contraseña",
    )
    btn_sel = _primer_selector(
        page,
        ["#btnIngresar", "button[type='submit']", "button:has-text('Ingresar')", "input[type='submit']"],
        "botón Ingresar",
    )
    print(f"  [P-002] Selectores login -> user={user_sel} pass={pass_sel} btn={btn_sel}")

    page.fill(user_sel, settings.DINET_USER)
    page.fill(pass_sel, settings.DINET_PASS)  # nunca imprimimos el valor
    print("  [P-002] Credenciales ingresadas. Enviando...")
    page.click(btn_sel)

    # Esperamos a que la cookie de sesion quede establecida antes de usar la API.
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        page.wait_for_timeout(3000)
    print("  [P-002] Login enviado. URL actual:", page.url)
