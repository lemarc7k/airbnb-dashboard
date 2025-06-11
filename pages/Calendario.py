# ====================================================================================================
# === TAB CALENDARIO ================================================================================  
# ====================================================================================================

from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

def mostrar_calendario(df):
    imagenes_habitaciones = {
        "Room 1": "https://i.ibb.co/LhQJfRYf/CBD-room-1.jpg",
        "Room 2": "https://i.ibb.co/27Nk8R7W/CBD-room-2.jpg",
        "Room 3": "https://i.ibb.co/xF9TQnB/IGW-room-3.jpg",
        "Room 4": "https://i.ibb.co/k2FrrwMp/IGW-room-4.jpg",
        "Room 5": "https://i.ibb.co/yFsWN03/IGW-room-5.jpg",
        "Garaje": "https://i.ibb.co/Xr5DGZ9/CBD-garage.jpg",
        "Garaje 2": "https://i.ibb.co/6nVMR0n/garaje2.png",
    }

    width = streamlit_js_eval(js_expressions="screen.width", key="width_key")
    bg_color = streamlit_js_eval(js_expressions="getComputedStyle(document.body).backgroundColor", key="bg_color_key") or ""
    modo_oscuro = "rgb(0" in bg_color or "black" in bg_color

    modo_oscuro = (
        st.get_option("theme.base") == "dark"
        or "rgb(0" in bg_color.lower()
        or "black" in bg_color.lower()
        or "#000" in bg_color.lower()
)


    fondo_color = "#0f1115" if modo_oscuro else "#FFFFFF"
    texto_color = "white" if modo_oscuro else "black"

    campos = ["Check-in", "Check-out", "Propiedad", "Habitación", "Huesped", "Precio", "Estado"]
    df_gantt = df[campos].dropna().copy()
    df_gantt["Check-in"] = pd.to_datetime(df_gantt["Check-in"])
    df_gantt["Check-out"] = pd.to_datetime(df_gantt["Check-out"])
    hoy = pd.to_datetime("today")

    df_gantt["Linea"] = df_gantt["Propiedad"] + " · " + df_gantt["Habitación"]

    lineas_validas = []
    for _, row in df_gantt.drop_duplicates(subset="Linea").iterrows():
        hab = row["Habitación"]
        if hab in imagenes_habitaciones:
            lineas_validas.append(row["Linea"])

    df_gantt = df_gantt[df_gantt["Linea"].isin(lineas_validas)]
    orden_lineas = sorted(lineas_validas)
    df_gantt["Linea"] = pd.Categorical(df_gantt["Linea"], categories=orden_lineas, ordered=True)

    df_gantt["Estado"] = df_gantt["Estado"].str.lower().map({
        "pagado": "Pagado",
        "pendiente": "Pendiente"
    })

    df_gantt["Tooltip"] = df_gantt.apply(
        lambda r: f"{r['Huesped']} – ${r['Precio'] * ((r['Check-out'] - r['Check-in']).days):,.0f}",
        axis=1
    )

    color_map = {
        "Pagado": "#008489",     # Verde Airbnb
        "Pendiente": "#FF5A5F"   # Rojo Airbnb
    }

    fig = px.timeline(
        df_gantt,
        x_start="Check-in",
        x_end="Check-out",
        y="Linea",
        color="Estado",
        color_discrete_map=color_map,
        custom_data=["Tooltip"]
    )

    fig.update_traces(
        marker_line_color="#151a1f",
        marker_line_width=0.5,
        hovertemplate="<b>%{y}</b><br>%{customdata[0]}<extra></extra>",
        constraintext='both',
        cliponaxis=False
)


    for _, r in df_gantt.iterrows():
        precio_total = r["Precio"] * ((r["Check-out"] - r["Check-in"]).days)
        fig.add_annotation(
            x=r["Check-in"] + (r["Check-out"] - r["Check-in"]) / 2,
            y=r["Linea"],
            text=f"{r['Huesped']} – ${precio_total:.0f}",
            yshift=15,
            showarrow=False,
            font=dict(size=11, color="#fff", family="Segoe UI"),
            bgcolor="rgba(16,24,40,0.9)",
            bordercolor=color_map[r["Estado"]],
            borderwidth=1,
            borderpad=5,
            align="center"
        )


    # Define el rango de fechas ANTES de las imágenes
    min_fecha = df_gantt["Check-in"].min() - pd.Timedelta(days=1)
    max_fecha = df_gantt["Check-out"].max() + pd.Timedelta(days=2)
    # Añadir imágenes directamente al gráfico
    for linea in orden_lineas:
        nombre = linea.split("·")[1].strip()
        url = imagenes_habitaciones.get(nombre)
        if url:
            fig.add_layout_image(
                dict(
                    source=url,
                    xref="x",
                    x=min_fecha - pd.Timedelta(days=1.5),  # Aquí lo has hecho perfecto
                    y=linea,
                    yref="y",
                    yanchor="middle",
                    sizex=1.5,
                    sizey=0.7,
                    xanchor="left",
                    layer="below"
                )
            )


    min_fecha = df_gantt["Check-in"].min() - pd.Timedelta(days=1)
    max_fecha = df_gantt["Check-out"].max() + pd.Timedelta(days=2)
    rango_dias = pd.date_range(min_fecha, max_fecha)

    # Botón para volver a HOY
    if st.button("📍 Volver a HOY"):
        fig.update_layout(xaxis_range=[hoy - pd.Timedelta(days=3), hoy + pd.Timedelta(days=4)])

    for dia in rango_dias:
        is_weekend = dia.weekday() >= 5
        if is_weekend:
            fig.add_vrect(
                x0=dia,
                x1=dia + pd.Timedelta(days=1),
                fillcolor="rgba(200,200,200,0.07)" if not modo_oscuro else "rgba(255,255,255,0.04)",
                line_width=0,
                layer="below"
            )

        fig.add_vline(x=dia, line_color="#333" if modo_oscuro else "#ddd", line_width=0.5, layer="below")

    for yval in range(len(orden_lineas)):
        fig.add_shape(
            type="line",
            x0=min_fecha,
            x1=max_fecha,
            y0=yval + 0.5,
            y1=yval + 0.5,
            line=dict(color="#444" if modo_oscuro else "#ccc", width=0.5),
            xref="x",
            yref="y"
        )
        if yval % 2 == 0:
            fig.add_hrect(
                y0=yval - 0.5,
                y1=yval + 0.5,
                fillcolor="rgba(255,255,255,0.03)" if modo_oscuro else "rgba(0,0,0,0.02)",
                line_width=0,
                layer="below"
            )

    fig.update_layout(
        height=max(600, 100 + 100 * len(orden_lineas)),
        xaxis_title="",
        yaxis_title="",
        xaxis=dict(
            tickformat="%a %d",
            tickangle=0,
            tickfont=dict(size=12),
            side="top",
            range=[min_fecha, max_fecha],
            fixedrange=False,
            showgrid=False
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(size=13),
            showgrid=False
        ),
        plot_bgcolor=fondo_color,
        paper_bgcolor=fondo_color,
        font=dict(color=texto_color, family="Segoe UI"),
        legend_title_text="Estado",
        margin=dict(l=20, r=20, t=60, b=30),
        hovermode="closest"
    )

    fig.add_vline(
        x=hoy,
        line_dash="dot",
        line_color="#00ffe1",
        line_width=2
    )

# Forzar fondo oscuro real del contenedor en Streamlit
    if modo_oscuro:
        st.markdown("""
            <style>
            .element-container:has(.js-plotly-plot) {
                background-color: #0f1115 !important;
                padding: 0.5rem;
                border-radius: 8px;
            }
            </style>
        """, unsafe_allow_html=True)

    st.plotly_chart(fig, use_container_width=True)
