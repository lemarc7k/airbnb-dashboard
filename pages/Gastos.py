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