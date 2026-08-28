"""
src/database/db.py
------------------
Conexion y creacion del esquema SQLite (P-013).

SQLite viene incluido en Python (modulo sqlite3), no instala nada.
La base vive en data/semaforo.db. El esquema sigue el modelo del
documento (EJECUCION, DETALLE_LOGIN, ERROR_EJECUCION, CONFIGURACION),
con un par de campos extra utiles (total_registros).
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "semaforo.db"

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS ejecucion (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha             TEXT NOT NULL,          -- YYYY-MM-DD
    hora              TEXT NOT NULL,          -- HH:MM:SS
    tipo_ejecucion    TEXT NOT NULL,          -- inicio / mediodia / cierre / manual
    estado            TEXT NOT NULL,          -- OK / PARCIAL / FALLIDA
    total_login       INTEGER DEFAULT 0,      -- ubicaciones pendientes
    total_lineas      INTEGER DEFAULT 0,      -- lineas (Ubic+Articulo+Lote)
    total_cajas       INTEGER DEFAULT 0,      -- cajas (suma CantidadFinalUMS)
    total_verde       INTEGER DEFAULT 0,
    total_amarillo    INTEGER DEFAULT 0,
    total_rojo        INTEGER DEFAULT 0,
    total_observacion INTEGER DEFAULT 0,
    total_nuevas      INTEGER DEFAULT 0,
    total_despejadas  INTEGER DEFAULT 0,
    porcentaje_avance REAL DEFAULT 0,
    fecha_creacion    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS detalle_login (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ejecucion_id        INTEGER NOT NULL,
    ubicacion           TEXT NOT NULL,
    num_lineas          INTEGER DEFAULT 0,
    total_cajas         INTEGER DEFAULT 0,
    ultima_modificacion TEXT,                 -- fecha mas antigua
    antiguedad_dias     INTEGER,
    estado_semaforo     TEXT,
    observacion         TEXT,
    FOREIGN KEY (ejecucion_id) REFERENCES ejecucion(id)
);

CREATE TABLE IF NOT EXISTS error_ejecucion (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ejecucion_id INTEGER,
    tipo_error   TEXT,
    modulo       TEXT,
    descripcion  TEXT,
    fecha        TEXT,
    hora         TEXT
);

CREATE TABLE IF NOT EXISTS configuracion (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    clave       TEXT UNIQUE,
    valor       TEXT,
    descripcion TEXT
);
"""


def get_conn() -> sqlite3.Connection:
    """Devuelve una conexion con filas accesibles por nombre de columna."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Crea las tablas si no existen (idempotente)."""
    with get_conn() as conn:
        conn.executescript(_ESQUEMA)
