"""
config/ubicaciones.py
---------------------
LISTA EDITABLE de ubicaciones a monitorear.

>>> PARA AGREGAR UNA NUEVA UBICACION EN EL FUTURO:
    Solo añade una linea nueva dentro de UBICACIONES_MONITOREADAS,
    con el codigo EXACTO entre comillas y una coma al final.
    Ejemplo:  "LOGI.DEVOL",

    Guarda el archivo y listo. No necesitas tocar nada mas ni saber
    programar: es una simple lista de textos.
"""

# Ubicaciones EXACTAS que el sistema considera "pendientes LOGIN".
UBICACIONES_MONITOREADAS = [
    # --- Lista vigente (2026-10-14) ---
    "LOGI.JAULA01",
    "LOGI.JAULA02",
    "LOGI.JAULA03",
    "LOGI.JAULA04",
    "LOGI.JAULA05",
    "LOGI.JAULA06",
    "LOGI.JAULA07",
    "LOGI.JAULA08",
    "LOGI.JAULA09",
    "LOGI.JAULA10",
    "LOGI.ALMACEN",
    "LOGI.RECEP",
    "LOGIN",
    # "LOGI.DEVOL",   # <- ejemplo: agrega nuevas ubicaciones aqui
]

# Modo de coincidencia:
#   "exacto"  -> solo coincide el codigo IDENTICO (LOGIN != LOGIN.RC.39).
#                Es lo que usamos: monitorea unicamente las de la lista.
#   "prefijo" -> cada texto seria una FAMILIA ("LOGIN" abarcaria
#                LOGIN, LOGIN.RC.39, etc.). NO se usa por ahora.
MODO_COINCIDENCIA = "exacto"
