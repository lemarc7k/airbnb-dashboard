# ---------- GENERAL ---------- #


# ====================================================================================================
# === TAB GENERAL ===============================================================================
# ====================================================================================================
with tabs[1]:
    # Esta pestaña presenta un resumen mensual de ingresos y niveles de ocupación global con análisis detallado.
    st.subheader("Resumen general")
    total = df["Precio"].sum()
    upcoming = df[df["Check-in"] > hoy]["Precio"].sum()
    mes_actual = pd.Timestamp(hoy).to_period("M").to_timestamp()
    ingreso_mes = df[df["Mes"] == mes_actual]["Precio"].sum()

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
    ).properties(height=300, background="#0f1115")

    chart = chart.configure_view(stroke=None)

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



    # === TABLA DETALLADA (MODO OSCURO SIN iframe) ===
    import streamlit.components.v1 as components

    # === TABLA DETALLADA CON HTML Y CSS FUNCIONANDO ===
    st.markdown("### 📋 Detalle completo por habitación")

    df_tabla = ocupacion_resumen[[ 
        "Habitación", "EsOcupado", "EsFuturo", "Disponible", "TotalDías",
        "Ocupado (%)", "Futuro (%)", "OcupadoFuturo (%)", "Estado general", "Recomendación"
    ]]
    df_tabla.columns = [
        "Habitación", "Noches Ocupadas", "Noches Futuras", "Disponibles", "Total Días",
        "% Ocupado", "% Futuro", "% Total", "Estado", "Recomendación"
    ]

    # Redondear columnas de porcentaje a 2 decimales
    df_tabla["% Ocupado"] = df_tabla["% Ocupado"].round(2)
    df_tabla["% Futuro"] = df_tabla["% Futuro"].round(2)
    df_tabla["% Total"] = df_tabla["% Total"].round(2)


    html_table = df_tabla.to_html(index=False, classes="dark-table", border=0)

    html_render = f"""
    <style>
    .dark-table {{
        width: 100%;
        border-collapse: collapse;
        background-color: #111827;
        color: #ccc;
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
    }}
    .dark-table th {{
        background-color: #1e1e21;
        color: #00ffe1;
        padding: 10px;
        text-align: center;
        border-bottom: 1px solid #333;
    }}
    .dark-table td {{
        padding: 8px;
        text-align: center;
        border-bottom: 1px solid #222;
    }}
    </style>
    <div style="background-color:#0f1115; padding: 15px 25px; border-radius: 14px; box-shadow: 0 0 20px #00ffe120; overflow-x: auto;">
        {html_table}
    </div>
    """

    # Renderizado real del HTML (no como markdown)
    components.html(html_render, height=200, scrolling=True)




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