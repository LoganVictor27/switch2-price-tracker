# Analizador de Precios - Nintendo Switch 2 (España) — MVP

MVP funcional del proyecto descrito: scraping de 2 tiendas permisivas
(**PcComponentes** y **GAME**), histórico en SQLite, motor de estadísticas,
predicción de precio, Índice Inteligente de Compra (0-100) y dashboard en
Streamlit. Amazon y MediaMarkt quedan preparadas en `config.py` para una
fase futura (requieren Playwright y medidas anti-bot más serias).

## Instalación

```bash
cd switch2_price_tracker
python3 -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

### 1. Ejecutar una recogida de precios manual

```bash
python main.py
```

Esto descarga el precio actual de PcComponentes y GAME, lo guarda en
`database/precios.db`, calcula estadísticas, predicción y score, e imprime
un resumen en consola.

### 2. Ejecutar en modo continuo (cada 6 horas, configurable en `config.py`)

```bash
python main.py --loop
```

Para producción real, es más robusto programarlo con `cron` (Linux/Mac) o
el Programador de tareas de Windows en vez de dejarlo en un bucle:

```
0 */6 * * * cd /ruta/al/proyecto && venv/bin/python main.py
```

### 3. Abrir el dashboard

```bash
streamlit run dashboard/app.py
```

## Ejecutarlo automáticamente cada día con GitHub Actions (recomendado)

Así no depende de que tengas ningún ordenador encendido. El workflow ya
está incluido en `.github/workflows/daily-summary.yml`.

### 1. Sube el proyecto a un repositorio de GitHub

```bash
cd switch2_price_tracker
git init
git add .
git commit -m "Primer commit del proyecto"
gh repo create switch2-price-tracker --private --source=. --push
# (o crea el repo desde github.com y haz git remote add origin ... && git push)
```

> El repositorio puede ser privado, GitHub Actions funciona igual.

### 2. Configura los "Secrets" del repositorio

En GitHub: tu repo → **Settings** → **Secrets and variables** → **Actions**
→ **New repository secret**. Añade:

| Nombre | Valor |
|---|---|
| `EMAIL_FROM` | tu_correo@gmail.com |
| `EMAIL_PASSWORD` | tu contraseña de aplicación de Gmail (16 letras) |
| `EMAIL_TO` | el correo donde quieres recibir el resumen |

(Opcional, si además quieres Telegram: `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`)

No hace falta tocar `config.py`: las alertas se activan solas en cuanto
detectan estas variables de entorno.

### 3. Ya está

El workflow se ejecuta automáticamente cada día a las 08:00 UTC (ajusta la
línea `cron` en el archivo `.yml` si quieres otra hora — recuerda que GitHub
Actions usa siempre UTC, no hora española). Cada ejecución:

1. Hace scraping de PcComponentes y GAME.
2. Guarda el precio nuevo en `database/precios.db`.
3. Te manda el email con el resumen del día.
4. Hace commit y push de la base de datos actualizada al propio repo, para
   que el histórico se mantenga entre ejecuciones (los runners de GitHub
   Actions no guardan nada por sí solos).

Puedes comprobar que funciona sin esperar al día siguiente: en tu repo, ve
a la pestaña **Actions** → selecciona el workflow → **Run workflow** (botón
a la derecha) para lanzarlo manualmente ahora mismo.

## Configurar alertas (opcional)

Edita `config.py` y pon `"activo": True` en `ALERTAS_CONFIG["telegram"]`
y/o `ALERTAS_CONFIG["email"]`, y define las variables de entorno
correspondientes:

```bash
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."

export EMAIL_FROM="tu_correo@gmail.com"
export EMAIL_PASSWORD="contraseña_de_aplicación"
export EMAIL_TO="destino@correo.com"
```

## ⚠️ Importante sobre el scraping

- Los selectores CSS en `scraper/pccomponentes.py` y `scraper/game.py` son
  un punto de partida. **Las webs cambian su HTML con frecuencia**, así
  que si un scraper deja de encontrar resultados, abre la página de
  búsqueda correspondiente con las herramientas de desarrollador del
  navegador (F12) e inspecciona las clases reales de la tarjeta de
  producto y del precio para actualizar los selectores.
- Respeta el `robots.txt` y los términos de uso de cada tienda, y no
  reduzcas la frecuencia por debajo de lo razonable (cada 6-12h es
  suficiente y evita bloqueos).
- Amazon España y MediaMarkt no están activadas en este MVP porque
  necesitan Playwright (renderizado JS) y son mucho más propensas a
  bloquear peticiones automatizadas.

## Estructura del proyecto

```
switch2_price_tracker/
├── config.py                 # Configuración central
├── main.py                   # Orquestador del flujo completo
├── requirements.txt
├── database/
│   └── sqlite.py              # Esquema y acceso a datos
├── scraper/
│   ├── base.py                 # Utilidades comunes (parseo de precio, etc.)
│   ├── pccomponentes.py
│   └── game.py
├── analysis/
│   ├── statistics.py           # Mínimo/máximo, medias móviles, tendencia...
│   ├── score.py                # Índice Inteligente de Compra
│   └── predictor.py            # Regresión lineal / ARIMA
├── alerts/
│   ├── telegram.py
│   └── email.py
└── dashboard/
    └── app.py                   # Dashboard Streamlit
```

## Próximos pasos sugeridos

- Añadir Amazon y MediaMarkt con Playwright.
- Añadir el resto de tiendas opcionales (Worten, Miravia, AliExpress, Coolmod).
- Sustituir la regresión lineal/ARIMA por Prophet o XGBoost cuando haya
  varios meses de histórico real (con pocos datos, un modelo complejo
  tiende a sobreajustar y predecir peor que uno simple).
- Detección automática de "chollos" (errores de precio).
- Exportar a Excel/PDF y API REST.
