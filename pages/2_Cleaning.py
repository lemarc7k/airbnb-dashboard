import streamlit as st
import pandas as pd
import datetime
from firebase_config import db  # Importa la configuración de Firebase

st.set_page_config(page_title="Gestión de Limpiezas", layout="wide")
st.title("🧹 Gestión de Limpiezas")

COLUMNS = ["Fecha", "Propiedad", "Habitación", "Cleaner", "Estado", "Origen"]

PRODUCTOS_POR_LIMPIEZA = {
    "Bolsas de basura": {"cantidad": 2, "unidad": "unidades"},
    "Esponja": {"cantidad": 1, "unidad": "unidades"},
    "Bayeta microfibra": {"cantidad": 1, "unidad": "unidades"},
    "Jabón líquido": {"cantidad": 0.1, "unidad": "litros"},
    "Ambientador": {"cantidad": 0.05, "unidad": "litros"}
}

def cargar_limpiezas():
    docs = db.collection("cleaning").stream()
    registros = []
    for doc in docs:
        data = doc.to_dict()
        data["doc_id"] = doc.id
        registros.append(data)
    return pd.DataFrame(registros, columns=COLUMNS + ["doc_id"])

def descontar_inventario():
    inv_docs = db.collection("inventory").stream()
    for inv in inv_docs:
        data = inv.to_dict()
        nombre = data.get("Producto")
        if nombre in PRODUCTOS_POR_LIMPIEZA:
            cantidad_actual = float(data.get("Cantidad", 0))
            cantidad_descuento = PRODUCTOS_POR_LIMPIEZA[nombre]["cantidad"]
            nueva_cantidad = max(0, cantidad_actual - cantidad_descuento)
            db.collection("inventory").document(inv.id).update({
                "Cantidad": nueva_cantidad,
                "Última actualización": str(datetime.date.today())
            })

df = cargar_limpiezas()

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
        nueva = {
            "Fecha": str(fecha),
            "Propiedad": propiedad,
            "Habitación": habitacion,
            "Cleaner": cleaner,
            "Estado": estado,
            "Origen": origen
        }
        db.collection("cleaning").add(nueva)
        st.success("✅ Limpieza registrada correctamente")
        st.rerun()

# ---- ACTUALIZAR ESTADO ----
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
                key=row["doc_id"]
            )
        with col4:
            if st.button("Actualizar", key=f"update_{row['doc_id']}"):
                db.collection("cleaning").document(row["doc_id"]).update({"Estado": nuevo_estado})
                if nuevo_estado == "Completado":
                    descontar_inventario()
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
