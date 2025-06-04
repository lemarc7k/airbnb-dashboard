import streamlit as st
import pandas as pd

st.cache_data.clear()


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

def mostrar_listings(df):
    mostrar_titulo("🏠 Propiedades Activas")

    if df.empty:
        st.warning("⚠️ No se han encontrado bookings registrados aún.")
        return

    propiedades = df["Propiedad"].dropna().unique()

    for propiedad in propiedades:
        df_prop = df[df["Propiedad"] == propiedad]
        habitaciones = df_prop["Habitación"].dropna().unique()

        mostrar_titulo(f"🏡 {propiedad}", size="22px", margin_top="25px")

        # Distribuye en columnas de 3 tarjetas por fila
        cols = st.columns(3)

        for i, habitacion in enumerate(habitaciones):
            df_hab = df_prop[df_prop["Habitación"] == habitacion]
            reservas = df_hab.shape[0]
            ingresos = df_hab["Precio"].sum()

            with cols[i % 3]:
                st.markdown(f"""
                <div style="background-color:#0f172a; border-radius:16px; 
                            box-shadow:0 0 12px #00ffe110; padding:0; margin-bottom:25px; overflow:hidden;">
                    <img src="https://api.dicebear.com/7.x/shapes/svg?seed={habitacion}" 
                        style="width:100%; height:180px; object-fit:cover; background:#0e172a; border-bottom:1px solid #00ffe120;">
                    <div style="padding:15px;">
                        <h4 style="color:#00ffe1; margin:0 0 8px 0;">🛏️ {habitacion}</h4>
                        <p style="color:#aaa; margin:0 0 4px 0;">📍 {propiedad}</p>
                        <p style="color:#ccc; font-size:13px; margin:0;">
                            📅 {reservas} reservas · 💰 ${ingresos:,.2f}
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)


