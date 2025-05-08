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


# Tabs
tabs = st.tabs(["📊 General", "🏘️ Registrar Reservas", "📈 Evolución", "📝 Propiedades", "📋 Detalles"])

# ---------- GENERAL ---------- #
with tabs[0]:
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
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from streamlit_js_eval import streamlit_js_eval  # 👈 asegúrate de tener esto instalado

with tabs[4]:
    st.markdown("## 🗓️ Calendario visual estilo Gantt (estado y tipo)")

    # Detectar ancho del navegador
    width = streamlit_js_eval(js_expressions="screen.width", key="width_key")

    # Ajuste dinámico de altura
    if width and width < 600:
        chart_height = 750  # móvil
    elif width and width < 1000:
        chart_height = 640  # tablet
    else:
        chart_height = 580  # escritorio

    campos = ["Check-in", "Check-out", "Habitación", "Huesped", "Precio"]
    df = obtener_datos()  # <-- Fuerza recarga de datos actualizados
    df_gantt = df[campos].dropna().copy()


    df_gantt["Check-in"] = pd.to_datetime(df_gantt["Check-in"])
    df_gantt["Check-out"] = pd.to_datetime(df_gantt["Check-out"])
    hoy = pd.to_datetime("today")

    # Leer estado desde la base real
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
        "Actual-Pagada": "#10b981",
        "Futura-Pendiente": "#6b21a8"
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
                f"<b>{r['Huesped']}</b><br>"
                f"💲 ${r['Precio']:,.0f}<br>"
                f"📅 {r['Check-in'].strftime('%d %b')} → {r['Check-out'].strftime('%d %b')}<br>"
                f"{r['EstadoTexto']}"
            )

            fig.add_annotation(
                x=center_date,
                y=r["Habitación"],
                yshift=yshift,
                text=text,
                showarrow=False,
                align="center",
                font=dict(color="white", size=12),
                bgcolor="rgba(0,0,0,0.3)",
                borderpad=5,
                bordercolor="white",
                borderwidth=0.5
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
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="#0f1115",
        paper_bgcolor="#0f1115",
        font=dict(color="white"),
        legend_title="Tipo de reserva",
        margin=dict(l=30, r=30, t=60, b=30)
    )
    fig.update_yaxes(
    categoryorder="category ascending",
    tickfont=dict(size=12),
    automargin=True
)


    fig.add_vline(
        x=hoy,
        line_dash="dot",
        line_color="#00ffe1",
        line_width=2
    )

    st.plotly_chart(fig, use_container_width=True)


    



