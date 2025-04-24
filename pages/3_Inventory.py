import streamlit as st
import datetime
from firebase_admin import firestore
from firebase_config import db

st.set_page_config(page_title="Inventario", layout="wide")
st.title("📦 Inventario de Suministros")

COLLECTION = "inventory"

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

# --------- Cargar datos de Firebase ---------
def cargar_inventario():
    docs = db.collection(COLLECTION).stream()
    return [
        {**doc.to_dict(), "id": doc.id}
        for doc in docs
    ]

def guardar_producto(nombre, cantidad, unidad):
    doc_ref = db.collection(COLLECTION).document(nombre)
    doc_ref.set({
        "Producto": nombre,
        "Cantidad": cantidad,
        "Unidad": unidad,
        "Última actualización": datetime.date.today().isoformat()
    })

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

# -------- MOSTRAR DATOS --------
datos = cargar_inventario()
df = st.data_editor(
    pd.DataFrame(datos),
    column_order=["Producto", "Cantidad", "Unidad", "Última actualización"],
    use_container_width=True,
    disabled=["id"]
)

# -------- ALERTA DE STOCK BAJO --------
st.subheader("🚨 Productos con bajo stock")
stock_minimo = st.slider("Mostrar alertas si la cantidad es menor a:", 1, 20, 5)
df_bajo_stock = df[df["Cantidad"] < stock_minimo]
st.dataframe(df_bajo_stock)
