import streamlit as st
st.set_page_config(page_title="Reports | KM Ventures", layout="wide")
import pandas as pd
import altair as alt
from firebase_admin import firestore
from firebase_config import db  # Asegúrate que firebase_config.py esté correcto

try:
    # tu lógica aquí
    st.write("✅ Página cargada correctamente")
except Exception as e:
    st.error(f"❌ Error cargando página: {e}")


st.title("📋 Reporte Semanal de Propiedades")

# ---------- FUNCIÓN PARA CARGAR DATOS DESDE FIRESTORE ---------- #
def cargar_reportes_firestore():
    ref = db.collection("reports")
    docs = ref.stream()
    data = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        data.append(d)
    df = pd.DataFrame(data)
    if not df.empty:
        df["Costo estimado"] = pd.to_numeric(df["Costo estimado"], errors="coerce").fillna(0)
        df["Incidencias"] = pd.to_numeric(df["Incidencias"], errors="coerce").fillna(0).astype(int)
        df["Propiedades atendidas"] = pd.to_numeric(df["Propiedades atendidas"], errors="coerce").fillna(0).astype(int)
    return df

# ---------- CARGAR DATOS ---------- #
df_reports = cargar_reportes_firestore()

if df_reports.empty:
    st.warning("⚠️ No se encontraron datos en la colección 'reports'")
    st.stop()

# ---------- TABLA PRINCIPAL ---------- #
st.subheader("📊 Tabla de Reportes")
st.dataframe(df_reports, use_container_width=True)

# ---------- GRÁFICO DE INCIDENCIAS ---------- #
st.markdown("### 📉 Incidencias por Semana")
chart1 = alt.Chart(df_reports).mark_line(point=True, color="#e53935").encode(
    x="Semana",
    y=alt.Y("Incidencias", title="Número de Incidencias"),
    tooltip=["Semana", "Incidencias"]
).properties(height=300)
st.altair_chart(chart1, use_container_width=True)

# ---------- GRÁFICO DE COSTOS ---------- #
st.markdown("### 💸 Costo Estimado por Semana")
chart2 = alt.Chart(df_reports).mark_bar(color="#43a047").encode(
    x="Semana",
    y=alt.Y("Costo estimado", title="Costo Estimado (AUD)"),
    tooltip=["Semana", "Costo estimado"]
).properties(height=300)
st.altair_chart(chart2, use_container_width=True)

# ---------- MÉTRICAS RESUMEN ---------- #
st.markdown("### 📌 Métricas Generales")
col1, col2, col3 = st.columns(3)
col1.metric("Total semanas registradas", len(df_reports))
col2.metric("Total de incidencias", int(df_reports["Incidencias"].sum()))
col3.metric("Costo total estimado", f"${df_reports['Costo estimado'].sum():,.2f}")
