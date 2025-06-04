# === IMPORTACIONES PRINCIPALES ===
import streamlit as st
# Config inicial
st.set_page_config(page_title="Real Estate | MV Ventures", layout="wide")
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from datetime import datetime as dt

#from auth import login  # ⬅️ después del set_page_config
#login()  # ⬅️ ejecuta el login justo después de importarlo

# PESTAÑAS 
from pages.Listings import mostrar_listings  # ✅ CORRECTO
from pages.Reservas import mostrar_reservas
from pages.Inversion import mostrar_inversion



st.cache_data.clear()






# Resto de imports y código
import hashlib
import os
import pandas as pd
import altair as alt
import streamlit.components.v1 as components


# === LIBRERÍAS DE VISUALIZACIÓN ===
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import plotly.express as px
import plotly.graph_objects as go

# === COMPONENTES STREAMLIT ===
import streamlit.components.v1 as components
from streamlit_js_eval import streamlit_js_eval

# === FIREBASE ===
from firebase_config import db

# === LIBRERÍAS ADICIONALES ===
import time




# Tabs funcionales de Streamlit (invisibles)
tabs = st.tabs(["INICIO", "LISTINGS", "RESERVAS", "INVERSION", "CALENDARIO", "SIMULACION"])


from datetime import datetime
from firebase_config import db

from datetime import datetime
import pandas as pd
import streamlit as st
from firebase_config import db

# === CARGAR BOOKINGS DE FIRESTORE CON ID ===
#@st.cache_data(ttl=60)
def cargar_bookings():
    try:
        docs = db.collection("bookings").stream()
        data = []
        doc_ids = {}
        for doc in docs:
            row = doc.to_dict()
            clave = f"{row.get('Huesped')}_{row.get('Habitación')}_{row.get('Check-in')}"
            doc_ids[clave] = doc.id
            data.append(row)
        return pd.DataFrame(data), doc_ids
    except Exception as e:
        st.error(f"❌ Error al cargar datos de Firestore: {e}")
        return pd.DataFrame(), {}

# === USO ===
df, doc_ids = cargar_bookings()

# === LIMPIEZA Y FORMATO DE DATOS ===
def limpiar_dataframe(df):
    df["Check-in"] = pd.to_datetime(df["Check-in"], errors="coerce")
    df["Check-out"] = pd.to_datetime(df["Check-out"], errors="coerce")
    df["Propiedad"] = df["Propiedad"].fillna("Sin asignar").astype(str).str.strip().str.title()
    df["Habitación"] = df["Habitación"].fillna("Sin asignar").astype(str).str.strip().str.title()
    df["Huesped"] = df["Huesped"].fillna("Sin nombre").astype(str).str.strip().str.title()
    df["id_unico"] = df["Check-in"].astype(str) + df["Huesped"]
    return df

df = limpiar_dataframe(df)
hoy = pd.to_datetime(datetime.today().date())

# === FILTRADOS PRINCIPALES ===
upcoming = df[
    (df["Check-in"].notna()) &
    (df["Check-out"].notna()) &
    (df["Check-in"].dt.date > hoy.date()) &
    (df["Check-out"].dt.date > hoy.date())
].sort_values("Check-in")

reservas_hoy = df[(df["Check-in"].dt.date <= hoy.date()) & (df["Check-out"].dt.date >= hoy.date())]
checkouts_hoy = df[df["Check-out"].dt.date == hoy.date()]






with tabs[0]:  # LISTINGS

    # === ENCABEZADO ===
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
        # Generamos clave única para acceder al doc_id rápidamente
        clave_doc = f"{reserva_dict['Huesped']}_{reserva_dict['Habitación']}_{reserva_dict['Check-in']}"
        doc_id = doc_ids.get(clave_doc)

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

                modo_edicion = st.checkbox("✏️ Editar reserva", key=f"edit-{key}")

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
                    nueva_propiedad = st.text_input("📍 Propiedad", value=reserva_dict["Propiedad"], key=f"prop-{key}")
                    nueva_habitacion = st.text_input("🛏️ Habitación", value=reserva_dict["Habitación"], key=f"hab-{key}")
                    nuevo_checkin = st.date_input("📅 Check-in", value=checkin.date(), key=f"cin-{key}")
                    nuevo_checkout = st.date_input("📅 Check-out", value=checkout.date(), key=f"cout-{key}")
                    nuevo_precio = st.number_input("💰 Precio", value=float(reserva_dict["Precio"]), step=1.0, key=f"precio-{key}")
                    nuevo_estado = st.selectbox("🔄 Estado", ["pendiente", "pagado"], 
                                                index=0 if reserva_dict["Estado"] == "pendiente" else 1, key=f"estado-{key}")

                    if st.button("💾 Guardar cambios", key=f"save-{key}"):
                        if doc_id:
                            try:
                                db.collection("bookings").document(doc_id).update({
                                    "Propiedad": nueva_propiedad.strip().title(),
                                    "Habitación": nueva_habitacion.strip().title(),
                                    "Check-in": str(nuevo_checkin),
                                    "Check-out": str(nuevo_checkout),
                                    "Precio": float(nuevo_precio),
                                    "Estado": nuevo_estado.lower()
                                })
                                st.success("✅ Cambios guardados correctamente.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error al guardar: {e}")
                        else:
                            st.warning("❌ No se encontró esta reserva en Firestore.")
                        
            # Botón eliminar (mantener al final por claridad)
            if doc_id and st.button(f"🗑️ Eliminar reserva de {reserva_dict['Huesped']}", key=f"del-{key}"):
                db.collection("bookings").document(doc_id).delete()
                st.success("✅ Reserva eliminada correctamente.")
                st.rerun()


    # === LIMPIEZA Y NORMALIZACIÓN DE CAMPOS ===
    df["Propiedad"] = df["Propiedad"].fillna("Sin asignar").astype(str).str.strip().str.title()
    df["Habitación"] = df["Habitación"].fillna("Sin asignar").astype(str).str.strip().str.title()
    df["Huesped"] = df["Huesped"].fillna("Sin nombre").astype(str).str.strip().str.title()

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
        texto_estancia = f"{dias_transcurridos} noche/s de {dias_totales} restantes"

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
    mostrar_listings(df)

with tabs[2]:  # RESERVAS
    mostrar_reservas(df)

with tabs[3]:  # INVERSION
    mostrar_inversion()


