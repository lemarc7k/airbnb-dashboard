   # ====================================================================================================
# === TAB EXPANSIÓN ==================================================================================
# ====================================================================================================
with tabs[5]:
    st.markdown("<h2 style='color:#00ffe1;'>🔮 SIMULACIÓN</h2>", unsafe_allow_html=True)
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

   

    # Estado persistente de las habitaciones
    if "habitaciones_personalizadas" not in st.session_state:
        st.session_state.habitaciones_personalizadas = [
            {"nombre": "Room 1", "precio": 60.0, "ocupacion": 80},
            {"nombre": "Room 2", "precio": 70.0, "ocupacion": 75},
        ]

    # Función para agregar una nueva habitación
    def agregar_habitacion():
        n = len(st.session_state.habitaciones_personalizadas) + 1
        st.session_state.habitaciones_personalizadas.append(
            {"nombre": f"Room {n}", "precio": 65.0, "ocupacion": 70}
        )

    if st.button("➕ Agregar habitación"):
        agregar_habitacion()

    # Mostrar formulario editable
    with st.form("form_simulacion"):
        cols = st.columns([4, 2, 2])
        cols[0].markdown("**Habitación**")
        cols[1].markdown("**Precio por noche ($)**")
        cols[2].markdown("**Ocupación estimada (%)**")

        for i, habitacion in enumerate(st.session_state.habitaciones_personalizadas):
            col1, col2, col3 = st.columns([4, 2, 2])
            habitacion["nombre"] = col1.text_input("Nombre", habitacion["nombre"], key=f"nombre_{i}")
            habitacion["precio"] = col2.number_input("Precio", 20.0, 300.0, habitacion["precio"], step=1.0, key=f"precio_{i}")
            habitacion["ocupacion"] = col3.slider("Ocupación", 0, 100, habitacion["ocupacion"], key=f"ocupacion_{i}")

        periodo = st.selectbox("Periodo de análisis", ["Semanal", "Mensual"], index=0)
        dias = 7 if periodo == "Semanal" else 30

        submitted = st.form_submit_button("🔄 Simular expansión")

    # Cálculo y visualización de resultados
    if submitted:
        habitaciones_data = st.session_state.habitaciones_personalizadas
        gasto_por_habitacion = 25  # Por día por habitación

        ingreso_total = sum(h["precio"] * (h["ocupacion"] / 100) * dias for h in habitaciones_data)
        gasto_total = gasto_por_habitacion * len(habitaciones_data) * dias
        beneficio_total = ingreso_total - gasto_total
        beneficio_pct = (beneficio_total / ingreso_total * 100) if ingreso_total > 0 else 0

        # Estilo de tarjetas
        st.markdown("""
        <style>
        .card-container {
            display: flex;
            justify-content: space-around;
            margin-top: 20px;
            gap: 20px;
        }
        .card {
            background-color: #111827;
            padding: 20px;
            border-radius: 14px;
            text-align: center;
            box-shadow: 0 0 15px #00ffe120;
            flex: 1;
        }
        .card-title {
            color: #ccc;
            font-size: 14px;
            margin-bottom: 6px;
        }
        .card-value {
            font-size: 24px;
            font-weight: bold;
            color: #00ffe1;
        }
        .card-green {
            color: #10b981;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card-container">
            <div class="card">
                <div class="card-title">Ingreso proyectado ({periodo.lower()})</div>
                <div class="card-value">${ingreso_total:,.2f}</div>
            </div>
            <div class="card">
                <div class="card-title">Gasto proyectado ({periodo.lower()})</div>
                <div class="card-value">${gasto_total:,.2f}</div>
            </div>
            <div class="card">
                <div class="card-title">Beneficio neto (%)</div>
                <div class="card-value card-green">{beneficio_pct:.1f}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
