# ====================================================================================================
# === TAB CALENDARIO ===================================================================================
# ====================================================================================================

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

    # === Selector de mes ===
    meses_disponibles = pd.date_range(
        df_gantt["Check-in"].min(), df_gantt["Check-out"].max(), freq="MS"
    ).to_period("M").unique()

    mes_seleccionado = st.selectbox(
        "📆 Elegir mes a visualizar",
        options=[str(m) for m in meses_disponibles],
        index=len(meses_disponibles)-1  # el más reciente por defecto
    )

    # Filtrar dataframe por el mes seleccionado
    inicio_mes = pd.to_datetime(f"{mes_seleccionado}-01")
    fin_mes = inicio_mes + pd.offsets.MonthEnd(0)

    df_gantt = df_gantt[
        (df_gantt["Check-in"] <= fin_mes) & (df_gantt["Check-out"] >= inicio_mes)
]


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