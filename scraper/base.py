"""
Utilidades comunes para los scrapers.
"""

import re
import sys
import os

import requests
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class ScraperError(Exception):
    pass


def descargar_html(url):
    """Descarga el HTML de una URL usando cabeceras de navegador real."""
    try:
        resp = requests.get(
            url, headers=config.HTTP_HEADERS, timeout=config.REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        raise ScraperError(f"Error descargando {url}: {e}") from e


def parsear_precio(texto):
    """
    Convierte un texto de precio en español (ej. '469,99 €' o '1.234,00€')
    a un float (1234.00).
    Devuelve None si no se puede parsear.
    """
    if not texto:
        return None
    texto = texto.strip()
    # Quita todo lo que no sea dígito, coma o punto
    limpio = re.sub(r"[^\d,.]", "", texto)
    if not limpio:
        return None
    # Formato español: punto = miles, coma = decimales
    if "," in limpio:
        limpio = limpio.replace(".", "").replace(",", ".")
    try:
        return float(limpio)
    except ValueError:
        return None


def soup_de(html):
    return BeautifulSoup(html, "html.parser")


def contiene_switch2(texto):
    """Filtro simple para descartar resultados que no sean la Switch 2."""
    if not texto:
        return False
    t = texto.lower()
    return "switch 2" in t or "switch2" in t
