import streamlit as st
import datetime
import pandas as pd
from firebase_admin import firestore
from firebase_config import db

st.set_page_config(page_title="Incidencias", layout="wide")
st.title("⚠️ Gestión de Incidencias")

COLLECTION = "incidents"

# ---------- FUNCIONES ---------- #
def cargar_incidencias():
    docs = db.collection(COLLECTION).stream()
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]

def registrar_incidencia(fecha, propiedad, descripcion, estado):
    doc_ref = db.collection(COLLECTION).document()
    doc_ref.set({
        "Fecha": fecha.isoformat(),
        "Propiedad": propiedad,
        "Descripción": descripcion,
        "Estado": estado
    })

def actualizar_estado(doc_id, nuevo_estado):
    db.collection(COLLECTION).document(doc_id).update({"Estado": nuevo_estado})

# ---------- FORMULARIO NUEVA INCIDENCIA ---------- #
st.subheader("📝 Reportar Nueva Incidencia")
with st.form("form_incidencia", clear_on_submit=True):
    fecha = st.date_input("Fecha del incidente", value=datetime.date.today())
    propiedad = st.text_input("Propiedad o dirección")
    descripcion = st.text_area("Descripción del incidente")
    estado = st.selectbox("Estado", ["Pendiente", "Resuelto"])
    submitted = st.form_submit_button("Registrar")

    if submitted:
        registrar_incidencia(fecha, propiedad, descripcion, estado)
        st.success("✅ Incidencia registrada correctamente")
        st.rerun()

# ---------- MOSTRAR INCIDENCIAS ---------- #
st.subheader("📋 Incidencias Registradas")
datos = cargar_incidencias()
df = pd.DataFrame(datos)

filtro_estado = st.selectbox("Filtrar por estado", ["Todos", "Pendiente", "Resuelto"], index=0)
if filtro_estado != "Todos":
    df = df[df["Estado"] == filtro_estado]

st.dataframe(df[["Fecha", "Propiedad", "Descripción", "Estado"]])

# ---------- ACTUALIZACIÓN DE ESTADO ---------- #
st.subheader("🔁 Cambiar Estado de Incidencias")
for _, row in df.iterrows():
    col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
    with col1:
        st.write(row["Fecha"])
    with col2:
        st.write(row["Propiedad"])
    with col3:
        nuevo_estado = st.selectbox(
            "Nuevo estado",
            ["Pendiente", "Resuelto"],
            index=["Pendiente", "Resuelto"].index(row["Estado"]),
            key=row["id"]
        )
    with col4:
        if st.button("Actualizar", key=f"upd_{row['id']}"):
            actualizar_estado(row["id"], nuevo_estado)
            st.success("✅ Estado actualizado correctamente")
            st.rerun()
