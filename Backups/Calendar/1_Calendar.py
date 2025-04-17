import streamlit as st
import pandas as pd
import os
import datetime
from streamlit_calendar import calendar

st.set_page_config(page_title="Calendario de Reservas", layout="wide")
st.title("📅 Calendario de reservas")

BOOKINGS_PATH = "data/bookings.csv"
BOOKINGS_COLUMNS = ["Fecha", "Propiedad", "Huesped", "Check-in", "Check-out", "Canal", "Noches", "Huespedes", "Precio", "Pago", "Notas"]

# Cargar reservas
if os.path.exists(BOOKINGS_PATH):
    df = pd.read_csv(BOOKINGS_PATH)
    for col in BOOKINGS_COLUMNS:
        if col not in df.columns:
            df[col] = ""
else:
    df = pd.DataFrame(columns=BOOKINGS_COLUMNS)

# Conversión de fechas
if not df.empty:
    df["Check-in"] = pd.to_datetime(df["Check-in"], errors="coerce")
    df["Check-out"] = pd.to_datetime(df["Check-out"], errors="coerce")

# Filtros
with st.sidebar:
    st.subheader("🔍 Filtros del calendario")
    propiedades = ["Todas"] + sorted(df["Propiedad"].dropna().unique())
    propiedad_filtrada = st.selectbox("Propiedad", propiedades)

df_filtrado = df.copy()
if propiedad_filtrada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Propiedad"] == propiedad_filtrada]

# Construcción de eventos
eventos = []
for i, row in df_filtrado.iterrows():
    if pd.notnull(row["Check-in"]) and pd.notnull(row["Check-out"]):
        eventos.append({
            "id": str(i),
            "title": f"{row['Huesped']} - {row['Propiedad']}",
            "start": row["Check-in"].strftime("%Y-%m-%d"),
            "end": (row["Check-out"] + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            "color": "#3b82f6"
        })

# Calendario visual
calendar(
    events=eventos,
    options={
        "locale": "es",
        "initialView": "dayGridMonth",
        "height": 650,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek"
        },
        "nowIndicator": True
    },
    key="visual_calendar"
)

# Navegación inversa
df_total = len(df)
st.markdown(f"\n---\n👁️ Visualizando {len(df_filtrado)} de {df_total} reservas")
st.markdown("[📋 Ir al registro de reservas](?page=Booking_Manager_Tab)")
