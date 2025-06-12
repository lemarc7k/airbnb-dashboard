# === CONFIGURACIÓN INICIAL ===
import streamlit as st
st.set_page_config(page_title="Real Estate | MV Ventures", layout="wide")

# === BIBLIOTECAS BASE ===
import os
import time
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# === FIREBASE ===
from firebase_config import db

# === COMPONENTES STREAMLIT ===
import streamlit.components.v1 as components
from streamlit_js_eval import streamlit_js_eval

# === LIBRERÍAS DE VISUALIZACIÓN ===
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import plotly.express as px
import plotly.graph_objects as go

# === CARGA DE PÁGINAS ===
from pages.Listings import mostrar_listings
from pages.Reservas import mostrar_reservas
from pages.Inversion import mostrar_inversion
from pages.Calendario import mostrar_calendario

# === CARGA CENTRALIZADA CON CACHÉ ===
@st.cache_data(ttl=300)  # Cache por 5 minutos
def cargar_datos_firebase():
    def fetch(col):
        docs = db.collection(col).stream()
        return [doc.to_dict() | {"doc_id": doc.id} for doc in docs]

    return {
        "bookings": fetch("bookings"),
        "inversiones": fetch("inversiones"),
        "gastos": fetch("gastos_fijos"),
        "reservas": fetch("reservas")
    }

datos = cargar_datos_firebase()

# === CONVERSIÓN A DATAFRAMES ===
df_bookings = pd.DataFrame(datos["bookings"])
df_inversiones = pd.DataFrame(datos["inversiones"])
df_gastos = pd.DataFrame(datos["gastos"])
df_reservas = pd.DataFrame(datos["reservas"])

# === INICIALIZAR ESTADO ===
if "edit_id" not in st.session_state:
    st.session_state["edit_id"] = None

# === LIMPIEZA Y FORMATO DE BOOKINGS ===
def limpiar_bookings(df):
    if df.empty:
        return df
    df["Check-in"] = pd.to_datetime(df["Check-in"], errors="coerce")
    df["Check-out"] = pd.to_datetime(df["Check-out"], errors="coerce")
    df["Propiedad"] = df["Propiedad"].fillna("Sin asignar").astype(str).str.strip().str.title()
    df["Habitación"] = df["Habitación"].fillna("Sin asignar").astype(str).str.strip().str.title()
    df["Huesped"] = df["Huesped"].fillna("Sin nombre").astype(str).str.strip().str.title()
    df["id_unico"] = df["Check-in"].astype(str) + df["Huesped"]
    return df

df_bookings = limpiar_bookings(df_bookings)

# === FECHA DE HOY ===
hoy = pd.to_datetime(datetime.today().date())

# === FILTROS DE BOOKING (opcional si los usas) ===
upcoming = df_bookings[
    (df_bookings["Check-in"].notna()) &
    (df_bookings["Check-out"].notna()) &
    (df_bookings["Check-in"].dt.date > hoy.date()) &
    (df_bookings["Check-out"].dt.date > hoy.date())
].sort_values("Check-in")

reservas_hoy = df_bookings[
    (df_bookings["Check-in"].dt.date <= hoy.date()) &
    (df_bookings["Check-out"].dt.date >= hoy.date())
]

checkouts_hoy = df_bookings[
    df_bookings["Check-out"].dt.date == hoy.date()
]

# === TABS ===
tabs = st.tabs(["INICIO", "LISTINGS", "RESERVAS", "INVERSION", "CALENDARIO", "SIMULACION"])

# === CARGA DE CADA SECCIÓN ===
with tabs[0]:  # INICIO
    st.markdown("<h2 style='text-align:center; color:#00ffe1;'>BIENVENIDO MR VERA</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888;'>Estas son las reservas activas de tus propiedades gestionadas en Airbnb</p>", unsafe_allow_html=True)


    # === SESIÓN PARA DETALLE ===
    if "reserva_seleccionada" not in st.session_state:
        st.session_state["reserva_seleccionada"] = None

    # === ESTILOS BASE ===
    st.markdown("""
    <style>
    .card-avatar {
        width: 45px;
        height: 45px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #00ffe1;
    }
    .section-title {
        font-size: 20px;
        color: #00ffe1;
        margin-top: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

    # === FUNCIÓN PARA TÍTULOS DE SECCIÓN ===
    # === FUNCIÓN FLEXIBLE PARA TÍTULOS DE SECCIÓN ===
    def mostrar_titulo(seccion, color="#00ffe1", size="26px", margin_top="30px", margin_bottom="15px"):
        st.markdown(f"""
        <div style="
            font-size: {size};
            color: {color};
            margin: {margin_top} 0 {margin_bottom} 0;
            font-weight: 700;
            letter-spacing: 0.5px;
        ">
            {seccion}
        </div>
        """, unsafe_allow_html=True)



    # === FUNCIÓN PARA TARJETAS EXPANDIBLES ===
    def mostrar_tarjeta_reserva(titulo, subtitulo, avatar_url, key, reserva_dict):
        # Obtenemos el doc_id directamente desde el diccionario de la reserva
        doc_id = reserva_dict.get("doc_id")


        with st.container():
            st.markdown(f"""
            <div style="background-color:#0f172a; padding:15px 18px; border-radius:16px;
                        border:1px solid #00ffe120; box-shadow:0 0 8px #00ffe110; margin-bottom:5px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="color:white;">
                        <div style="font-size:15px; font-weight:600; color:#00ffe1;">{titulo}</div>
                        <div style="font-size:13px; color:#aaa;">{subtitulo}</div>
                    </div>
                    <img src="{avatar_url}" class="card-avatar" />
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("Ver detalles de esta reserva"):
                checkin = pd.to_datetime(reserva_dict["Check-in"])
                checkout = pd.to_datetime(reserva_dict["Check-out"])

                modo_edicion = st.checkbox("✏️ Editar reserva", key=f"edit-{doc_id}")

                if not modo_edicion:
                    st.markdown(f"""
                    <div style="font-size:16px; line-height:1.8; margin-top:10px;">
                        <p><b>📍 Propiedad:</b> {reserva_dict['Propiedad']}</p>
                        <p><b>🛏️ Habitación:</b> {reserva_dict['Habitación']}</p>
                        <p><b>📅 Check-in:</b> {checkin.strftime('%d %b %Y')}</p>
                        <p><b>📅 Check-out:</b> {checkout.strftime('%d %b %Y')}</p>
                        <p><b>💰 Precio:</b> ${reserva_dict['Precio']:,.2f}</p>
                        <p><b>🔄 Estado:</b> {reserva_dict['Estado'].capitalize()}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    nueva_propiedad = st.text_input("📍 Propiedad", value=reserva_dict["Propiedad"], key=f"prop-{doc_id}")
                    nueva_habitacion = st.text_input("🛏️ Habitación", value=reserva_dict["Habitación"], key=f"hab-{doc_id}")
                    nuevo_checkin = st.date_input("📅 Check-in", value=checkin.date(), key=f"cin-{doc_id}")
                    nuevo_checkout = st.date_input("📅 Check-out", value=checkout.date(), key=f"cout-{doc_id}")
                    nuevo_precio = st.number_input("💰 Precio", value=float(reserva_dict["Precio"]), step=1.0, key=f"precio-{doc_id}")
                    nuevo_huesped = st.text_input("👤 Huésped", value=reserva_dict["Huesped"], key=f"huesped-{doc_id}")
                    nuevo_estado = st.selectbox("🔄 Estado", ["pendiente", "pagado"], 
                                                index=0 if reserva_dict["Estado"] == "pendiente" else 1, key=f"estado-{doc_id}")


                    if st.button("💾 Guardar cambios", key=f"save-{key}"):
                        if doc_id:
                            try:
                                db.collection("bookings").document(doc_id).update({
                                    "Propiedad": nueva_propiedad.strip().title(),
                                    "Habitación": nueva_habitacion.strip().title(),
                                    "Check-in": str(nuevo_checkin),
                                    "Check-out": str(nuevo_checkout),
                                    "Precio": float(nuevo_precio),
                                    "Huesped": nuevo_huesped.strip().title(),
                                    "Estado": nuevo_estado.lower()
                                })
                                st.success("✅ Cambios guardados correctamente.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error al guardar: {e}")
                        else:
                            st.warning("❌ No se encontró esta reserva en Firestore.")
                        
                # --- ELIMINACIÓN DENTRO DEL FORMULARIO ---
                st.markdown("""
                    <style>
                    .delete-box {
                        margin-top: 20px;
                        display: flex;
                        align-items: center;
                        gap: 10px;
                    }
                    .delete-btn {
                        background-color: transparent;
                        color: #ff4d4f;
                        border: 1px solid #ff4d4f;
                        padding: 6px 14px;
                        border-radius: 10px;
                        font-weight: 500;
                        transition: all 0.25s ease;
                        font-size: 14px;
                    }
                    .delete-btn:hover {
                        background-color: #ff4d4f22;
                        box-shadow: 0 0 10px #ff4d4f66;
                        cursor: pointer;
                    }
                    </style>
                """, unsafe_allow_html=True)

                with st.container():
                    st.markdown('<div class="delete-box">', unsafe_allow_html=True)
                    confirmar = st.checkbox("🗑️ Eliminar reserva", key=f"confirmar-{doc_id}")
                    if confirmar and doc_id:
                        eliminar = st.button("🗑️ Eliminar reserva", key=f"del-{doc_id}")
                        if eliminar:
                            db.collection("bookings").document(doc_id).delete()
                            st.success("✅ Reserva eliminada correctamente.")
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)




    # === LIMPIEZA Y NORMALIZACIÓN DE CAMPOS ===
    # === LIMPIEZA Y NORMALIZACIÓN DE CAMPOS ===
    df_bookings["Propiedad"] = df_bookings["Propiedad"].fillna("Sin asignar").astype(str).str.strip().str.title()
    df_bookings["Habitación"] = df_bookings["Habitación"].fillna("Sin asignar").astype(str).str.strip().str.title()
    df_bookings["Huesped"] = df_bookings["Huesped"].fillna("Sin nombre").astype(str).str.strip().str.title()


    # === SECCIONES DE RESERVAS ===
    mostrar_titulo("Hoy")


    for _, row in checkouts_hoy.iterrows():
        mostrar_tarjeta_reserva(
            f"{row['Huesped']} ⮕ checkout",
            f"{row['Habitación']} · {row['Propiedad']}",
            f"https://i.pravatar.cc/150?u={row['Huesped']}",
            key=f"out-{row['Huesped']}-{row['Check-in']}",
            reserva_dict=row.to_dict()
        )

    for _, row in reservas_hoy.iterrows():
        checkin = pd.to_datetime(row["Check-in"])
        checkout = pd.to_datetime(row["Check-out"])
        dias_totales = (checkout - checkin).days
        dias_transcurridos = (hoy - checkin).days
        dias_restantes = dias_totales - dias_transcurridos
        texto_estancia = f"{dias_transcurridos} días de {dias_totales} totales"

        mostrar_tarjeta_reserva(
            f"{row['Huesped']} ⮕ {texto_estancia}",
            f"{row['Habitación']} · {row['Propiedad']}",
            f"https://i.pravatar.cc/150?u={row['Huesped']}",
            key=f"hoy-{row['Huesped']}-{row['Check-in']}",
            reserva_dict=row.to_dict()
        )



    # Agrupamos y mostramos Upcoming por propiedad
    mostrar_titulo("Upcoming")


    # Agrupar por propiedad
    for propiedad, grupo in upcoming.groupby("Propiedad"):
        mostrar_titulo(propiedad, color="#00ffe1", size="20px", margin_top="15px", margin_bottom="8px")
        
        for _, row in grupo.iterrows():
            checkin = row["Check-in"].strftime("%d %b")
            checkout = row["Check-out"].strftime("%d %b")
            mostrar_tarjeta_reserva(
                f"{checkin} → {checkout}",
                f"{row['Huesped']} · {row['Habitación']} · {row['Propiedad']}",
                f"https://i.pravatar.cc/150?u={row['Huesped']}",
                key=f"upcoming-{row['Huesped']}-{row['Check-in']}",
                reserva_dict=row.to_dict()
            )
with tabs[1]:  # LISTINGS
    mostrar_listings(df_bookings)

with tabs[2]:  # RESERVAS
    mostrar_reservas(df_reservas)

with tabs[3]:  # INVERSION
    mostrar_inversion(df_inversiones, df_gastos, df_reservas)

with tabs[4]:  # CALENDARIO
    mostrar_calendario(df_bookings)
