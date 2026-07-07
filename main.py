"""
Punto de entrada principal.

Flujo:
    1. Obtener precios de todas las tiendas activas.
    2. Guardarlos en SQLite.
    3. Actualizar estadísticas.
    4. Ejecutar el modelo predictivo.
    5. Calcular el Score de compra.
    6. Enviar alertas si corresponde.

Uso:
    python main.py            # ejecuta una vez
    python main.py --loop     # ejecuta cada FRECUENCIA_HORAS (ver config.py)
"""

import sys
import argparse
import time

import config
from database import sqlite as db
from scraper import pccomponentes, game
from analysis.statistics import calcular_estadisticas, cargar_dataframe
from analysis.score import calcular_score
from analysis.predictor import predecir_precio
from alerts.telegram import enviar_alerta_telegram
from alerts.email import enviar_alerta_email

SCRAPERS = {
    "pccomponentes": pccomponentes.obtener_precio,
    "game": game.obtener_precio,
}


def ejecutar_scraping():
    resultados = []
    for tienda in config.TIENDAS_ACTIVAS:
        scraper_fn = SCRAPERS.get(tienda)
        if not scraper_fn:
            print(f"[main] No hay scraper implementado todavía para '{tienda}'")
            continue
        print(f"[main] Consultando {tienda}...")
        resultado = scraper_fn()
        if resultado:
            db.insertar_precio(
                tienda=resultado["tienda"],
                precio=resultado["precio"],
                envio=resultado.get("envio", 0.0),
                stock=resultado.get("stock", True),
                bundle=resultado.get("bundle", False),
                url=resultado.get("url", ""),
            )
            resultados.append(resultado)
            print(f"[main]   -> {resultado['precio']} € (stock: {resultado['stock']})")
        else:
            print(f"[main]   -> Sin resultado válido para {tienda}")
    return resultados


def evaluar_y_alertar(estadisticas, score_info):
    if "error" in estadisticas or score_info["score"] is None:
        return

    razones = []
    if estadisticas["precio_actual"] <= estadisticas["media_90_dias"]:
        razones.append("precio por debajo de la media de 90 días")
    if estadisticas["precio_actual"] <= estadisticas["precio_minimo_historico"]:
        razones.append("nuevo mínimo histórico")
    if score_info["score"] > 90:
        razones.append("score de compra superior a 90")

    if not razones:
        return

    mensaje = (
        f"🎮 Nintendo Switch 2 - Alerta de precio\n"
        f"Precio actual: {estadisticas['precio_actual']} €\n"
        f"Score de compra: {score_info['score']} ({score_info['recomendacion']})\n"
        f"Motivo: {', '.join(razones)}"
    )
    print(f"[main] ALERTA: {mensaje}")
    enviar_alerta_telegram(mensaje)
    enviar_alerta_email("Alerta de precio - Nintendo Switch 2", mensaje)


def enviar_resumen_diario(estadisticas, score_info, prediccion):
    """Envía un email con el estado del día, haya o no una oferta especial."""
    if "error" in estadisticas or score_info["score"] is None:
        print("[main] No hay datos suficientes todavía para el resumen diario.")
        return

    ultimos = db.obtener_ultimo_precio_por_tienda()
    lineas_tiendas = "\n".join(
        f"  - {p['tienda']}: {p['precio']} € "
        f"{'(sin stock)' if not p['stock'] else ''}"
        for p in sorted(ultimos, key=lambda x: x["precio"])
    )

    linea_prediccion = ""
    if prediccion.get("probabilidad_bajada_pct") is not None:
        linea_prediccion = (
            f"\nPredicción ({prediccion['metodo']}): "
            f"{prediccion['probabilidad_bajada_pct']}% de probabilidad de que baje "
            f"en los próximos días."
        )

    mensaje = (
        f"🎮 Resumen diario - Nintendo Switch 2\n"
        f"Fecha: {__import__('datetime').date.today().isoformat()}\n\n"
        f"Precios actuales por tienda:\n{lineas_tiendas}\n\n"
        f"Mínimo histórico: {estadisticas['precio_minimo_historico']} €\n"
        f"Media últimos 30 días: {estadisticas['media_30_dias']} €\n"
        f"Media últimos 90 días: {estadisticas['media_90_dias']} €\n"
        f"Tendencia: {estadisticas['tendencia']}\n"
        f"{linea_prediccion}\n\n"
        f"Score de compra: {score_info['score']}/100 -> {score_info['recomendacion']}"
    )

    print(f"[main] Enviando resumen diario por email...")
    enviado = enviar_alerta_email("Resumen diario - Nintendo Switch 2", mensaje)
    if enviado:
        print("[main] Resumen diario enviado correctamente.")


def ejecutar_ciclo_completo(resumen_diario=False):
    db.init_db()
    ejecutar_scraping()

    df = cargar_dataframe()
    estadisticas = calcular_estadisticas(df)
    print("\n--- Estadísticas ---")
    for k, v in estadisticas.items():
        print(f"  {k}: {v}")

    prediccion = predecir_precio(df=df)
    print("\n--- Predicción ---")
    print(f"  Método: {prediccion['metodo']}")
    if prediccion.get("probabilidad_bajada_pct") is not None:
        print(f"  Probabilidad de bajada: {prediccion['probabilidad_bajada_pct']}%")

    score_info = calcular_score(estadisticas)
    print("\n--- Score de compra ---")
    print(f"  Score: {score_info['score']} -> {score_info['recomendacion']}")

    evaluar_y_alertar(estadisticas, score_info)

    if resumen_diario:
        enviar_resumen_diario(estadisticas, score_info, prediccion)


def main():
    parser = argparse.ArgumentParser(description="Analizador de precios Nintendo Switch 2")
    parser.add_argument("--loop", action="store_true", help="Ejecutar continuamente cada FRECUENCIA_HORAS")
    parser.add_argument(
        "--resumen-diario",
        action="store_true",
        help="Envía por email un resumen con los precios del día, haya o no una oferta especial",
    )
    args = parser.parse_args()

    if args.loop:
        print(f"[main] Modo continuo activado (cada {config.FRECUENCIA_HORAS}h). Ctrl+C para detener.")
        while True:
            ejecutar_ciclo_completo(resumen_diario=args.resumen_diario)
            time.sleep(config.FRECUENCIA_HORAS * 3600)
    else:
        ejecutar_ciclo_completo(resumen_diario=args.resumen_diario)


if __name__ == "__main__":
    main()
