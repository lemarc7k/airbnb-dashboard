import streamlit as st
import pandas as pd
import altair as alt
from firebase_config import db

st.set_page_config(page_title="📋 Reportes Semanales", layout="wide")
st.title("📋 Reporte Semanal de Propiedades")

# ---------- FUNCIÓN DE CARGA ---------- #
def cargar_reportes():
    docs = db.collection("reports").stream()
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]

# ---------- CARGA ---------- #
datos = cargar_reportes()
if not datos:
    st.warning("⚠️ Aún no hay reportes cargados en Firebase.")
    st.stop()

df = pd.DataFrame(datos)
df["Costo estimado"] = pd.to_numeric(df["Costo estimado"], errors="coerce").fillna(0)
df["Incidencias"] = pd.to_numeric(df["Incidencias"], errors="coerce").fillna(0)
df["Propiedades atendidas"] = pd.to_numeric(df["Propiedades atendidas"], errors="coerce").fillna(0)

# ---------- TABLA DE DATOS ---------- #
st.subheader("📊 Tabla de Reportes")
st.dataframe(df[["Semana", "Propiedades atendidas", "Incidencias", "Costo estimado"]], use_container_width=True)

# ---------- GRÁFICO: Incidencias ---------- #
st.markdown("### 📉 Incidencias por Semana")
chart1 = alt.Chart(df).mark_line(point=True, color="#e53935").encode(
    x="Semana",
    y=alt.Y("Incidencias", title="Número de Incidencias"),
    tooltip=["Semana", "Incidencias"]
).properties(height=300)
st.altair_chart(chart1, use_container_width=True)

# ---------- GRÁFICO: Costo ---------- #
st.markdown("### 💸 Costo Estimado por Semana")
chart2 = alt.Chart(df).mark_bar(color="#43a047").encode(
    x="Semana",
    y=alt.Y("Costo estimado", title="Costo Estimado (AUD)"),
    tooltip=["Semana", "Costo estimado"]
).properties(height=300)
st.altair_chart(chart2, use_container_width=True)

# ---------- MÉTRICAS ---------- #
st.markdown("### 📌 Métricas Generales")
col1, col2, col3 = st.columns(3)
col1.metric("Total semanas registradas", len(df))
col2.metric("Total de incidencias", int(df["Incidencias"].sum()))
col3.metric("Costo total estimado", f"${df['Costo estimado'].sum():,.2f}")
