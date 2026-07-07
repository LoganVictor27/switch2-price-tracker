"""
Envío de alertas por correo electrónico (SMTP).

Configura las variables de entorno:
    SMTP_HOST, EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO
Para Gmail, usa una "contraseña de aplicación", no tu contraseña normal.
"""

import sys
import os
import smtplib
from email.mime.text import MIMEText

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def enviar_alerta_email(asunto, mensaje):
    cfg = config.ALERTAS_CONFIG["email"]
    if not cfg["activo"]:
        print("[Email] Alertas desactivadas (config.ALERTAS_CONFIG['email']['activo'] = False)")
        return False

    if not cfg["remitente"] or not cfg["password"] or not cfg["destinatario"]:
        print("[Email] Faltan variables de entorno EMAIL_FROM / EMAIL_PASSWORD / EMAIL_TO")
        return False

    msg = MIMEText(mensaje)
    msg["Subject"] = asunto
    msg["From"] = cfg["remitente"]
    msg["To"] = cfg["destinatario"]

    try:
        with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"]) as server:
            server.starttls()
            server.login(cfg["remitente"], cfg["password"])
            server.sendmail(cfg["remitente"], [cfg["destinatario"]], msg.as_string())
        return True
    except Exception as e:
        print(f"[Email] Error enviando alerta: {e}")
        return False


if __name__ == "__main__":
    enviar_alerta_email("Prueba - Analizador Switch 2", "Esto es una prueba de alerta por email.")
