import streamlit as st
import pandas as pd
import datetime
import altair as alt
from firebase_config import db  # Tu archivo de configuración Firebase

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("📊 Dashboard de Ingresos y Ocupación")

# ---------- FUNCIONES PARA FIRESTORE ---------- #
def obtener_datos_bookings():
    bookings_ref = db.collection("bookings")
    docs = bookings_ref.stream()
    data = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        data.append(d)
    df = pd.DataFrame(data)
    if not df.empty:
        df["Check-in"] = pd.to_datetime(df["Check-in"], errors="coerce")
        df["Check-out"] = pd.to_datetime(df["Check-out"], errors="coerce")
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df["Precio"] = pd.to_numeric(df["Precio"], errors="coerce").fillna(0)
        df["Huespedes"] = pd.to_numeric(df["Huespedes"], errors="coerce").fillna(0).astype(int)
        df["Noches"] = pd.to_numeric(df["Noches"], errors="coerce").fillna(0).astype(int)
        df["Mes"] = df["Check-in"].dt.to_period("M").astype(str)
        df["Semana"] = df["Check-in"].dt.to_period("W-MON").astype(str)
        df["Día"] = df["Check-in"].dt.date
        df["Año"] = df["Check-in"].dt.year.astype(str)
    return df

df = obtener_datos_bookings()
hoy = datetime.date.today()
mes_actual = hoy.strftime("%Y-%m")
mes_anterior = (hoy.replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")

# ---------- KPIs ---------- #
st.markdown("### 📈 KPIs generales")
col1, col2, col3 = st.columns(3)
ingresos_mes = df[df["Mes"] == mes_actual]["Precio"].sum()
ingresos_anterior = df[df["Mes"] == mes_anterior]["Precio"].sum()
reservas_mes = len(df[df["Mes"] == mes_actual])
reservas_anterior = len(df[df["Mes"] == mes_anterior])
huespedes_mes = df[df["Mes"] == mes_actual]["Huespedes"].sum()
huespedes_anterior = df[df["Mes"] == mes_anterior]["Huespedes"].sum()

col1.metric("Ingresos actuales", f"${ingresos_mes:,.2f}", f"${ingresos_mes - ingresos_anterior:,.2f} vs mes anterior")
col2.metric("Reservas del mes", reservas_mes, f"{reservas_mes - reservas_anterior:+} respecto al mes anterior")
col3.metric("Huéspedes del mes", huespedes_mes, f"{huespedes_mes - huespedes_anterior:+} respecto al mes anterior")

# ---------- GRÁFICOS ---------- #
st.markdown("---")
st.markdown("### 📅 Análisis temporal de ingresos y ocupación")

rango = st.selectbox("📆 Agrupar por", ["Día", "Semana", "Mes", "Año"], index=2)
columna = {"Día": "Día", "Semana": "Semana", "Mes": "Mes", "Año": "Año"}[rango]

ingresos = df.groupby(columna)["Precio"].sum().reset_index()
ocupacion = df.groupby(columna)["Noches"].sum().reset_index()
huespedes = df.groupby(columna)["Huespedes"].sum().reset_index()

col_g1, col_g2 = st.columns(2)

chart1 = alt.Chart(ingresos).mark_bar(color="#4caf50").encode(
    x=columna, y=alt.Y("Precio", title="Ingresos ($)"), tooltip=[columna, "Precio"]
).properties(title=f"Ingresos por {rango.lower()}", height=300)
col_g1.altair_chart(chart1, use_container_width=True)

chart2 = alt.Chart(ocupacion).mark_line(point=True, color="#2196f3").encode(
    x=columna, y=alt.Y("Noches", title="Noches ocupadas"), tooltip=[columna, "Noches"]
).properties(title=f"Ocupación por {rango.lower()}", height=300)
col_g2.altair_chart(chart2, use_container_width=True)

chart3 = alt.Chart(huespedes).mark_area(opacity=0.5, color="#ff9800").encode(
    x=columna, y=alt.Y("Huespedes", title="Total huéspedes"), tooltip=[columna, "Huespedes"]
).properties(title=f"Huéspedes por {rango.lower()}", height=300)
st.altair_chart(chart3, use_container_width=True)

# ---------- TABLAS AGRUPADAS ---------- #
st.markdown("---")
st.markdown("### 📊 Análisis por categoría")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("#### 🏠 Ingresos por propiedad")
    st.dataframe(df.groupby("Propiedad")["Precio"].sum().reset_index().sort_values("Precio", ascending=False), use_container_width=True)
    st.markdown("#### 🛏️ Ingresos por habitación")
    st.dataframe(df.groupby("Habitación")["Precio"].sum().reset_index().sort_values("Precio", ascending=False), use_container_width=True)

with col_b:
    st.markdown("#### 🔄 Ingresos por tipo de alquiler")
    st.dataframe(df.groupby("Tipo de alquiler")["Precio"].sum().reset_index().sort_values("Precio", ascending=False), use_container_width=True)
    st.markdown("#### ⏳ Ingresos por duración")
    st.dataframe(df.groupby("Duración")["Precio"].sum().reset_index().sort_values("Precio", ascending=False), use_container_width=True)


# ---------- RENTABILIDAD NETA (desde Firestore) ---------- #
from firebase_admin import firestore  # Ya debe estar importado arriba

def obtener_rentabilidad(df_bookings):
    gastos_ref = firestore.client().collection("gastos")
    gastos_docs = gastos_ref.stream()
    
    data_gastos = []
    for doc in gastos_docs:
        g = doc.to_dict()
        g["id"] = doc.id
        data_gastos.append(g)

    df_gastos = pd.DataFrame(data_gastos)
    if df_gastos.empty:
        return None

    df_gastos["Fecha"] = pd.to_datetime(df_gastos["Fecha"], errors="coerce")
    df_gastos["Monto"] = pd.to_numeric(df_gastos["Monto"], errors="coerce").fillna(0)

    ingresos_por_prop = df_bookings.groupby("Propiedad")["Precio"].sum().reset_index(name="Ingresos")
    gastos_por_prop = df_gastos.groupby("Propiedad")["Monto"].sum().reset_index(name="Gastos")

    rentabilidad = pd.merge(ingresos_por_prop, gastos_por_prop, on="Propiedad", how="left")
    rentabilidad["Gastos"] = rentabilidad["Gastos"].fillna(0)
    rentabilidad["Rentabilidad Neta"] = rentabilidad["Ingresos"] - rentabilidad["Gastos"]
    
    return rentabilidad

# Mostrar rentabilidad
st.markdown("---")
st.markdown("### 💸 Rentabilidad neta por propiedad")
rentabilidad = obtener_rentabilidad(df)
if rentabilidad is not None:
    st.dataframe(rentabilidad, use_container_width=True)
else:
    st.info("Aún no se han registrado gastos en Firestore.")
