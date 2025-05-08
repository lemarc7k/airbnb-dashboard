# Este es un esquema base con las 5 mejoras integradas paso a paso.
# Comenzamos por integrar el punto 1: tooltips con detalles al hacer hover
# Continuamos con filtros combinados (punto 2), KPIs (punto 3), dark/light mode (4) y vista semanal dinámica (5)

import streamlit as st
import pandas as pd
import datetime
import streamlit.components.v1 as components
from firebase_config import db


# Dark mode/light mode
modo_oscuro = st.sidebar.toggle("🌗 Modo oscuro", value=True)
color_fondo = "#0f1115" if modo_oscuro else "white"
color_texto = "white" if modo_oscuro else "black"

st.markdown(f"""
    <style>
        body {{
            background-color: {color_fondo};
            color: {color_texto};
        }}
        .fc-event-title, .fc-event-time {{
            font-size: 13px !important;
        }}
    </style>
""", unsafe_allow_html=True)

st.success("✅ Página cargada correctamente")
st.title("📅 Calendario de Reservas")

# Cargar reservas de Firestore
@st.cache_data
def cargar_reservas():
    docs = db.collection("bookings").stream()
    data = []
    for doc in docs:
        d = doc.to_dict()
        if "Check-in" in d and "Check-out" in d:
            d["Check-in"] = pd.to_datetime(d["Check-in"], errors="coerce")
            d["Check-out"] = pd.to_datetime(d["Check-out"], errors="coerce")
            data.append(d)
    df = pd.DataFrame(data)
    return df

df = cargar_reservas()
hoy = datetime.date.today()

# Filtros
st.sidebar.header("🔍 Filtros")
propiedades = ["Todas"] + sorted(df["Propiedad"].dropna().unique()) if not df.empty else ["Todas"]
estados = ["Todos", "Pasadas", "Activas", "Futuras"]
propiedad_sel = st.sidebar.selectbox("Propiedad", propiedades)
estado_sel = st.sidebar.selectbox("Estado", estados)

# Aplicar filtros
df_filtrado = df.copy()
if propiedad_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Propiedad"] == propiedad_sel]

if estado_sel != "Todos":
    df_filtrado["Check-out"] = pd.to_datetime(df_filtrado["Check-out"], errors="coerce")
    df_filtrado["Check-in"] = pd.to_datetime(df_filtrado["Check-in"], errors="coerce")
    hoy_ts = pd.to_datetime(hoy)
    if estado_sel == "Pasadas":
        df_filtrado = df_filtrado[df_filtrado["Check-out"] < hoy_ts]
    elif estado_sel == "Activas":
        df_filtrado = df_filtrado[(df_filtrado["Check-in"] <= hoy_ts) & (df_filtrado["Check-out"] >= hoy_ts)]
    elif estado_sel == "Futuras":
        df_filtrado = df_filtrado[df_filtrado["Check-in"] > hoy_ts]

# KPI's
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("🔢 Total Reservas", len(df_filtrado))
with col2:
    st.metric("💵 Ingresos Estimados", f"${df_filtrado['Precio'].sum():,.2f}")
with col3:
    noches = (df_filtrado["Check-out"] - df_filtrado["Check-in"]).dt.days.sum()
    st.metric("🛌 Noches Ocupadas", int(noches))

# Eventos para FullCalendar con tooltip (punto 1)
eventos = []
for _, row in df_filtrado.iterrows():
    if pd.notnull(row["Check-in"]) and pd.notnull(row["Check-out"]):
        estado = "futura"
        if row["Check-out"].date() < hoy:
            color = "#a3a3a3"  # gris
        elif row["Check-in"].date() <= hoy <= row["Check-out"].date():
            color = "#3b82f6"  # azul
        else:
            color = "#10b981"  # verde

        tooltip = f"{row.get('Huesped', '').title()}\n{row.get('Propiedad', '')}\nCheck-in: {row['Check-in'].date()}\nCheck-out: {row['Check-out'].date()}\nPrecio: ${row.get('Precio', 0)}"

        eventos.append({
            "title": f"{row.get('Huesped', '').upper()} | {row.get('Propiedad', '')} | ${row.get('Precio', 0)}",
            "start": row["Check-in"].strftime("%Y-%m-%d"),
            "end": (row["Check-out"] + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            "color": color,
            "extendedProps": {"tooltip": tooltip}
        })

# HTML para calendario FullCalendar con vista semanal (punto 5)
calendar_html = f"""
<!DOCTYPE html>
<html>
  <head>
    <link href='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css' rel='stylesheet' />
    <script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js'></script>
    <script>
      document.addEventListener('DOMContentLoaded', function() {{
        var calendarEl = document.getElementById('calendar');
        var calendar = new FullCalendar.Calendar(calendarEl, {{
          initialView: 'dayGridMonth',
          height: 700,
          locale: 'es',
          headerToolbar: {{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek'
          }},
          eventDidMount: function(info) {{
            if (info.event.extendedProps.tooltip) {{
              info.el.setAttribute("title", info.event.extendedProps.tooltip);
            }}
          }},
          events: {eventos}
        }});
        calendar.render();
      }});
    </script>
  </head>
  <body>
    <div id='calendar'></div>
  </body>
</html>
"""

# Renderizar
components.html(calendar_html, height=750, scrolling=True)


