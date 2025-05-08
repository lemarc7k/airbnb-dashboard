import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from firebase_config import db
from datetime import date
import streamlit.components.v1 as components
from firebase_config import db  # Asegúrate de tener tu config correctamente importada
from datetime import datetime as dt



# Config inicial
st.set_page_config(page_title="Real Estate | KM Ventures", layout="wide")
st.title("🏡 Real Estate Dashboard")
st.markdown("### Gestión profesional de tus propiedades Airbnb")


def obtener_datos():
    docs = db.collection("bookings").stream()
    data = [doc.to_dict() for doc in docs]
    df = pd.DataFrame(data)
    if not df.empty:
        df["Check-in"] = pd.to_datetime(df.get("Check-in"), errors="coerce")
        df["Check-out"] = pd.to_datetime(df.get("Check-out"), errors="coerce")
        df["Fecha"] = pd.to_datetime(df.get("Fecha"), errors="coerce")
        df["Precio"] = pd.to_numeric(df.get("Precio"), errors="coerce").fillna(0)
        df["Mes"] = df["Check-in"].dt.to_period("M").dt.to_timestamp()
    return df

hoy = pd.to_datetime(datetime.today())
df = obtener_datos()

# Tabs
tabs = st.tabs(["📊 General", "🏘️ Registrar Reservas", "📈 Evolución", "📝 Propiedades", "📋 Detalles"])

# ---------- GENERAL ---------- #
with tabs[0]:
    st.subheader("Resumen general")
    total = df["Precio"].sum()
    upcoming = df[df["Check-in"] > hoy]["Precio"].sum()
    ingreso_mes = df[df["Mes"] == hoy.to_period("M").to_timestamp()]["Precio"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Ingresado", f"${total:,.2f} AUD")
    col2.metric("📅 Ingresos Próximos", f"${upcoming:,.2f} AUD")
    col3.metric("📈 Este Mes", f"${ingreso_mes:,.2f} AUD")

    # Gráfico mensual de ingresos
    meses_fijos = pd.date_range(start="2025-01-01", end="2025-12-01", freq="MS")
    df_meses = pd.DataFrame({"Mes": meses_fijos})
    df_bar = df.groupby("Mes")["Precio"].sum().reset_index()
    df_bar = df_meses.merge(df_bar, on="Mes", how="left").fillna(0)
    df_bar["MesNombre"] = df_bar["Mes"].dt.strftime("%b")

    chart = alt.Chart(df_bar).mark_bar(
        color="#e60073",
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4
    ).encode(
        x=alt.X("MesNombre:N", title="Mes", sort=list(df_bar["MesNombre"])),
        y=alt.Y("Precio:Q", title="$ AUD"),
        tooltip=["MesNombre", "Precio"]
    ).properties(height=300)

    st.markdown("---")
    st.subheader("Evolución mensual de ingresos")
    st.altair_chart(chart, use_container_width=True)

# GRAFICO DE OCUPACION

# Convertir fechas y preparar datos
df["Check-in"] = pd.to_datetime(df["Check-in"], errors="coerce")
df["Check-out"] = pd.to_datetime(df["Check-out"], errors="coerce")
df_validas = df.dropna(subset=["Check-in", "Check-out"]).copy()
df_validas["Habitación"] = df_validas["Habitación"].fillna("Desconocida")

# Fechas del mes actual
hoy = pd.to_datetime(dt.today().date())
fecha_inicio = pd.to_datetime(datetime(hoy.year, hoy.month, 1))
fecha_fin = fecha_inicio + pd.offsets.MonthEnd(0)
dias_mes = pd.date_range(fecha_inicio, fecha_fin, freq='D')

# Habitaciones únicas
habitaciones = df_validas["Habitación"].unique()

# Dataset por día y habitación
data_ocupacion = []
for habitacion in habitaciones:
    reservas = df_validas[df_validas["Habitación"] == habitacion]
    for dia in dias_mes:
        estado = "Disponible"
        for _, row in reservas.iterrows():
            if row["Check-in"] <= dia <= row["Check-out"]:
                estado = "Futuro" if row["Check-in"].date() > hoy.date() else "Ocupado"
                break
        data_ocupacion.append({"Habitación": habitacion, "Día": dia, "Estado": estado})

df_ocupacion = pd.DataFrame(data_ocupacion)

# Porcentaje ocupación por habitación
ocupacion_stats = df_ocupacion.copy()
ocupacion_stats["Ocupado"] = ocupacion_stats["Estado"] == "Ocupado"
porcentaje_ocupacion = ocupacion_stats.groupby("Habitación")["Ocupado"].mean().reset_index()
porcentaje_ocupacion["Ocupado (%)"] = (porcentaje_ocupacion["Ocupado"] * 100).round(0).astype(int)
df_ocupacion = df_ocupacion.merge(porcentaje_ocupacion, on="Habitación")

# Colores personalizados
colores = alt.Scale(domain=["Ocupado", "Futuro", "Disponible"],
                    range=["#10b981", "#3b82f6", "#d1d5db"])

# Gráfico
st.subheader("Días ocupados/proyectados/disponibles (mes actual)")
chart = alt.Chart(df_ocupacion).mark_bar().encode(
    x=alt.X("Día:T", title="Días del mes"),
    y=alt.Y("Habitación:N", title="Habitación", sort="-x"),
    color=alt.Color("Estado:N", scale=colores, legend=alt.Legend(title="Estado")),
    tooltip=["Día:T", "Habitación:N", "Estado:N"]
).properties(height=400)

st.altair_chart(chart, use_container_width=True)

# === CALCULAR OCUPACIÓN REAL Y FUTURA ===
ocupacion_stats["EsOcupado"] = ocupacion_stats["Estado"] == "Ocupado"
ocupacion_stats["EsFuturo"] = ocupacion_stats["Estado"] == "Futuro"

# Total de días por habitación
dias_totales = ocupacion_stats.groupby("Habitación")["Estado"].count().reset_index(name="TotalDías")

# Sumar ocupación por tipo
ocupacion_resumen = ocupacion_stats.groupby("Habitación")[["EsOcupado", "EsFuturo"]].sum().reset_index()
ocupacion_resumen = ocupacion_resumen.merge(dias_totales, on="Habitación")
ocupacion_resumen["Disponible"] = ocupacion_resumen["TotalDías"] - ocupacion_resumen["EsOcupado"] - ocupacion_resumen["EsFuturo"]

# Calcular porcentajes
ocupacion_resumen["Ocupado (%)"] = (ocupacion_resumen["EsOcupado"] / ocupacion_resumen["TotalDías"] * 100).round(1)
ocupacion_resumen["Futuro (%)"] = (ocupacion_resumen["EsFuturo"] / ocupacion_resumen["TotalDías"] * 100).round(1)
ocupacion_resumen["Disponible (%)"] = 100 - ocupacion_resumen["Ocupado (%)"] - ocupacion_resumen["Futuro (%)"]
ocupacion_resumen["OcupadoFuturo (%)"] = ocupacion_resumen["Ocupado (%)"] + ocupacion_resumen["Futuro (%)"]

# Clasificación y recomendación
def clasificar_estado(p):
    if p < 50:
        return "🔴 Bajo", "📉 Lanzar promoción urgente"
    elif p < 70:
        return "🟡 Aceptable", "📊 Considera ajustar precio"
    else:
        return "🟢 Excelente", "✅ Mantén estrategia"

estado_info = ocupacion_resumen["OcupadoFuturo (%)"].apply(clasificar_estado)
ocupacion_resumen["Estado general"] = estado_info.apply(lambda x: x[0])
ocupacion_resumen["Recomendación"] = estado_info.apply(lambda x: x[1])

# === MÉTRICAS HORIZONTALES DISEÑADAS ===
st.markdown("### 📈 Ocupación por habitación (real + proyectada)")

st.markdown("<div style='display: flex; gap: 30px; flex-wrap: wrap;'>", unsafe_allow_html=True)

for _, row in ocupacion_resumen.iterrows():
    color = "#10b981" if "🟢" in row["Estado general"] else "#facc15" if "🟡" in row["Estado general"] else "#ef4444"
    st.markdown(f"""
    <div style='
        flex: 1;
        min-width: 250px;
        background-color: #1f2937;
        border-radius: 12px;
        padding: 16px 24px;
        color: white;
        box-shadow: 0 0 8px rgba(0,0,0,0.2);
    '>
        <div style='font-size: 18px; font-weight: bold; margin-bottom: 8px;'>{row['Habitación']}</div>
        <div style='font-size: 32px; font-weight: bold; color: {color};'>{row['OcupadoFuturo (%)']}%</div>
        <div style='margin-top: 6px; font-size: 15px;'>{row['Estado general']}</div>
        <div style='font-size: 13px; color: #cbd5e1; margin-top: 4px;'>{row['Recomendación']}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# === GRAFICO DE OCUPACIÓN APILADA ===
st.markdown("### 📊 Gráfico de ocupación real vs. futura")

df_long = ocupacion_resumen.melt(id_vars="Habitación",
                                  value_vars=["Ocupado (%)", "Futuro (%)"],
                                  var_name="Tipo", value_name="Porcentaje")

color_map = {
    "Ocupado (%)": "#10b981",  # verde
    "Futuro (%)": "#3b82f6"    # azul
}

chart = alt.Chart(df_long).mark_bar(size=30).encode(
    x=alt.X("Porcentaje:Q", stack="zero", title="Ocupación (%)", scale=alt.Scale(domain=[0, 100])),
    y=alt.Y("Habitación:N", sort="-x"),
    color=alt.Color("Tipo:N", scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())),
                    legend=alt.Legend(title="Tipo de ocupación")),
    tooltip=["Habitación", "Tipo", "Porcentaje"]
).properties(height=240)

st.altair_chart(chart, use_container_width=True)

# === TABLA DETALLADA ===
st.markdown("### 📋 Detalle completo por habitación")
df_tabla = ocupacion_resumen[[
    "Habitación", "EsOcupado", "EsFuturo", "Disponible", "TotalDías",
    "Ocupado (%)", "Futuro (%)", "OcupadoFuturo (%)", "Estado general", "Recomendación"
]]
df_tabla.columns = [
    "Habitación", "Noches Ocupadas", "Noches Futuras", "Disponibles", "Total Días",
    "% Ocupado", "% Futuro", "% Total", "Estado", "Recomendación"
]

try:
    tools.display_dataframe_to_user("Detalle de Ocupación", df_tabla)
except:
    st.dataframe(df_tabla, use_container_width=True)

# CALENDARIO DE DISPONIBILIDAD - HEATMAP
# === Preparar días del mes actual ===
hoy = pd.to_datetime(datetime.today().date())
fecha_inicio = pd.to_datetime(datetime(hoy.year, hoy.month, 1))
fecha_fin = fecha_inicio + pd.offsets.MonthEnd(0)
dias_mes = pd.date_range(fecha_inicio, fecha_fin, freq='D')

# === Calcular días sin reservas (asegúrate de tener df_ocupacion definido antes) ===
dias_vacios = df_ocupacion.groupby("Día")["Estado"].apply(lambda x: all(s == "Disponible" for s in x))
dias_vacios = dias_vacios[dias_vacios].index

# === Construir dataframe calendario ===
df_cal = pd.DataFrame({
    "Día": dias_mes,
    "Ocupado": [not d in dias_vacios for d in dias_mes],
    "Semana": [d.isocalendar()[1] for d in dias_mes],
    "Día_nombre": [d.strftime('%A') for d in dias_mes]
})

# Traducir estados a formato visual
df_cal["Estado"] = df_cal["Ocupado"].replace({True: "Ocupado", False: "Vacío"})

# === Mostrar heatmap ===
st.markdown("### 📅 Calendario de disponibilidad")
heatmap = alt.Chart(df_cal).mark_rect().encode(
    x=alt.X("Día_nombre:N", title="Día de la semana"),
    y=alt.Y("Semana:O", title="Semana del mes"),
    color=alt.Color("Estado:N",
        scale=alt.Scale(domain=["Ocupado", "Vacío"],
                        range=["#10b981", "#f87171"]),
        legend=alt.Legend(title="Estado")
    ),
    tooltip=[
        alt.Tooltip("Día:T", title="Fecha"),
        alt.Tooltip("Estado:N", title="Estado")
    ]
).properties(height=240)

st.altair_chart(heatmap, use_container_width=True)





# === RECOMENDACIÓN AI: Martes ===
martes = [d for d in dias_mes if d.weekday() == 1]
ocupacion_martes = df_ocupacion[df_ocupacion["Día"].isin(martes)]
ocupacion_baja = (ocupacion_martes["Estado"] == "Ocupado").mean()

st.markdown("### 🧠 Recomendación AI")

if ocupacion_baja < 0.4:
    st.markdown(f"""
    <div style="background-color:#f1f5f9; color:#111827; padding:15px; border-radius:12px;">
        <b>Baja el precio los martes</b> (ocupación: <span style='color:#ef4444;'>{ocupacion_baja*100:.0f}%</span>)<br>
        Considera promociones de mínimo 2 noches.
    </div>
    """, unsafe_allow_html=True)
elif ocupacion_baja < 0.6:
    st.markdown(f"""
    <div style="background-color:#f1f5f9; color:#111827; padding:15px; border-radius:12px;">
        <b>🧠 Considera descuento leve los martes</b> (ocupación moderada: {ocupacion_baja*100:.0f}%)
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="background-color:#f1f5f9; color:#111827; padding:15px; border-radius:12px;">
        ✅ Martes con buena ocupación, mantén tu estrategia actual.
    </div>
    """, unsafe_allow_html=True)

# === INSIGHT: Día con menor ocupación ===
ocupacion_por_dia = df_ocupacion.drop_duplicates(subset=["Día", "Habitación"]).copy()
ocupacion_por_dia["DíaSemana"] = ocupacion_por_dia["Día"].dt.day_name()
grupo_dia = ocupacion_por_dia.groupby("DíaSemana")["Estado"].apply(lambda x: (x == "Ocupado").mean())

# Ordenar días para visualización coherente (Lunes a Domingo)
orden_dias = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
grupo_dia = grupo_dia.reindex(orden_dias).dropna()

peor_dia = grupo_dia.idxmin()
porcentaje_peor = grupo_dia.min()

st.markdown(f"""
<div style="background-color:#fef9c3; color:#111827; padding:15px; border-radius:12px; margin-top:10px;">
    <b>📅 Día con menor demanda:</b> {peor_dia} ({porcentaje_peor:.0%})<br>
    Ideal para promociones o ajustes dinámicos.
</div>
""", unsafe_allow_html=True)

# === INSIGHT: Días consecutivos sin reservas ===
dias_disponibles = df_ocupacion[df_ocupacion["Estado"] == "Disponible"]["Día"].drop_duplicates().sort_values().reset_index(drop=True)

bloques = []
bloque = []

for i in range(len(dias_disponibles)):
    if i == 0 or (dias_disponibles[i] - dias_disponibles[i-1]).days == 1:
        bloque.append(dias_disponibles[i])
    else:
        if len(bloque) >= 3:
            bloques.append(bloque)
        bloque = [dias_disponibles[i]]
if len(bloque) >= 3:
    bloques.append(bloque)

if bloques:
    html_bloques = ""
    for bloque in bloques:
        inicio = bloque[0].strftime("%d %b")
        fin = bloque[-1].strftime("%d %b")
        html_bloques += f"<li>Del {inicio} al {fin} ({len(bloque)} días)</li>"

    st.markdown(f"""
    <div style="background-color:#fee2e2; color:#111827; padding:15px; border-radius:12px; margin-top:10px;">
        <b>📌 Días consecutivos sin reservas:</b>
        <ul style="margin-top:8px;">{html_bloques}</ul>
    </div>
    """, unsafe_allow_html=True)


# ---------- REGISTRAR RESERVA ---------- #
with tabs[1]:
    st.markdown("## 🧾 Registrar nueva reserva")

    with st.form("formulario_reserva"):
        st.markdown("### 🏠 Información Básica")
        col1, col2 = st.columns(2)
        with col1:
            propiedad = st.text_input("Propiedad")
            canal = st.selectbox("Canal de reserva", ["Airbnb", "Booking", "Instagram", "Whatsapp", "Otro"])
        with col2:
            habitacion = st.text_input("Habitación")
            estado = st.selectbox("Estado", ["Pagado", "Pendiente"])

        st.markdown("### 📅 Fechas de la Reserva")
        col1, col2 = st.columns(2)
        with col1:
            check_in = st.date_input("Check-in")
        with col2:
            noches = st.number_input("Número de noches", min_value=1, step=1)

        check_out = check_in + timedelta(days=int(noches))
        st.text_input("Check-out (calculado)", value=check_out.strftime("%Y-%m-%d"), disabled=True)

        st.markdown("### 💳 Información del Pago")
        col1, col2 = st.columns(2)
        with col1:
            precio_total = st.number_input("Precio total (AUD)", min_value=0.0, step=10.0)
            metodo_pago = st.selectbox("Método de pago", ["Transferencia", "Efectivo", "Airbnb", "Booking", "Otro"])
        with col2:
            limpieza = st.number_input("Precio limpieza (AUD)", min_value=0.0, step=5.0)
            precio_noche_calculado = round(precio_total / noches, 2) if noches else 0.0
            st.text_input("Precio por noche (calculado)", value=str(precio_noche_calculado), disabled=True)

        st.markdown("### 👤 Información del huésped")
        col1, col2 = st.columns(2)
        with col1:
            huesped = st.text_input("Nombre del huésped")
            personas = st.number_input("Número de huéspedes", min_value=1, step=1)
            ciudad = st.text_input("Ciudad de residencia")
        with col2:
            telefono = st.text_input("Teléfono")

            paises_populares = [
                "Alemania", "Argentina", "Arabia Saudita", "Australia", "Austria", "Bélgica", "Brasil", "Canadá",
                "Chile", "China", "Colombia", "Corea del Sur", "Ecuador", "Egipto", "Emiratos Árabes Unidos",
                "España", "Estados Unidos", "Filipinas", "Finlandia", "Francia", "Grecia", "Hong Kong", "India",
                "Indonesia", "Irlanda", "Israel", "Italia", "Japón", "Malasia", "Marruecos", "México", "Noruega",
                "Nueva Zelanda", "Países Bajos", "Perú", "Polonia", "Portugal", "Reino Unido", "Rumanía",
                "Singapur", "Sudáfrica", "Suecia", "Suiza", "Tailandia", "Taiwán", "Turquía", "Uruguay",
                "Venezuela", "Vietnam", "Otros"
            ]
            pais = st.selectbox("País de origen", sorted(paises_populares))

            sexo = st.selectbox("Sexo", ["Masculino", "Femenino", "Otro", "Prefiero no decir"])

        st.markdown("### 📝 Notas del anfitrión")
        notas = st.text_area("Notas adicionales")

        submit = st.form_submit_button("✅ Registrar")

    if submit:
        datos = {
            "Propiedad": propiedad,
            "Habitación": habitacion,
            "Canal": canal,
            "Estado": estado.lower(),
            "Check-in": str(check_in),
            "Check-out": str(check_out),
            "Noches": noches,
            "Precio": precio_total,
            "Limpieza": limpieza,
            "Precio_noche": precio_noche_calculado,
            "Metodo_pago": metodo_pago,
            "Huesped": huesped,
            "Huespedes": personas,
            "Telefono": telefono,
            "Pais": pais,
            "Ciudad": ciudad,
            "Sexo": sexo,
            "Notas": notas,
            "Fecha": datetime.now().isoformat()
        }
        db.collection("bookings").add(datos)
        st.success("✅ Reserva registrada correctamente.")




# ---------- PROPIEDADES ---------- #
with tabs[2]:
    st.subheader("Ranking de propiedades")
    if "Propiedad" in df.columns:
        ranking = df.groupby("Propiedad")["Precio"].sum().reset_index().sort_values("Precio", ascending=False)
        st.dataframe(ranking, use_container_width=True)
    else:
        st.warning("No hay datos de propiedades disponibles.")

# ---------- EVOLUCIÓN ---------- #
with tabs[3]:
    st.subheader("Evolución de ingresos")
    periodo = st.selectbox("Rango de tiempo", ["Últimos 7 días", "Último mes", "Últimos 6 meses", "Último año"])
    dias = {"Últimos 7 días": 7, "Último mes": 30, "Últimos 6 meses": 180, "Último año": 365}[periodo]
    df_evo = df[df["Check-in"] >= hoy - timedelta(days=dias)]
    df_evo = df_evo.groupby("Check-in")["Precio"].sum().reset_index()

    linea = alt.Chart(df_evo).mark_line(color="#00ffe1").encode(
        x="Check-in:T",
        y="Precio:Q"
    ).properties(height=300)
    st.altair_chart(linea, use_container_width=True)



# DETALLES
with tabs[4]:
    st.markdown("## 📋 Vista detallada de reservas")

    campos_esenciales = [
        "Check-in", "Check-out", "Propiedad", "Habitación",
        "Canal", "Precio", "Huesped"
    ]
    for campo in campos_esenciales:
        if campo not in df.columns:
            df[campo] = ""

    df_vista = df[campos_esenciales].copy()
    df_vista = df_vista.sort_values("Check-in", ascending=False)

    def formato_canal(canal):
        icono = {
            "Airbnb": "🌐",
            "Booking": "🏨",
            "Instagram": "📸",
            "Whatsapp": "💬",
            "Otro": "🔗"
        }.get(canal, "🔗")
        return f"{icono} {canal}"

    df_vista["Canal"] = df_vista["Canal"].apply(formato_canal)
    df_vista["Precio"] = df_vista["Precio"].apply(lambda x: f"${x:,.2f}")

    df_html = df_vista.to_html(escape=False, index=False)

    st.markdown("""
        <style>
        .responsive-table {
            overflow-x: auto;
            margin-top: 10px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            font-size: 13px;
            min-width: 750px;
            border-radius: 8px;
        }
        th {
            background-color: #f4f4f4;
            color: #333;
            padding: 8px;
            text-align: left;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }
        td {
            padding: 8px;
            border-bottom: 1px solid #ddd;
            vertical-align: top;
        }
        tr:hover {
            background-color: #f9f9f9;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<div class='responsive-table'>{df_html}</div>", unsafe_allow_html=True)

    # ---------- CALENDARIO ----------
    st.markdown("## 📅 Calendario de reservas")

    # Gestión de modo oscuro con estado persistente y actualización visual forzada
    if "modo_oscuro" not in st.session_state:
        st.session_state.modo_oscuro = True

    nuevo_modo = st.sidebar.toggle("🌗 Modo oscuro", value=st.session_state.modo_oscuro)

    if nuevo_modo != st.session_state.modo_oscuro:
        st.session_state.modo_oscuro = nuevo_modo
        st.experimental_rerun()

    modo_oscuro = st.session_state.modo_oscuro
    vista = st.radio("🗓️ Vista del calendario", ["Mes", "Semana"], horizontal=True)

    hoy = date.today()
    eventos = []
    for _, row in df.iterrows():
        if pd.notnull(row["Check-in"]) and pd.notnull(row["Check-out"]):
            checkin = pd.to_datetime(row["Check-in"])
            checkout = pd.to_datetime(row["Check-out"])
            color = "#10b981"  # verde

            if checkout.date() < hoy:
                color = "#a3a3a3"
            elif checkin.date() <= hoy <= checkout.date():
                color = "#3b82f6"

            tooltip = f"{row.get('Huesped', '').title()}\n{row.get('Propiedad', '')}\nCheck-in: {checkin.date()}\nCheck-out: {checkout.date()}\nPrecio: ${row.get('Precio', 0)}"

            eventos.append({
                "title": f"{row.get('Huesped', '').upper()} | {row.get('Propiedad', '')} | ${row.get('Precio', 0)}",
                "start": checkin.strftime("%Y-%m-%d"),
                "end": (checkout + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                "color": color,
                "extendedProps": {"tooltip": tooltip}
            })

    fc_view = "dayGridMonth" if vista == "Mes" else "timeGridWeek"
    bg_color = "#0f1115" if modo_oscuro else "white"
    text_color = "white" if modo_oscuro else "black"
    border_color = "#444" if modo_oscuro else "#ccc"

    calendar_html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <link href='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css' rel='stylesheet' />
        <script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js'></script>
        <style>
            body {{
                background-color: {bg_color};
                color: {text_color};
            }}
            #calendar {{
                background-color: {bg_color};
                color: {text_color};
            }}
            .fc-daygrid-day, .fc-scrollgrid-sync-table {{
                background-color: {bg_color};
                color: {text_color};
            }}
            .fc td, .fc th {{
                border-color: {border_color};
            }}
        </style>
        <script>
          document.addEventListener('DOMContentLoaded', function() {{
            var calendarEl = document.getElementById('calendar');
            var calendar = new FullCalendar.Calendar(calendarEl, {{
              initialView: '{fc_view}',
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
                info.el.style.borderRadius = '6px';
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

    components.html(calendar_html, height=750, scrolling=True)

    # Leyenda
    st.markdown("""
    <div style='margin-top: 20px;'>
      <strong>🎨 Leyenda de colores:</strong>
      <ul style='list-style: none; padding-left: 0; font-size: 14px;'>
        <li><span style='display:inline-block; width:16px; height:16px; background-color:#10b981; margin-right:8px; border-radius:4px;'></span>Reserva futura</li>
        <li><span style='display:inline-block; width:16px; height:16px; background-color:#3b82f6; margin-right:8px; border-radius:4px;'></span>Reserva activa</li>
        <li><span style='display:inline-block; width:16px; height:16px; background-color:#a3a3a3; margin-right:8px; border-radius:4px;'></span>Reserva pasada</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)



