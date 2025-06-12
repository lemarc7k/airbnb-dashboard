import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
import plotly.express as px
from firebase_config import db


def mostrar_inversion(df_inv, df_gas, df_res):
    if df_inv is None or df_gas is None or df_res is None:
        st.warning("⚠️ No se pudieron cargar los datos.")
        return






# ========================
# PANEL DE INVERSIÓN
# ========================
    st.markdown("""
        <style>
        .metric-card {
            background-color: #0f1115;
            border: 1px solid #00ffe1;
            border-radius: 14px;
            padding: 25px;
            font-family: 'Segoe UI', sans-serif;
            color: white;
            box-shadow: 0 0 20px #00ffe130;
            text-align: center;
        }
        .metric-card h3 {
            margin: 0;
            font-size: 16px;
            color: #ccc;
        }
        .metric-card p {
            margin: 5px 0 0;
            font-size: 22px;
            font-weight: bold;
            color: #00ffe1;
        }
        </style>
    """, unsafe_allow_html=True)

    # === FORMULARIO PARA NUEVA INVERSIÓN ===
    with st.expander("➕ Registrar Nueva Inversión"):
        with st.form("form_inversion"):
            st.subheader("📍 Datos de la Inversión")
            col1, col2 = st.columns(2)
            with col1:
                propiedad = st.text_input("🏠 Propiedad")
                monto_inicial = st.number_input("💰 Monto Inicial (AUD)", min_value=0.0, step=100.0)
                fianza = st.number_input("🔒 Fianza (AUD)", min_value=0.0, step=100.0)
            with col2:
                muebles = st.number_input("🛋️ Muebles (AUD)", min_value=0.0, step=100.0)
                fecha = st.date_input("📅 Fecha", value=datetime.today())

            st.markdown("---")
            st.subheader("🧾 Gastos Fijos Mensuales")
            col3, col4 = st.columns(2)
            with col3:
                renta = st.number_input("🏡 Alquiler mensual", min_value=0.0, step=10.0)
                luz = st.number_input("💡 Electricidad", min_value=0.0, step=10.0)
            with col4:
                agua = st.number_input("🚿 Agua", min_value=0.0, step=10.0)
                internet = st.number_input("🌐 Internet", min_value=0.0, step=10.0)

            submit = st.form_submit_button("✅ Registrar Inversión + Gastos")
            if submit and propiedad:
                nombre_prop = propiedad.strip().title()

                db.collection("inversiones").add({
                    "Propiedad": nombre_prop,
                    "Monto_inicial": monto_inicial,
                    "Fianza": fianza,
                    "Muebles": muebles,
                    "Fecha": str(fecha)
                })

                db.collection("gastos_fijos").add({
                    "Propiedad": nombre_prop,
                    "Alquiler": renta,
                    "Luz": luz,
                    "Agua": agua,
                    "Internet": internet
                })

                st.success("✅ Inversión y gastos registrados correctamente.")
                st.rerun()

    

    if df_inv.empty:
        st.warning("⚠️ No hay inversiones registradas.")
        return

    
    # === ENCABEZADO ===
    st.markdown("<h3 style='text-align:center; color:#00ffe1;'>BIENVENIDO MR VERA</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888;'>Estas son las inversiones activas gestionadas en Airbnb</p>", unsafe_allow_html=True)
    
    # === TABLA DETALLADA EN MODO OSCURO ===
    st.markdown("INVERSIONES")

    df_tabla = df_inv[["Propiedad", "Monto_inicial", "Fianza", "Muebles", "Fecha"]].copy()
    df_tabla["Total"] = df_tabla[["Monto_inicial", "Fianza", "Muebles"]].sum(axis=1)
    df_tabla["Fecha"] = pd.to_datetime(df_tabla["Fecha"]).dt.strftime("%d %b %Y")
    df_tabla = df_tabla.rename(columns={
        "Propiedad": "🏠 Propiedad",
        "Monto_inicial": "💰 Monto Inicial",
        "Fianza": "🔒 Fianza",
        "Muebles": "🛋️ Muebles",
        "Fecha": "📅 Fecha",
        "Total": "📊 Total Inversión"
    })

    for col in ["💰 Monto Inicial", "🔒 Fianza", "🛋️ Muebles", "📊 Total Inversión"]:
        df_tabla[col] = df_tabla[col].apply(lambda x: f"${x:,.0f}")


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
        margin: 0;
    }}
    .dark-table th {{
        background-color: #1e1e21;
        color: #00ffe1;
        padding: 10px;
        text-align: center;
        border-bottom: 1px solid #333;
        position: sticky;
        top: 0;
        z-index: 1;
    }}
    .dark-table td {{
        padding: 8px;
        text-align: center;
        border-bottom: 1px solid #222;
    }}
    .table-wrapper {{
        margin: 0;
        padding: 15px 25px;
        background-color:#0f1115;
        border-radius: 14px;
        box-shadow: 0 0 20px #00ffe120;
        overflow-x: auto;
    }}
    </style>
    <div class="table-wrapper">
        {html_table}
    </div>
    """


    components.html(html_render, height=min(200 + 10 * len(df_tabla), 400), scrolling=True)




    
    # === TABLA DETALLADA DE GASTOS FIJOS EN MODO OSCURO ===
    st.markdown("GASTOS FIJOS")

    if not df_gas.empty:
        df_gastos = df_gas[["Propiedad", "Alquiler", "Luz", "Agua", "Internet"]].copy()
        df_gastos["Total Mensual"] = df_gastos[["Alquiler", "Luz", "Agua", "Internet"]].sum(axis=1)
        df_gastos = df_gastos.rename(columns={
            "Propiedad": "🏠 Propiedad",
            "Alquiler": "💸 Alquiler",
            "Luz": "💡 Electricidad",
            "Agua": "🚿 Agua",
            "Internet": "🌐 Internet",
            "Total Mensual": "📊 Total mensual"
        })

        for col in ["💸 Alquiler", "💡 Electricidad", "🚿 Agua", "🌐 Internet", "📊 Total mensual"]:
            df_gastos[col] = df_gastos[col].apply(lambda x: f"${x:,.0f}")

        html_gastos = df_gastos.to_html(index=False, classes="dark-table", border=0)

        html_render_gastos = f"""
        <style>
        .dark-table {{
            width: 100%;
            border-collapse: collapse;
            background-color: #111827;
            color: #ccc;
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
            margin: 0;
        }}
        .dark-table th {{
            background-color: #1e1e21;
            color: #00ffe1;
            padding: 10px;
            text-align: center;
            border-bottom: 1px solid #333;
            position: sticky;
            top: 0;
            z-index: 1;
        }}
        .dark-table td {{
            padding: 8px;
            text-align: center;
            border-bottom: 1px solid #222;
        }}
        .table-wrapper {{
            margin: 0;
            padding: 15px 25px;
            background-color:#0f1115;
            border-radius: 14px;
            box-shadow: 0 0 20px #00ffe120;
            overflow-x: auto;
        }}
        </style>
        <div class="table-wrapper">
            {html_gastos}
        </div>
        """

        components.html(html_render_gastos, height=min(200 + 10 * len(df_gastos), 400), scrolling=True)

    else:
        st.info("ℹ️ Aún no hay gastos fijos registrados.")



    # === CONTROLES DE EDICIÓN Y ELIMINACIÓN ===
    st.markdown("Editar")

    for i, row in df_inv.iterrows():
        with st.expander(f"🏠 {row['Propiedad']} — ${row['Monto_inicial'] + row['Fianza'] + row['Muebles']:,.0f}"):
            col1, col2 = st.columns(2)
            with col1:
                with st.form(f"form_edit_{i}"):
                    nueva_propiedad = st.text_input("🏷️ Propiedad", value=row["Propiedad"])
                    nuevo_monto = st.number_input("💰 Monto Inicial", value=float(row["Monto_inicial"]))
                    nueva_fianza = st.number_input("🔒 Fianza", value=float(row["Fianza"]))
                    nuevos_muebles = st.number_input("🛋️ Muebles", value=float(row["Muebles"]))
                    nueva_fecha = st.date_input("📅 Fecha", value=pd.to_datetime(row["Fecha"]))

                    guardar = st.form_submit_button("💾 Guardar cambios")
                    if guardar:
                        db.collection("inversiones").document(row["doc_id"]).update({
                            "Propiedad": nueva_propiedad.strip().title(),
                            "Monto_inicial": nuevo_monto,
                            "Fianza": nueva_fianza,
                            "Muebles": nuevos_muebles,
                            "Fecha": str(nueva_fecha)
                        })
                        st.success("✅ Cambios guardados.")
                        st.rerun()

            with col2:
                confirmar = st.checkbox(f"❗ Confirmar eliminación {row['Propiedad']}", key=f"confirmar_{i}")
                eliminar = st.button(f"🗑️ Eliminar inversión {row['Propiedad']}", key=f"eliminar_{i}")
                if eliminar and confirmar:
                    db.collection("inversiones").document(row["doc_id"]).delete()
                    st.success("✅ Inversión eliminada.")
                    st.rerun()


    #### ELIMINAR GASTOS FIJOS

    st.markdown("Editar")

    for i, row in df_gas.iterrows():
        with st.expander(f"🏠 {row['Propiedad']} — ${row['Alquiler'] + row['Luz'] + row.get('Agua',0) + row['Internet']:,.0f} / mes"):
            col1, col2 = st.columns(2)
            with col1:
                with st.form(f"form_gasto_{i}"):
                    nueva_prop = st.text_input("🏷️ Propiedad", value=row["Propiedad"])
                    nuevo_alquiler = st.number_input("💸 Alquiler", value=float(row["Alquiler"]))
                    nueva_luz = st.number_input("💡 Electricidad", value=float(row["Luz"]))
                    nueva_agua = st.number_input("🚿 Agua", value=float(row.get("Agua", 0)))
                    nuevo_internet = st.number_input("🌐 Internet", value=float(row["Internet"]))

                    guardar = st.form_submit_button("💾 Guardar cambios")
                    if guardar:
                        db.collection("gastos_fijos").document(row["doc_id"]).update({
                            "Propiedad": nueva_prop.strip().title(),
                            "Alquiler": nuevo_alquiler,
                            "Luz": nueva_luz,
                            "Agua": nueva_agua,
                            "Internet": nuevo_internet
                        })
                        st.success("✅ Cambios guardados.")
                        st.rerun()
            with col2:
                confirmar = st.checkbox(f"❗ Confirmar eliminación gasto {row['Propiedad']}", key=f"confirmar_gasto_{i}")
                eliminar = st.button(f"🗑️ Eliminar gasto {row['Propiedad']}", key=f"eliminar_gasto_{i}")
                if eliminar and confirmar:
                    db.collection("gastos_fijos").document(row["doc_id"]).delete()
                    st.success("✅ Gasto fijo eliminado.")
                    st.rerun()


    



    