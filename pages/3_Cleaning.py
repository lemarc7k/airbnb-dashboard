import streamlit as st
st.set_page_config(page_title="🧹 Gestión de Limpiezas", layout="wide")
import pandas as pd
import datetime
from firebase_config import db

try:
    # tu lógica aquí
    st.write("✅ Página cargada correctamente")
except Exception as e:
    st.error(f"❌ Error cargando página: {e}")


st.title("🧹 Gestión de Limpiezas")

# ----- PRODUCTOS POR LIMPIEZA -----
PRODUCTOS_POR_LIMPIEZA = {
    "Bolsas de basura": {"cantidad": 2, "unidad": "unidades"},
    "Esponja": {"cantidad": 1, "unidad": "unidades"},
    "Bayeta microfibra": {"cantidad": 1, "unidad": "unidades"},
    "Jabón líquido": {"cantidad": 0.1, "unidad": "litros"},
    "Ambientador": {"cantidad": 0.05, "unidad": "litros"}
}

# ----- FUNCIONES FIRESTORE -----
def cargar_limpiezas():
    docs = db.collection("cleaning").stream()
    data = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        data.append(d)
    df = pd.DataFrame(data)
    if not df.empty:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce").dt.date
    return df

def guardar_limpieza(nueva):
    db.collection("cleaning").add(nueva)

def actualizar_estado_limpieza(doc_id, nuevo_estado):
    db.collection("cleaning").document(doc_id).update({"Estado": nuevo_estado})
    if nuevo_estado == "Completado":
        descontar_inventario()

def descontar_inventario():
    inventario_ref = db.collection("inventory")
    docs = inventario_ref.stream()
    for doc in docs:
        data = doc.to_dict()
        producto = data["Producto"]
        if producto in PRODUCTOS_POR_LIMPIEZA:
            cantidad_actual = float(data.get("Cantidad", 0))
            cantidad_usada = PRODUCTOS_POR_LIMPIEZA[producto]["cantidad"]
            nueva_cantidad = max(0, cantidad_actual - cantidad_usada)
            inventario_ref.document(doc.id).update({
                "Cantidad": nueva_cantidad,
                "Última actualización": datetime.date.today().isoformat()
            })

# ----- CARGAR DATOS -----
df = cargar_limpiezas()

# ----- FILTROS -----
st.subheader("🔍 Filtros")
col1, col2 = st.columns(2)

if not df.empty and "Propiedad" in df.columns:
    with col1:
        filtro_propiedad = st.selectbox("Propiedad", ["Todas"] + sorted(df["Propiedad"].dropna().unique()), index=0)
else:
    filtro_propiedad = "Todas"
    with col1:
        st.warning("No hay datos o falta el campo 'Propiedad'")

with col2:
    filtro_estado = st.selectbox("Estado", ["Todos", "Pendiente", "En progreso", "Completado"], index=0)

filtro_fecha = None
if st.checkbox("Filtrar por fecha específica"):
    filtro_fecha = st.date_input("Seleccionar fecha")

df_filtrado = df.copy()
if filtro_propiedad != "Todas" and "Propiedad" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Propiedad"] == filtro_propiedad]
if filtro_estado != "Todos" and "Estado" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Estado"] == filtro_estado]
if filtro_fecha and "Fecha" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Fecha"] == filtro_fecha]

st.dataframe(df_filtrado)


# ----- FORMULARIO -----
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
        nueva = {
            "Fecha": fecha.isoformat(),
            "Propiedad": propiedad,
            "Habitación": habitacion,
            "Cleaner": cleaner,
            "Estado": estado,
            "Origen": origen
        }
        guardar_limpieza(nueva)
        st.success("✅ Limpieza registrada correctamente")
        st.rerun()

# ----- ACTUALIZAR ESTADO -----
st.subheader("🔁 Actualizar Estado")
if not df.empty:
    for _, row in df.iterrows():
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
                key=row["id"] + "_estado"
            )
        with col4:
            if st.button("Actualizar", key=f"update_{row['id']}"):
                actualizar_estado_limpieza(row["id"], nuevo_estado)
                st.success("✅ Estado actualizado")
                st.rerun()

# ----- MÉTRICAS -----
st.subheader("📊 Métricas de Limpieza")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total tareas", len(df))

if "Estado" in df.columns:
    with col2:
        st.metric("Pendientes", len(df[df["Estado"] == "Pendiente"]))
    with col3:
        st.metric("Completadas", len(df[df["Estado"] == "Completado"]))
else:
    st.warning("Algunas tareas no tienen estado asignado. Revisa los datos.")


# ----- ALERTAS VISUALES -----
st.subheader("🚨 Alertas visuales (tareas atrasadas)")
today = datetime.date.today()

def evaluar_estado(row):
    if pd.isna(row.get("Fecha")):
        return "⚠️ Sin fecha"
    delta = (today - row["Fecha"]).days
    if row.get("Estado") == "Pendiente" and delta > 2:
        return "🔴 ATRASADA"
    elif row.get("Estado") == "En progreso" and delta > 1:
        return "🟠 EN PROGRESO RETRASADA"
    elif row.get("Estado") == "Completado":
        return "✅ Ok"
    else:
        return "🕓 A tiempo"

# Aplica alertas solo si df no está vacío y tiene columnas necesarias
if not df.empty and "Fecha" in df.columns and "Estado" in df.columns:
    df["Alerta"] = df.apply(evaluar_estado, axis=1)
    st.dataframe(df[["Fecha", "Propiedad", "Habitación", "Cleaner", "Estado", "Alerta"]])
else:
    st.warning("No hay datos suficientes para mostrar alertas.")
