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
st.title("RESERVAS")

# ---------- FUNCIONES AUXILIARES ----------
def cargar_datos_csv(path, columnas):
    if os.path.exists(path):
        df = pd.read_csv(path)
        for col in columnas:
            if col not in df.columns:
                df[col] = ""
        return df
    return pd.DataFrame(columns=columnas)

def sincronizar_limpiezas_auto(df_bookings):
    df_clean = cargar_datos_csv(CLEANING_PATH, CLEANING_COLUMNS)
    nuevas = []
    for _, row in df_bookings.iterrows():
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
df_bookings = cargar_datos_csv(BOOKINGS_PATH, BOOKINGS_COLUMNS)
df_bookings["Check-in"] = pd.to_datetime(df_bookings["Check-in"], errors="coerce")
df_bookings["Check-out"] = pd.to_datetime(df_bookings["Check-out"], errors="coerce")

# ---------- CATEGORIZACIÓN DE ESTADOS ----------
def clasificar_estado(row):
    if pd.isnull(row["Check-in"]) or pd.isnull(row["Check-out"]):
        return ""
    hoy_dt = pd.to_datetime(datetime.date.today())
    if row["Check-in"] <= hoy_dt <= row["Check-out"]:
        return "Currently hosting"
    elif row["Check-in"] > hoy_dt:
        return "Upcoming"
    elif row["Check-out"] == hoy_dt:
        return "Checking out"
    elif row["Check-in"] == hoy_dt:
        return "Arriving soon"
    elif row["Check-out"] < hoy_dt:
        return "Pending review"
    return ""

df_bookings["Estado"] = df_bookings.apply(clasificar_estado, axis=1)

# ---------- CATEGORÍAS DINÁMICAS ----------
st.subheader("Filtrado por estado de reservas")
conteos = df_bookings["Estado"].value_counts().to_dict()
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
if estado_actual in df_bookings["Estado"].values:
    current = df_bookings[df_bookings["Estado"] == estado_actual].iloc[0]
    st.markdown(f"""
    <div style='background: white; border: 1px solid #ccc; border-radius: 10px; padding: 15px; margin-top: 15px; width: 240px;'>
        <p style='color: crimson; font-weight: bold;'>{estado_actual}</p>
        <p style='margin: 0; font-size: 18px; font-weight: bold;'>{current['Huesped']}</p>
        <p style='margin: 0;'>{current['Check-in'].strftime('%d %b')} – {current['Check-out'].strftime('%d %b')}</p>
        <p style='margin: 0;'>{current['Propiedad']}</p>
    </div>
    """, unsafe_allow_html=True)

# ---------- FORMULARIO ----------
st.subheader("Añadir o Editar una reserva")

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

if st.session_state.edit_id is not None:
    row = df_bookings.loc[st.session_state.edit_id]
    modo = "Editar"
else:
    row = {col: "" for col in BOOKINGS_COLUMNS}
    modo = "Nueva"

with st.form("form_booking", clear_on_submit=True):
    st.markdown(f"### {modo} reserva")
    col1, col2 = st.columns(2)
    with col1:
        propiedad = st.text_input("Nombre de la propiedad", value=row["Propiedad"])
        huesped = st.text_input("Nombre del huésped", value=row["Huesped"])
        canal = st.selectbox("Canal de reserva", ["Airbnb", "Booking", "Directo", "StayMate", "Otro"], index=0 if row["Canal"] == "" else ["Airbnb", "Booking", "Directo", "StayMate", "Otro"].index(row["Canal"]))
        noches = st.number_input("Número de noches", min_value=1, value=int(row["Noches"]) if row["Noches"] else 1)
        huespedes = st.number_input("Nº de huéspedes", min_value=1, value=int(row["Huespedes"]) if row["Huespedes"] else 1)
    with col2:
        check_in = st.date_input("Fecha de Check-in", value=pd.to_datetime(row["Check-in"]).date() if row["Check-in"] else datetime.date.today())
        check_out = st.date_input("Fecha de Check-out", value=pd.to_datetime(row["Check-out"]).date() if row["Check-out"] else datetime.date.today())
        precio = st.number_input("Precio total (AUD)", min_value=0.0, step=10.0, value=float(row["Precio"]) if row["Precio"] else 0.0)
        pago = st.text_input("Método de pago", value=row["Pago"])
        notas = st.text_area("Notas internas", value=row["Notas"])

    submitted = st.form_submit_button("Guardar")
    if submitted:
        nueva_fila = pd.DataFrame([[datetime.date.today(), propiedad, huesped, check_in, check_out, canal, noches, huespedes, precio, pago, notas]], columns=BOOKINGS_COLUMNS)
        if st.session_state.edit_id is not None:
            df_bookings.loc[st.session_state.edit_id] = nueva_fila.iloc[0]
            st.success("Reserva actualizada correctamente")
            st.session_state.edit_id = None
        else:
            df_bookings = pd.concat([df_bookings, nueva_fila], ignore_index=True)
            st.success("Reserva añadida correctamente")
        df_bookings.to_csv(BOOKINGS_PATH, index=False)
        sincronizar_limpiezas_auto(df_bookings)
        st.rerun()

# ---------- HISTORIAL DE RESERVAS ----------
st.subheader("Historial de reservas")

for idx, row in df_bookings.iterrows():
    with st.expander(f"{row['Propiedad']} - {row['Huesped']} ({row['Check-in']} ➜ {row['Check-out']})"):
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
            if st.button("Eliminar", key=f"del_{idx}"):
                df_bookings.drop(index=idx, inplace=True)
                df_bookings.reset_index(drop=True, inplace=True)
                df_bookings.to_csv(BOOKINGS_PATH, index=False)
                st.success("Reserva eliminada")
                st.rerun()
        with col4:
            if st.button("Editar", key=f"edit_{idx}"):
                st.session_state.edit_id = idx
                st.rerun()
