import streamlit as st
import pandas as pd
import datetime
from firebase_config import db

try:
    # tu lógica aquí
    st.write("✅ Página cargada correctamente")
except Exception as e:
    st.error(f"❌ Error cargando página: {e}")

st.title("📦 Inventario de Suministros")

# -------- PRODUCTOS PREDEFINIDOS --------
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

# -------- FUNCIONES FIRESTORE --------
def obtener_inventario():
    docs = db.collection("inventory").stream()
    data = [doc.to_dict() | {"id": doc.id} for doc in docs]
    return pd.DataFrame(data) if data else pd.DataFrame(columns=["Producto", "Cantidad", "Unidad", "Última actualización"])

def guardar_producto(producto, cantidad, unidad):
    ref = db.collection("inventory").document(producto)
    ref.set({
        "Producto": producto,
        "Cantidad": cantidad,
        "Unidad": unidad,
        "Última actualización": datetime.date.today().isoformat()
    })

# -------- CARGAR INVENTARIO --------
df = obtener_inventario()

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
    guardar_producto(producto_sel, cantidad, unidad)
    st.success("✅ Producto guardado correctamente")
    st.rerun()

# -------- ALERTA DE STOCK BAJO --------
st.subheader("🚨 Productos con bajo stock")
stock_minimo = st.slider("Mostrar alertas si la cantidad es menor a:", 1, 20, 5)
df_alerta = df[df["Cantidad"] < stock_minimo]
st.dataframe(df_alerta)

# -------- VER TODO EL INVENTARIO --------
st.subheader("📋 Inventario Completo")
st.dataframe(df)