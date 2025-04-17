
import streamlit as st
import pandas as pd
import os
import datetime

FILE_PATH = "data/incidents.csv"
COLUMNS = ["Fecha", "Propiedad", "Descripción", "Estado"]

# Cargar o inicializar el archivo
if os.path.exists(FILE_PATH):
    df = pd.read_csv(FILE_PATH)
else:
    df = pd.DataFrame(columns=COLUMNS)

st.title("⚠️ Gestión de Incidencias")

# -------- FORMULARIO PARA NUEVA INCIDENCIA --------
st.subheader("📝 Reportar Nueva Incidencia")
with st.form("form_incidencia", clear_on_submit=True):
    fecha = st.date_input("Fecha del incidente", value=datetime.date.today())
    propiedad = st.text_input("Propiedad o dirección")
    descripcion = st.text_area("Descripción del incidente")
    estado = st.selectbox("Estado", ["Pendiente", "Resuelto"])
    submitted = st.form_submit_button("Registrar")

    if submitted:
        nueva = pd.DataFrame([[fecha, propiedad, descripcion, estado]], columns=COLUMNS)
        df = pd.concat([df, nueva], ignore_index=True)
        df.to_csv(FILE_PATH, index=False)
        st.success("✅ Incidencia registrada correctamente")
        st.experimental_rerun()

# -------- MOSTRAR INCIDENCIAS EXISTENTES --------
st.subheader("📋 Incidencias Registradas")
filtro_estado = st.selectbox("Filtrar por estado", ["Todos", "Pendiente", "Resuelto"], index=0)

df_filtrado = df.copy()
if filtro_estado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Estado"] == filtro_estado]

st.dataframe(df_filtrado)

# -------- ACTUALIZAR ESTADO DE INCIDENCIAS --------
st.subheader("🔁 Cambiar Estado de Incidencias")
if not df.empty:
    df["ID"] = df.index
    for _, row in df.iterrows():
        col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
        with col1:
            st.write(row["Fecha"])
        with col2:
            st.write(row["Propiedad"])
        with col3:
            nuevo_estado = st.selectbox("Nuevo estado", ["Pendiente", "Resuelto"], index=["Pendiente", "Resuelto"].index(row["Estado"]), key=row["ID"])
        with col4:
            if st.button("Actualizar", key=f"inc_{row['ID']}"):
                df.loc[df["ID"] == row["ID"], "Estado"] = nuevo_estado
                df.drop(columns="ID", inplace=True)
                df.to_csv(FILE_PATH, index=False)
                st.success("✅ Estado actualizado correctamente")
                st.experimental_rerun()
