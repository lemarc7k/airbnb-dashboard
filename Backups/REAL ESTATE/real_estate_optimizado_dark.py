# === IMPORTACIONES PRINCIPALES ===
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from datetime import datetime as dt

# === LIBRERÍAS DE VISUALIZACIÓN ===
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import plotly.express as px
import plotly.graph_objects as go

# === COMPONENTES STREAMLIT ===
import streamlit.components.v1 as components
from streamlit_js_eval import streamlit_js_eval

# === FIREBASE ===
from firebase_config import db

# === LIBRERÍAS ADICIONALES ===
import time


# Config inicial
st.set_page_config(page_title="Real Estate | MV Ventures", layout="wide")

# === MODO OSCURO FORZADO GLOBAL ===
st.markdown("""
    <style>
        html, body, [class*="st-"] {
            background-color: #0f1115 !important;
            color: #ccc !important;
        }
    </style>
""", unsafe_allow_html=True)

# ====================================================================================================
# === FUNCIONES COMUNES =========================================================================================
# ====================================================================================================

def calcular_ingresos_diarios(df, inicio, fin):
    """Expande las reservas en ingresos diarios para un rango dado."""
    ingresos_expandido = []
    df_validos = df.dropna(subset=["Check-in", "Check-out"]).copy()

    for _, row in df_validos.iterrows():
        start = row["Check-in"]
        end = row["Check-out"]
        total_dias = (end - start).days
        if total_dias <= 0:
            continue
        ingreso_diario = row["Precio"] / total_dias
        for i in range(total_dias):
            dia = start + pd.Timedelta(days=i)
            if inicio <= dia <= fin:
                ingresos_expandido.append({
                    "Día": dia,
                    "Ingreso_dia": ingreso_diario
                })
    return pd.DataFrame(ingresos_expandido)


def calcular_gastos_periodo(df_gastos, inicio, fin):
    """Suma los gastos en un periodo dado."""
    df_gastos["Fecha"] = pd.to_datetime(df_gastos["Fecha"], errors="coerce", utc=True).dt.tz_convert(None)
    return df_gastos[(df_gastos["Fecha"] >= inicio) & (df_gastos["Fecha"] <= fin)]["Monto"].sum()


def calcular_ocupacion(df, inicio, fin):
    """Calcula ocupación semanal por habitación."""
    df_validas = df.dropna(subset=["Check-in", "Check-out"]).copy()
    ocupacion_expandida = []
    for _, row in df_validas.iterrows():
        checkin = row["Check-in"]
        checkout = row["Check-out"]
        if pd.isnull(checkin) or pd.isnull(checkout):
            continue
        for dia in pd.date_range(start=checkin, end=checkout - pd.Timedelta(days=1)):
            if inicio <= dia <= fin:
                ocupacion_expandida.append({
                    "Día": dia,
                    "Habitación": row["Habitación"]
                })
    return pd.DataFrame(ocupacion_expandida)


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

# Añade esto justo después:
if "recargado" not in st.session_state:
    st.session_state.recargado = False

if not st.session_state.recargado:
    st.session_state.recargado = True
    import time
    time.sleep(0.5)  # Espera breve para que Firebase procese
    st.rerun()


# ACTUALIZAR ESTADO DE RESERVAS PENDIENTES
hoy = pd.to_datetime(datetime.today())
pendientes = df[(df["Estado"] == "pendiente") & (df["Check-in"] + pd.Timedelta(days=1) <= hoy)]

for _, reserva in pendientes.iterrows():
    reserva_id = None
    # Buscar el ID del documento por coincidencia exacta (Check-in + Huesped + Habitacion)
    for doc in db.collection("bookings").stream():
        data = doc.to_dict()
        if (
            data.get("Huesped") == reserva["Huesped"]
            and data.get("Habitación") == reserva["Habitación"]
            and pd.to_datetime(data.get("Check-in")) == reserva["Check-in"]
        ):
            reserva_id = doc.id
            break
    if reserva_id:
        db.collection("bookings").document(reserva_id).update({"Estado": "pagado"})


# ===== MENÚ DE PESTAÑAS CON ESTILO GLASS MODERNO =====
st.markdown("""
    <style>
        .custom-tabs {
            display: flex;
            justify-content: center;
            gap: 40px;
            background: rgba(255, 255, 255, 0.02);
            padding: 15px 30px;
            border-radius: 14px;
            margin-bottom: 30px;
            border: 1px solid rgba(0, 255, 225, 0.1);
            box-shadow: 0 0 15px rgba(0, 255, 225, 0.05);
        }
        .custom-tab {
            color: #aaa;
            font-weight: 500;
            font-size: 15px;
            text-decoration: none;
            padding: 8px 14px;
            border-radius: 8px;
            transition: all 0.2s ease;
        }
        .custom-tab:hover {
            background-color: rgba(0, 255, 225, 0.05);
            color: #00ffe1;
        }
        .custom-tab.selected {
            background-color: rgba(0, 255, 225, 0.08);
            color: #00ffe1;
            font-weight: 600;
            box-shadow: inset 0 0 6px rgba(0, 255, 225, 0.2);
        }
    </style>
""", unsafe_allow_html=True)


# Tabs funcionales de Streamlit (invisibles)
tabs = st.tabs(["INICIO", "GENERAL", "RESERVAS", "GASTOS", "DETALLES", "EXPANSION"])


# INICIO


# ====================================================================================================
# === TAB INICIO ===============================================================================
# ====================================================================================================
with tabs[0]:
    # Esta pestaña muestra un resumen visual del rendimiento semanal: ingresos, gastos, ocupación y métricas clave.
    import time
    import numpy as np

# === CALCULAR MÉTRICAS SEMANALES PARA EL MENSAJE DE IA ===
    hoy = pd.Timestamp.now(tz=None)
    inicio_semana = hoy.to_period("W").start_time
    fin_semana = inicio_semana + pd.Timedelta(days=6)

    # Procesar fechas
    df["Check-in"] = pd.to_datetime(df["Check-in"], errors="coerce", utc=True).dt.tz_convert(None)
    df["Check-out"] = pd.to_datetime(df["Check-out"], errors="coerce", utc=True).dt.tz_convert(None)

    # === INGRESOS: pagos y pendientes distribuidos por día ===
    df_ingresos_diarios = calcular_ingresos_diarios(df, inicio_semana, fin_semana)
    ingresos = df_ingresos_diarios["Ingreso_dia"].sum()


    # === GASTOS ===
    docs = db.collection("gastos").stream()
    data = [doc.to_dict() | {"id": doc.id} for doc in docs]
    df_gastos = pd.DataFrame(data)
    df_gastos["Fecha"] = pd.to_datetime(df_gastos["Fecha"], errors="coerce", utc=True).dt.tz_convert(None)

    gastos_periodo = df_gastos[
    (df_gastos["Fecha"] >= inicio_semana) & (df_gastos["Fecha"] <= fin_semana)
    ]["Monto"].sum()

    beneficio_pct = ((ingresos - gastos_periodo) / ingresos * 100) if ingresos > 0 else 0
    color = "#10b981" if beneficio_pct >= 0 else "#ef4444"

    # === OCUPACIÓN SEMANAL POR HABITACIÓN (pagados + pendientes) ===
    df_ocupacion_dias = calcular_ocupacion(df, inicio_semana, fin_semana)

    dias_semana = 7
    habitaciones = df["Habitación"].dropna().unique()
    ocupacion_resumen = pd.DataFrame({
        "Habitación": habitaciones,
        "Ocupado (días)": [df_ocupacion_dias[df_ocupacion_dias["Habitación"] == h].shape[0] for h in habitaciones]
    })
    ocupacion_resumen["Ocupado (%)"] = (ocupacion_resumen["Ocupado (días)"] / dias_semana) * 100


    # DATOS PARA PODER MOSTRAR CORRECTAMENTE LOS TITULOS CON FECHA, ETC, SIEMPRE NECESARIO ANTES DEL CODIGO
    hoy = pd.Timestamp.today()
    inicio_semana = hoy.to_period("W").start_time
    fin_semana = inicio_semana + pd.Timedelta(days=6)
    periodo_str = f"{inicio_semana.strftime('%d %b')} – {fin_semana.strftime('%d %b %Y')}".upper()


    # === CONSTRUIR MENSAJE JARVIS ===
    lineas_ocupacion = ""
    for _, row in ocupacion_resumen.iterrows():
        lineas_ocupacion += f"<span class='jarvis-line'> <b>{row['Habitación']}:</b> <span style='color:#00ffe1;'>{row['Ocupado (%)']:.1f}%</span></span>"

    mensaje_ia = f"""
    <div class="jarvis-box">
        <div class="jarvis-header">🧠 JARVIS ANALYTICS // PERTH // {periodo_str}</div>
        <div class="jarvis-body">
            <span class="jarvis-line"> <b>Beneficio semanal neto:</b> <span style="color:#10b981;">{beneficio_pct:.1f}%</span></span>
            <span class="jarvis-line"> <b>Ingresos esta semana:</b> <span style="color:#00ffe1;">${ingresos:,.2f}</span></span>
            <span class="jarvis-line"> <b>Gastos:</b> <span style="color:#00ffe1;">${gastos_periodo:,.2f}</span></span>
            {lineas_ocupacion}
            <span class="jarvis-status"> Sistema operativo en expansión...</span>
        </div>
    </div>
    """


    st.markdown("""
    <style>
    .jarvis-box {
        background-color: #0f1115;
        border: 1px solid #00ffe1;
        border-radius: 14px;
        padding: 24px;
        font-family: 'Consolas', monospace;
        color: #ccc;
        box-shadow: 0 0 30px #00ffe120;
        animation: flicker 1s infinite alternate;
    }
    .jarvis-header {
        font-size: 16px;
        color: #00ffe1;
        margin-bottom: 12px;
        border-bottom: 1px dashed #00ffe180;
        padding-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .jarvis-body {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .jarvis-line {
        font-size: 15px;
        animation: fadein 1.2s ease-in;
    }
    .jarvis-status {
        margin-top: 12px;
        font-size: 13px;
        color: #10b981;
        font-style: italic;
    }
    @keyframes flicker {
    0% { box-shadow: 0 0 10px #00ffe110; }
    100% { box-shadow: 0 0 25px #00ffe140; }
    }
    @keyframes fadein {
    from { opacity: 0; transform: translateY(-3px); }
    to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(mensaje_ia, unsafe_allow_html=True)

    # JARVIS 2 === INSIGHT EJECUTIVO SEMANAL =======================================================

    # Preparar variables necesarias
    habitaciones_activas = df["Habitación"].nunique()
    total_reservas_semana = df_ingresos_diarios["Día"].nunique()
    ocupacion_total_dias = ocupacion_resumen["Ocupado (días)"].sum()
    ocupacion_promedio = (ocupacion_total_dias / (habitaciones_activas * 7)) * 100 if habitaciones_activas > 0 else 0

    # Formar mensaje con datos reales de la semana
    # === INSIGHT EJECUTIVO SEMANAL – VERSIÓN MEJORADA =========================================

    insight_text = f"""
    <div class="insight-box">
        <div class="insight-title">📊 INSIGHT EJECUTIVO SEMANAL</div>
        <div class="insight-body">
            <p><strong>🗓️ Periodo:</strong> <span>{inicio_semana.strftime('%d %b')} – {fin_semana.strftime('%d %b %Y')}</span></p>
            <p><strong>💰 Ingresos reales:</strong> <span style="color:#00ffe1;">${ingresos:,.2f} AUD</span></p>
            <p><strong>🛏️ Habitaciones activas:</strong> {habitaciones_activas}  
            &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp; 
            <strong>🏠 Ocupación promedio:</strong> <span style="color:#10b981;">{ocupacion_promedio:.1f}%</span></p>
            <p><strong>💸 Gastos totales:</strong> <span style="color:#00ffe1;">${gastos_periodo:,.2f} AUD</span></p>
            <p><strong>📈 Beneficio neto semanal:</strong> <span style="color:{color};">{beneficio_pct:.1f}%</span></p>
            <hr style="border: none; height: 1px; background-color: #00ffe120; margin: 12px 0;">
            <p style="font-style: italic; color: #aaa;">Basado en ocupación real proporcional<br>independientemente del estado de pago.</p>
        </div>
    </div>
    """

    st.markdown(insight_text, unsafe_allow_html=True)

    # === ESTILOS MEJORADOS =====================================================
    st.markdown("""
    <style>
    .insight-box {
        background-color: #0f1115;
        border: 1px solid #00ffe1;
        border-radius: 14px;
        padding: 24px;
        margin-top: 32px;
        box-shadow: 0 0 25px #00ffe120;
        font-family: 'Segoe UI', sans-serif;
    }
    .insight-title {
        font-size: 18px;
        color: #00ffe1;
        font-weight: bold;
        margin-bottom: 16px;
        text-transform: uppercase;
        letter-spacing: 1px;
        text-shadow: 0 0 4px #00ffe180;
    }
    .insight-body p {
        font-size: 15px;
        color: #ccc;
        line-height: 1.6;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)




    # === CÁLCULOS CLAVE ===
    total_reservas = len(df)
    ingresos_totales = df["Precio"].sum() if "Precio" in df.columns else 0
    habitaciones_activas = df["Habitación"].nunique() if "Habitación" in df.columns else 0

    mes_actual = hoy.to_period("M").to_timestamp()
    mes_anterior = (hoy - pd.DateOffset(months=1)).to_period("M").to_timestamp()

    ingreso_mes_actual = df[df["Mes"] == mes_actual]["Precio"].sum()
    ingreso_mes_anterior = df[df["Mes"] == mes_anterior]["Precio"].sum()
    variacion = ingreso_mes_actual - ingreso_mes_anterior
    variacion_pct = (variacion / ingreso_mes_anterior * 100) if ingreso_mes_anterior > 0 else 0

    habitaciones_bajas = df["Habitación"].value_counts().sort_values().head(2).index.tolist()

    ocupadas = df[(df["Check-in"] <= hoy) & (df["Check-out"] >= hoy)]
    dias_ocupados = len(ocupadas)
    dias_totales = habitaciones_activas * 30
    ocupacion_general = dias_ocupados / dias_totales * 100 if dias_totales > 0 else 0

    

    # === INGRESOS MENSUALES PARA GRÁFICA ===
    df_mensual = df.groupby("Mes")["Precio"].sum().reset_index()
    df_mensual["Mes"] = df_mensual["Mes"].dt.strftime('%b')
    df_mensual = df_mensual.sort_values("Mes")

    # === ESTILOS GLOBALES ===
    st.markdown("""
        <style>
            .dashboard-grid {
                display: grid;
                grid-template-columns: 3fr 1fr;
                gap: 30px;
                margin-top: 40px;
            }
            .box {
                background-color: #0f1115;
                border: 1px solid #00ffe180;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 0 20px #00ffe130;
            }
            .metrics {
                display: flex;
                justify-content: center;
                gap: 30px;
                margin-top: 20px;
                flex-wrap: wrap;
                text-align: center;
            }
            .metric-card {
                background: linear-gradient(to bottom right, #101828, #1e293b);
                border-radius: 18px;
                padding: 25px 30px;
                box-shadow: 0 0 20px rgba(0,255,225,0.07);
                width: 220px;
            }
            .metric-label {
                color: #ccc;
                font-size: 14px;
                margin-bottom: 5px;
            }
            .metric-value {
                color: #00ffe1;
                font-size: 26px;
                font-weight: bold;
            }
        </style>
    """, unsafe_allow_html=True)


    


    # === ENCABEZADO ===
    st.markdown("<h2 style='text-align:center; color:#00ffe1;'>BIENVENIDO MR VERA</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888;'>Estas son las métricas clave de tus propiedades gestionadas en Airbnb</p>", unsafe_allow_html=True)

    # === MÉTRICAS PRINCIPALES ===
    st.markdown(f"""
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-label">Total Reservas</div>
                <div class="metric-value">{total_reservas}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Ingresos Totales (AUD)</div>
                <div class="metric-value">${ingresos_totales:,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Habitaciones activas</div>
                <div class="metric-value">{habitaciones_activas}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # === RESUMEN FINANCIERO SEMANAL (ACTUALIZADO AUTOMÁTICAMENTE) ===

    # Obtener fecha de hoy y límites de semana
    hoy = pd.Timestamp.today()
    inicio_semana = hoy.to_period("W").start_time
    fin_semana = inicio_semana + pd.Timedelta(days=6)
    periodo_str = f"{inicio_semana.strftime('%d %b')} – {fin_semana.strftime('%d %b %Y')}".upper()

    st.markdown(f"""
    <div style="text-align: center; margin: 40px 0;">
        <hr style="border: none; height: 2px; background-color: #00ffe1; margin-bottom: 10px;">
        <h4 style="color:#00ffe1; margin: 0;">{periodo_str}</h4>
        <hr style="border: none; height: 2px; background-color: #00ffe1; margin-top: 10px;">
    </div>
    """, unsafe_allow_html=True)

    # === Cargar y procesar gastos ===
    docs = db.collection("gastos").stream()
    data = [doc.to_dict() | {"id": doc.id} for doc in docs]
    df_gastos = pd.DataFrame(data)
    df_gastos["Fecha"] = pd.to_datetime(df_gastos["Fecha"], errors="coerce", utc=True).dt.tz_convert(None)

    # ✅ INGRESOS: pagos y pendientes distribuidos por día
    df_validos = df.dropna(subset=["Check-in", "Check-out"]).copy()

    df_ingresos_expandido = []
    for _, row in df_validos.iterrows():
        start = row["Check-in"]
        end = row["Check-out"]
        total_dias = (end - start).days
        if total_dias <= 0:
            continue
        ingreso_diario = row["Precio"] / total_dias
        for i in range(total_dias):
            dia = start + pd.Timedelta(days=i)
            if inicio_semana <= dia <= fin_semana:
                df_ingresos_expandido.append({
                    "Día": dia,
                    "Ingreso_dia": ingreso_diario
                })

    df_ingresos_diarios = pd.DataFrame(df_ingresos_expandido)
    ingresos = df_ingresos_diarios["Ingreso_dia"].sum()


        # Filtrar gastos de la semana actual
    gastos_periodo = df_gastos[
            (df_gastos["Fecha"] >= inicio_semana) & (df_gastos["Fecha"] <= fin_semana)
        ]["Monto"].sum()

    # Calcular beneficio neto %
    beneficio_pct = ((ingresos - gastos_periodo) / ingresos * 100) if ingresos > 0 else 0
    color = "#10b981" if beneficio_pct >= 0 else "#ef4444"

    # === Mostrar tarjetas ===
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
            <div style="background-color:#111827; padding:20px; border-radius:12px; text-align:center">
                <span style="color:#ccc;">Ingreso semana actual</span><br>
                <span style="font-size:24px; font-weight:bold; color:#00ffe1;">${ingresos:,.2f}</span>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div style="background-color:#111827; padding:20px; border-radius:12px; text-align:center">
                <span style="color:#ccc;">Gasto semanal (rent + limpieza)</span><br>
                <span style="font-size:24px; font-weight:bold; color:#00ffe1;">${gastos_periodo:,.2f}</span>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div style="background-color:#111827; padding:20px; border-radius:12px; text-align:center">
                <span style="color:#ccc;">Beneficio neto (%)</span><br>
                <span style="font-size:24px; font-weight:bold; color:{color};">{beneficio_pct:.1f}%</span>
            </div>
        """, unsafe_allow_html=True)


# === GRÁFICO COMPARATIVO DE INGRESOS Y GASTOS POR MES ===

    # Base de meses fijos
    meses_fijos = pd.date_range(start="2025-01-01", end="2025-12-01", freq="MS")
    df_meses = pd.DataFrame({"Mes": meses_fijos})

    # Ingresos por mes
    df_ingresos_mensuales = df[df["Estado"].str.lower() == "pagado"].groupby("Mes")["Precio"].sum().reset_index()
    df_ingresos_mensuales.columns = ["Mes", "Ingresos"]

    # Gastos por mes
    df_gastos["Mes"] = df_gastos["Fecha"].dt.to_period("M").dt.to_timestamp()
    df_gastos_mensuales = df_gastos.groupby("Mes")["Monto"].sum().reset_index()
    df_gastos_mensuales.columns = ["Mes", "Gastos"]

    # Fusionar todo
    df_merge = df_meses.merge(df_ingresos_mensuales, on="Mes", how="left")
    df_merge = df_merge.merge(df_gastos_mensuales, on="Mes", how="left")
    df_merge = df_merge.fillna(0)
    df_merge["MesNombre"] = df_merge["Mes"].dt.strftime("%b")

    # Transformar a formato largo (melt)
    df_long = df_merge.melt(id_vars=["MesNombre"], value_vars=["Ingresos", "Gastos"], var_name="Tipo", value_name="Valor")

    # Gráfico Altair
    chart = alt.Chart(df_long).mark_bar().encode(
        x=alt.X("MesNombre:N", title="Mes", sort=list(df_meses["Mes"].dt.strftime("%b"))),
        y=alt.Y("Valor:Q", title="$ AUD"),
        color=alt.Color("Tipo:N", scale=alt.Scale(domain=["Ingresos", "Gastos"], range=["#00ffe1", "#e60073"])),
        tooltip=["MesNombre", "Tipo", "Valor"]
    ).properties(
        height=300,
        background="#0f1115",
        title="Evolución mensual de ingresos vs gastos"
    ).configure_axis(
        labelColor="#ccc",
        titleColor="#00ffe1"
    ).configure_legend(
        title=None,
        labelColor="#ccc"
    ).configure_title(
        color="#00ffe1"
    ).configure_view(
        stroke=None
    )

    # Mostrar el gráfico
    st.markdown("---")
    st.altair_chart(chart, use_container_width=True)


# ---------- GENERAL ---------- #


# ====================================================================================================
# === TAB GENERAL ===============================================================================
# ====================================================================================================
with tabs[1]:
    # Esta pestaña presenta un resumen mensual de ingresos y niveles de ocupación global con análisis detallado.
    st.subheader("Resumen general")
    total = df["Precio"].sum()
    upcoming = df[df["Check-in"] > hoy]["Precio"].sum()
    ingreso_mes = df[df["Mes"] == hoy.to_period("M").to_timestamp()]["Precio"].sum()

    st.markdown("""
    <style>
    .resumen-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 20px;
        margin-top: 20px;
    }
    .resumen-card-block {
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 160px;
        flex: 1 1 180px;
    }
    .resumen-title {
        font-size: 13px;
        color: #d1d5db;
        font-family: 'Segoe UI', 'Inter', sans-serif;
        margin-bottom: 6px;
        text-align: center;
        font-weight: 600;
    }
    .resumen-card {
        background: linear-gradient(to bottom right, #1e1e21, #29292e);
        padding: 16px 20px;
        border-radius: 14px;
        text-align: center;
        font-family: 'Segoe UI', 'Inter', sans-serif;
        box-shadow: 0 0 8px rgba(0,0,0,0.2);
        transition: transform 0.2s ease;
        width: 100%;
        max-width: 220px;
    }
    .resumen-card:hover {
        transform: scale(1.03);
        box-shadow: 0 0 14px #00ffe1;
    }
    .resumen-valor {
        font-size: 24px;
        font-weight: bold;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='resumen-container'>
        <div class='resumen-card-block'>
            <div class='resumen-title'>💰 INGRESOS PAGADOS</div>
            <div class='resumen-card'><div class='resumen-valor'>${total:,.2f} AUD</div></div>
        </div>
        <div class='resumen-card-block'>
            <div class='resumen-title'>📅 PRÓXIMOS INGRESOS</div>
            <div class='resumen-card'><div class='resumen-valor'>${upcoming:,.2f} AUD</div></div>
        </div>
        <div class='resumen-card-block'>
            <div class='resumen-title'>📈 MES ACTUAL</div>
            <div class='resumen-card'><div class='resumen-valor'>${ingreso_mes:,.2f} AUD</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


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

    # === CALCULAR OCUPACIÓN RESUMIDA ===
    ocupacion_stats["EsOcupado"] = ocupacion_stats["Estado"] == "Ocupado"
    ocupacion_stats["EsFuturo"] = ocupacion_stats["Estado"] == "Futuro"

    dias_totales = ocupacion_stats.groupby("Habitación")["Estado"].count().reset_index(name="TotalDías")
    ocupacion_resumen = ocupacion_stats.groupby("Habitación")[["EsOcupado", "EsFuturo"]].sum().reset_index()
    ocupacion_resumen = ocupacion_resumen.merge(dias_totales, on="Habitación")
    ocupacion_resumen["Disponible"] = ocupacion_resumen["TotalDías"] - ocupacion_resumen["EsOcupado"] - ocupacion_resumen["EsFuturo"]

    ocupacion_resumen["Ocupado (%)"] = (ocupacion_resumen["EsOcupado"] / ocupacion_resumen["TotalDías"] * 100)
    ocupacion_resumen["Futuro (%)"] = (ocupacion_resumen["EsFuturo"] / ocupacion_resumen["TotalDías"] * 100)
    ocupacion_resumen["OcupadoFuturo (%)"] = ocupacion_resumen["Ocupado (%)"] + ocupacion_resumen["Futuro (%)"]

    # Clasificación visual y recomendaciones
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


    # === MÉTRICAS ESTILO BUSINESS-CARD ===

    # === CSS Y ESTILO PARA TARJETAS DE OCUPACIÓN ===
    st.markdown("""
    <style>
    .ocupacion-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 20px;
        margin-top: 20px;
    }
    .ocupacion-card-block {
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 160px;
        flex: 1 1 180px;
    }
    .ocupacion-title {
        font-size: 13px;
        color: #d1d5db;
        font-family: 'Segoe UI', 'Inter', sans-serif;
        margin-bottom: 6px;
        text-align: center;
        font-weight: 600;
    }
    .ocupacion-card {
        background: linear-gradient(to bottom right, #1e1e21, #29292e);
        padding: 16px 20px;
        border-radius: 14px;
        text-align: center;
        font-family: 'Segoe UI', 'Inter', sans-serif;
        box-shadow: 0 0 8px rgba(0,0,0,0.2);
        transition: transform 0.2s ease;
        width: 100%;
        max-width: 220px;
    }
    .ocupacion-card:hover {
        transform: scale(1.03);
        box-shadow: 0 0 14px #00ffe1;
    }
    .ocupacion-valor {
        font-size: 24px;
        font-weight: bold;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)


    #CONSTRUCCION DE TARJETAS

    st.markdown("### NIVEL DE OCUPACIÓN")

    st.markdown("<div class='ocupacion-container'>", unsafe_allow_html=True)

    for _, row in ocupacion_resumen.iterrows():
        porcentaje = round(row["OcupadoFuturo (%)"], 1)
        st.markdown(f"""
            <div class='ocupacion-card-block'>
                <div class='ocupacion-title'>{row["Habitación"]}</div>
                <div class='ocupacion-card'>
                    <div class='ocupacion-valor'>{porcentaje}%</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


    # === GRAFICO DE OCUPACIÓN APILADA ===
    st.markdown("### OCUPACIÓN REAL / FUTURA")

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

    # === CALENDARIO DE DISPONIBILIDAD - COMPLETO ===
    from datetime import datetime

    # Preparar días del mes actual
    hoy = pd.to_datetime(datetime.today().date())
    fecha_inicio = pd.to_datetime(datetime(hoy.year, hoy.month, 1))
    fecha_fin = fecha_inicio + pd.offsets.MonthEnd(0)
    dias_mes = pd.date_range(fecha_inicio, fecha_fin, freq='D')

    # Días sin reservas (usa df_ocupacion ya definido)
    dias_vacios = df_ocupacion.groupby("Día")["Estado"].apply(lambda x: all(s == "Disponible" for s in x))
    dias_vacios = dias_vacios[dias_vacios].index

    # Construir DataFrame calendario
    df_cal = pd.DataFrame({
        "Día": dias_mes,
        "Ocupado": [not d in dias_vacios for d in dias_mes],
        "Semana": [d.isocalendar()[1] for d in dias_mes],
        "Día_nombre": [d.strftime('%A') for d in dias_mes]
    })

    # Traducir estado
    df_cal["Estado"] = df_cal["Ocupado"].replace({True: "Ocupado", False: "Vacío"})

    # Ordenar días (Lunes a Domingo)
    orden_dias = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df_cal["Día_nombre"] = pd.Categorical(df_cal["Día_nombre"], categories=orden_dias, ordered=True)

    # === Mostrar Heatmap elegante ===
    st.markdown("### 📅 Calendario de disponibilidad")

    heatmap = alt.Chart(df_cal).mark_rect(
        cornerRadius=6,
        stroke='rgba(255,255,255,0.1)',
        strokeWidth=0.4
    ).encode(
        x=alt.X("Día_nombre:N", title="Día de la semana", sort=orden_dias),
        y=alt.Y("Semana:O", title="Semana del mes"),
        color=alt.Color("Estado:N",
            scale=alt.Scale(domain=["Ocupado", "Vacío"], range=["#10b981", "#ef4444"]),
            legend=alt.Legend(title="Estado de ocupación")
        ),
        tooltip=[
            alt.Tooltip("Día:T", title="Fecha exacta"),
            alt.Tooltip("Estado:N", title="Estado del día")
        ]
    ).properties(
        height=280
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_view(
        stroke=None
    )

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

# REGISTRAR RESERVAS 


# ====================================================================================================
# === TAB RESERVAS ===============================================================================
# ====================================================================================================
with tabs[2]:
    # Aquí se registran y editan manualmente todas las reservas de huéspedes, con generación automática de gastos.
    st.markdown("""
        <style>
        .formulario-box {
            background-color: #0f1115;
            border: 1px solid #00ffe1;
            border-radius: 14px;
            padding: 30px;
            font-family: 'Segoe UI', sans-serif;
            color: #ccc;
            box-shadow: 0 0 20px #00ffe130;
        }
        .formulario-box h3 {
            color: #00ffe1;
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("""
        <div style="background-color:#0f1115; border:1px solid #00ffe1; border-radius:14px; padding:30px; margin-bottom:30px; box-shadow:0 0 20px #00ffe130;">
            <h3 style="color:#00ffe1; font-family:'Segoe UI',sans-serif;"> REGISTRAR RESERVA</h3>
        </div>
    """, unsafe_allow_html=True)

    with st.form("formulario_reserva"):
        # 🏠 Información Básica
        st.markdown("""
        <div style="text-align: center; margin: 40px 0;">
            <hr style="border: none; height: 2px; background-color: #00ffe1; margin-bottom: 10px;">
            <h4 style="color:#00ffe1; margin: 0;">INFORMACIÓN BÁSICA</h4>
            <hr style="border: none; height: 2px; background-color: #00ffe1; margin-top: 10px;">
        </div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            propiedad = st.text_input("Propiedad")
            canal = st.selectbox("Canal de reserva", ["Airbnb", "Booking", "Instagram", "Whatsapp", "Otro"])
        with col2:
            habitacion = st.text_input("Habitación")
            estado = st.selectbox("Estado", ["Pagado", "Pendiente"])

        # 📅 Fechas
        st.markdown("""
        <div style="text-align: center; margin: 40px 0;">
            <hr style="border: none; height: 2px; background-color: #00ffe1; margin-bottom: 10px;">
            <h4 style="color:#00ffe1; margin: 0;">FECHA DE BOOKINGS</h4>
            <hr style="border: none; height: 2px; background-color: #00ffe1; margin-top: 10px;">
        </div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            check_in = st.date_input("Check-in")
        with col2:
            noches = st.number_input("Número de noches", min_value=1, step=1)

        check_out = check_in + timedelta(days=int(noches))
        st.text_input("Check-out (calculado)", value=check_out.strftime("%Y-%m-%d"), disabled=True)

        # 💳 Pago
        st.markdown("""
        <div style="text-align: center; margin: 40px 0;">
            <hr style="border: none; height: 2px; background-color: #00ffe1; margin-bottom: 10px;">
            <h4 style="color:#00ffe1; margin: 0;">INFORMACIÓN DE PAGO</h4>
            <hr style="border: none; height: 2px; background-color: #00ffe1; margin-top: 10px;">
        </div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            precio_total = st.number_input("Precio total (AUD)", min_value=0.0, step=10.0)
            metodo_pago = st.selectbox("Método de pago", ["Transferencia", "Efectivo", "Airbnb", "Booking", "Otro"])
        with col2:
            limpieza = st.number_input("Precio limpieza (AUD)", min_value=0.0, step=5.0)
            precio_noche_calculado = round(precio_total / noches, 2) if noches else 0.0
            st.text_input("Precio por noche (calculado)", value=str(precio_noche_calculado), disabled=True)

        # 👤 Huésped
        st.markdown("""
        <div style="text-align: center; margin: 40px 0;">
            <hr style="border: none; height: 2px; background-color: #00ffe1; margin-bottom: 10px;">
            <h4 style="color:#00ffe1; margin: 0;">INFORMACIÓN GUEST</h4>
            <hr style="border: none; height: 2px; background-color: #00ffe1; margin-top: 10px;">
        </div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            huesped = st.text_input("Nombre del huésped")
            personas = st.number_input("Número de huéspedes", min_value=1, step=1)
            ciudad = st.text_input("Ciudad de residencia")
        with col2:
            telefono = st.text_input("Teléfono")
            paises_populares = sorted([
                # América
                "Argentina", "Bolivia", "Brasil", "Canadá", "Chile", "Colombia", "Costa Rica", "Cuba", "Ecuador",
                "El Salvador", "Estados Unidos", "Guatemala", "Honduras", "México", "Nicaragua", "Panamá",
                "Paraguay", "Perú", "República Dominicana", "Uruguay", "Venezuela",

                # Europa
                "Alemania", "Austria", "Bélgica", "Bulgaria", "Croacia", "Dinamarca", "Eslovaquia", "Eslovenia",
                "España", "Estonia", "Finlandia", "Francia", "Grecia", "Hungría", "Irlanda", "Islandia", "Italia",
                "Letonia", "Lituania", "Noruega", "Países Bajos", "Polonia", "Portugal", "Reino Unido",
                "República Checa", "Rumanía", "Suecia", "Suiza", "Ucrania",

                # Asia
                "Arabia Saudita", "Bangladés", "Camboya", "China", "Corea del Sur", "Emiratos Árabes Unidos",
                "Filipinas", "India", "Indonesia", "Irak", "Irán", "Israel", "Japón", "Jordania", "Kazajistán",
                "Kuwait", "Laos", "Líbano", "Malasia", "Mongolia", "Nepal", "Pakistán", "Qatar", "Singapur",
                "Sri Lanka", "Tailandia", "Turquía", "Uzbekistán", "Vietnam",

                # Oceanía
                "Australia", "Fiyi", "Nueva Zelanda", "Papúa Nueva Guinea", "Samoa",

                # África
                "Argelia", "Angola", "Camerún", "Egipto", "Etiopía", "Ghana", "Kenia", "Marruecos",
                "Nigeria", "Senegal", "Sudáfrica", "Tanzania", "Túnez", "Uganda", "Zimbabue",

                # Otros
                "Otros"
            ])

            pais = st.selectbox("País de origen", sorted(paises_populares))
            sexo = st.selectbox("Sexo", ["Masculino", "Femenino", "Otro", "Prefiero no decir"])

        # 📝 Notas
        st.markdown("""
        <div style="text-align: center; margin: 40px 0;">
            <hr style="border: none; height: 2px; background-color: #00ffe1; margin-bottom: 10px;">
            <h4 style="color:#00ffe1; margin: 0;">NOTAS PARA EL ANFITRIÓN</h4>
            <hr style="border: none; height: 2px; background-color: #00ffe1; margin-top: 10px;">
        </div>
        """, unsafe_allow_html=True)
        notas = st.text_area("Notas adicionales")

        # 🔚 Cerrar contenedor AQUÍ
        st.markdown("</div>", unsafe_allow_html=True)

        # Botón submit
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

        # === REGISTRAR GASTOS AUTOMÁTICOS ===
        huesped_norm = datos.get("Huesped", "").lower().strip()
        checkin_date = pd.to_datetime(datos.get("Check-in"))
        propiedad = datos.get("Propiedad", "Sin asignar")

        # --- 1. Gasto variable general ($120 por booking)
        gasto_existente = db.collection("gastos")\
            .where("Fecha", "==", checkin_date)\
            .where("Tipo", "==", "Variable")\
            .where("Huesped", "==", huesped_norm)\
            .limit(1)\
            .stream()

        if not any(gasto_existente):
            gasto_variable = {
                "Fecha": checkin_date,
                "Monto": 120,
                "Tipo": "Variable",
                "Categoria": "Variable",
                "Propiedad": propiedad,
                "Descripción": f"Gasto variable por booking de {datos.get('Huesped', 'desconocido')}",
                "Huesped": huesped_norm,
                "Relacionado": True
            }
            db.collection("gastos").add(gasto_variable)

        # --- 2. Gasto de limpieza (si aplica y es mayor a 0)
        limpieza = datos.get("Limpieza", 0)
        if limpieza > 0:
            gasto_limpieza_existente = db.collection("gastos")\
                .where("Fecha", "==", checkin_date)\
                .where("Tipo", "==", "Limpieza")\
                .where("Huesped", "==", huesped_norm)\
                .limit(1)\
                .stream()

            if not any(gasto_limpieza_existente):
                gasto_limpieza = {
                    "Fecha": checkin_date,
                    "Monto": limpieza,
                    "Tipo": "Limpieza",
                    "Categoria": "Variable",
                    "Propiedad": propiedad,
                    "Descripción": f"Limpieza para booking de {datos.get('Huesped', 'desconocido')}",
                    "Huesped": huesped_norm,
                    "Relacionado": True
                }
                db.collection("gastos").add(gasto_limpieza)


# EDICION DE RESERVAS

        st.markdown("---")
    st.markdown("### ✏️ Reservas registradas (edición manual)")

    # Obtener reservas desde Firestore
    docs = db.collection("bookings").stream()
    data = [doc.to_dict() | {"id": doc.id} for doc in docs]
    df_editar = pd.DataFrame(data)

    if not df_editar.empty:
        df_editar = df_editar.sort_values("Check-in", ascending=False)
        df_editar_display = df_editar[[
            "Check-in", "Check-out", "Huesped", "Habitación", "Estado", "Precio", "id"
        ]].copy()
        df_editar_display["Precio"] = df_editar_display["Precio"].apply(lambda x: f"${x:,.2f}")
        df_editar_display = df_editar_display.rename(columns={
            "Check-in": "📅 Check-in",
            "Check-out": "📅 Check-out",
            "Huesped": "👤 Huésped",
            "Habitación": "🛏️ Habitación",
            "Estado": "💳 Estado",
            "Precio": "💰 Precio",
            "id": "🔧 ID"
        })

        st.dataframe(df_editar_display, use_container_width=True)

    st.markdown("Selecciona el ID para editar una reserva:")

    id_seleccionado = st.selectbox("🔧 ID de la reserva", df_editar["id"])
    reserva = next((item for item in data if item["id"] == id_seleccionado), None)

    if reserva:
        estado_actual = reserva.get("Estado", "pendiente") or "pendiente"

        with st.form("editar_reserva"):
            col1, col2 = st.columns(2)
            with col1:
                nuevo_estado = st.selectbox("Nuevo estado", ["pagado", "pendiente"], 
                                            index=["pagado", "pendiente"].index(estado_actual.lower()))
                nuevo_checkin = st.date_input("Nuevo Check-in", value=pd.to_datetime(reserva["Check-in"]).date())
                nuevo_checkout = st.date_input("Nuevo Check-out", value=pd.to_datetime(reserva["Check-out"]).date())
                nuevo_precio = st.number_input("Precio total (AUD)", min_value=0.0, step=10.0, 
                                            value=float(reserva.get("Precio", 0)))
            with col2:
                nuevo_huesped = st.text_input("Nombre del huésped", value=reserva.get("Huesped", ""))
                nueva_habitacion = st.text_input("Habitación", value=reserva.get("Habitación", ""))
                nuevo_canal = st.selectbox("Canal", ["Airbnb", "Booking", "Instagram", "Whatsapp", "Otro"], 
                                        index=["Airbnb", "Booking", "Instagram", "Whatsapp", "Otro"].index(
                                            reserva.get("Canal", "Airbnb")))

            actualizar = st.form_submit_button("💾 Actualizar")

            if actualizar:
                db.collection("bookings").document(reserva["id"]).update({
                    "Estado": nuevo_estado,
                    "Check-in": str(nuevo_checkin),
                    "Check-out": str(nuevo_checkout),
                    "Precio": nuevo_precio,
                    "Huesped": nuevo_huesped,
                    "Habitación": nueva_habitacion,
                    "Canal": nuevo_canal
                })
                st.success("✅ Reserva actualizada correctamente.")
                st.experimental_rerun()


#DATOS HISTORICOS DE GASTOS FIJOS PARA LA PESTAÑA DE GASTOS

from datetime import datetime, timedelta

# === Registrar histórico de gastos fijos semanales desde enero ===
inicio = datetime(2025, 1, 1)
hoy = datetime.today()
martes_fechas = []

# Generar todos los martes desde enero
dia = inicio
while dia <= hoy:
    if dia.weekday() == 1:  # Martes
        martes_fechas.append(datetime.combine(dia.date(), datetime.min.time()))
    dia += timedelta(days=1)

# Obtener todos los gastos existentes
docs = db.collection("gastos").stream()
existentes = [doc.to_dict() for doc in docs]

# Crear set de fechas-tipo ya registradas
existentes_set = {
    (d.get("Fecha").date().isoformat(), d.get("Tipo"))
    for d in existentes if "Fecha" in d and "Tipo" in d and hasattr(d.get("Fecha"), "date")
}


# Registrar los que no existan
for fecha in martes_fechas:
    fecha_str = fecha.strftime("%Y-%m-%d")
    for gasto in [
        {"Tipo": "Renta semanal", "Monto": 690},
        {"Tipo": "Internet semanal", "Monto": 12.5},
        {"Tipo": "Electricidad semanal", "Monto": 30}
    ]:
        if (fecha_str, gasto["Tipo"]) not in existentes_set:
            db.collection("gastos").add({
                "Fecha": fecha,
                "Tipo": gasto["Tipo"],
                "Monto": gasto["Monto"],
                "Categoria": "Fijo",
                "Propiedad": "CBD"
            })


# ---------- GASTOS DEDUCIBLES ACTUALIZADOS (tabs[3]) ----------


# ====================================================================================================
# === TAB GASTOS ===============================================================================
# ====================================================================================================
with tabs[3]:
    # En esta pestaña se visualizan los gastos fijos y variables, y se comparan contra los ingresos por periodo.
    import altair as alt
    from datetime import datetime
    import pandas as pd

    st.markdown("")

    # === Cargar datos de gastos desde Firestore ===
    docs = db.collection("gastos").stream()
    data = [doc.to_dict() | {"id": doc.id} for doc in docs]
    df_gastos = pd.DataFrame(data)
    df_gastos["Fecha"] = pd.to_datetime(df_gastos["Fecha"], errors="coerce", utc=True).dt.tz_convert(None)

    # === TARJETAS FINANCIERAS INTELIGENTES ===
    

    # Selección de período
    periodo_resumen = st.selectbox("Selecciona el período:", ["Semana actual", "Mes actual", "Últimos 6 meses", "Año actual"])

    hoy = pd.Timestamp.today()

    if periodo_resumen == "Semana actual":
        inicio = hoy.to_period("W").start_time
    elif periodo_resumen == "Mes actual":
        inicio = hoy.to_period("M").to_timestamp()
    elif periodo_resumen == "Últimos 6 meses":
        inicio = hoy - pd.DateOffset(months=6)
    else:
        inicio = hoy.to_period("Y").to_timestamp()

    # === Ingresos (bookings pagados) ===
    df["Check-in"] = pd.to_datetime(df["Check-in"], errors="coerce", utc=True).dt.tz_convert(None)
    df["Check-out"] = pd.to_datetime(df["Check-out"], errors="coerce", utc=True).dt.tz_convert(None)

    df_pagos = df[df["Estado"].str.lower() == "pagado"].copy()
    df_periodo = df_pagos[df_pagos["Check-in"] >= inicio]

    # Expandir ingresos diarios como en la tabla
    df_ingresos_expandido = []
    for _, row in df_pagos.iterrows():
        start = pd.to_datetime(row["Check-in"])
        end = pd.to_datetime(row["Check-out"])
        total_dias = (end - start).days
        if total_dias <= 0:
            continue
        ingreso_diario = row["Precio"] / total_dias

        for i in range(total_dias):
            dia = start + pd.Timedelta(days=i)
            if dia >= inicio:
                df_ingresos_expandido.append({
                    "Día": dia,
                    "Ingreso_dia": ingreso_diario
                })

    df_ingresos_diarios = pd.DataFrame(df_ingresos_expandido)
    ingresos = df_ingresos_diarios["Ingreso_dia"].sum()


    # === Gastos del mismo periodo ===
    gastos_periodo = df_gastos[df_gastos["Fecha"] >= inicio]["Monto"].sum()

    # === Beneficio en % ===
    if ingresos > 0:
        beneficio_pct = ((ingresos - gastos_periodo) / ingresos) * 100
    else:
        beneficio_pct = 0

    
    # === 1. SEPARADOR VISUAL ENTRE CARDS (CENTRADO Y EXTENDIDO) ===
    st.markdown("""
    <div style="text-align: center; margin: 40px 0;">
        <hr style="border: none; height: 2px; background-color: #00ffe1; margin-bottom: 10px;">
        <h4 style="color:#00ffe1; margin: 0;">RESUMEN FINANCIERO SEMANAL</h4>
        <hr style="border: none; height: 2px; background-color: #00ffe1; margin-top: 10px;">
    </div>
    """, unsafe_allow_html=True)


    # === Tarjetas ===
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
            <div style="background-color:#111827; padding:20px; border-radius:12px; text-align:center">
                <span style="color:#ccc;">Ingreso semana actual</span><br>
                <span style="font-size:24px; font-weight:bold; color:#00ffe1;">${ingresos:,.2f}</span>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div style="background-color:#111827; padding:20px; border-radius:12px; text-align:center">
                <span style="color:#ccc;">Gasto semanal (rent + limpieza)</span><br>
                <span style="font-size:24px; font-weight:bold; color:#00ffe1;">${gastos_periodo:,.2f}</span>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        color = "#10b981" if beneficio_pct >= 0 else "#ef4444"
        st.markdown(f"""
            <div style="background-color:#111827; padding:20px; border-radius:12px; text-align:center">
                <span style="color:#ccc;">Beneficio neto (%)</span><br>
                <span style="font-size:24px; font-weight:bold; color:{color};">{beneficio_pct:.1f}%</span>
            </div>
        """, unsafe_allow_html=True)

# === 2. SEPARADOR VISUAL ENTRE CARDS (CENTRADO Y EXTENDIDO) ===
    st.markdown("""
    <div style="text-align: center; margin: 40px 0;">
        <hr style="border: none; height: 2px; background-color: #00ffe1; margin-bottom: 10px;">
        <h4 style="color:#00ffe1; margin: 0;">RESUMEN FINANCIERO ANUAL</h4>
        <hr style="border: none; height: 2px; background-color: #00ffe1; margin-top: 10px;">
    </div>
    """, unsafe_allow_html=True)


    # Continúa con el resto de KPIs, gráficos y tablas como lo tienes en el resto del código
    # Solo asegúrate de aplicar esta misma conversión de fechas donde sea necesario:
    # pd.to_datetime(..., utc=True).dt.tz_convert(None)


    # === KPIs DE GASTOS ===
    hoy = pd.Timestamp.today()

    total_gastos = df_gastos["Monto"].sum()
    df_gastos["Mes"] = df_gastos["Fecha"].dt.to_period("M").dt.to_timestamp()
    mes_actual = hoy.to_period("M").to_timestamp()
    gasto_mes = df_gastos[df_gastos["Mes"] == mes_actual]["Monto"].sum()

    categoria_top = (
        df_gastos.groupby("Categoria")["Monto"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .iloc[0]
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div style="background-color:#111827; padding:20px; border-radius:12px; text-align:center">
                <span style="color:#ccc;">Gasto acomulado 2025</span><br>
                <span style="font-size:24px; font-weight:bold; color:#00ffe1;">${total_gastos:,.2f}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style="background-color:#111827; padding:20px; border-radius:12px; text-align:center">
                <span style="color:#ccc;">Gastos mes actual</span><br>
                <span style="font-size:24px; font-weight:bold; color:#00ffe1;">${gasto_mes:,.2f}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div style="background-color:#111827; padding:20px; border-radius:12px; text-align:center">
                <span style="color:#ccc;">Categoría dominante</span><br>
                <span style="font-size:24px; font-weight:bold; color:#00ffe1;">{categoria_top['Categoria']}<br>${categoria_top['Monto']:,.0f}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # === Selector de intervalo ===
    periodo = st.selectbox("🕒 Ver gastos por:", ["Semanal", "Mensual", "Anual"])

    if periodo == "Semanal":
        df_gastos["Periodo"] = df_gastos["Fecha"].dt.to_period("W").dt.start_time
    elif periodo == "Mensual":
        df_gastos["Periodo"] = df_gastos["Fecha"].dt.to_period("M").dt.to_timestamp()
    else:
        df_gastos["Periodo"] = df_gastos["Fecha"].dt.to_period("Y").dt.to_timestamp()

    df_gastos_grouped = df_gastos.groupby("Periodo")["Monto"].sum().reset_index()
    df_gastos_grouped.columns = ["Periodo", "Gastos"]

    # === Obtener datos de ingresos desde Firestore (solo pagados) ===
    df_ingresos = obtener_datos()

    # 🔁 Usar fecha de Check-in para ubicar ingresos en el periodo correcto
    df_ingresos["Check-in"] = pd.to_datetime(df_ingresos["Check-in"], errors="coerce")

    # Filtrar solo bookings pagados
    df_ingresos = df_ingresos[df_ingresos["Estado"].str.lower().isin(["pagado", "pendiente"])]


    # Agrupar ingresos por periodo usando Check-in
    if periodo == "Semanal":
        df_ingresos["Periodo"] = df_ingresos["Check-in"].dt.to_period("W").dt.start_time
    elif periodo == "Mensual":
        df_ingresos["Periodo"] = df_ingresos["Check-in"].dt.to_period("M").dt.to_timestamp()
    else:
        df_ingresos["Periodo"] = df_ingresos["Check-in"].dt.to_period("Y").dt.to_timestamp()

    df_ingresos_grouped = df_ingresos.groupby("Periodo")["Precio"].sum().reset_index()
    df_ingresos_grouped.columns = ["Periodo", "Ingresos"]

    # Agrupar también los gastos si es necesario
    df_gastos_grouped = df_gastos.groupby("Periodo")["Monto"].sum().reset_index()
    df_gastos_grouped.columns = ["Periodo", "Gastos"]

    # Unir ingresos y gastos
    df_comparado = pd.merge(df_gastos_grouped, df_ingresos_grouped, on="Periodo", how="outer").fillna(0)


    # 🔁 Usar fecha de Check-in para ubicar ingresos en el periodo correcto
    df_ingresos["Check-in"] = pd.to_datetime(df_ingresos["Check-in"], errors="coerce")

    # Filtrar solo bookings pagados
    df_ingresos = df_ingresos[df_ingresos["Estado"].str.lower() == "pagado"]

    # Agrupar ingresos por periodo usando Check-in
    if periodo == "Semanal":
        df_ingresos["Periodo"] = df_ingresos["Check-in"].dt.to_period("W").dt.start_time
    elif periodo == "Mensual":
        df_ingresos["Periodo"] = df_ingresos["Check-in"].dt.to_period("M").dt.to_timestamp()
    else:
        df_ingresos["Periodo"] = df_ingresos["Check-in"].dt.to_period("Y").dt.to_timestamp()

    df_ingresos_grouped = df_ingresos.groupby("Periodo")["Precio"].sum().reset_index()
    df_ingresos_grouped.columns = ["Periodo", "Ingresos"]

    df_comparado = df_comparado.sort_values("Periodo")
    df_comparado["PeriodoStr"] = df_comparado["Periodo"].dt.strftime({
        "Semanal": "%d %b",
        "Mensual": "%b",
        "Anual": "%Y"
    }[periodo])

    # Calcular mes actual
    mes_actual = pd.Timestamp.today().to_period("M").to_timestamp()

    # Filtrar solo semanas del mes actual
    if periodo == "Semanal":
        df_comparado = df_comparado[df_comparado["Periodo"].dt.to_period("M").dt.to_timestamp() == mes_actual]


    # === 3. Gráfico Ingresos vs Gastos ===
    df_melted = df_comparado.melt(
        id_vars="PeriodoStr",
        value_vars=["Gastos", "Ingresos"],
        var_name="Tipo",
        value_name="Valor"
    )

    comparativo = alt.Chart(df_melted).mark_line(point=True).encode(
        x=alt.X("PeriodoStr:N", title="Periodo"),
        y=alt.Y("Valor:Q", title="Total $AUD"),
        color=alt.Color("Tipo:N", scale=alt.Scale(domain=["Gastos", "Ingresos"], range=["#e60073", "#10b981"])),
        tooltip=["PeriodoStr", "Tipo", "Valor"]
    ).properties(
        height=300,
        width="container",
        title="📊 Ingresos vs Gastos"
    ).configure_axis(
        labelColor="#ccc", titleColor="#00ffe1"
    ).configure_title(color="#00ffe1").configure_view(stroke=None)

    st.altair_chart(comparativo, use_container_width=True)


    # === GASTOS VARIABLES AUTOMÁTICOS (SEMANAL + EDITABLE) ===
    st.markdown("## 🧼 Gastos variables semanales (automáticos y manuales)")

    hoy = pd.Timestamp.today()
    inicio_semana = hoy.to_period("W").start_time
    fin_semana = inicio_semana + pd.Timedelta(days=6)

    TARIFA_HORA_STAFF = 30  # Tarifa global para Staff por hora

    # === LIMPIAR DOCUMENTOS INCOMPLETOS (si los hay) ===
    docs_clean = db.collection("gastos_variables").where("Semana", "==", inicio_semana).stream()
    for doc in docs_clean:
        doc_data = doc.to_dict()
        if "Tipo" in doc_data and "Monto" in doc_data and "Laundry" not in doc_data:
            db.collection("gastos_variables").document(doc.id).delete()

    # === GENERAR GASTOS VARIABLES DETALLADOS SI NO EXISTEN ===
    df["Check-out"] = pd.to_datetime(df["Check-out"], errors="coerce")
    df["Habitación"] = df["Habitación"].fillna("Desconocida")
    df["Propiedad"] = df["Propiedad"].fillna("No asignada")

    df_semana = df[
        (df["Check-out"] >= inicio_semana) &
        (df["Check-out"] <= fin_semana)
    ]

    for _, row in df_semana.iterrows():
        habitacion = row.get("Habitación", "Desconocida")
        propiedad = row.get("Propiedad", "No asignada")
        fecha_checkout = row["Check-out"]

        existe = db.collection("gastos_variables")\
            .where("Semana", "==", inicio_semana)\
            .where("CheckOut", "==", fecha_checkout)\
            .where("Habitacion", "==", habitacion)\
            .limit(1).stream()

        if not any(existe):
            laundry = 20
            staff_horas_valor = 2.0  # horas reales
            materiales = 15
            amenities = 10
            reposicion = 5
            transporte = 15
            total = laundry + (staff_horas_valor * TARIFA_HORA_STAFF) + materiales + amenities + reposicion + transporte

            gasto = {
                "Semana": inicio_semana,
                "Propiedad": propiedad,
                "Habitacion": habitacion,
                "Laundry": laundry,
                "StaffHoras": staff_horas_valor,  # ← Correcto
                "Materiales": materiales,
                "Amenities": amenities,
                "Reposicion": reposicion,
                "Transporte": transporte,
                "Total": total,
                "CheckOut": fecha_checkout,
                "Fuente": "Automático",
                "Creado": pd.Timestamp.now()
            }
            db.collection("gastos_variables").add(gasto)

    # === CARGAR DATOS ACTUALES ===
    docs_var = db.collection("gastos_variables").where("Semana", "==", inicio_semana).stream()
    data_var = [doc.to_dict() | {"id": doc.id} for doc in docs_var]
    df_var = pd.DataFrame(data_var)

    if df_var.empty:
        st.info("No hay gastos variables registrados para esta semana.")
    else:
        columnas_ordenadas = [
            "Propiedad", "Habitacion", "Laundry", "StaffHoras", "Materiales", "Amenities", "Reposicion", "Transporte", "Total", "Fuente"
        ]

        # Calcular de nuevo el total para visualizar correctamente
        df_var["Total"] = (
            df_var["Laundry"].astype(float) +
            (df_var["StaffHoras"].astype(float) * TARIFA_HORA_STAFF) +
            df_var["Materiales"].astype(float) +
            df_var["Amenities"].astype(float) +
            df_var["Reposicion"].astype(float) +
            df_var["Transporte"].astype(float)
        )

        # Aplicar formato monetario
        for col in ["Laundry", "Materiales", "Amenities", "Reposicion", "Transporte", "Total"]:
            df_var[col] = df_var[col].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "$0.00")

        # Mostrar StaffHoras sin formato monetario
        df_var["StaffHoras"] = df_var["StaffHoras"].apply(lambda x: f"{x:.1f} h" if pd.notnull(x) else "0.0 h")

        st.dataframe(df_var[columnas_ordenadas], use_container_width=True)


    # === NUEVA TABLA: Beneficio neto por período ===
    st.markdown("## 🧾 Beneficio neto por período")

    # === Cálculo de ingresos diarios proporcional (ya lo tienes correcto arriba) ===
    df_ingresos_expandido = []

    df_ingresos = obtener_datos()
    df_ingresos = df_ingresos[df_ingresos["Estado"].str.lower().isin(["pagado", "pendiente"])]


    for _, row in df_ingresos.iterrows():
        start = pd.to_datetime(row["Check-in"])
        end = pd.to_datetime(row["Check-out"])
        total_dias = (end - start).days
        if total_dias <= 0:
            continue
        ingreso_diario = row["Precio"] / total_dias

        for i in range(total_dias):
            dia = start + pd.Timedelta(days=i)
            if periodo == "Semanal":
                periodo_dia = dia.to_period("W").start_time
            elif periodo == "Mensual":
                periodo_dia = dia.to_period("M").to_timestamp()
            else:
                periodo_dia = dia.to_period("Y").to_timestamp()

            df_ingresos_expandido.append({
                "Periodo": periodo_dia,
                "Ingreso_dia": ingreso_diario
            })

    df_ingresos_diarios = pd.DataFrame(df_ingresos_expandido)
    df_ingresos_grouped = df_ingresos_diarios.groupby("Periodo")["Ingreso_dia"].sum().reset_index()
    df_ingresos_grouped.columns = ["Periodo", "Ingresos"]

    # === Agrupar gastos ===
    df_gastos_grouped = df_gastos.groupby("Periodo")["Monto"].sum().reset_index()
    df_gastos_grouped.columns = ["Periodo", "Gastos"]

    # === Calcular beneficio neto ===
    df_beneficio = pd.merge(df_ingresos_grouped, df_gastos_grouped, on="Periodo", how="outer").fillna(0)
    df_beneficio["Beneficio neto"] = df_beneficio["Ingresos"] - df_beneficio["Gastos"]

    # === Calcular porcentaje beneficio neto
    df_beneficio["% Beneficio neto"] = df_beneficio.apply(
        lambda row: (row["Beneficio neto"] / row["Ingresos"] * 100) if row["Ingresos"] > 0 else 0,
        axis=1
    )

    # === Agregar columna de mes para filtrar
    df_beneficio["MesFiltro"] = df_beneficio["Periodo"].dt.to_period("M").dt.to_timestamp()
    meses_disponibles = df_beneficio["MesFiltro"].sort_values(ascending=False).unique()
    mes_actual = pd.Timestamp.today().to_period("M").to_timestamp()

    # === Filtro de mes
    mes_seleccionado = st.selectbox("📅 Selecciona el mes:", meses_disponibles, index=list(meses_disponibles).index(mes_actual))

    df_filtrado = df_beneficio[df_beneficio["MesFiltro"] == mes_seleccionado]

    # === Formato de periodo legible
    if periodo == "Semanal":
        df_filtrado["PeriodoStr"] = df_filtrado["Periodo"].dt.strftime("%d %b") + " – " + (
            df_filtrado["Periodo"] + pd.Timedelta(days=6)
        ).dt.strftime("%d %b")
    else:
        df_filtrado["PeriodoStr"] = df_filtrado["Periodo"].dt.strftime({
            "Mensual": "%b %Y",
            "Anual": "%Y"
        }[periodo])

    # Añadir columna de % beneficio neto si hay ingresos
    df_filtrado["Beneficio %"] = df_filtrado.apply(
        lambda row: ((row["Beneficio neto"] / row["Ingresos"]) * 100) if row["Ingresos"] > 0 else 0,
        axis=1
    )


    # === Mostrar tabla final con símbolos y formato ===
    df_tabla_beneficio = df_filtrado[["PeriodoStr", "Ingresos", "Gastos", "Beneficio neto", "Beneficio %"]].rename(columns={
        "PeriodoStr": "🗓️ Periodo",
        "Ingresos": "💰 Ingresos",
        "Gastos": "🌿 Gastos",
        "Beneficio neto": "📈 Beneficio neto",
        "Beneficio %": "📊 % Beneficio neto"
    })

    # Aplicar formato a moneda y porcentaje
    df_tabla_beneficio["💰 Ingresos"] = df_tabla_beneficio["💰 Ingresos"].apply(lambda x: f"${x:,.2f}")
    df_tabla_beneficio["🌿 Gastos"] = df_tabla_beneficio["🌿 Gastos"].apply(lambda x: f"${x:,.2f}")
    df_tabla_beneficio["📈 Beneficio neto"] = df_tabla_beneficio["📈 Beneficio neto"].apply(lambda x: f"${x:,.2f}")
    df_tabla_beneficio["📊 % Beneficio neto"] = df_tabla_beneficio["📊 % Beneficio neto"].apply(lambda x: f"{x:.1f}%")

    # Mostrar tabla
    try:
        import ace_tools as tools
        tools.display_dataframe_to_user("📊 Beneficio neto por período", df_tabla_beneficio)
    except:
        st.dataframe(df_tabla_beneficio, use_container_width=True)

    st.dataframe(df_var[columnas_ordenadas], use_container_width=True)


    # === INFOGRAFÍA: Bookings filtrables por período ===
    st.markdown("## 📆 Bookings del mes actual")

    # Opciones de período
    opcion_periodo = st.selectbox(
        "🕓 Filtrar por período:",
        ["Mes actual", "Mes anterior", "Últimas 4 semanas", "Últimos 3 meses", "Todos"]
    )

    hoy = pd.Timestamp.today()

    # Agregar columna "Mes" para referencia
    df["Mes"] = df["Check-in"].dt.to_period("M").dt.to_timestamp()

    # Aplicar filtro por fecha
    if opcion_periodo == "Mes actual":
        fecha_inicio = hoy.to_period("M").to_timestamp()
        df_filtrado = df[df["Mes"] == fecha_inicio]
    elif opcion_periodo == "Mes anterior":
        fecha_inicio = (hoy - pd.DateOffset(months=1)).to_period("M").to_timestamp()
        df_filtrado = df[df["Mes"] == fecha_inicio]
    elif opcion_periodo == "Últimas 4 semanas":
        fecha_inicio = hoy - pd.DateOffset(weeks=4)
        df_filtrado = df[df["Check-in"] >= fecha_inicio]
    elif opcion_periodo == "Últimos 3 meses":
        fecha_inicio = hoy - pd.DateOffset(months=3)
        df_filtrado = df[df["Check-in"] >= fecha_inicio]
    else:
        df_filtrado = df.copy()

    # Verificar si hay datos
    if df_filtrado.empty:
        st.info("No hay bookings registrados para este período.")
    else:
        # Columnas calculadas
        df_filtrado["Gasto variable"] = 120
        df_filtrado["Ingreso neto"] = df_filtrado["Precio"] - df_filtrado["Gasto variable"]
        df_filtrado["Check-in"] = df_filtrado["Check-in"].dt.strftime("%d %b")
        df_filtrado["Check-out"] = df_filtrado["Check-out"].dt.strftime("%d %b")

        # Selección de columnas para mostrar
        df_tabla = df_filtrado[[
            "Huesped", "Propiedad", "Habitación", "Check-in", "Check-out",
            "Precio", "Gasto variable", "Ingreso neto", "Estado", "Canal"
        ]].rename(columns={
            "Huesped": "👤 Huésped",
            "Propiedad": "🏠 Propiedad",
            "Habitación": "🛏️ Habitación",
            "Check-in": "📅 Check-in",
            "Check-out": "📅 Check-out",
            "Precio": "💰 Ingreso",
            "Gasto variable": "💸 Gasto variable",
            "Ingreso neto": "📈 Ingreso neto",
            "Estado": "💳 Estado",
            "Canal": "🌐 Canal"
        })

        df_tabla = df_tabla.sort_values("📅 Check-in")

        # Mostrar tabla
        try:
            import ace_tools as tools
            tools.display_dataframe_to_user("📊 Bookings filtrados", df_tabla)
        except:
            st.dataframe(df_tabla, use_container_width=True)


#DETALLES

from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from streamlit_js_eval import streamlit_js_eval  # 👈 asegúrate de tener esto instalado

with tabs[4]:
    st.markdown("## BOOKINGS")
    

    # Detectar ancho del navegador
    width = streamlit_js_eval(js_expressions="screen.width", key="width_key")

    from streamlit_js_eval import streamlit_js_eval

    # Detectar si el fondo real del navegador es oscuro
    bg_color = streamlit_js_eval(js_expressions="getComputedStyle(document.body).backgroundColor", key="bg_color_key") or ""
    modo_oscuro = "rgb(0" in bg_color or "black" in bg_color  # Heurística simple

    fondo_color = "#0f1115" if modo_oscuro else "#FFFFFF"
    texto_color = "white" if modo_oscuro else "black"
    anotacion_fondo = "rgba(0,0,0,0.3)" if modo_oscuro else "rgba(240,240,240,0.9)"
    anotacion_borde = "white" if modo_oscuro else "black"


    # Ajuste dinámico de altura
    if width and width < 600:
        chart_height = 750  # móvil
    elif width and width < 1000:
        chart_height = 640  # tablet
    else:
        chart_height = 580  # escritorio

    campos = ["Check-in", "Check-out", "Habitación", "Huesped", "Precio"]
    df = obtener_datos()
    df_gantt = df[campos].dropna().copy()

    df_gantt["Check-in"] = pd.to_datetime(df_gantt["Check-in"])
    df_gantt["Check-out"] = pd.to_datetime(df_gantt["Check-out"])
    hoy = pd.to_datetime("today")

    df_gantt["Estado"] = df["Estado"].str.lower().map({
        "pagado": "Actual-Pagada",
        "pendiente": "Futura-Pendiente"
    })

    df_gantt["EstadoTexto"] = df_gantt["Estado"].map({
        "Actual-Pagada": "✅ Pagado",
        "Futura-Pendiente": "⏳ Pendiente"
    })

    df_gantt["Tooltip"] = df_gantt.apply(
        lambda r: f"<b>{r['Huesped']}</b><br>Habitación: {r['Habitación']}<br>Precio: ${r['Precio']:,.2f}<br>{r['Check-in'].date()} → {r['Check-out'].date()}<br>{r['EstadoTexto']}",
        axis=1
    )

    color_map = {
    "Actual-Pagada": "#00ffe1",       # Aqua neón
    "Futura-Pendiente": "#e60073"     # Fucsia vibrante
}


    fig = px.timeline(
        df_gantt,
        x_start="Check-in",
        x_end="Check-out",
        y="Habitación",
        color="Estado",
        color_discrete_map=color_map,
        custom_data=["Tooltip"]
    )

    fig.update_traces(
        marker_line_color="#111",
        marker_line_width=1,
        hovertemplate="%{customdata[0]}<extra></extra>"
    )

    # Alternar etiquetas
    for habitacion in df_gantt["Habitación"].unique():
        reservas = df_gantt[df_gantt["Habitación"] == habitacion].sort_values("Check-in")
        alturas_ocupadas = []
        for _, r in reservas.iterrows():
            inicio, fin = r["Check-in"], r["Check-out"]
            center_date = inicio + (fin - inicio) / 2

            for yshift in [60, -60, 100, -100, 140, -140]:
                disponible = all(not (
                    (inicio <= o["fin"]) and (fin >= o["inicio"]) and (o["yshift"] == yshift)
                ) for o in alturas_ocupadas)
                if disponible:
                    alturas_ocupadas.append({"inicio": inicio, "fin": fin, "yshift": yshift})
                    break

            text = (
    f"<b style='color:#00ffe1'>{r['Huesped']}</b><br>"
    f"<span style='color:#ccc;'>💲 ${r['Precio']:,.0f}</span><br>"
    f"<span style='color:#aaa;'>📅 {r['Check-in'].strftime('%d %b')} → {r['Check-out'].strftime('%d %b')}</span><br>"
    f"<span style='color:#999;'>{r['EstadoTexto']}</span>"
)

            fig.add_annotation(
                x=center_date,
                y=r["Habitación"],
                yshift=yshift,
                text=text,
                showarrow=False,
                align="center",
                font=dict(color=texto_color, size=12),
                bgcolor="#101828",
                borderpad=6,
                bordercolor="#00ffe1",
                borderwidth=1
            )


    min_fecha = df_gantt["Check-in"].min() - pd.Timedelta(days=1)
    max_fecha = df_gantt["Check-out"].max() + pd.Timedelta(days=1)

    fig.update_layout(
        height=chart_height,
        xaxis_title="",
        yaxis_title="Habitación",
        xaxis=dict(
            tickformat="%a %d",
            tickangle=0,
            tickfont=dict(size=11),
            side="top",
            range=[min_fecha, max_fecha]
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(size=12),
            automargin=True
        ),
        plot_bgcolor="#0f1115",
        paper_bgcolor="#0f1115",
        font=dict(color="#ccc"),
        legend_title_text="Tipo de reserva",
        margin=dict(l=30, r=30, t=60, b=30)
    )

    fig.add_vline(
        x=hoy,
        line_dash="dot",
        line_color="#00ffe1",
        line_width=2
    )

    st.plotly_chart(fig, use_container_width=True)


    




# ====================================================================================================
# === TAB DETALLES ===================================================================================
# ====================================================================================================

with tabs[4]:
    # Esta sección permite analizar a fondo los bookings, filtrando por estado ('pagado', 'pendiente'), fechas, etc.
    st.subheader("📊 Análisis Detallado de Bookings")

    # Filtro por estado
    estado_filtro = st.multiselect("Estado de reserva", ["pagado", "pendiente"], default=["pagado", "pendiente"])

    # Filtro por mes
    meses_disponibles = df["Mes"].dropna().sort_values().unique()
    mes_filtro = st.selectbox("Filtrar por mes", opciones := list(meses_disponibles.astype(str)))

    # Filtrar el DataFrame
    df_filtrado = df[
        (df["Estado"].isin(estado_filtro)) &
        (df["Mes"].astype(str) == mes_filtro)
    ].copy()

    # Agrupar por propiedad o habitación
    resumen = df_filtrado.groupby("Habitación")["Precio"].sum().reset_index().sort_values("Precio", ascending=False)

    st.markdown("### 💸 Ingresos por habitación")
    st.bar_chart(resumen.set_index("Habitación"))

    # Mostrar tabla de reservas filtradas
    st.markdown("### 📋 Reservas del mes filtrado")
    st.dataframe(df_filtrado[["Check-in", "Check-out", "Huesped", "Habitación", "Precio", "Estado"]], use_container_width=True)

    # ====================================================================================================
# === TAB EXPANSIÓN ==================================================================================
# ====================================================================================================
with tabs[5]:
    st.markdown("<h2 style='color:#00ffe1;'>🔮 MODO EXPANSIÓN</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#ccc;'>Proyecta el impacto de agregar nuevas habitaciones a tu operación usando datos reales actuales.</p>", unsafe_allow_html=True)
    st.markdown("---")

    # === SELECTORES DE SIMULACIÓN ===
    nuevas_habitaciones = st.slider("Número de habitaciones nuevas", 1, 10, 2)
    periodo = st.selectbox("Periodo de análisis", ["Semanal", "Mensual"])

    

    # === RECONSTRUIR OCUPACIÓN DE LA SEMANA ACTUAL ===
    df_ocupacion_dias = calcular_ocupacion(df, inicio_semana, fin_semana)
    dias_semana = 7
    habitaciones = df["Habitación"].dropna().unique()
    ocupacion_resumen = pd.DataFrame({
        "Habitación": habitaciones,
        "Ocupado (días)": [df_ocupacion_dias[df_ocupacion_dias["Habitación"] == h].shape[0] for h in habitaciones]
    })
    ocupacion_resumen["Ocupado (%)"] = (ocupacion_resumen["Ocupado (días)"] / dias_semana) * 100


    # === DATOS BASE ACTUALES ===
    ocupacion_actual = ocupacion_resumen["Ocupado (días)"].sum() / (7 * habitaciones_activas) if habitaciones_activas > 0 else 0
    ingreso_diario_promedio = ingresos / (ocupacion_resumen["Ocupado (días)"].sum()) if ocupacion_resumen["Ocupado (días)"].sum() > 0 else 0
    gasto_diario_por_habitacion = gastos_periodo / (7 * habitaciones_activas) if habitaciones_activas > 0 else 0

    

    # === PROYECCIÓN EXPANDIDA ===
    dias = 7 if periodo == "Semanal" else 30

    nuevas_ocupaciones = nuevas_habitaciones * dias * ocupacion_actual
    ingreso_proyectado = nuevas_ocupaciones * ingreso_diario_promedio
    gasto_proyectado = nuevas_ocupaciones * gasto_diario_por_habitacion
    beneficio_estimado = ingreso_proyectado - gasto_proyectado
    beneficio_pct = (beneficio_estimado / ingreso_proyectado) * 100 if ingreso_proyectado > 0 else 0
    color = "#10b981" if beneficio_estimado >= 0 else "#ef4444"

    # === MOSTRAR RESULTADOS ===
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div style='background-color:#111827; padding:20px; border-radius:12px; text-align:center'>
            <span style='color:#ccc;'>Ingreso proyectado</span><br>
            <span style='font-size:24px; font-weight:bold; color:#00ffe1;'>${ingreso_proyectado:,.2f}</span>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style='background-color:#111827; padding:20px; border-radius:12px; text-align:center'>
            <span style='color:#ccc;'>Gasto proyectado</span><br>
            <span style='font-size:24px; font-weight:bold; color:#00ffe1;'>${gasto_proyectado:,.2f}</span>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style='background-color:#111827; padding:20px; border-radius:12px; text-align:center'>
            <span style='color:#ccc;'>Beneficio estimado</span><br>
            <span style='font-size:24px; font-weight:bold; color:{color};'>{beneficio_pct:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)

        # === INSIGHT DE IMPACTO EXPANSIVO ===
    variacion = beneficio_estimado
    icono = "📈" if variacion >= 0 else "📉"
    verbo = "aumentar" if variacion >= 0 else "reducir"
    color_monto = "#10b981" if variacion >= 0 else "#ef4444"

    insight_expansion = f"""
    <div class="expansion-insight">
        <div class="expansion-title">📊 INSIGHT DE EXPANSIÓN</div>
        <p>{icono} Si agregas <strong>{nuevas_habitaciones}</strong> habitaciones en modalidad <em>{periodo.lower()}</em>, podrías <strong>{verbo}</strong> tu beneficio neto en:</p>
        <p style="font-size: 20px; font-weight: bold; color: {color_monto}; margin-top: 5px;">${variacion:,.2f} AUD</p>
        <p style="color:#888; font-size:13px; margin-top:8px;">Simulación basada en tu ocupación y rentabilidad promedio actuales.</p>
    </div>
    """

    st.markdown(insight_expansion, unsafe_allow_html=True)

    # === ESTILO VISUAL DEL INSIGHT DE EXPANSIÓN ===
    st.markdown("""
    <style>
    .expansion-insight {
        background-color: #0f1115;
        border: 1px solid #00ffe180;
        border-radius: 14px;
        padding: 20px;
        margin-top: 30px;
        text-align: center;
        box-shadow: 0 0 20px #00ffe120;
    }
    .expansion-title {
        color: #00ffe1;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 15px;
        margin-bottom: 10px;
        letter-spacing: 1px;
    }
    </style>
    """, unsafe_allow_html=True)

    # === GRÁFICO DE ESCENARIOS DE EXPANSIÓN ===

    # Proyección para 3 escenarios (1, 2 y 3 nuevas habitaciones)
    escenarios = [1, 2, 3]
    beneficios = []

    for n in escenarios:
        nuevas_ocupaciones = n * dias * ocupacion_actual
        ingreso_proy = nuevas_ocupaciones * ingreso_diario_promedio
        gasto_proy = nuevas_ocupaciones * gasto_diario_por_habitacion
        beneficio = ingreso_proy - gasto_proy
        beneficios.append(beneficio)

    df_escenarios = pd.DataFrame({
        "Escenario": [f"{i} Habitación{'es' if i > 1 else ''}" for i in escenarios],
        "Beneficio neto estimado ($)": beneficios
    })

    # Crear gráfico horizontal
    chart = alt.Chart(df_escenarios).mark_bar(size=40).encode(
        y=alt.Y("Escenario:N", title="Expansión simulada", sort="-x"),
        x=alt.X("Beneficio neto estimado ($):Q", title="$ AUD"),
        color=alt.value("#10b981"),
        tooltip=["Escenario", "Beneficio neto estimado ($)"]
    ).properties(
        height=240,
        background="#0f1115",
        title="Proyección de beneficio neto según número de habitaciones nuevas"
    ).configure_axis(
        labelColor="#ccc",
        titleColor="#00ffe1"
    ).configure_view(
        stroke=None
    ).configure_title(
        color="#00ffe1",
        anchor="start"
    )

    st.altair_chart(chart, use_container_width=True)


    

