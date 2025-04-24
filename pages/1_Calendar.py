import streamlit as st
import pandas as pd
import datetime
from firebase_config import db

st.set_page_config(page_title="Calendario", layout="wide")
st.title("📅 Calendario de Reservas")

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

# ✅ Validar antes de aplicar la función
if not df.empty and "Check-in" in df.columns and "Check-out" in df.columns:
    df["Estado"] = df.apply(clasificar_estado, axis=1)
else:
    df["Estado"] = []

# ---------- MOSTRAR RESERVAS ----------
st.subheader("Reservas para hoy")
df_hoy = df[df["Estado"] == "Currently hosting"]
if df_hoy.empty:
    st.info("No hay reservas activas para hoy.")
else:
    st.dataframe(df_hoy[["Huesped", "Propiedad", "Check-in", "Check-out"]], use_container_width=True)
