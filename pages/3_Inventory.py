
import streamlit as st
import pandas as pd
import os
import datetime

FILE_PATH = "data/inventory.csv"
COLUMNS = ["Producto", "Cantidad", "Unidad", "Última actualización"]

PRODUCTOS_PREDEFINIDOS = [
    {"nombre": "Bolsas de basura", "unidad": "unidades"},
    {"nombre": "Esponja", "unidad": "unidades"},
    {"nombre": "Bayeta microfibra", "unidad": "unidades"},
    {"nombre": "Jabón líquido", "unidad": "litros"},
    {"nombre": "Ambientador", "unidad": "litros"},
    {"nombre": "Toilet paper", "unidad": "pack"},
    {"nombre": "Detergente", "unidad": "litros"},
    {"nombre": "Guantes", "unidad": "pares"},
    {"nombre": "Paño de cocina", "unidad": "unidades"},
    {"nombre": "Spray multiusos", "unidad": "litros"},
    {"nombre": "Papel higiénico", "unidad": "rollos"},
    {"nombre": "Desinfectante", "unidad": "litros"},
    {"nombre": "Fregona", "unidad": "unidades"},
    {"nombre": "Escoba", "unidad": "unidades"},
    {"nombre": "Recogedor", "unidad": "unidades"},
    {"nombre": "Ambientador en spray", "unidad": "unidades"},
    {"nombre": "Toallas extra", "unidad": "unidades"},
    {"nombre": "Fundas de almohada", "unidad": "unidades"},
    {"nombre": "Sábanas", "unidad": "unidades"},
    {"nombre": "Alfombra de baño", "unidad": "unidades"}
]


# Cargar o crear archivo
if os.path.exists(FILE_PATH):
    df = pd.read_csv(FILE_PATH)
else:
    df = pd.DataFrame(columns=COLUMNS)

st.title("📦 Inventario de Suministros")

# -------- FORMULARIO RÁPIDO PARA PRODUCTOS PREDEFINIDOS --------
st.subheader("➕ Añadir o Actualizar Producto (Predefinido)")
producto_sel = st.selectbox("Seleccionar producto", [p["nombre"] for p in PRODUCTOS_PREDEFINIDOS])
unidad_sugerida = next((p["unidad"] for p in PRODUCTOS_PREDEFINIDOS if p["nombre"] == producto_sel), "")
col1, col2 = st.columns(2)
with col1:
    cantidad = st.number_input("Cantidad disponible", min_value=0.0, step=1.0, format="%.2f")
with col2:
    unidad = st.text_input("Unidad", value=unidad_sugerida)

if st.button("Guardar"):
    fecha = datetime.date.today()
    nueva_fila = pd.DataFrame([[producto_sel, cantidad, unidad, fecha]], columns=COLUMNS)

    if producto_sel in df["Producto"].values:
        df.loc[df["Producto"] == producto_sel, ["Cantidad", "Unidad", "Última actualización"]] = [cantidad, unidad, fecha]
        st.success("✅ Producto actualizado.")
    else:
        df = pd.concat([df, nueva_fila], ignore_index=True)
        st.success("✅ Producto añadido.")

    df.to_csv(FILE_PATH, index=False)
    st.experimental_rerun()

# -------- ALERTA DE STOCK BAJO --------
st.subheader("🚨 Productos con bajo stock")
stock_minimo = st.slider("Mostrar alertas si la cantidad es menor a:", 1, 20, 5)
df_alerta = df[df["Cantidad"] < stock_minimo]
st.dataframe(df_alerta)

# -------- VER TODO EL INVENTARIO --------
st.subheader("📋 Inventario Completo")
st.dataframe(df)
