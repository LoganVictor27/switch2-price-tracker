"""
Scraper para PcComponentes.

NOTA IMPORTANTE:
Las webs cambian su HTML con frecuencia. Los selectores CSS de aquí abajo
son un punto de partida razonable a fecha de escritura, pero es MUY
probable que tengas que ajustarlos abriendo la página de resultados con
las herramientas de desarrollador del navegador (F12 -> Inspeccionar) y
comprobando las clases reales de la tarjeta de producto y del precio.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from scraper.base import descargar_html, soup_de, parsear_precio, contiene_switch2, ScraperError

TIENDA = "pccomponentes"


def obtener_precio():
    """
    Devuelve un dict con: tienda, precio, envio, stock, bundle, url
    o None si no se ha podido obtener ningún resultado válido.
    """
    url_busqueda = config.TIENDAS_URLS[TIENDA]["url_busqueda"]

    try:
        html = descargar_html(url_busqueda)
    except ScraperError as e:
        print(f"[{TIENDA}] {e}")
        return None

    soup = soup_de(html)

    # Tarjetas de producto en el listado de búsqueda.
    # Selector orientativo: ajustar tras inspeccionar el HTML real.
    tarjetas = soup.select("article[data-product-id], div.product-card, a.product-card-title")

    if not tarjetas:
        print(f"[{TIENDA}] No se encontraron tarjetas de producto. "
              f"Revisa el selector CSS en scraper/pccomponentes.py")
        return None

    for tarjeta in tarjetas:
        titulo = tarjeta.get_text(" ", strip=True)
        if not contiene_switch2(titulo):
            continue

        # Busca el precio dentro de la tarjeta o en un contenedor cercano
        precio_el = tarjeta.select_one(
            "span.pdp-price, span[class*='price'], div[class*='price']"
        )
        precio = parsear_precio(precio_el.get_text() if precio_el else None)
        if precio is None:
            continue

        # Enlace al producto
        link_el = tarjeta if tarjeta.name == "a" else tarjeta.select_one("a")
        href = link_el.get("href") if link_el else None
        url_producto = (
            href if (href and href.startswith("http"))
            else f"https://www.pccomponentes.com{href}" if href else url_busqueda
        )

        stock_el = tarjeta.select_one("[class*='stock'], [class*='availability']")
        stock_texto = stock_el.get_text(strip=True).lower() if stock_el else ""
        sin_stock = any(p in stock_texto for p in ["agotado", "sin stock", "no disponible"])

        return {
            "tienda": TIENDA,
            "precio": precio,
            "envio": 0.0,  # PcComponentes normalmente muestra envío gratis para este tipo de producto
            "stock": not sin_stock,
            "bundle": "bundle" in titulo.lower() or "pack" in titulo.lower(),
            "url": url_producto,
        }

    print(f"[{TIENDA}] Se encontraron tarjetas pero ninguna coincide con 'Switch 2'.")
    return None


if __name__ == "__main__":
    resultado = obtener_precio()
    print(resultado)
