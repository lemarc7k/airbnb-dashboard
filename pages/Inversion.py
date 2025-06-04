import streamlit as st
from firebase_config import db
import pandas as pd
from datetime import datetime
import plotly.express as px

st.cache_data.clear()



def mostrar_inversion(df_bookings):
    st.markdown("""
        <h2 style='text-align:center; color:#00ffe1;'>💼 Análisis de Inversión</h2>
        <p style='text-align:center; color:#ccc;'>Gestiona la inversión inicial de cada propiedad y analiza su retorno</p>
        <hr style='border: 1px solid #00ffe1;'>
    """, unsafe_allow_html=True)

    # =================== FORMULARIO PARA NUEVA INVERSIÓN =====================
    with st.form("form_inversion"):
        st.subheader("Registrar nueva inversión")
        col1, col2 = st.columns(2)
        with col1:
            propiedad = st.text_input("🏠 Propiedad")
        with col2:
            monto = st.number_input("💰 Monto inversión (AUD)", min_value=0.0, step=100.0)

        descripcion = st.text_area("📝 Descripción (opcional)")
        fecha = st.date_input("📅 Fecha", value=datetime.today())

        registrar = st.form_submit_button("✅ Registrar inversión")

        if registrar:
            db.collection("inversiones").add({
                "Propiedad": propiedad.strip().upper(),
                "Monto": monto,
                "Descripcion": descripcion,
                "Fecha": str(fecha)
            })
            st.success("✅ Inversión registrada correctamente.")

    st.markdown("---")

    # =================== CARGAR INVERSIONES DESDE FIRESTORE =====================
    inversiones_raw = db.collection("inversiones").stream()
    inversiones_data = [inv.to_dict() for inv in inversiones_raw]
    df_inversiones = pd.DataFrame(inversiones_data)

    if df_inversiones.empty:
        st.warning("Aún no se han registrado inversiones.")
        return

    # Normalizamos
    df_inversiones["Fecha"] = pd.to_datetime(df_inversiones["Fecha"], errors="coerce")
    df_inversiones["Propiedad"] = df_inversiones["Propiedad"].astype(str).str.strip().str.upper()

    # =================== CÁLCULOS DE ROI =====================
    df_bookings["Propiedad"] = df_bookings["Propiedad"].astype(str).str.strip().str.upper()
    ingresos_por_prop = df_bookings.groupby("Propiedad")["Precio"].sum().reset_index()
    inversiones_por_prop = df_inversiones.groupby("Propiedad")["Monto"].sum().reset_index()

    df_merged = pd.merge(inversiones_por_prop, ingresos_por_prop, on="Propiedad", how="outer").fillna(0)
    df_merged["ROI (%)"] = ((df_merged["Precio"] / df_merged["Monto"]) * 100).round(2)
    df_merged.rename(columns={"Monto": "Inversión (AUD)", "Precio": "Ingresos (AUD)"}, inplace=True)

    st.markdown("### 📊 Resumen por propiedad")
    st.dataframe(df_merged, use_container_width=True)

    # =================== GRÁFICO DE RECUPERACIÓN =====================
    fig = px.bar(df_merged, x="Propiedad", y=["Inversión (AUD)", "Ingresos (AUD)"],
                 barmode="group", color_discrete_sequence=["#00ffe1", "#1f77b4"],
                 title="Comparación Inversión vs. Ingresos")

    st.plotly_chart(fig, use_container_width=True)

    # =================== HISTORIAL DE INVERSIONES =====================
    with st.expander("🧾 Ver historial completo de inversiones"):
        df_inversiones = df_inversiones.sort_values("Fecha", ascending=False)
        st.dataframe(df_inversiones, use_container_width=True)
