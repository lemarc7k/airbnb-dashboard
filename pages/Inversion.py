import streamlit as st
from firebase_config import db
from datetime import datetime
import pandas as pd

def mostrar_inversion():
    st.markdown("""
        <h2 style='text-align:center; color:#00ffe1;'>📊 ANÁLISIS DE INVERSIÓN</h2>
        <p style='text-align:center; color:#aaa;'>Registra aquí la inversión inicial y los gastos fijos mensuales de cada propiedad</p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    .card-box {
        background-color: #0f172a;
        border: 1px solid #00ffe1;
        border-radius: 14px;
        padding: 25px;
        box-shadow: 0 0 20px #00ffe130;
        margin-bottom: 30px;
    }
    .card-box h4 {
        color: #00ffe1;
    }
    </style>
    """, unsafe_allow_html=True)

     # === Métricas ===
    
    inversiones = db.collection("inversiones").stream()
    gastos = db.collection("gastos_fijos").stream()

    data_inv = []
    for x in inversiones:
        d = x.to_dict()
        d['id'] = x.id
        data_inv.append(d)

    data_gastos = []
    for x in gastos:
        d = x.to_dict()
        d['id'] = x.id
        data_gastos.append(d)

    df_inv = pd.DataFrame(data_inv)
    df_gastos = pd.DataFrame(data_gastos)

    if not df_inv.empty:
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        st.markdown("<h4>📈 Métricas por propiedad</h4>", unsafe_allow_html=True)

        propiedades = df_inv["Propiedad"].unique()
        cols = st.columns(3)
        for i, prop in enumerate(propiedades):
            df_inv_prop = df_inv[df_inv["Propiedad"] == prop]
            df_gastos_prop = df_gastos[df_gastos["Propiedad"] == prop] if not df_gastos.empty and "Propiedad" in df_gastos.columns else pd.DataFrame()
            inv_total = df_inv_prop["Inversion_total"].sum()
            fecha_adq = pd.to_datetime(df_inv_prop["Fecha_adquisicion"].values[0])
            meses_activo = max((datetime.now() - fecha_adq).days // 30, 1)
            gasto_mensual = df_gastos_prop["Gasto_total"].sum() if not df_gastos_prop.empty else 0.0
            gasto_acumulado = gasto_mensual * meses_activo
            total_invertido = inv_total + gasto_acumulado

            with cols[i % 3]:
                st.markdown(f"""
                <div style="background-color:#0f172a; border-radius:16px; box-shadow:0 0 12px #00ffe110;
                            padding:0; margin-bottom:25px; overflow:hidden;">
                    <div style="height:180px; background:#0e172a; border-bottom:1px solid #00ffe120;
                                background-image:url('https://i.ibb.co/LhQJfRYf/CBD-room-1.jpg,{prop}');
                                background-size:cover; background-position:center;"></div>
                    <div style="padding:15px;">
                        <h4 style="color:#00ffe1; margin:0 0 8px 0;">🏡 {prop.upper()}</h4>
                        <p style="color:#ccc; font-size:13px; margin:0;">
                            💰 Inversión inicial: ${inv_total:,.2f}<br>
                            📆 Meses operando: {meses_activo}<br>
                            🧾 Gastos mensuales: ${gasto_mensual:,.2f}<br>
                            📉 Acumulado: ${gasto_acumulado:,.2f}<br>
                            📊 Total invertido: ${total_invertido:,.2f}
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    else:
        st.warning("⚠️ Aún no hay datos de inversión registrados.")

        st.markdown("</div>", unsafe_allow_html=True)

    # === Formulario combinado ===
    with st.container():
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        with st.form("form_inversion_gastos"):
            st.markdown("<h4>🏠 Inversión + Gastos Fijos</h4>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                propiedad = st.text_input("Nombre de la propiedad")
                monto_inicial = st.number_input("Monto total de inversión (adquisición)", min_value=0.0, step=100.0)
                fianza = st.number_input("Fianza pagada (Bond)", min_value=0.0, step=50.0)
                muebles = st.number_input("Muebles y decoración", min_value=0.0, step=50.0)
                alquiler = st.number_input("Alquiler mensual", min_value=0.0, step=50.0)
                limpieza = st.number_input("Limpieza mensual", min_value=0.0, step=10.0)
            with col2:
                fees = st.number_input("Otros fees (legales, comisiones...)", min_value=0.0, step=50.0)
                internet = st.number_input("Internet mensual", min_value=0.0, step=10.0)
                luz = st.number_input("Luz mensual", min_value=0.0, step=10.0)
                otros = st.number_input("Otros gastos mensuales", min_value=0.0, step=10.0)
                fecha_adquisicion = st.date_input("Fecha de adquisición")
                notas = st.text_area("Notas adicionales")

            registrar = st.form_submit_button("💾 Registrar todo")

            if registrar:
                try:
                    total_inversion = monto_inicial + fianza + muebles + fees
                    total_gastos = alquiler + luz + internet + limpieza + otros
                    fecha_actual = datetime.now().isoformat()

                    # Inversión inicial
                    db.collection("inversiones").add({
                        "Propiedad": propiedad,
                        "Monto_inicial": monto_inicial,
                        "Fianza": fianza,
                        "Muebles": muebles,
                        "Fees": fees,
                        "Inversion_total": total_inversion,
                        "Fecha_adquisicion": str(fecha_adquisicion),
                        "Notas": notas,
                        "Fecha_registro": fecha_actual
                    })

                    # Gastos fijos
                    db.collection("gastos_fijos").add({
                        "Propiedad": propiedad,
                        "Alquiler": alquiler,
                        "Luz": luz,
                        "Internet": internet,
                        "Limpieza": limpieza,
                        "Otros": otros,
                        "Gasto_total": total_gastos,
                        "Fecha_registro": fecha_actual
                    })

                    st.success("✅ Datos registrados correctamente")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

   