"""
Scraper para GAME (game.es).

A diferencia de otras tiendas, GAME tiene una URL de ficha de producto FIJA
para la Nintendo Switch 2 (confirmada por el usuario):
    https://www.game.es/hardware/consola/nintendo-switch-2/nintendo-switch-2/243868

Por eso este scraper va directo a esa ficha en vez de depender de la
página de resultados de búsqueda (más simple y más fiable: no depende de
que el buscador siga devolviendo el producto en primera posición).

Estructura real del precio en la ficha (comprobada en julio 2026):
    <div class="buy--price">
        <span class="int">469</span>
        <span class="decimal">'99</span>
        <span class="currency">€</span>
    </div>

NOTA: si GAME cambia el HTML de la ficha, habrá que volver a inspeccionar
la página (F12 -> Inspector) y ajustar los selectores de aquí abajo.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from scraper.base import descargar_html, soup_de, ScraperError

TIENDA = "game"


def obtener_precio():
    """
    Devuelve un dict con: tienda, precio, envio, stock, bundle, url
    o None si no se ha podido obtener el precio.
    """
    url_producto = config.TIENDAS_URLS[TIENDA]["url_busqueda"]

    try:
        html = descargar_html(url_producto)
    except ScraperError as e:
        print(f"[{TIENDA}] {e}")
        return None

    soup = soup_de(html)

    precio = _extraer_precio(soup)
    if precio is None:
        print(f"[{TIENDA}] No se encontró el precio en la ficha de producto. "
              f"Revisa el selector CSS en scraper/game.py (puede que GAME "
              f"haya cambiado el HTML).")
        return None

    # Si no hay bloque de "Añadir a la cesta" activo, asumimos sin stock
    # (GAME sustituye la compra por el botón "Avísame" cuando se agota).
    boton_compra = soup.select_one("button.buy-button, #btnNEW")
    hay_stock = boton_compra is not None

    titulo_el = soup.find("title")
    titulo = titulo_el.get_text(strip=True) if titulo_el else ""

    return {
        "tienda": TIENDA,
        "precio": precio,
        "envio": 0.0,
        "stock": hay_stock,
        "bundle": "bundle" in titulo.lower() or "pack" in titulo.lower(),
        "url": url_producto,
    }


def _extraer_precio(soup):
    """
    Reconstruye el precio a partir de los 3 spans (entero, decimal, moneda)
    dentro de div.buy--price.
    """
    contenedor = soup.select_one("div.buy--price")
    if contenedor is None:
        return None

    entero_el = contenedor.select_one("span.int")
    decimal_el = contenedor.select_one("span.decimal")

    if entero_el is None:
        return None

    entero = entero_el.get_text(strip=True)
    # El decimal viene como "'99" (con comilla simple delante) -> limpiar
    decimal = (decimal_el.get_text(strip=True) if decimal_el else "00").lstrip("'").lstrip(",")

    if not decimal:
        decimal = "00"

    try:
        return float(f"{entero}.{decimal}")
    except ValueError:
        return None


if __name__ == "__main__":
    resultado = obtener_precio()
    print(resultado)
