"""
src/w4w/context.py
------------------
Proceso P-003: fijar el contexto HUACHIPA / UNILEVER SIN clics de UI.

En lugar de navegar los <select> de la pantalla de seleccion, replicamos
las 3 llamadas de backend que hace la web (patron tomado del robot ya
probado). Requiere que el login ya haya dejado las cookies activas.

    1) RedirectSystem      -> entra al sistema WMSD (W4WWEB)
    2) ListarCuentas       -> el backend prepara las cuentas del CD
    3) AssignmentCredentials -> fija CD=HUACHIPA y Cuenta=UNILEVER en la sesion
"""

from playwright.sync_api import BrowserContext

from config import settings


def fijar_contexto_unilever(context: BrowserContext) -> None:
    """Deja la sesion configurada en HUACHIPA + UNILEVER via API."""
    req = context.request

    print("  [P-003] (1/3) RedirectSystem -> WMSD")
    r1 = req.post(settings.URL_REDIRECT_SYSTEM, data={"SystemCode": settings.SYSTEM_CODE}, timeout=120000)
    print(f"           HTTP {r1.status}")

    print("  [P-003] (2/3) ListarCuentas -> CD", settings.DISTRIBUTION_CENTER)
    r2 = req.post(
        settings.URL_LISTAR_CUENTAS,
        data={"CodigoCentroDistribucion": settings.DISTRIBUTION_CENTER_CODE},
        timeout=120000,
    )
    print(f"           HTTP {r2.status}")

    print("  [P-003] (3/3) AssignmentCredentials -> Cuenta", settings.ACCOUNT)
    r3 = req.post(
        settings.URL_ASSIGNMENT_CREDENTIALS,
        data={
            "distributionCenterCode": settings.DISTRIBUTION_CENTER_CODE,
            "distributionCenter": settings.DISTRIBUTION_CENTER,
            "accountCode": settings.ACCOUNT_CODE,
            "account": settings.ACCOUNT,
        },
        timeout=120000,
    )
    print(f"           HTTP {r3.status}")

    if not (r1.ok and r2.ok and r3.ok):
        raise RuntimeError(
            "[P-003] Alguna llamada de contexto no respondio OK. "
            "Verifica que el login haya sido exitoso (cookies activas)."
        )
    print("  [P-003] Contexto HUACHIPA/UNILEVER fijado correctamente.")
