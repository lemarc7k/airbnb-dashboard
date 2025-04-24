import streamlit as st
import datetime
import pandas as pd
from firebase_config import db

st.set_page_config(page_title="Registrar Gastos", layout="wide")
st.title("💸 Registro de Gastos en Firestore")

# ---------- FORMULARIO ---------- #
st.subheader("📝 Añadir Gasto")

with st.form("form_gasto", clear_on_submit=True):
    descripcion = st.text_input("Descripción del gasto")
    monto = st.number_input("Monto en AUD", min_value=0.0, step=1.0)
    propiedad = st.text_input("Propiedad relacionada")
    fecha = st.date_input("Fecha del gasto", value=datetime.date.today())
    submit = st.form_submit_button("Guardar")

    if submit:
        nuevo_gasto = {
            "descripcion": descripcion,
            "monto": monto,
            "propiedad": propiedad,
            "fecha": fecha
        }
        db.collection("gastos").add(nuevo_gasto)
        st.success("✅ Gasto registrado correctamente")

# ---------- MOSTRAR GASTOS ---------- #
st.markdown("---")
st.subheader("📋 Historial de Gastos")

docs = db.collection("gastos").stream()
gastos = []

for doc in docs:
    data = doc.to_dict()
    gastos.append(data)

if gastos:
    df_gastos = pd.DataFrame(gastos)
    df_gastos["fecha"] = pd.to_datetime(df_gastos["fecha"], errors="coerce")
    df_gastos["monto"] = pd.to_numeric(df_gastos["monto"], errors="coerce")

    st.dataframe(df_gastos.sort_values("fecha", ascending=False), use_container_width=True)
    st.metric("Total de Gastos", f"${df_gastos['monto'].sum():,.2f}")
else:
    st.info("No hay gastos registrados aún.")
