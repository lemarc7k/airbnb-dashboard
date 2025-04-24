import streamlit as st
import pandas as pd
import datetime
import streamlit.components.v1 as components
from firebase_config import db

st.set_page_config(layout="wide")
st.title("📅 Calendario de Reservas")

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

# Filtros en el sidebar
st.sidebar.header("🔍 Filtros")
if not df.empty and "Propiedad" in df.columns:
    propiedades = ["Todas"] + sorted(df["Propiedad"].dropna().unique())
else:
    propiedades = ["Todas"]

propiedad_filtrada = st.sidebar.selectbox("Filtrar por propiedad", propiedades)

# Filtrar por propiedad
df_filtrado = df.copy()
if propiedad_filtrada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Propiedad"] == propiedad_filtrada]

# Crear eventos
eventos = []
for _, row in df_filtrado.iterrows():
    if pd.notnull(row["Check-in"]) and pd.notnull(row["Check-out"]):
        eventos.append({
            "title": f"{row.get('Huesped', '').upper()} | {row.get('Propiedad', '')} | ${row.get('Precio', 0)}",
            "start": row["Check-in"].strftime("%Y-%m-%d"),
            "end": (row["Check-out"] + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            "color": "#60a5fa"  # azul bonito
        })

# Generar HTML del calendario
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
          height: 650,
          locale: 'es',
          headerToolbar: {{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek'
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

# Incrustar componente
components.html(calendar_html, height=700, scrolling=True) 

# Enlace a registro
st.markdown("[➕ Registrar nueva reserva](?page=6_Registrar_Reserva)")
