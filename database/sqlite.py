"""
Capa de acceso a datos - SQLite

Tabla `precios`:
    id, fecha, hora, tienda, precio, envio, stock, bundle, url
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


@contextmanager
def get_connection():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Crea la tabla `precios` si no existe."""
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS precios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                tienda TEXT NOT NULL,
                precio REAL NOT NULL,
                envio REAL DEFAULT 0,
                stock INTEGER NOT NULL,
                bundle INTEGER DEFAULT 0,
                url TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_fecha ON precios (fecha)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tienda ON precios (tienda)"
        )


def insertar_precio(tienda, precio, envio=0.0, stock=True, bundle=False, url=""):
    """Inserta un registro de precio con la fecha/hora actuales."""
    ahora = datetime.now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO precios (fecha, hora, tienda, precio, envio, stock, bundle, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ahora.strftime("%Y-%m-%d"),
                ahora.strftime("%H:%M:%S"),
                tienda,
                precio,
                envio,
                int(bool(stock)),
                int(bool(bundle)),
                url,
            ),
        )


def obtener_todos(dias=None):
    """Devuelve todos los registros, opcionalmente limitados a los últimos N días."""
    query = "SELECT * FROM precios"
    params = ()
    if dias is not None:
        query += " WHERE date(fecha) >= date('now', ?)"
        params = (f"-{dias} days",)
    query += " ORDER BY fecha, hora"
    with get_connection() as conn:
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def obtener_ultimo_precio_por_tienda():
    """Devuelve el último registro conocido de cada tienda."""
    query = """
        SELECT p.*
        FROM precios p
        INNER JOIN (
            SELECT tienda, MAX(fecha || ' ' || hora) AS max_fh
            FROM precios
            GROUP BY tienda
        ) ult ON p.tienda = ult.tienda AND (p.fecha || ' ' || p.hora) = ult.max_fh
    """
    with get_connection() as conn:
        cursor = conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    init_db()
    print(f"Base de datos inicializada en: {config.DB_PATH}")
