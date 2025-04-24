import streamlit as st
import pandas as pd
import datetime
from streamlit_calendar import calendar
from firebase_admin import credentials, firestore, initialize_app
import os

# ---------- CONFIGURACIÓN ----------
st.set_page_config(layout="wide")
st.title("📅 Calendario de Reservas")

# ---------- FIREBASE SETUP ----------
if "firebase_initialized" not in st.session_state:
    cred = credentials.Certificate("firebase_key.json")
    initialize_app(cred)
    st.session_state.firebase_initialized = True

db = firestore.client()

# ---------- CARGAR RESERVAS ----------
@st.cache_data
def cargar_reservas():
    reservas_ref = db.collection("bookings")
    docs = reservas_ref.stream()

    data = []
    for doc in docs:
        d = doc.to_dict()
        if "Check-in" in d and "Check-out" in d:
            d["Check-in"] = pd.to_datetime(d["Check-in"], errors="coerce")
            d["Check-out"] = pd.to_datetime(d["Check-out"], errors="coerce")
            data.append(d)

    df = pd.DataFrame(data)
    return df

df = cargar_reservas()
hoy = datetime.date.today()

# ---------- CATEGORIZAR ESTADO ----------
def clasificar_estado(row):
    if pd.isnull(row["Check-in"]) or pd.isnull(row["Check-out"]):
        return ""
    hoy_dt = pd.to_datetime(hoy)
    if row["Check-in"].date() <= hoy <= row["Check-out"].date():
        return "Currently hosting"
    elif row["Check-in"].date() > hoy:
        return "Upcoming"
    elif row["Check-out"].date() == hoy:
        return "Checking out"
    elif row["Check-in"].date() == hoy:
        return "Arriving soon"
    elif row["Check-out"].date() < hoy:
        return "Pending review"
    return ""

df["Estado"] = df.apply(clasificar_estado, axis=1)

# ---------- FILTROS Y ESTADÍSTICAS ----------
conteos = df["Estado"].value_counts().to_dict()
selected_estado = st.session_state.get("selected_estado", None)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button(f"Currently hosting ({conteos.get('Currently hosting', 0)})"):
        st.session_state.selected_estado = "Currently hosting"
with col2:
    if st.button(f"Upcoming ({conteos.get('Upcoming', 0)})"):
        st.session_state.selected_estado = "Upcoming"
with col3:
    if st.button(f"Checking out ({conteos.get('Checking out', 0)})"):
        st.session_state.selected_estado = "Checking out"
with col4:
    if st.button(f"Arriving soon ({conteos.get('Arriving soon', 0)})"):
        st.session_state.selected_estado = "Arriving soon"
with col5:
    if st.button(f"Pending review ({conteos.get('Pending review', 0)})"):
        st.session_state.selected_estado = "Pending review"

estado_actual = st.session_state.get("selected_estado")
if estado_actual in df["Estado"].values:
    current = df[df["Estado"] == estado_actual].iloc[0]
    st.markdown(f"""
    <div style='background: white; border: 1px solid #ccc; border-radius: 10px; padding: 15px; margin-top: 15px; width: 240px;'>
        <p style='color: crimson; font-weight: bold;'>{estado_actual}</p>
        <p style='margin: 0; font-size: 18px; font-weight: bold;'>{current.get('Huesped', '')}</p>
        <p style='margin: 0;'>{current['Check-in'].strftime('%d %b')} – {current['Check-out'].strftime('%d %b')}</p>
        <p style='margin: 0;'>{current.get('Propiedad', '')}</p>
    </div>
    """, unsafe_allow_html=True)

# ---------- SIDEBAR: FILTROS ----------
st.sidebar.header("🔍 Filtros")
propiedades = ["Todas"] + sorted(df["Propiedad"].dropna().unique())
propiedad_filtrada = st.sidebar.selectbox("Filtrar por propiedad", propiedades)
meses = sorted(df["Check-in"].dropna().dt.strftime("%Y-%m").unique())
mes_actual = hoy.strftime("%Y-%m")
mes_seleccionado = st.sidebar.selectbox("Filtrar por mes", meses, index=meses.index(mes_actual) if mes_actual in meses else 0)

# ---------- APLICAR FILTROS ----------
df_filtrado = df.copy()
if propiedad_filtrada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Propiedad"] == propiedad_filtrada]

# ---------- ESTADÍSTICAS ----------
colx1, colx2, colx3 = st.columns(3)
colx1.metric("Reservas", len(df_filtrado))
colx2.metric("Huéspedes", df_filtrado["Huespedes"].fillna(0).astype(int).sum())
colx3.metric("Ingresos (AUD)", f"${df_filtrado['Precio'].fillna(0).astype(float).sum():,.2f}")

# ---------- EVENTOS EN CALENDARIO ----------
eventos = []
for i, row in df_filtrado.iterrows():
    if pd.notnull(row["Check-in"]) and pd.notnull(row["Check-out"]):
        eventos.append({
            "id": str(i),
            "title": f"{str(row['Huesped']).upper()} ({row['Propiedad']}) - {row['Noches']} noches | {row['Huespedes']} pax | ${row['Precio']}",
            "start": row["Check-in"].strftime("%Y-%m-%d"),
            "end": (row["Check-out"] + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            "color": "#f87171"
        })

calendar(events=eventos, options={
    "locale": "es",
    "initialView": "dayGridMonth",
    "height": 600,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek"
    },
    "nowIndicator": True
}, key="calendar_reservas")

# ---------- ENLACE INVERSO ----------
st.markdown("\n[🔁 Ir al módulo de Registrar Reservas](?page=6_Registrar Reservas)")
