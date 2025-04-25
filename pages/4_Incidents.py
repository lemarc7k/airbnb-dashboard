import streamlit as st
st.set_page_config(page_title="Incidentes", layout="wide")
import pandas as pd
import datetime
from firebase_config import db

try:
    # tu lógica aquí
    st.write("✅ Página cargada correctamente")
except Exception as e:
    st.error(f"❌ Error cargando página: {e}")


st.title("⚠️ Gestión de Incidencias")

# ---- FIRESTORE CONFIG ----
coleccion = "incidents"
CAMPOS = ["fecha", "propiedad", "descripcion", "estado"]

# ----- CARGAR DATOS DE INCIDENCIAS ----- #
docs = db.collection(coleccion).stream()
data = [{**doc.to_dict(), "id": doc.id} for doc in docs]
df = pd.DataFrame(data)

# -------- FORMULARIO PARA NUEVA INCIDENCIA --------
st.subheader("📝 Reportar Nueva Incidencia")
with st.form("form_incidencia", clear_on_submit=True):
    fecha = st.date_input("Fecha del incidente", value=datetime.date.today())
    propiedad = st.text_input("Propiedad o dirección")
    descripcion = st.text_area("Descripción del incidente")
    estado = st.selectbox("Estado", ["Pendiente", "Resuelto"])
    submitted = st.form_submit_button("Registrar")

    if submitted:
        if not propiedad.strip() or not descripcion.strip():
            st.error("❌ Todos los campos son obligatorios.")
        else:
            nueva = {
                "fecha": str(fecha),
                "propiedad": propiedad.strip(),
                "descripcion": descripcion.strip(),
                "estado": estado
            }
            db.collection(coleccion).add(nueva)
            st.success("✅ Incidencia registrada correctamente")
            st.rerun()

# -------- MOSTRAR INCIDENCIAS EXISTENTES --------
st.subheader("📋 Incidencias Registradas")
filtro_estado = st.selectbox("Filtrar por estado", ["Todos", "Pendiente", "Resuelto"], index=0)

# Aplicar filtro solo si la columna existe
if "estado" in df.columns and filtro_estado != "Todos":
    df = df[df["estado"] == filtro_estado]

# Mostrar solo columnas que realmente existan
columnas_disponibles = [col for col in CAMPOS if col in df.columns]
if columnas_disponibles:
    st.dataframe(df[columnas_disponibles], use_container_width=True)
else:
    st.warning("No hay columnas disponibles para mostrar.")

# -------- ACTUALIZAR ESTADO DE INCIDENCIAS --------
st.subheader("🔁 Cambiar Estado de Incidencias")
if not df.empty and all(k in df.columns for k in ["estado", "id", "propiedad", "fecha"]):
    for _, row in df.iterrows():
        col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
        with col1:
            st.write(row["fecha"])
        with col2:
            st.write(row["propiedad"])
        with col3:
            nuevo_estado = st.selectbox(
                "Nuevo estado",
                ["Pendiente", "Resuelto"],
                index=["Pendiente", "Resuelto"].index(row["estado"]),
                key=row["id"]
            )
        with col4:
            if st.button("Actualizar", key=f"inc_{row['id']}"):
                db.collection(coleccion).document(row["id"]).update({"estado": nuevo_estado})
                st.success("✅ Estado actualizado correctamente")
                st.rerun()
