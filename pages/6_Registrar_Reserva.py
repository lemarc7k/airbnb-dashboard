import streamlit as st
import pandas as pd
import datetime
from firebase_config import db

st.set_page_config(page_title="Registrar Reservas", layout="wide")
st.title("📘 Registro de Reservas (conectado a Firebase)")

# ----------------------- FUNCIONES FIREBASE --------------------------- #
def obtener_reservas():
    docs = db.collection("bookings").stream()
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]

def agregar_o_actualizar_reserva(data, edit_id=None):
    if edit_id:
        db.collection("bookings").document(edit_id).set(data)
    else:
        db.collection("bookings").add(data)

def eliminar_reserva(doc_id):
    db.collection("bookings").document(doc_id).delete()

# ----------------------- DATOS --------------------------- #
datos = obtener_reservas()
df = pd.DataFrame(datos)

if not df.empty:
    df["Check-in"] = pd.to_datetime(df["Check-in"], errors="coerce")
    df["Check-out"] = pd.to_datetime(df["Check-out"], errors="coerce")
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

# ----------------------- ESTADOS --------------------------- #
def clasificar_estado(row):
    hoy = pd.to_datetime(datetime.date.today())
    if pd.isnull(row["Check-in"]) or pd.isnull(row["Check-out"]): return ""
    if row["Check-in"] <= hoy <= row["Check-out"]: return "Currently hosting"
    if row["Check-in"] > hoy: return "Upcoming"
    if row["Check-out"] == hoy: return "Checking out"
    if row["Check-in"] == hoy: return "Arriving soon"
    if row["Check-out"] < hoy: return "Pending review"
    return ""

df["Estado"] = df.apply(clasificar_estado, axis=1)

# ----------------------- FILTRADO --------------------------- #
st.subheader("🔍 Filtrado por estado")
conteos = df["Estado"].value_counts().to_dict()
col1, col2, col3, col4, col5 = st.columns(5)
with col1: st.button(f"Currently hosting ({conteos.get('Currently hosting', 0)})", key="f1", on_click=lambda: st.session_state.update({"selected_estado": "Currently hosting"}))
with col2: st.button(f"Upcoming ({conteos.get('Upcoming', 0)})", key="f2", on_click=lambda: st.session_state.update({"selected_estado": "Upcoming"}))
with col3: st.button(f"Checking out ({conteos.get('Checking out', 0)})", key="f3", on_click=lambda: st.session_state.update({"selected_estado": "Checking out"}))
with col4: st.button(f"Arriving soon ({conteos.get('Arriving soon', 0)})", key="f4", on_click=lambda: st.session_state.update({"selected_estado": "Arriving soon"}))
with col5: st.button(f"Pending review ({conteos.get('Pending review', 0)})", key="f5", on_click=lambda: st.session_state.update({"selected_estado": "Pending review"}))

estado_actual = st.session_state.get("selected_estado")
if estado_actual and estado_actual in df["Estado"].values:
    df_estado = df[df["Estado"] == estado_actual]
    for _, row in df_estado.iterrows():
        st.markdown(f"""
            <div style='background:#fff;border:1px solid #ccc;border-radius:10px;padding:10px;margin:5px;width:260px;display:inline-block'>
                <p style='color:crimson;font-weight:bold'>{estado_actual}</p>
                <p style='margin:0;font-size:18px;font-weight:bold'>{row["Huesped"]}</p>
                <p style='margin:0'>{row["Check-in"].strftime('%d %b')} - {row["Check-out"].strftime('%d %b')}</p>
                <p style='margin:0'>{row["Propiedad"]}</p>
            </div>
        """, unsafe_allow_html=True)

# ----------------------- FORMULARIO --------------------------- #
st.subheader("📝 Añadir o Editar una reserva")
edit_id = st.session_state.get("edit_id")
modo = "Editar" if edit_id else "Nueva"

datos_editar = next((d for d in datos if d["id"] == edit_id), None)
hoy = datetime.date.today()

with st.form("form_reserva", clear_on_submit=True):
    st.markdown(f"### {modo} reserva")
    col1, col2 = st.columns(2)
    with col1:
        propiedad = st.text_input("Propiedad", value=datos_editar.get("Propiedad", "") if datos_editar else "")
        habitacion = st.text_input("Habitación", value=datos_editar.get("Habitación", "") if datos_editar else "")
        huesped = st.text_input("Huésped", value=datos_editar.get("Huesped", "") if datos_editar else "")
        canal = st.selectbox("Canal", ["Airbnb", "Booking", "Directo", "StayMate", "Otro"], index=0)
        noches = st.number_input("Noches", min_value=1, value=int(datos_editar.get("Noches", 1)) if datos_editar else 1)
        huespedes = st.number_input("Huéspedes", min_value=1, value=int(datos_editar.get("Huespedes", 1)) if datos_editar else 1)
    with col2:
        check_in = st.date_input("Check-in", value=pd.to_datetime(datos_editar.get("Check-in")).date() if datos_editar else hoy)
        check_out = st.date_input("Check-out", value=pd.to_datetime(datos_editar.get("Check-out")).date() if datos_editar else hoy)
        precio = st.number_input("Precio (AUD)", min_value=0.0, step=10.0, value=float(datos_editar.get("Precio", 0.0)) if datos_editar else 0.0)
        pago = st.text_input("Método de pago", value=datos_editar.get("Pago", "") if datos_editar else "")
        notas = st.text_area("Notas", value=datos_editar.get("Notas", "") if datos_editar else "")

    enviar = st.form_submit_button("Guardar")
    if enviar:
        data = {
            "Fecha": pd.Timestamp.now(),
            "Propiedad": propiedad,
            "Habitación": habitacion,
            "Huesped": huesped,
            "Check-in": str(check_in),
            "Check-out": str(check_out),
            "Canal": canal,
            "Noches": noches,
            "Huespedes": huespedes,
            "Precio": precio,
            "Pago": pago,
            "Notas": notas
        }
        agregar_o_actualizar_reserva(data, edit_id)
        st.success("✅ Reserva guardada correctamente")
        st.session_state.edit_id = None
        st.rerun()

# ----------------------- HISTORIAL --------------------------- #
st.subheader("📚 Historial de reservas")

for r in datos:
    with st.expander(f"{r['Propiedad']} - {r['Huesped']} ({r['Check-in']} ➜ {r['Check-out']})"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Canal:** {r['Canal']}")
            st.markdown(f"**Noches:** {r['Noches']}")
            st.markdown(f"**Huéspedes:** {r['Huespedes']}")
        with col2:
            st.markdown(f"**Precio:** ${r['Precio']}")
            st.markdown(f"**Pago:** {r['Pago']}")
        st.markdown(f"**Notas:** {r['Notas']}")

        col3, col4 = st.columns([1, 6])
        with col3:
            if st.button("Eliminar", key=f"del_{r['id']}"):
                eliminar_reserva(r["id"])
                st.success("✅ Eliminada correctamente")
                st.rerun()
        with col4:
            if st.button("Editar", key=f"edit_{r['id']}"):
                st.session_state.edit_id = r["id"]
                st.rerun()
