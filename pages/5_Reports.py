import streamlit as st
import pandas as pd
import altair as alt
import os

st.set_page_config(page_title="📋 Reportes Semanales", layout="wide")
st.title("📋 Reporte Semanal de Propiedades")

# Ruta al archivo
REPORTS_PATH = "data/reports.csv"

# Cargar datos
if os.path.exists(REPORTS_PATH):
    df_reports = pd.read_csv(REPORTS_PATH)
    df_reports["Costo estimado"] = pd.to_numeric(df_reports["Costo estimado"], errors="coerce")
    df_reports["Incidencias"] = pd.to_numeric(df_reports["Incidencias"], errors="coerce")
    df_reports["Propiedades atendidas"] = pd.to_numeric(df_reports["Propiedades atendidas"], errors="coerce")
else:
    st.error("⚠️ No se encontró el archivo reports.csv")
    st.stop()

# Mostrar tabla
st.subheader("📊 Tabla de Reportes")
st.dataframe(df_reports, use_container_width=True)

# Gráfico 1: Incidencias por semana
st.markdown("### 📉 Incidencias por Semana")
chart1 = alt.Chart(df_reports).mark_line(point=True, color="#e53935").encode(
    x="Semana",
    y=alt.Y("Incidencias", title="Número de Incidencias"),
    tooltip=["Semana", "Incidencias"]
).properties(height=300)
st.altair_chart(chart1, use_container_width=True)

# Gráfico 2: Costo estimado por semana
st.markdown("### 💸 Costo Estimado por Semana")
chart2 = alt.Chart(df_reports).mark_bar(color="#43a047").encode(
    x="Semana",
    y=alt.Y("Costo estimado", title="Costo Estimado (AUD)"),
    tooltip=["Semana", "Costo estimado"]
).properties(height=300)
st.altair_chart(chart2, use_container_width=True)

# Métricas resumen
st.markdown("### 📌 Métricas Generales")
col1, col2, col3 = st.columns(3)
col1.metric("Total semanas registradas", len(df_reports))
col2.metric("Total de incidencias", int(df_reports["Incidencias"].sum()))
col3.metric("Costo total estimado", f"${df_reports['Costo estimado'].sum():,.2f}")
