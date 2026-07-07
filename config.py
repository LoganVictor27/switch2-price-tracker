"""
Configuración central del Analizador de Precios - Nintendo Switch 2 (España)
"""

import os

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "precios.db")

# ---------------------------------------------------------------------------
# Producto a monitorizar
# ---------------------------------------------------------------------------
PRODUCTO_NOMBRE = "Nintendo Switch 2"
PVP_OFICIAL_NINTENDO = 469.99  # Ajustar si Nintendo cambia el PVP oficial

# ---------------------------------------------------------------------------
# Tiendas activas en esta fase (las más permisivas para scraping)
#
# IMPORTANTE: Amazon España y MediaMarkt usan protecciones anti-bot fuertes
# (JS dinámico, captchas, bloqueo por IP/rate-limit). Se dejan preparadas
# como "próximamente" pero no se activan en el MVP para evitar bloqueos.
# ---------------------------------------------------------------------------
TIENDAS_ACTIVAS = ["pccomponentes", "game"]

TIENDAS_URLS = {
    "pccomponentes": {
        "url_busqueda": "https://www.pccomponentes.com/buscar/?query=nintendo+switch+2",
    },
    "game": {
        # Ficha de producto fija (confirmada por el usuario), más fiable que
        # depender de la página de resultados de búsqueda.
        "url_busqueda": "https://www.game.es/hardware/consola/nintendo-switch-2/nintendo-switch-2/243868",
    },
    # Preparadas para el futuro (requieren Playwright + medidas anti-bot):
    "amazon": {
        "url_busqueda": "https://www.amazon.es/s?k=nintendo+switch+2",
    },
    "mediamarkt": {
        "url_busqueda": "https://www.mediamarkt.es/es/search.html?query=nintendo+switch+2",
    },
}

# ---------------------------------------------------------------------------
# Cabeceras HTTP para las peticiones (simulan un navegador real)
# ---------------------------------------------------------------------------
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
}
REQUEST_TIMEOUT = 15  # segundos

# ---------------------------------------------------------------------------
# Frecuencia de ejecución automática (horas)
# ---------------------------------------------------------------------------
FRECUENCIA_HORAS = 6

# ---------------------------------------------------------------------------
# Ventanas de análisis (días)
# ---------------------------------------------------------------------------
VENTANA_CORTA = 30
VENTANA_MEDIA = 90
VENTANA_LARGA = 180

# ---------------------------------------------------------------------------
# Pesos del Índice Inteligente de Compra (deben sumar 1.0)
# ---------------------------------------------------------------------------
PESOS_SCORE = {
    "cercania_minimo": 0.40,
    "tendencia_bajista": 0.30,
    "descuento_media": 0.20,
    "epoca_del_anio": 0.10,
}

UMBRAL_COMPRAR = 75
UMBRAL_ESPERAR = 45  # por debajo de esto -> NO RECOMENDADO

# ---------------------------------------------------------------------------
# Eventos comerciales relevantes en España (mes, prioridad 0-1)
# Se usan para el componente "época del año" del score.
# ---------------------------------------------------------------------------
EVENTOS_COMERCIALES = {
    1: {"nombre": "Rebajas de enero", "peso": 0.9},
    7: {"nombre": "Rebajas de verano", "peso": 0.8},
    7.5: {"nombre": "Prime Day (aprox. mediados de julio)", "peso": 1.0},
    9: {"nombre": "Vuelta al cole", "peso": 0.5},
    11: {"nombre": "Black Friday", "peso": 1.0},
    12: {"nombre": "Cyber Monday / Navidad", "peso": 1.0},
}

# ---------------------------------------------------------------------------
# Alertas
# ---------------------------------------------------------------------------
_TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
_EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
_EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
_EMAIL_TO = os.environ.get("EMAIL_TO", "")

ALERTAS_CONFIG = {
    "telegram": {
        # Se activa solo si existen las variables de entorno necesarias.
        "activo": bool(_TELEGRAM_TOKEN and _TELEGRAM_CHAT),
        "bot_token": _TELEGRAM_TOKEN,
        "chat_id": _TELEGRAM_CHAT,
    },
    "email": {
        # Se activa solo si existen las variables de entorno necesarias.
        "activo": bool(_EMAIL_FROM and _EMAIL_PASSWORD and _EMAIL_TO),
        "smtp_host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": 587,
        "remitente": _EMAIL_FROM,
        "password": _EMAIL_PASSWORD,
        "destinatario": _EMAIL_TO,
    },
}
