"""
Envío de alertas por Telegram.

Requiere crear un bot con @BotFather y definir las variables de entorno:
    TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID
"""

import sys
import os

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def enviar_alerta_telegram(mensaje):
    cfg = config.ALERTAS_CONFIG["telegram"]
    if not cfg["activo"]:
        print("[Telegram] Alertas desactivadas (config.ALERTAS_CONFIG['telegram']['activo'] = False)")
        return False

    if not cfg["bot_token"] or not cfg["chat_id"]:
        print("[Telegram] Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")
        return False

    url = f"https://api.telegram.org/bot{cfg['bot_token']}/sendMessage"
    try:
        resp = requests.post(
            url,
            data={"chat_id": cfg["chat_id"], "text": mensaje, "parse_mode": "HTML"},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"[Telegram] Error enviando alerta: {e}")
        return False


if __name__ == "__main__":
    enviar_alerta_telegram("🔔 Prueba de alerta - Analizador Switch 2")
