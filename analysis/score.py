"""
Índice Inteligente de Compra (0-100).

Componentes (pesos configurables en config.PESOS_SCORE):
    40% Cercanía al mínimo histórico
    30% Tendencia bajista
    20% Descuento respecto a la media (90 días)
    10% Época del año (proximidad a eventos comerciales fuertes)
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def _score_cercania_minimo(precio_actual, minimo, maximo):
    """100 si precio_actual == minimo, 0 si precio_actual == maximo."""
    if maximo == minimo:
        return 50.0
    posicion = (maximo - precio_actual) / (maximo - minimo)
    return max(0.0, min(100.0, posicion * 100))


def _score_tendencia(tendencia, variacion_semanal_pct):
    if tendencia == "bajando":
        # cuanto más negativa la variación, más puntos (tope 100)
        magnitud = min(abs(variacion_semanal_pct or 0), 10) / 10
        return 60 + magnitud * 40
    if tendencia == "estable":
        return 50.0
    if tendencia == "subiendo":
        magnitud = min(abs(variacion_semanal_pct or 0), 10) / 10
        return max(0.0, 40 - magnitud * 40)
    return 50.0  # datos insuficientes -> neutro


def _score_descuento_media(precio_actual, media_90):
    if not media_90 or media_90 == 0:
        return 50.0
    descuento_pct = ((media_90 - precio_actual) / media_90) * 100
    # +15% de descuento -> 100 puntos; 0% -> 50 puntos; -15% (más caro) -> 0
    return max(0.0, min(100.0, 50 + (descuento_pct / 15) * 50))


def _score_epoca_del_anio(fecha=None):
    fecha = fecha or datetime.now()
    mes = fecha.month
    dia = fecha.day

    mejor_peso = 0.0
    for mes_evento, info in config.EVENTOS_COMERCIALES.items():
        mes_entero = int(mes_evento)
        if mes_entero == mes:
            mejor_peso = max(mejor_peso, info["peso"])
    return mejor_peso * 100


def calcular_score(estadisticas):
    """
    Recibe el dict devuelto por analysis.statistics.calcular_estadisticas()
    y devuelve: {"score": int, "recomendacion": str, "detalle": {...}}
    """
    if "error" in estadisticas:
        return {
            "score": None,
            "recomendacion": "SIN DATOS",
            "detalle": {},
            "mensaje": estadisticas["error"],
        }

    s_minimo = _score_cercania_minimo(
        estadisticas["precio_actual"],
        estadisticas["precio_minimo_historico"],
        estadisticas["precio_maximo_historico"],
    )
    s_tendencia = _score_tendencia(
        estadisticas["tendencia"], estadisticas.get("variacion_semanal_pct")
    )
    s_descuento = _score_descuento_media(
        estadisticas["precio_actual"], estadisticas.get("media_90_dias")
    )
    s_epoca = _score_epoca_del_anio()

    pesos = config.PESOS_SCORE
    score_final = (
        s_minimo * pesos["cercania_minimo"]
        + s_tendencia * pesos["tendencia_bajista"]
        + s_descuento * pesos["descuento_media"]
        + s_epoca * pesos["epoca_del_anio"]
    )
    score_final = round(score_final)

    if score_final >= config.UMBRAL_COMPRAR:
        recomendacion = "COMPRAR"
    elif score_final >= config.UMBRAL_ESPERAR:
        recomendacion = "ESPERAR"
    else:
        recomendacion = "NO RECOMENDADO"

    return {
        "score": score_final,
        "recomendacion": recomendacion,
        "detalle": {
            "cercania_minimo": round(s_minimo, 1),
            "tendencia": round(s_tendencia, 1),
            "descuento_media": round(s_descuento, 1),
            "epoca_del_anio": round(s_epoca, 1),
        },
    }


if __name__ == "__main__":
    from analysis.statistics import calcular_estadisticas

    stats = calcular_estadisticas()
    resultado = calcular_score(stats)
    print(resultado)
