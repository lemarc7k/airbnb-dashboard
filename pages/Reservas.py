# ====================================================================================================
# === TAB RESERVAS ===================================================================================
# ====================================================================================================

# === IMPORTACIONES ===
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# === FIREBASE ===
from firebase_config import db



def mostrar_reservas(df):
    st.markdown("### ➕ Registrar nueva reserva")

    if df.empty:
        st.warning("⚠️ No hay reservas disponibles en este momento.")
        return

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
                check_in = st.date_input("Check-in", value=datetime.today())
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
                pais = st.selectbox("País de origen", paises_populares)
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

            st.markdown("</div>", unsafe_allow_html=True)

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

    # Últimas reservas como cards
    st.markdown("---")
    st.markdown("<h4 style='color:#00ffe1;'>🧾 Últimas reservas registradas</h4>", unsafe_allow_html=True)

    ultimos = df.sort_values("Check-in", ascending=False).head(3)

    for _, row in ultimos.iterrows():
        st.markdown(f"""
        <div style='background:#111; border-left:4px solid #00ffe1; padding:12px; margin:10px 0; border-radius:10px;'>
            <strong>👤 {row['Huesped']}</strong> – {row['Propiedad']} / {row['Habitación']}<br>
            <span style='color:#ccc;'>📅 {row['Check-in']} → {row['Check-out']} | 💰 {row['Precio']} AUD</span>
        </div>
        """, unsafe_allow_html=True)

    # Primer botón
    if st.button("🔍 Ver todas las reservas", key="ver_reservas_arriba"):
        st.dataframe(df.sort_values("Check-in", ascending=False), use_container_width=True)

    # Segundo botón
    if st.button("🔍 Ver todas las reservas", key="ver_reservas_abajo"):
        st.markdown("""
            <h4 style='color:#00ffe1; margin-top: 40px;'>📅 Todas las reservas</h4>
        """, unsafe_allow_html=True)
        st.dataframe(df.sort_values("Check-in", ascending=False), use_container_width=True)

