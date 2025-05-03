import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Historial de Accesos", layout="wide")
st.title("📋 Historial de Accesos al Dashboard")

LOG_FILE = "access_log.csv"

# Si el archivo no existe
if not os.path.exists(LOG_FILE):
    st.warning("Aún no hay accesos registrados.")
    st.stop()

# Leer registros
df = pd.read_csv(LOG_FILE)

# Convertir fecha a datetime para orden
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values(by="timestamp", ascending=False)

# Mostrar tabla
st.dataframe(df, use_container_width=True)

# Filtro por usuario
usuarios = df["usuario"].unique()
selected_user = st.selectbox("Filtrar por usuario", options=["Todos"] + list(usuarios))

if selected_user != "Todos":
    df = df[df["usuario"] == selected_user]

# Mostrar tabla filtrada
st.write("Últimos accesos:")
st.dataframe(df, use_container_width=True)
