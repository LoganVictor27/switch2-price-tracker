"""
Predicción de precios a corto plazo.

Empieza con un modelo simple y robusto (regresión lineal sobre los últimos
N días) que funciona incluso con pocos datos, y usa ARIMA (statsmodels)
en cuanto hay histórico suficiente (>= 14 puntos). Prophet/XGBoost/LightGBM
quedan como mejoras futuras marcadas en el propio código: con pocos meses
de histórico real, un modelo simple es más fiable que uno complejo
sobre-ajustado.
"""

import sys
import os
import warnings

import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis.statistics import cargar_dataframe

MIN_PUNTOS_REGRESION = 3
MIN_PUNTOS_ARIMA = 14


def _serie_diaria(df):
    """Colapsa el histórico a un precio medio por día."""
    diaria = df.groupby(df["fecha_dt"].dt.date)["precio_total"].mean()
    diaria.index = pd.to_datetime(diaria.index)
    return diaria.sort_index()


def predecir_precio(dias_adelante=7, df=None):
    """
    Devuelve:
        {
          "metodo": "regresion_lineal" | "arima" | "insuficiente",
          "prediccion": [{"fecha": ..., "precio_estimado": ...}, ...],
          "probabilidad_bajada_pct": float | None,
        }
    """
    if df is None:
        df = cargar_dataframe()

    if df.empty:
        return {"metodo": "insuficiente", "prediccion": [], "probabilidad_bajada_pct": None}

    serie = _serie_diaria(df)

    if len(serie) < MIN_PUNTOS_REGRESION:
        return {
            "metodo": "insuficiente",
            "prediccion": [],
            "probabilidad_bajada_pct": None,
            "mensaje": "Aún no hay histórico suficiente para predecir (mínimo 3 días con datos).",
        }

    if len(serie) >= MIN_PUNTOS_ARIMA:
        resultado = _predecir_arima(serie, dias_adelante)
        if resultado is not None:
            return resultado
        # Si ARIMA falla por cualquier motivo, cae a regresión lineal

    return _predecir_regresion_lineal(serie, dias_adelante)


def _predecir_regresion_lineal(serie, dias_adelante):
    x = np.arange(len(serie))
    y = serie.values
    pendiente, intercepto = np.polyfit(x, y, 1)

    ultima_fecha = serie.index[-1]
    predicciones = []
    for i in range(1, dias_adelante + 1):
        valor = pendiente * (len(serie) - 1 + i) + intercepto
        fecha = ultima_fecha + pd.Timedelta(days=i)
        predicciones.append({"fecha": fecha.strftime("%Y-%m-%d"), "precio_estimado": round(float(valor), 2)})

    precio_actual = float(y[-1])
    precio_final_previsto = predicciones[-1]["precio_estimado"]
    prob_bajada = _pendiente_a_probabilidad(pendiente, precio_actual)

    return {
        "metodo": "regresion_lineal",
        "prediccion": predicciones,
        "probabilidad_bajada_pct": prob_bajada,
    }


def _predecir_arima(serie, dias_adelante):
    try:
        from statsmodels.tsa.arima.model import ARIMA
    except ImportError:
        return None

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            modelo = ARIMA(serie.values, order=(1, 1, 1))
            ajuste = modelo.fit()
            forecast = ajuste.forecast(steps=dias_adelante)
    except Exception:
        return None

    ultima_fecha = serie.index[-1]
    predicciones = [
        {
            "fecha": (ultima_fecha + pd.Timedelta(days=i + 1)).strftime("%Y-%m-%d"),
            "precio_estimado": round(float(v), 2),
        }
        for i, v in enumerate(forecast)
    ]

    precio_actual = float(serie.values[-1])
    pendiente_aprox = (predicciones[-1]["precio_estimado"] - precio_actual) / max(dias_adelante, 1)
    prob_bajada = _pendiente_a_probabilidad(pendiente_aprox, precio_actual)

    return {
        "metodo": "arima",
        "prediccion": predicciones,
        "probabilidad_bajada_pct": prob_bajada,
    }


def _pendiente_a_probabilidad(pendiente, precio_actual):
    """
    Heurística simple: convierte la pendiente diaria (en % del precio actual)
    en una probabilidad de bajada entre 5% y 95% (nunca 0/100% con tan poco histórico).
    """
    if precio_actual == 0:
        return 50.0
    pendiente_pct_diaria = (pendiente / precio_actual) * 100
    # Pendiente muy negativa -> probabilidad alta de bajada
    probabilidad = 50 - pendiente_pct_diaria * 20
    return round(max(5.0, min(95.0, probabilidad)), 1)


if __name__ == "__main__":
    resultado = predecir_precio()
    print(resultado)
