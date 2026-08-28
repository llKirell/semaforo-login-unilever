# Semáforo Login — Monitoreo LOGIN Unilever (W4W)

Automatizacion **solo de consulta** para monitorear ubicaciones con LOGIN
de la cuenta UNILEVER (CD HUACHIPA) en W4W DINET.

> Estado: **Fase 1**. Reutiliza el patron probado del robot
> `w4w-legacy-bridge`: login por UI + fijar contexto por backend +
> consulta por **API (JSON)**, sin descargar Excel.

## Flujo

```
Login (UI)  ->  Fijar contexto HUACHIPA/UNILEVER (3 POST backend)  ->  Inventario Saldo (API JSON)
```

## Instalacion (una sola vez)

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
```

## Credenciales

Copia la plantilla y complétala (misma convencion que el robot de referencia):

```bash
copy .env.example .env
```

Rellena en `.env`: `DINET_USER`, `DINET_PASS`. Nunca se versiona.

## Paso actual: descubrir el endpoint de Inventario Saldo

Aun no conocemos la URL de API del saldo. La detectamos con:

```bash
python descubrir_endpoint_saldo.py
```

El script hace login, fija contexto, abre Inventario Saldo y **espia la red**.
Cuando presiones "Consultar" en el navegador, captura los endpoints POST y
genera `descubrimiento_saldo.json` con URL, payload y muestra de respuesta.
El endpoint marcado `*** PROBABLE ***` es el candidato.

Una vez confirmado, se fija en `.env` como `W4W_SALDO_ENDPOINT` y se cablea
la consulta por API.

## Probar la navegacion base (sin descubrimiento)

```bash
python main.py
```

Resultado esperado: termina en
`https://w4w.dinet.com.pe/AppWeb/Consultas/InventarioSaldo/` y guarda
`validacion_fase1.png` con el saldo de UNILEVER visible.

## Estructura

```
config/settings.py      credenciales (.env) + endpoints/codigos confirmados
src/w4w/login.py        P-002 autenticar (selectores reales)
src/w4w/context.py      P-003 fijar HUACHIPA/UNILEVER por backend
descubrir_endpoint_saldo.py   herramienta de diagnostico (una vez)
main.py                 orquestador Fase 1
```
