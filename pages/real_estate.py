# ------------------- IMPORTS -------------------
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import sys
import os
import pandas as pd
import datetime
import altair as alt
import streamlit.components.v1 as components
from firebase_config import db



st.set_page_config(page_title="Real Estate | KM Ventures", layout="wide")


if "real_estate_page" not in st.session_state:
    st.session_state.real_estate_page = "home"

def go_to(page):
    st.session_state.real_estate_page = page

# ------------------- FUNCIONES GENERALES -------------------
def obtener_datos_bookings():
    bookings_ref = db.collection("bookings")
    docs = bookings_ref.stream()
    data = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        data.append(d)
    df = pd.DataFrame(data)
    if not df.empty:
        df["Check-in"] = pd.to_datetime(df.get("Check-in"), errors="coerce")
        df["Mes"] = df["Check-in"].dt.to_period("M").dt.to_timestamp()
        df["Check-out"] = pd.to_datetime(df.get("Check-out"), errors="coerce")
        df["Fecha"] = pd.to_datetime(df.get("Fecha"), errors="coerce")
        df["Precio"] = pd.to_numeric(df.get("Precio"), errors="coerce").fillna(0)
        df["Huespedes"] = pd.to_numeric(df.get("Huespedes"), errors="coerce").fillna(0).astype(int)
        df["Noches"] = pd.to_numeric(df.get("Noches"), errors="coerce").fillna(0).astype(int)
    return df

# ------------------- CARGA INICIAL -------------------
df = obtener_datos_bookings()
hoy = datetime.date.today()
anio_actual = hoy.year
mes_actual = pd.to_datetime(hoy).to_period("M").to_timestamp()
meses_completos = pd.date_range(start=f"{anio_actual}-01-01", end=f"{anio_actual}-12-01", freq="MS")
df_meses = pd.DataFrame({"Mes": meses_completos})

# ------------------- CSS -------------------
st.markdown("""
<style>
/* -------- CONFIGURACIÓN GLOBAL -------- */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background-color: #0f1115;
    color: white;
    font-size: 16px;
}

/* -------- NAVBAR -------- */
.navbar {
    display: flex;
    justify-content: center;
    gap: 50px;
    padding: 20px 0;
    background-color: #1a1a1d;
    border-bottom: 1px solid #333;
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 999;
}
.navbar-item {
    color: white;
    text-decoration: none;
    position: relative;
    padding: 8px 12px;
    cursor: pointer;
    transition: color 0.3s ease;
}
.navbar-item:hover {
    color: #00ffe1;
}

/* -------- TÍTULOS -------- */
.header-title {
    font-size: 48px;
    font-weight: 800;
    text-align: center;
    margin-top: 50px;
    margin-bottom: 10px;
    color: #00ffe1;
    text-shadow: 0 0 10px #00ffe1;
}
.subtitle {
    text-align: center;
    font-size: 18px;
    color: #aaa;
    margin-bottom: 50px;
}

/* -------- SEPARADOR (LASER LINE) -------- */
.laser-line {
    width: 100%;
    height: 5px;
    background: linear-gradient(to right, #00ffe1, transparent, #00ffe1);
    margin: 50px 0;
    border-radius: 10px;
    animation: pulse 2s infinite ease-in-out;
}
@keyframes pulse {
    0% {opacity: 0.4;}
    50% {opacity: 1;}
    100% {opacity: 0.4;}
}

/* -------- KPIs PRINCIPALES -------- */
.big-title {
    font-size: 36px;
    font-weight: 600;
    margin-bottom: 10px;
}
.big-number {
    font-size: 48px;
    font-weight: bold;
    color: #e60073;
    margin-bottom: 10px;
}
.upcoming {
    color: grey;
    font-size: 16px;
    margin-bottom: 30px;
}

/* -------- RESUMEN ANUAL -------- */
.box-summary {
    background-color: #ffffff;
    color: #1a1a1d;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 20px;
    font-size: 14px;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.1);
}

/* -------- KPI CARDS -------- */
.kpi-card {
    background-color: #f9f9f9;
    color: #1a1a1d;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    margin-bottom: 20px;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.15);
    transition: background-color 0.3s, color 0.3s;
}
.kpi-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 10px;
}
.kpi-value {
    font-size: 28px;
    font-weight: bold;
    color: black;
}

/* -------- FOOTER -------- */
.footer {
    text-align: center;
    margin-top: 60px;
    font-size: 12px;
    color: #666;
}

/* -------- RESPONSIVE (Móvil) -------- */
@media screen and (max-width: 768px) {
    .navbar {
        flex-direction: column;
        gap: 10px;
    }
    .header-title {
        font-size: 36px;
    }
    .big-number {
        font-size: 36px;
    }
    .kpi-value {
        font-size: 22px;
    }
}

/* -------- MODO LIGHT/DARK DETECCIÓN -------- */
@media (prefers-color-scheme: light) {
    html, body, [class*="css"] {
        background-color: #f7f7f7;
        color: #1a1a1d;
    }
    .navbar {
        background-color: #ffffff;
        border-bottom: 1px solid #ccc;
    }
    .navbar-item {
        color: #333;
    }
    .navbar-item:hover {
        color: #00c4b3;
    }
    .header-title {
        color: #00c4b3;
        text-shadow: none;
    }
    .subtitle {
        color: #666;
    }
    .box-summary {
        background-color: #ffffff;
        color: #1a1a1d;
    }
    .kpi-card {
        background-color: #ffffff;
        color: #1a1a1d;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.05);
    }
    .kpi-title {
        color: #555;
    }
    .kpi-value {
        color: #222;
    }
    .footer {
        color: #999;
    }
}
</style>
""", unsafe_allow_html=True)


# ------------------- NUEVO NAVBAR DE NAVEGACIÓN -------------------

st.markdown("""
    <style>
    .custom-navbar {
        display: flex;
        justify-content: center;
        gap: 50px;
        padding: 20px 0;
        background-color: #f7f7f7;
        border-bottom: 1px solid #ccc;
        font-weight: 600;
        font-size: 18px;
    }
    .nav-item {
        cursor: pointer;
        transition: all 0.3s;
        padding: 8px 15px;
        border-radius: 10px;
        color: #1a1a1d;
    }
    .nav-item:hover {
        background-color: #00c4b3;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="custom-navbar">', unsafe_allow_html=True)

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    if st.button("Registrar Reserva", key="nav_registrar"):
        switch_page("Registrar_Reserva")

with col2:
    if st.button("Calendario", key="nav_calendario"):
        switch_page("Calendar")

with col3:
    if st.button("Gastos", key="nav_gastos"):
        switch_page("Add_Gastos_Firestore")

with col4:
    if st.button("Inventario", key="nav_inventario"):
        switch_page("Inventory")

with col5:
    if st.button("Incidencias", key="nav_incidencias"):
        switch_page("Incidents")

with col6:
    if st.button("Reportes", key="nav_reportes"):
        switch_page("Reports")

st.markdown('</div>', unsafe_allow_html=True)


# ------------------- HOME PAGE -------------------
if st.session_state.real_estate_page == "home":
    st.markdown("<div class='header-title'>Real Estate</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Herramientas especializadas para la gestión y análisis de propiedades.</div>", unsafe_allow_html=True)

    try:
        st.write("✅ Página cargada correctamente")
    except Exception as e:
        st.error(f"❌ Error cargando página: {e}")

    st.markdown("## Earnings")

    ingresos_mes = df[df["Mes"] == mes_actual]["Precio"].sum()
    upcoming = df[df["Check-in"] > pd.to_datetime(hoy)]["Precio"].sum()

    ingresos_por_mes = df.groupby("Mes")["Precio"].sum().reset_index()
    ingresos_por_mes = df_meses.merge(ingresos_por_mes, on="Mes", how="left").fillna(0)
    ingresos_por_mes["Mes"] = ingresos_por_mes["Mes"].dt.strftime("%b")

    col_main, col_side = st.columns([3, 1])

    with col_main:
        st.markdown(f"<div class='big-title'>You’ve made</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-number'>${ingresos_mes:,.2f} AUD</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='upcoming'>Upcoming ${upcoming:,.2f} AUD</div>", unsafe_allow_html=True)

        chart = alt.Chart(ingresos_por_mes).mark_bar(
            cornerRadiusTopLeft=8,
            cornerRadiusTopRight=8,
            color="#e60073"
        ).encode(
            x=alt.X("Mes", sort=list(ingresos_por_mes["Mes"])),
            y=alt.Y("Precio", title="$ AUD"),
            tooltip=["Mes", "Precio"]
        ).properties(height=300)

        st.altair_chart(chart, use_container_width=True)

    with col_side:
        total = df["Precio"].sum()
        fee = total * 0.03
        neto = total - fee
        st.markdown(f"""
        <div class='box-summary'>
            <h4>Year-to-date summary</h4>
            <p style='margin-bottom: 5px;'>1 Jan – {hoy:%d %b %Y}</p>
            <p><strong>Gross earnings</strong><br/>${total:,.2f} AUD</p>
            <p><strong>Airbnb service fee (3%)</strong><br/>-${fee:,.2f} AUD</p>
            <p><strong>Tax withheld</strong><br/>$0.00 AUD</p>
            <hr/>
            <p><strong>Total (AUD)</strong><br/><b>${neto:,.2f} AUD</b></p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='margin-top:30px;'>", unsafe_allow_html=True)

# ---------- KPIs de Real Estate mejorados (sin iconos, diseño profesional) ---------- #
if not df.empty:
    st.markdown("---")
    st.subheader("KPIs de Real Estate")

    # KPIs de precios medios
    precio_medio_noche = df["Precio"].sum() / df["Noches"].sum() if df["Noches"].sum() != 0 else 0
    precio_medio_semana = precio_medio_noche * 7
    precio_medio_mes = precio_medio_noche * 30

    # KPIs de ingresos
    ingreso_total_semana = df[df["Check-in"] >= pd.to_datetime(hoy) - pd.Timedelta(weeks=1)]["Precio"].sum()
    ingreso_total_mes = df[df["Check-in"] >= pd.to_datetime(hoy) - pd.DateOffset(months=1)]["Precio"].sum()
    ingreso_total_6m = df[df["Check-in"] >= pd.to_datetime(hoy) - pd.DateOffset(months=6)]["Precio"].sum()
    ingreso_total_anual = df[df["Check-in"] >= pd.to_datetime(hoy) - pd.DateOffset(years=1)]["Precio"].sum()

    # Organización visual de KPIs
    st.markdown("<div style='display: flex; flex-wrap: wrap; justify-content: space-between;'>", unsafe_allow_html=True)

    def kpi_card(title, value):
        st.markdown(f"""
        <div style='flex: 1; min-width: 250px; background-color: #ffffff10; margin: 10px; padding: 20px; border-radius: 12px; text-align: center;'>
            <h5 style='color: #00ffe1; margin-bottom: 8px;'>{title}</h5>
            <h2 style='color: white; font-weight: bold;'>${value:,.2f} AUD</h2>
        </div>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        kpi_card("Precio medio por noche", precio_medio_noche)
    with col2:
        kpi_card("Precio medio por semana", precio_medio_semana)
    with col3:
        kpi_card("Precio medio por mes", precio_medio_mes)

    col4, col5, col6, col7 = st.columns(4)
    with col4:
        kpi_card("Ingreso última semana", ingreso_total_semana)
    with col5:
        kpi_card("Ingreso último mes", ingreso_total_mes)
    with col6:
        kpi_card("Ingreso últimos 6 meses", ingreso_total_6m)
    with col7:
        kpi_card("Ingreso último año", ingreso_total_anual)

    st.markdown("</div>", unsafe_allow_html=True)


# ----------- GRÁFICO ULTRA PREMIUM DE INGRESOS ----------- #
st.markdown("---")
st.subheader("📈 Evolución de Ingresos")

periodo = st.radio("Selecciona el rango de tiempo:", ["Últimos 7 días", "Último mes", "Últimos 6 meses", "Último año"], horizontal=True)

if periodo == "Últimos 7 días":
    df_filtrado = df[df["Check-in"] >= pd.to_datetime(hoy) - pd.Timedelta(days=7)]
    agrupacion = "D"  # Día
elif periodo == "Último mes":
    df_filtrado = df[df["Check-in"] >= pd.to_datetime(hoy) - pd.DateOffset(months=1)]
    agrupacion = "D"  # Día
elif periodo == "Últimos 6 meses":
    df_filtrado = df[df["Check-in"] >= pd.to_datetime(hoy) - pd.DateOffset(months=6)]
    agrupacion = "W"  # Semana
elif periodo == "Último año":
    df_filtrado = df[df["Check-in"] >= pd.to_datetime(hoy) - pd.DateOffset(years=1)]
    agrupacion = "M"  # Mes

# Agrupar por el periodo seleccionado
if not df_filtrado.empty:
    df_grafico = df_filtrado.groupby(df_filtrado["Check-in"].dt.to_period(agrupacion)).agg({"Precio": "sum"}).reset_index()
    df_grafico["Check-in"] = df_grafico["Check-in"].dt.start_time

    base = alt.Chart(df_grafico).encode(
        x=alt.X('Check-in:T', title='Fecha'),
        y=alt.Y('Precio:Q', title='Ingresos ($ AUD)')
    )

    linea = base.mark_line(
        interpolate='monotone',
        color="#00ffe1",
        strokeWidth=3
    )

    puntos = base.mark_circle(
        color="#00ffe1",
        size=70
    ).encode(
        tooltip=[
            alt.Tooltip('Check-in:T', title='Fecha'),
            alt.Tooltip('Precio:Q', title='Ingresos ($ AUD)')
        ]
    )

    chart = (linea + puntos).interactive(bind_y=False).properties(height=400)

    st.altair_chart(chart, use_container_width=True)
else:
    st.warning("No hay datos suficientes para este periodo.")


        

# ----------- BOTONES DE NAVEGACIÓN ----------- #
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📘 Registrar Reserva"):
        go_to("registrar")
        st.rerun()
    if st.button("📦 Inventario"):
        go_to("inventory")
        st.rerun()

with col2:
    if st.button("📅 Calendario"):
        go_to("calendar")
        st.rerun()
    if st.button("📒 Gastos"):
        go_to("gastos")
        st.rerun()

with col3:
    if st.button("⚠️ Incidencias"):
        go_to("incidents")
        st.rerun()
    if st.button("📋 Reportes"):
        go_to("reports")
        st.rerun()

st.markdown("<div class='laser-line'></div>", unsafe_allow_html=True)
st.markdown("<div class='footer'>KM Ventures Real Estate Unit ©2025</div>", unsafe_allow_html=True)


# ----------- RESUMEN AUTOMÁTICO DE CRECIMIENTO ----------- #
st.markdown('---')
st.subheader("📢 Resumen de crecimiento mensual")

try:
    mes_pasado = (pd.to_datetime(hoy) - pd.DateOffset(months=1)).to_period("M").to_timestamp()
    ingreso_mes_pasado = df[df["Mes"] == mes_pasado]["Precio"].sum()

    if ingreso_mes_pasado > 0:
        variacion = ((ingresos_mes - ingreso_mes_pasado) / ingreso_mes_pasado) * 100
        variacion = round(variacion, 2)

        if variacion > 0:
            st.success(f"📈 ¡Tus ingresos aumentaron un {variacion}% respecto al mes pasado!")
        elif variacion < 0:
            st.error(f"📉 Tus ingresos cayeron un {abs(variacion)}% respecto al mes pasado. ¡Hora de analizar oportunidades!")
        else:
            st.info("➖ Tus ingresos se mantuvieron estables respecto al mes pasado.")
    else:
        st.info("ℹ️ No hay datos de ingresos del mes pasado para comparar.")
except Exception as e:
    st.warning(f"⚠️ No se pudo calcular el resumen de crecimiento: {e}")


    # ----------- LASER LINE + FOOTER ----------- #
    st.markdown("<div class='laser-line'></div>", unsafe_allow_html=True)

    st.markdown("<div class='footer'>KM Ventures Real Estate Unit ©2025</div>", unsafe_allow_html=True)



# ------------------- SUBPÁGINAS -------------------
if st.session_state.real_estate_page == "registrar":
    if st.button("⬅️ Volver a Real Estate Home"):
        go_to("home")
        st.rerun()
    exec(open("pages/modules/Registrar_Reserva.py", encoding="utf-8").read())

elif st.session_state.real_estate_page == "inventory":
    if st.button("⬅️ Volver a Real Estate Home"):
        go_to("home")
        st.rerun()
    exec(open("pages/modules/Inventory.py", encoding="utf-8").read())

elif st.session_state.real_estate_page == "calendar":
    if st.button("⬅️ Volver a Real Estate Home"):
        go_to("home")
        st.rerun()
    exec(open("pages/modules/Calendar Redesign.py", encoding="utf-8").read())

elif st.session_state.real_estate_page == "gastos":
    if st.button("⬅️ Volver a Real Estate Home"):
        go_to("home")
        st.rerun()
    exec(open("pages/modules/Add_Gastos_Firestore.py", encoding="utf-8").read())

elif st.session_state.real_estate_page == "incidents":
    if st.button("⬅️ Volver a Real Estate Home"):
        go_to("home")
        st.rerun()
    exec(open("pages/modules/Incidents.py", encoding="utf-8").read())

elif st.session_state.real_estate_page == "reports":
    if st.button("⬅️ Volver a Real Estate Home"):
        go_to("home")
        st.rerun()
    exec(open("pages/modules/Reports.py", encoding="utf-8").read())
