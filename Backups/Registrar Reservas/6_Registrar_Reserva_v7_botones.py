import streamlit as st
import pandas as pd
import os
import datetime

# RUTAS Y CONFIG
BOOKINGS_PATH = "data/bookings.csv"
CLEANING_PATH = "data/cleaning_schedule.csv"
BOOKINGS_COLUMNS = ["Fecha", "Propiedad", "Huesped", "Check-in", "Check-out", "Canal", "Noches", "Huespedes", "Precio", "Pago", "Notas"]
CLEANING_COLUMNS = ["Fecha", "Propiedad", "Cleaner", "Estado"]

st.set_page_config(page_title="Registrar Reservas", layout="wide")
st.title("📋 RESERVAS")

# ---------- FUNCIONES AUXILIARES ----------
def cargar_datos_csv(path, columnas):
    if os.path.exists(path):
        df = pd.read_csv(path)
        for col in columnas:
            if col not in df.columns:
                df[col] = ""
        return df
    return pd.DataFrame(columns=columnas)

def sincronizar_limpiezas_auto(df):
    df_clean = cargar_datos_csv(CLEANING_PATH, CLEANING_COLUMNS)
    nuevas = []
    for _, row in df.iterrows():
        if pd.notnull(row["Check-out"]):
            fecha_limpieza = (pd.to_datetime(row["Check-out"]) + pd.Timedelta(days=1)).date()
            existe = df_clean[
                (pd.to_datetime(df_clean["Fecha"]).dt.date == fecha_limpieza) &
                (df_clean["Propiedad"] == row["Propiedad"])
            ]
            if existe.empty:
                nuevas.append({
                    "Fecha": fecha_limpieza,
                    "Propiedad": row["Propiedad"],
                    "Cleaner": "",
                    "Estado": "Pendiente"
                })
    if nuevas:
        df_clean_actualizado = pd.concat([df_clean, pd.DataFrame(nuevas)], ignore_index=True)
        df_clean_actualizado.to_csv(CLEANING_PATH, index=False)

# ---------- CARGA DE DATOS ----------
df = cargar_datos_csv(BOOKINGS_PATH, BOOKINGS_COLUMNS)

# ---------- CATEGORÍAS DINÁMICAS ----------
st.subheader("📂 Filtrado por estado de reservas")
col_a, col_b, col_c, col_d = st.columns(4)
hoy = datetime.date.today()

currently_hosting = df[(pd.to_datetime(df["Check-in"]).dt.date <= hoy) & (pd.to_datetime(df["Check-out"]).dt.date >= hoy)]
upcoming = df[pd.to_datetime(df["Check-in"]).dt.date > hoy]
past = df[pd.to_datetime(df["Check-out"]).dt.date < hoy]

with col_a:
    st.metric("Currently Hosting", len(currently_hosting))
with col_b:
    st.metric("Upcoming", len(upcoming))
with col_c:
    st.metric("Completed", len(past))
with col_d:
    st.markdown("[📅 Ir al calendario](?page=Calendar)")

# ---------- FORMULARIO ----------
st.subheader("➕ Añadir o Editar una reserva")

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

if st.session_state.edit_id is not None:
    row = df.loc[st.session_state.edit_id]
    modo = "Editar"
else:
    row = {col: "" for col in BOOKINGS_COLUMNS}
    modo = "Nueva"

with st.form("form_booking", clear_on_submit=True):
    st.markdown(f"### ✏️ {modo} reserva")
    col1, col2 = st.columns(2)
    with col1:
        propiedad = st.text_input("🏡 Nombre de la propiedad", value=row["Propiedad"])
        huesped = st.text_input("👤 Nombre del huésped", value=row["Huesped"])
        canal = st.selectbox("🌐 Canal de reserva", ["Airbnb", "Booking", "Directo", "StayMate", "Otro"], index=0 if row["Canal"] == "" else ["Airbnb", "Booking", "Directo", "StayMate", "Otro"].index(row["Canal"]))
        noches = st.number_input("🌙 Número de noches", min_value=1, value=int(row["Noches"]) if row["Noches"] else 1)
        huespedes = st.number_input("👥 Nº de huéspedes", min_value=1, value=int(row["Huespedes"]) if row["Huespedes"] else 1)
    with col2:
        check_in = st.date_input("📅 Fecha de Check-in", value=pd.to_datetime(row["Check-in"]).date() if row["Check-in"] else datetime.date.today())
        check_out = st.date_input("📅 Fecha de Check-out", value=pd.to_datetime(row["Check-out"]).date() if row["Check-out"] else datetime.date.today())
        precio = st.number_input("💰 Precio total (AUD)", min_value=0.0, step=10.0, value=float(row["Precio"]) if row["Precio"] else 0.0)
        pago = st.text_input("💳 Método de pago", value=row["Pago"])
        notas = st.text_area("📝 Notas internas", value=row["Notas"])

    submitted = st.form_submit_button("Guardar")
    if submitted:
        nueva_fila = pd.DataFrame([[datetime.date.today(), propiedad, huesped, check_in, check_out, canal, noches, huespedes, precio, pago, notas]], columns=BOOKINGS_COLUMNS)
        if st.session_state.edit_id is not None:
            df.loc[st.session_state.edit_id] = nueva_fila.iloc[0]
            st.success("✏️ Reserva actualizada correctamente")
            st.session_state.edit_id = None
        else:
            df = pd.concat([df, nueva_fila], ignore_index=True)
            st.success("✅ Reserva añadida correctamente")
        df.to_csv(BOOKINGS_PATH, index=False)
        sincronizar_limpiezas_auto(df)
        st.rerun()

# ---------- HISTORIAL DE RESERVAS ----------
st.subheader("📑 Historial de reservas")

for idx, row in df.iterrows():
    with st.expander(f"🏡 {row['Propiedad']} - 👤 {row['Huesped']} ({row['Check-in']} ➜ {row['Check-out']})"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Canal:** {row['Canal']}")
            st.markdown(f"**Noches:** {row['Noches']}")
            st.markdown(f"**Huéspedes:** {row['Huespedes']}")
        with col2:
            st.markdown(f"**Precio:** ${row['Precio']}")
            st.markdown(f"**Pago:** {row['Pago']}")
        st.markdown(f"**Notas:** {row['Notas']}")

        col3, col4 = st.columns([1, 6])
        with col3:
            if st.button("🗑️ Eliminar", key=f"del_{idx}"):
                df.drop(index=idx, inplace=True)
                df.reset_index(drop=True, inplace=True)
                df.to_csv(BOOKINGS_PATH, index=False)
                st.success("🗑️ Reserva eliminada")
                st.rerun()
        with col4:
            if st.button("✏️ Editar", key=f"edit_{idx}"):
                st.session_state.edit_id = idx
                st.rerun()
