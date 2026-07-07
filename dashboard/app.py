"""
Dashboard Streamlit - Analizador de Precios Nintendo Switch 2

Ejecutar con:
    streamlit run dashboard/app.py
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go

import config
from database import sqlite as db
from analysis.statistics import calcular_estadisticas, cargar_dataframe
from analysis.score import calcular_score
from analysis.predictor import predecir_precio

st.set_page_config(page_title="Switch 2 - Price Tracker", page_icon="🎮", layout="wide")

db.init_db()

st.title("🎮 Analizador de Precios - Nintendo Switch 2 (España)")

df = cargar_dataframe()

if df.empty:
    st.warning(
        "Todavía no hay datos en la base de datos. Ejecuta `python main.py` "
        "al menos una vez para obtener el primer precio."
    )
    st.stop()

estadisticas = calcular_estadisticas(df)
score_info = calcular_score(estadisticas)
prediccion = predecir_precio(df=df)

# ---------------------------------------------------------------------------
# Fila superior: métricas clave
# ---------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Precio actual", f"{estadisticas['precio_actual']} €")
col2.metric("Mínimo histórico", f"{estadisticas['precio_minimo_historico']} €")
col3.metric("Media 30 días", f"{estadisticas['media_30_dias']} €" if estadisticas["media_30_dias"] else "N/D")
col4.metric("Media 90 días", f"{estadisticas['media_90_dias']} €" if estadisticas["media_90_dias"] else "N/D")

st.divider()

# ---------------------------------------------------------------------------
# Indicador grande de recomendación
# ---------------------------------------------------------------------------
colores_semaforo = {
    "COMPRAR": ("🟢", "#1e7d32"),
    "ESPERAR": ("🟡", "#b8860b"),
    "NO RECOMENDADO": ("🔴", "#b22222"),
    "SIN DATOS": ("⚪", "#808080"),
}
emoji, color = colores_semaforo.get(score_info["recomendacion"], ("⚪", "#808080"))

st.markdown(
    f"""
    <div style="text-align:center; padding: 24px; border-radius: 12px;
                background-color: {color}22; border: 2px solid {color};">
        <div style="font-size: 48px;">{emoji}</div>
        <div style="font-size: 32px; font-weight: bold; color: {color};">
            {score_info['recomendacion']}
        </div>
        <div style="font-size: 20px;">Score de compra: {score_info['score']} / 100</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("Ver desglose del score"):
    st.json(score_info["detalle"])

st.divider()

# ---------------------------------------------------------------------------
# Gráfico de evolución de precios
# ---------------------------------------------------------------------------
st.subheader("Evolución del precio")

fig = go.Figure()
for tienda in df["tienda"].unique():
    sub = df[df["tienda"] == tienda].sort_values("fecha_dt")
    fig.add_trace(go.Scatter(
        x=sub["fecha_dt"], y=sub["precio_total"], mode="lines+markers", name=tienda
    ))

fig.add_hline(
    y=estadisticas["media_90_dias"],
    line_dash="dash",
    annotation_text="Media 90 días",
    line_color="gray",
)

# Añadir predicción si existe
if prediccion["prediccion"]:
    fechas_pred = [p["fecha"] for p in prediccion["prediccion"]]
    precios_pred = [p["precio_estimado"] for p in prediccion["prediccion"]]
    fig.add_trace(go.Scatter(
        x=fechas_pred, y=precios_pred, mode="lines+markers",
        name=f"Predicción ({prediccion['metodo']})",
        line=dict(dash="dot"),
    ))

fig.update_layout(xaxis_title="Fecha", yaxis_title="Precio (€)", height=450)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Predicción
# ---------------------------------------------------------------------------
st.subheader("Predicción de precio a corto plazo")
if prediccion["metodo"] == "insuficiente":
    st.info(prediccion.get("mensaje", "Datos insuficientes para predecir todavía."))
else:
    c1, c2 = st.columns(2)
    c1.metric("Método usado", prediccion["metodo"])
    if prediccion["probabilidad_bajada_pct"] is not None:
        c2.metric("Probabilidad estimada de bajada", f"{prediccion['probabilidad_bajada_pct']}%")
    st.dataframe(prediccion["prediccion"], use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Tabla de estadísticas completas
# ---------------------------------------------------------------------------
with st.expander("Ver todas las estadísticas"):
    st.json(estadisticas)

with st.expander("Ver histórico completo de precios"):
    st.dataframe(df.drop(columns=["fecha_dt"]), use_container_width=True)
