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


#.-------------STYLE CSS--------------

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

/* -------- KPIs -------- */
.kpi-card {
    background-color: #ffffff;
    color: #1a1a1d;
    border-radius: 12px;
    padding: 8px 14px;
    margin: 10px 0;
    text-align: center;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.06);
    transition: all 0.3s ease;
}
.kpi-card .kpi-title {
    font-size: 14px;
    font-weight: 600;
    color: #666;
    margin-bottom: 5px;
}
.kpi-card .kpi-value {
    font-size: 18px;
    font-weight: bold;
    color: #111;
}

/* -------- FOOTER -------- */
.footer {
    text-align: center;
    margin-top: 60px;
    font-size: 12px;
    color: #666;
}

/* -------- RESPONSIVE MÓVIL & TABLET -------- */
@media screen and (max-width: 768px) {
    .navbar {
        flex-direction: column;
        gap: 10px;
    }
    .header-title {
        font-size: 32px;
    }
    .big-number {
        font-size: 32px;
    }
    .kpi-card {
        margin: 8px 0;
        padding: 10px 8px;
    }
    .kpi-card .kpi-title {
        font-size: 13px;
    }
    .kpi-card .kpi-value {
        font-size: 20px;
    }
}

/* -------- ESCRITORIO (más compacto) -------- */
@media screen and (min-width: 1024px) {
    .kpi-card {
        padding: 8px 14px;
        margin: 10px 0;
    }
    .kpi-card .kpi-title {
        font-size: 13px;
    }
    .kpi-card .kpi-value {
        font-size: 17px;
    }
    .block-container {
        padding: 2rem 4rem !important;
    }
    h3, h4 {
        margin-top: 30px;
    }
}

/* -------- LIGHT MODE -------- */
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
    .kpi-card {
        background-color: #ffffff;
        color: #1a1a1d;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
    }
    .kpi-card .kpi-title {
        color: #555;
    }
    .kpi-card .kpi-value {
        color: #222;
    }
    .footer {
        color: #999;
    }
}

/* -------- MENÚ SUPERIOR CUSTOM -------- */
.custom-navbar {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 18px;
    padding: 20px 15px;
    background: rgba(243, 244, 246, 0.88);
    border-radius: 12px;
    margin-bottom: 40px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    transition: background 0.3s ease;
}
.nav-link {
    font-family: 'Segoe UI', sans-serif;
    font-weight: 600;
    font-size: 15px;
    padding: 8px 18px;
    border-radius: 10px;
    background: linear-gradient(135deg, #00c4b3, #00ffe1);
    color: white !important;
    text-decoration: none;
    white-space: nowrap;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);
    transition: all 0.3s ease;
}
.nav-link:hover {
    background: linear-gradient(135deg, #009e8d, #00c4b3);
    transform: scale(1.05);
}
@media screen and (max-width: 768px) {
    .custom-navbar {
        flex-direction: column;
        align-items: center;
        gap: 10px;
    }
    .nav-link {
        font-size: 15px;
        padding: 12px 20px;
        width: 100%;
        max-width: 320px;
        text-align: center;
    }
}
</style>
""", unsafe_allow_html=True)






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

# ----------- RESUMEN EJECUTIVO ----------- #
st.markdown("### 📊 Resumen Ejecutivo")

# 1. Ingresos por mes actual y anterior
mes_actual = hoy.strftime("%Y-%m")
mes_anterior = (hoy - pd.DateOffset(months=1)).strftime("%Y-%m")

df["Mes"] = df["Check-in"].dt.strftime("%Y-%m")
ingreso_actual = df[df["Mes"] == mes_actual]["Precio"].sum()
ingreso_anterior = df[df["Mes"] == mes_anterior]["Precio"].sum()

variacion = ((ingreso_actual - ingreso_anterior) / ingreso_anterior * 100) if ingreso_anterior != 0 else 0

# 2. Habitación más rentable en los últimos 6 meses
df_ultimos_6m = df[df["Check-in"] >= hoy - pd.DateOffset(months=6)]
habitacion_rentable = (
    df_ultimos_6m.groupby("Habitación")["Precio"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

if not habitacion_rentable.empty:
    habitacion_top = habitacion_rentable.iloc[0]["Habitación"]
    ingreso_top = habitacion_rentable.iloc[0]["Precio"]
else:
    habitacion_top = "N/A"
    ingreso_top = 0

# Visualización
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-title'>Ingreso Mes Actual</div>
        <div class='kpi-value'>${ingreso_actual:,.2f} AUD</div>
    </div>
    <div class='kpi-card'>
        <div class='kpi-title'>Ingreso Mes Anterior</div>
        <div class='kpi-value'>${ingreso_anterior:,.2f} AUD</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-title'>Variación Mensual</div>
        <div class='kpi-value'>{variacion:.2f}%</div>
    </div>
    <div class='kpi-card'>
        <div class='kpi-title'>Habitación más rentable</div>
        <div class='kpi-value'>{habitacion_top}: ${ingreso_top:,.2f} AUD</div>
    </div>
    """, unsafe_allow_html=True)


# ----------- KPIs FINANCIEROS CON VISUALIZACIÓN Y DISEÑO RESPONSIVO ----------- #

st.subheader("KPIs Financieros")

# ---------- CONFIGURACIÓN GENERAL ---------- #
hoy = pd.to_datetime(datetime.date.today())
df["Check-in"] = pd.to_datetime(df["Check-in"], errors="coerce")
df["Precio"] = pd.to_numeric(df["Precio"], errors="coerce").fillna(0)
df["Habitación"] = df.get("Habitación", "Desconocida")

# ---------- LAYOUT ---------- #
col_izq, col_der = st.columns([1.3, 1])

# ---------- BLOQUE IZQUIERDO (DETALLES) ---------- #
with col_izq:
    st.markdown("### Ingresos Totales")
    ingresos_totales = {
        "Semana": df[df["Check-in"] >= hoy - pd.Timedelta(days=7)]["Precio"].sum(),
        "Mes": df[df["Check-in"] >= hoy - pd.DateOffset(months=1)]["Precio"].sum(),
        "6 Meses": df[df["Check-in"] >= hoy - pd.DateOffset(months=6)]["Precio"].sum(),
        "Año": df[df["Check-in"] >= hoy - pd.DateOffset(years=1)]["Precio"].sum()
    }
    for k, v in ingresos_totales.items():
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-title'>Total últimos {k}</div>
            <div class='kpi-value'>${v:,.2f} AUD</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### Ingresos por Tipo de Habitación")
    periodos = {
        "Semana": hoy - pd.Timedelta(days=7),
        "Mes": hoy - pd.DateOffset(months=1),
        "6 Meses": hoy - pd.DateOffset(months=6),
        "Año": hoy - pd.DateOffset(years=1)
    }
    for tipo in df["Habitación"].unique():
        with st.expander(f"{tipo.capitalize()}"):
            for nombre, desde in periodos.items():
                total = df[(df["Habitación"] == tipo) & (df["Check-in"] >= desde)]["Precio"].sum()
                st.markdown(f"""
                <div class='kpi-card small'>
                    <div class='kpi-title'>Últimos {nombre}</div>
                    <div class='kpi-value'>${total:,.2f} AUD</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### Ingresos Medios")
    dias = (df["Check-in"].max() - df["Check-in"].min()).days or 1
    ingreso_diario = df["Precio"].sum() / dias
    ingreso_semanal_medio = ingreso_diario * 7
    ingreso_mensual_medio = ingreso_diario * 30
    medios = {
        "Diario": ingreso_diario,
        "Semanal": ingreso_semanal_medio,
        "Mensual": ingreso_mensual_medio
    }
    for label, val in medios.items():
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-title'>Ingreso medio {label.lower()}</div>
            <div class='kpi-value'>${val:,.2f} AUD</div>
        </div>
        """, unsafe_allow_html=True)

# ---------- BLOQUE DERECHO (GRÁFICOS) ---------- #
with col_der:
    with st.container():
        st.markdown("### Ingresos por Habitación (Gráfico)")
        df_chart = (
            df[df["Check-in"] >= hoy - pd.DateOffset(months=6)]
            .groupby("Habitación")["Precio"]
            .sum()
            .reset_index()
        )
        bar = alt.Chart(df_chart).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X('Precio:Q', title='Ingresos (AUD)'),
            y=alt.Y('Habitación:N', sort='-x'),
            color=alt.value("#00c4b3")
        ).properties(height=250)
        st.altair_chart(bar, use_container_width=True)

        st.markdown("### Evolución Mensual (Ingresos Totales)")
        df_mes = df.copy()
        df_mes["Mes"] = df_mes["Check-in"].dt.to_period("M").astype(str)
        df_grouped = df_mes.groupby("Mes")["Precio"].sum().reset_index()
        line = alt.Chart(df_grouped).mark_line().encode(
            x="Mes",
            y="Precio"
        ).properties(height=200)
        st.altair_chart(line, use_container_width=True)

        st.markdown("### Comparativa de Ingresos Medios")
        df_medios = pd.DataFrame({
            "Periodo": ["Diario", "Semanal", "Mensual"],
            "Ingreso": [ingreso_diario, ingreso_semanal_medio, ingreso_mensual_medio]
        })
        comp = alt.Chart(df_medios).mark_bar().encode(
            x="Periodo",
            y="Ingreso",
            color=alt.value("#00c4b3")
        ).properties(height=200)
        st.altair_chart(comp, use_container_width=True)





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
