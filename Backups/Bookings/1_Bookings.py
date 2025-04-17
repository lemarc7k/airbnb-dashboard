import streamlit as st
import pandas as pd
import os
import datetime
from streamlit_calendar import calendar

# CONFIGURACIÓN
st.set_page_config(layout="wide")
st.title("🗕️ Calendario Estilo Airbnb de Reservas")

# RUTAS
BOOKINGS_PATH = "data/bookings.csv"
CLEANING_PATH = "data/cleaning_schedule.csv"

# COLUMNAS
BOOKINGS_COLUMNS = ["Fecha", "Propiedad", "Húsped", "Check-in", "Check-out", "Notas"]
CLEANING_COLUMNS = ["Fecha", "Propiedad", "Cleaner", "Estado"]

# ---------- FUNCION LIMPIEZAS ----------
def sincronizar_limpiezas_auto(df_bookings):
    if os.path.exists(CLEANING_PATH):
        df_clean = pd.read_csv(CLEANING_PATH)
        if "Cleaner" not in df_clean.columns:
            df_clean["Cleaner"] = ""
    else:
        df_clean = pd.DataFrame(columns=CLEANING_COLUMNS)

    nuevas = []
    for _, row in df_bookings.iterrows():
        if pd.notnull(row["Check-out"]):
            fecha_limpieza = (pd.to_datetime(row["Check-out"]) + pd.Timedelta(days=1)).date()
            existe = df_clean[
                (pd.to_datetime(df_clean["Fecha"]).dt.date == fecha_limpieza) &
                (df_clean["Propiedad"] == row["Propiedad"])
            ]
            if existe.empty:
                nuevas.append({
                    "Fecha": fecha_limpieza,
                    "Propiedad": row["Propiedad"],
                    "Cleaner": "",
                    "Estado": "Pendiente"
                })

    if nuevas:
        nuevos_df = pd.DataFrame(nuevas)
        df_clean_actualizado = pd.concat([df_clean, nuevos_df], ignore_index=True)
        df_clean_actualizado.to_csv(CLEANING_PATH, index=False)

# ---------- CARGA DE DATOS ----------
if os.path.exists(BOOKINGS_PATH):
    df = pd.read_csv(BOOKINGS_PATH)
    for col in BOOKINGS_COLUMNS:
        if col not in df.columns:
            df[col] = ""
else:
    df = pd.DataFrame(columns=BOOKINGS_COLUMNS)

# Asegurar tipos correctos
for col in ["Check-in", "Check-out", "Fecha"]:
    df[col] = pd.to_datetime(df[col], errors="coerce")

# ---------- FILTROS ----------
with st.sidebar:
    st.subheader("🔍 Filtros")
    propiedad_filtrada = st.selectbox("Filtrar por propiedad", ["Todas"] + sorted(df["Propiedad"].dropna().unique()), index=0)
    hoy = datetime.date.today()
    mes_actual = hoy.strftime("%Y-%m")
    meses = sorted(df["Check-in"].dropna().dt.strftime("%Y-%m").unique())
    mes_seleccionado = st.selectbox("Filtrar por mes", meses, index=meses.index(mes_actual) if mes_actual in meses else 0)

df_filtrado = df.copy()
if propiedad_filtrada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Propiedad"] == propiedad_filtrada]
df_filtrado = df_filtrado[df_filtrado["Check-in"].dt.strftime("%Y-%m") == mes_seleccionado]

# ---------- EVENTOS EN CALENDARIO ----------
eventos = []
for i, row in df_filtrado.iterrows():
    if pd.notnull(row["Check-in"]) and pd.notnull(row["Check-out"]):
        eventos.append({
            "id": str(i),
            "title": f"{row['Húsped']} - {row['Propiedad']}",
            "start": row["Check-in"].strftime("%Y-%m-%d"),
            "end": (row["Check-out"] + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            "color": "#3b82f6"
        })

clicked_event = calendar(
    events=eventos,
    options={
        "locale": "es",
        "initialView": "dayGridMonth",
        "height": 600,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek"
        },
        "nowIndicator": True,
        "eventClick": True
    },
    key="calendar"
)

# ---------- ESTADO DE EDICION ----------
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None
if clicked_event and clicked_event.get("id"):
    st.session_state.edit_id = int(clicked_event["id"])

# ---------- FORMULARIO DE RESERVA ----------
with st.expander("✏️ Añadir o Editar Reserva"):
    st.subheader("Formulario de Reserva")
    if st.session_state.edit_id is not None and st.session_state.edit_id < len(df):
        row = df.loc[st.session_state.edit_id]
        propiedad = st.text_input("🏡 Propiedad", value=row["Propiedad"])
        huesped = st.text_input("👤 Huésped", value=row["Húsped"])
        check_in = st.date_input("🗓️ Check-in", value=pd.to_datetime(row["Check-in"]).date())
        check_out = st.date_input("📺 Check-out", value=pd.to_datetime(row["Check-out"]).date())
        notas = st.text_area("📜 Notas internas", value=row.get("Notas", ""))
    else:
        propiedad = st.text_input("🏡 Propiedad")
        huesped = st.text_input("👤 Huésped")
        check_in = st.date_input("🗓️ Check-in")
        check_out = st.date_input("📺 Check-out")
        notas = st.text_area("📜 Notas internas")

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.session_state.edit_id is not None and st.session_state.edit_id < len(df):
            if st.button("✅ Guardar cambios"):
                if not propiedad or not huesped:
                    st.error("❌ Todos los campos deben estar completos antes de guardar.")
                else:
                    df.loc[st.session_state.edit_id] = [
                        datetime.datetime.now(), propiedad, huesped, check_in, check_out, notas
                    ]
                    df.to_csv(BOOKINGS_PATH, index=False)
                    sincronizar_limpiezas_auto(df)
                    st.success("✏️ Reserva actualizada")
                    st.session_state.edit_id = None
                    st.experimental_rerun()
        else:
            if st.button("➕ Añadir reserva"):
                if not propiedad or not huesped:
                    st.error("❌ Todos los campos deben estar completos antes de guardar.")
                else:
                    nueva = pd.DataFrame([{ 
                        "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Propiedad": propiedad,
                        "Húsped": huesped,
                        "Check-in": pd.to_datetime(check_in),
                        "Check-out": pd.to_datetime(check_out),
                        "Notas": notas
                    }])
                    df = pd.concat([df, nueva], ignore_index=True)
                    df.to_csv(BOOKINGS_PATH, index=False)
                    sincronizar_limpiezas_auto(df)
                    st.success("✅ Nueva reserva añadida")
                    st.experimental_rerun()

    with col2:
        if st.session_state.edit_id is not None and st.button("❌ Cancelar edición"):
            st.session_state.edit_id = None
            st.experimental_rerun()

# ---------- CHECK-IN / CHECK-OUT PRÓXIMOS ----------
st.subheader("📌 Llegadas y salidas en los próximos días")
hoy = datetime.date.today()
proximos = df[(df["Check-in"].dt.date <= hoy + datetime.timedelta(days=3)) & (df["Check-out"].dt.date >= hoy)]
st.table(proximos[["Propiedad", "Húsped", "Check-in", "Check-out"]].sort_values("Check-in"))

# ---------- VISTA LISTADA ----------
st.subheader("📂 Todas las Reservas (gestión rápida)")
for _, row in df.iterrows():
    row_index = row.name
    with st.expander(f"🏡 {row['Propiedad']} - 👤 {row['Húsped']}"):
        col1, col2, col3 = st.columns([3, 3, 1])
        with col1:
            st.markdown(f"**📃 Check-in:** {str(row['Check-in'])[:10]}")
            st.markdown(f"**🚪 Check-out:** {str(row['Check-out'])[:10]}")
        with col2:
            st.markdown(f"**📜 Notas:** {row.get('Notas', '')}")
        with col3:
            edit = st.button("✏️ Editar", key=f"edit_{row_index}")
            delete = st.button("🗑️ Borrar", key=f"delete_{row_index}")
            if edit:
                st.session_state.edit_id = row_index
                st.experimental_rerun()
            if delete:
                check_out = pd.to_datetime(row["Check-out"], errors="coerce")
                fecha_limpieza = (check_out + pd.Timedelta(days=1)).date() if pd.notnull(check_out) else None
                df.drop(index=row_index, inplace=True)
                df.reset_index(drop=True, inplace=True)
                df.to_csv(BOOKINGS_PATH, index=False)

                if os.path.exists(CLEANING_PATH) and fecha_limpieza:
                    df_clean = pd.read_csv(CLEANING_PATH)
                    df_clean = df_clean[
                        ~(
                            (pd.to_datetime(df_clean["Fecha"]).dt.date == fecha_limpieza) &
                            (df_clean["Propiedad"] == row["Propiedad"])
                        )
                    ]
                    df_clean.to_csv(CLEANING_PATH, index=False)

                st.success("🗑️ Reserva (y limpieza asociada) eliminadas")
                st.experimental_rerun()