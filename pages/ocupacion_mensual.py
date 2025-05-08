# ------------------- Ocupación Mensual -------------------
import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt

# ------------ CONFIGURACIÓN ------------
st.set_page_config(page_title="Ocupación Mensual", layout="wide")

# ------------ CARGA DE DATOS ------------
from firebase_config import db

docs = db.collection("bookings").stream()
data = []
for doc in docs:
    d = doc.to_dict()
    data.append({
        "Check-in": pd.to_datetime(d.get("Check-in")),
        "Check-out": pd.to_datetime(d.get("Check-out")),
        "Nombre propiedad": d.get("Propiedad", "Desconocido"),
        "Habitación": d.get("Habitación", "1")
    })

df = pd.DataFrame(data)

# ------------ SELECCIÓN DE MES ------------
hoy = datetime.date.today()
meses = pd.date_range(end=hoy, periods=12, freq='MS').to_list()
mes_seleccionado = st.selectbox("Seleccionar mes", options=meses[::-1], format_func=lambda d: d.strftime('%B %Y'))

inicio_mes = pd.to_datetime(mes_seleccionado).replace(day=1)
fin_mes = (inicio_mes + pd.DateOffset(months=1)) - pd.DateOffset(days=1)

# ------------ EXPANDIR RESERVAS A DÍAS INDIVIDUALES ------------
def expandir_fechas(row):
    fechas = pd.date_range(start=row["Check-in"], end=row["Check-out"] - pd.Timedelta(days=1))
    return pd.DataFrame({
        "Fecha": fechas,
        "Nombre propiedad": row["Nombre propiedad"],
        "Habitación": row["Habitación"]
    })

df_expandido = pd.concat([expandir_fechas(row) for _, row in df.iterrows()], ignore_index=True)
df_mes = df_expandido[(df_expandido["Fecha"] >= inicio_mes) & (df_expandido["Fecha"] <= fin_mes)]

# ------------ CÁLCULOS DE OCUPACIÓN ------------
dias_mes = (fin_mes - inicio_mes).days + 1
ocupacion = (
    df_mes.groupby(["Nombre propiedad", "Habitación"])["Fecha"]
    .count()
    .reset_index(name="Días ocupados")
)
ocupacion["Días disponibles"] = dias_mes - ocupacion["Días ocupados"]
ocupacion["Ocupación %"] = (ocupacion["Días ocupados"] / dias_mes * 100).round(2)

# ------------ MOSTRAR RESULTADOS ------------
st.title("📊 Ocupación Mensual")
st.caption(f"Mostrando datos de ocupación para el mes de **{mes_seleccionado.strftime('%B %Y')}**")

st.dataframe(ocupacion, use_container_width=True)

import plotly.express as px

# ------------ GRÁFICO DE OCUPACIÓN % POR HABITACIÓN ------------
st.subheader("📈 Tasa de ocupación por habitación")

fig1 = px.bar(
    ocupacion,
    x="Ocupación %",
    y="Habitación",
    color_discrete_sequence=["#14D2DC"],
    orientation="h",
    labels={"Ocupación %": "Porcentaje", "Habitación": "Habitación"},
    height=300
)
fig1.update_layout(
    xaxis=dict(title="Porcentaje de Ocupación"),
    yaxis=dict(title=""),
    margin=dict(l=10, r=10, t=30, b=10),
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig1, use_container_width=True)

# ------------ GRÁFICO DE DÍAS OCUPADOS VS DISPONIBLES ------------
st.subheader("📊 Días Ocupados")

ocupacion_stacked = ocupacion.copy()
ocupacion_stacked["label"] = ocupacion_stacked["Habitación"]

fig2 = px.bar(
    ocupacion_stacked,
    y="Habitación",
    x=["Días ocupados", "Días disponibles"],
    orientation="h",
    labels={"value": "Días", "variable": "Tipo"},
    color_discrete_sequence=["#00CC96", "#CCCCCC"],
    height=300
)
fig2.update_layout(
    barmode="stack",
    xaxis=dict(title="Días"),
    yaxis=dict(title=""),
    margin=dict(l=10, r=10, t=30, b=10),
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig2, use_container_width=True)


# ---------- RESUMEN RÁPIDO ----------
col1, col2, col3, col4, col5 = st.columns(5)

ocupacion_promedio = ocupacion["Ocupación %"].mean().round(2)
total_ocupados = ocupacion["Días ocupados"].sum()
total_disponibles = ocupacion["Días disponibles"].sum()

habitacion_mayor = ocupacion.loc[ocupacion["Ocupación %"].idxmax()]["Habitación"]
habitacion_menor = ocupacion.loc[ocupacion["Ocupación %"].idxmin()]["Habitación"]

col1.metric("📊 Ocupación promedio", f"{ocupacion_promedio}%")
col2.metric("📅 Total días ocupados", f"{total_ocupados}")
col3.metric("🕓 Días disponibles", f"{total_disponibles}")
col4.metric("🔝 Mayor ocupación", habitacion_mayor)
col5.metric("🔻 Menor ocupación", habitacion_menor)


propiedades_unicas = ["Todas"] + sorted(ocupacion["Nombre propiedad"].unique())
propiedad_filtrada = st.selectbox("Filtrar por propiedad", propiedades_unicas)

if propiedad_filtrada != "Todas":
    ocupacion = ocupacion[ocupacion["Nombre propiedad"] == propiedad_filtrada]
