import streamlit as st
import pandas as pd
import os
import datetime

# ---- CONFIG ----
FILE_PATH = "data/cleaning_schedule.csv"
COLUMNS = ["Fecha", "Propiedad", "Habitación", "Cleaner", "Estado", "Origen"]

# ---- CONSUMO DE INVENTARIO POR LIMPIEZA ----
PRODUCTOS_POR_LIMPIEZA = {
    "Bolsas de basura": {"cantidad": 2, "unidad": "unidades"},
    "Esponja": {"cantidad": 1, "unidad": "unidades"},
    "Bayeta microfibra": {"cantidad": 1, "unidad": "unidades"},
    "Jabón líquido": {"cantidad": 0.1, "unidad": "litros"},
    "Ambientador": {"cantidad": 0.05, "unidad": "litros"}
}

def descontar_inventario():
    inv_path = "data/inventory.csv"
    if not os.path.exists(inv_path):
        return
    df_inv = pd.read_csv(inv_path)
    for producto, info in PRODUCTOS_POR_LIMPIEZA.items():
        if producto in df_inv["Producto"].values:
            index = df_inv[df_inv["Producto"] == producto].index[0]
            actual = float(df_inv.at[index, "Cantidad"])
            nuevo = max(0, actual - info["cantidad"])
            df_inv.at[index, "Cantidad"] = nuevo
            df_inv.at[index, "Última actualización"] = datetime.date.today()
    df_inv.to_csv(inv_path, index=False)

# ---- CARGAR O CREAR ARCHIVO DE LIMPIEZAS ----
if os.path.exists(FILE_PATH):
    df = pd.read_csv(FILE_PATH)
else:
    df = pd.DataFrame(columns=COLUMNS)

st.title("🧹 Gestión de Limpiezas")

# ---- FILTROS ----
st.subheader("🔍 Filtros")
col1, col2 = st.columns(2)
with col1:
    filtro_propiedad = st.selectbox("Propiedad", ["Todas"] + sorted(df["Propiedad"].dropna().unique()), index=0)
with col2:
    filtro_estado = st.selectbox("Estado", ["Todos", "Pendiente", "En progreso", "Completado"], index=0)

filtro_fecha = None
if st.checkbox("Filtrar por fecha específica"):
    filtro_fecha = st.date_input("Seleccionar fecha")

df_filtrado = df.copy()
if filtro_propiedad != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Propiedad"] == filtro_propiedad]
if filtro_estado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Estado"] == filtro_estado]
if filtro_fecha:
    df_filtrado = df_filtrado[df_filtrado["Fecha"] == str(filtro_fecha)]

st.dataframe(df_filtrado)

# ---- FORMULARIO NUEVA LIMPIEZA ----
st.subheader("➕ Programar Nueva Limpieza")
with st.form("form_limpieza", clear_on_submit=True):
    fecha = st.date_input("Fecha")
    propiedad = st.text_input("Nombre de la propiedad")
    habitacion = st.text_input("Habitación")
    cleaner = st.text_input("Nombre del cleaner")
    estado = st.selectbox("Estado inicial", ["Pendiente", "En progreso", "Completado"])
    origen = st.selectbox("Origen", ["Manual", "Auto"])
    submitted = st.form_submit_button("Guardar limpieza")

    if submitted:
        nueva = pd.DataFrame([[fecha, propiedad, habitacion, cleaner, estado, origen]], columns=COLUMNS)
        df = pd.concat([df, nueva], ignore_index=True)
        df.to_csv(FILE_PATH, index=False)
        st.success("✅ Limpieza registrada correctamente")
        st.rerun()

# ---- ACTUALIZAR ESTADO ----
st.subheader("🔁 Actualizar Estado")
if not df.empty:
    df_actualizacion = df.copy()
    df_actualizacion["ID"] = df_actualizacion.index
    for _, row in df_actualizacion.iterrows():
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            st.write(row["Fecha"])
        with col2:
            st.write(f"{row['Propiedad']} - {row['Habitación']}")
        with col3:
            nuevo_estado = st.selectbox(
                "Cambiar estado",
                ["Pendiente", "En progreso", "Completado"],
                index=["Pendiente", "En progreso", "Completado"].index(row["Estado"]),
                key=row["ID"]
            )
        with col4:
            if st.button("Actualizar", key=f"update_{row['ID']}"):
                df.loc[row["ID"], "Estado"] = nuevo_estado
                if nuevo_estado == "Completado":
                    descontar_inventario()
                df.to_csv(FILE_PATH, index=False)
                st.success("✅ Estado actualizado")
                st.rerun()

# ---- MÉTRICAS ----
st.subheader("📊 Métricas de Limpieza")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total tareas", len(df))
with col2:
    st.metric("Pendientes", len(df[df["Estado"] == "Pendiente"]))
with col3:
    st.metric("Completadas", len(df[df["Estado"] == "Completado"]))

# ---- ALERTAS VISUALES ----
st.subheader("🚨 Alertas visuales (tareas atrasadas)")

today = datetime.date.today()
df_alertas = df.copy()
df_alertas["Fecha"] = pd.to_datetime(df_alertas["Fecha"], errors="coerce").dt.date

def evaluar_estado(row):
    if pd.isna(row["Fecha"]):
        return "⚠️ Sin fecha"
    delta = (today - row["Fecha"]).days
    if row["Estado"] == "Pendiente" and delta > 2:
        return "🔴 ATRASADA"
    elif row["Estado"] == "En progreso" and delta > 1:
        return "🟠 EN PROGRESO RETRASADA"
    elif row["Estado"] == "Completado":
        return "✅ Ok"
    else:
        return "🕓 A tiempo"

df_alertas["Alerta"] = df_alertas.apply(evaluar_estado, axis=1)

st.dataframe(df_alertas[["Fecha", "Propiedad", "Habitación", "Cleaner", "Estado", "Alerta"]])
