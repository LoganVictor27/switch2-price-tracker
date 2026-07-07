"""
Motor de análisis estadístico sobre el histórico de precios.
"""

import sys
import os
from datetime import datetime, timedelta

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from database import sqlite as db


def cargar_dataframe(dias=None):
    """Carga el histórico (opcionalmente limitado a N días) como DataFrame."""
    registros = db.obtener_todos(dias=dias)
    if not registros:
        return pd.DataFrame(
            columns=["fecha", "hora", "tienda", "precio", "envio", "stock", "bundle", "url"]
        )
    df = pd.DataFrame(registros)
    df["fecha_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"])
    df["precio_total"] = df["precio"] + df["envio"].fillna(0)
    return df


def calcular_estadisticas(df=None):
    """
    Devuelve un diccionario con las métricas clave:
    mínimo/máximo histórico, medias móviles, desviación estándar,
    variación semanal/mensual y tendencia.
    """
    if df is None:
        df = cargar_dataframe()

    if df.empty:
        return {"error": "No hay datos suficientes en el histórico todavía."}

    ahora = datetime.now()

    precio_min = df["precio_total"].min()
    precio_max = df["precio_total"].max()

    def media_ultimos(dias):
        corte = ahora - timedelta(days=dias)
        subset = df[df["fecha_dt"] >= corte]
        return subset["precio_total"].mean() if not subset.empty else None

    media_30 = media_ultimos(config.VENTANA_CORTA)
    media_90 = media_ultimos(config.VENTANA_MEDIA)
    media_180 = media_ultimos(config.VENTANA_LARGA)

    desviacion = df["precio_total"].std()

    # Variación semanal / mensual: comparación del precio medio de la
    # última semana/mes frente al periodo anterior equivalente.
    def variacion(dias):
        corte_actual = ahora - timedelta(days=dias)
        corte_anterior = ahora - timedelta(days=dias * 2)
        actual = df[df["fecha_dt"] >= corte_actual]["precio_total"].mean()
        anterior = df[
            (df["fecha_dt"] >= corte_anterior) & (df["fecha_dt"] < corte_actual)
        ]["precio_total"].mean()
        if pd.isna(actual) or pd.isna(anterior) or anterior == 0:
            return None
        return round(((actual - anterior) / anterior) * 100, 2)

    variacion_semanal = variacion(7)
    variacion_mensual = variacion(30)

    precio_actual = df.sort_values("fecha_dt").iloc[-1]["precio_total"]

    if variacion_semanal is None:
        tendencia = "insuficientes datos"
    elif variacion_semanal < -0.5:
        tendencia = "bajando"
    elif variacion_semanal > 0.5:
        tendencia = "subiendo"
    else:
        tendencia = "estable"

    return {
        "precio_actual": round(float(precio_actual), 2),
        "precio_minimo_historico": round(float(precio_min), 2),
        "precio_maximo_historico": round(float(precio_max), 2),
        "media_30_dias": round(float(media_30), 2) if media_30 is not None else None,
        "media_90_dias": round(float(media_90), 2) if media_90 is not None else None,
        "media_180_dias": round(float(media_180), 2) if media_180 is not None else None,
        "desviacion_estandar": round(float(desviacion), 2) if pd.notna(desviacion) else None,
        "variacion_semanal_pct": variacion_semanal,
        "variacion_mensual_pct": variacion_mensual,
        "tendencia": tendencia,
    }


if __name__ == "__main__":
    stats = calcular_estadisticas()
    for k, v in stats.items():
        print(f"{k}: {v}")
