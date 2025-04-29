import streamlit as st
import pandas as pd
import datetime
from firebase_config import db  # ✅ Firebase seguro con st.secrets

try:
    # tu lógica aquí
    st.write("✅ Página cargada correctamente")
except Exception as e:
    st.error(f"❌ Error cargando página: {e}")


st.title("📒 Registro de Gastos en Firestore")

# ---------- FORMULARIO ---------- #
st.subheader("🧾 Añadir Gasto")
descripcion = st.text_input("Descripción del gasto")
monto = st.number_input("Monto en AUD", min_value=0.0, step=0.5)
propiedad = st.text_input("Propiedad relacionada")
fecha = st.date_input("Fecha del gasto", value=datetime.date.today())

if st.button("Guardar"):
    nuevo_gasto = {
        "descripcion": descripcion,
        "monto": monto,
        "propiedad": propiedad,
        "fecha": str(fecha)
    }
    db.collection("gastos").add(nuevo_gasto)
    st.success("✅ Gasto registrado correctamente")

# ---------- HISTORIAL DE GASTOS ---------- #
st.subheader("📊 Historial de Gastos")

gastos_ref = db.collection("gastos")
docs = gastos_ref.stream()
data = [doc.to_dict() for doc in docs]
df = pd.DataFrame(data)

if not df.empty:
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["monto"] = pd.to_numeric(df["monto"], errors="coerce").fillna(0)
    st.dataframe(df.sort_values("fecha", ascending=False), use_container_width=True)
    st.markdown(f"**Total de Gastos:** ${df['monto'].sum():,.2f}")
else:
    st.info("No hay gastos registrados aún.")
