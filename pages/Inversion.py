import streamlit as st
from firebase_config import db
from datetime import datetime
import pandas as pd

st.cache_data.clear()

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

imagenes_propiedades = {
    "CBD": "https://i.ibb.co/LhQJfRYf/CBD-room-1.jpg",
    "INGLEWOOD": "https://i.ibb.co/k2FrrwMp/IGW-room-4.jpg",
    "GARAJE": "https://i.ibb.co/Xr5DGZ9R/CBD-garage.jpg",
}

def mostrar_inversion():
    mostrar_cards_inversiones()

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
        .card-actions {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 10px;
        }
        .icon-button {
            background-color: #0f172a;
            border: 1px solid #00ffe1;
            border-radius: 12px;
            padding: 0.4rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            color: #00ffe1;
            width: 38px;
            height: 38px;
            transition: all 0.2s ease-in-out;
            box-shadow: 0 0 8px #00ffe140;
        }
        .icon-button:hover {
            background-color: #00ffe110;
            transform: scale(1.07);
            box-shadow: 0 0 12px #00ffe180;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("""
        <div class="formulario-box">
            <h3>REGISTRAR INVERSIÓN</h3>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.edit_id:
        doc_ref = db.collection("inversiones").document(st.session_state.edit_id).get()
        inv_data = doc_ref.to_dict()
        if inv_data:
            st.markdown(f"<p style='color:#00ffe1;'>🛠 Editando inversión: {inv_data['Propiedad']}</p>", unsafe_allow_html=True)
        else:
            st.session_state.edit_id = None
            st.warning("❗ Esta inversión fue eliminada o no existe.")
            st.rerun()
    else:
        inv_data = {}

    with st.form("formulario_inversion"):
        col1, col2 = st.columns(2)
        with col1:
            propiedad = st.text_input("Propiedad", value=inv_data.get("Propiedad", "")).strip()
            fecha_adq = st.date_input("Fecha de adquisición", value=pd.to_datetime(inv_data.get("Fecha_adquisicion", datetime.today())))
            localizacion = st.text_input("Localización", value=inv_data.get("Localizacion", "")).strip()
        with col2:
            precio_adquisicion = st.number_input("Precio de adquisición", min_value=0.0, step=100.0, value=inv_data.get("Monto_inicial", 0.0))
            fianza = st.number_input("Fianza pagada", min_value=0.0, step=50.0, value=inv_data.get("Fianza", 0.0))
            renta_semanal = st.number_input("Renta semanal estimada", min_value=0.0, step=10.0)

        col3, col4 = st.columns(2)
        with col3:
            decoracion = st.number_input("Muebles y decoración", min_value=0.0, step=50.0, value=inv_data.get("Muebles", 0.0))
            luz = st.number_input("Electricidad mensual", min_value=0.0, step=10.0)
        with col4:
            internet = st.number_input("Internet mensual", min_value=0.0, step=10.0)
            otros = st.number_input("Otros gastos fijos", min_value=0.0, step=10.0)

        notas = st.text_area("Notas o comentarios extra", value=inv_data.get("Notas", ""))
        submit = st.form_submit_button("💾 Guardar Inversión")

    if submit:
        if not propiedad or precio_adquisicion == 0:
            st.error("❌ Por favor completa todos los campos obligatorios.")
        else:
            try:
                total_inversion = precio_adquisicion + fianza + decoracion
                gasto_mensual = luz + internet + otros
                fecha_actual = datetime.now().isoformat()

                datos_inversion = {
                    "Propiedad": propiedad,
                    "Monto_inicial": precio_adquisicion,
                    "Fianza": fianza,
                    "Muebles": decoracion,
                    "Fees": 0.0,
                    "Inversion_total": total_inversion,
                    "Fecha_adquisicion": str(fecha_adq),
                    "Localizacion": localizacion,
                    "Notas": notas,
                    "Fecha_registro": fecha_actual
                }

                if st.session_state.edit_id:
                    db.collection("inversiones").document(st.session_state.edit_id).set(datos_inversion)
                    st.success("✅ Inversión actualizada correctamente.")
                    st.session_state.edit_id = None
                else:
                    db.collection("inversiones").add(datos_inversion)
                    db.collection("gastos_fijos").add({
                        "Propiedad": propiedad,
                        "Alquiler": renta_semanal * 4,
                        "Luz": luz,
                        "Internet": internet,
                        "Limpieza": 0.0,
                        "Otros": otros,
                        "Gasto_total": gasto_mensual,
                        "Fecha_registro": fecha_actual
                    })
                    st.success("✅ Inversión registrada correctamente.")

                st.rerun()

            except Exception as e:
                st.error(f"❌ Error al registrar: {e}")

def mostrar_cards_inversiones():
    inversiones_ref = db.collection("inversiones").stream()
    gastos_ref = db.collection("gastos_fijos").stream()

    data_inv = [dict(x.to_dict(), id=x.id) for x in inversiones_ref]
    data_gastos = [dict(x.to_dict(), id=x.id) for x in gastos_ref]

    df_inv = pd.DataFrame(data_inv)
    df_gastos = pd.DataFrame(data_gastos)

    if df_inv.empty:
        st.warning("⚠️ No hay inversiones registradas.")
        return

    propiedades = df_inv["Propiedad"].unique()
    cols = st.columns(3)

    for i, prop in enumerate(propiedades):
        inv = df_inv[df_inv["Propiedad"] == prop].iloc[0]
        gastos = df_gastos[df_gastos["Propiedad"] == prop].iloc[0] if not df_gastos.empty and prop in df_gastos["Propiedad"].values else {}

        imagen_url = imagenes_propiedades.get(prop.upper(), f"https://api.dicebear.com/7.x/shapes/svg?seed={prop}")
        fianza = inv.get("Fianza", 0.0)
        luz = gastos.get("Luz", 0.0)
        internet = gastos.get("Internet", 0.0)
        renta_mensual = gastos.get("Alquiler", 0.0)
        localizacion = inv.get('Localizacion', 'Sin info')

        with cols[i % 3]:
            with st.form(f"form_{inv['id']}", clear_on_submit=False):
                st.markdown(f"""
                    <div style="background-color:#0f172a; border-radius:16px;
                                box-shadow:0 0 12px #00ffe120; overflow:hidden; margin-bottom:12px;
                                position:relative;">
                        <img src="{imagen_url}" style="width:100%; height:180px; object-fit:cover; border-top-left-radius:16px; border-top-right-radius:16px;">
                        <div style="padding:15px;">
                            <h4 style="color:#00ffe1; margin-bottom:6px;">🛏️ {prop}</h4>
                            <p style="color:#aaa; margin:0;">📍 {localizacion}</p>
                            <p style="color:#ccc; font-size:13px; margin:4px 0 0 0;">
                                💵 Renta mensual: ${renta_mensual:,.2f}<br>
                                🔐 Fianza: ${fianza:,.2f}<br>
                                💡 Luz: ${luz:,.2f}<br>
                                🌐 Internet: ${internet:,.2f}
                            </p>
                            <div class="card-actions" style="margin-top:10px; display:flex; gap:12px;">
                                <button type="submit" name="action" value="ver" class="icon-button" title="Ver detalles">🔍</button>
                                <button type="submit" name="action" value="editar" class="icon-button" title="Editar">✏️</button>
                                <button type="submit" name="action" value="eliminar" class="icon-button" title="Eliminar">🗑️</button>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                submitted_action = st.form_submit_button()
                if submitted_action:
                    action = st.session_state.get(f"form_{inv['id']}_action")
                else:
                    action = st.session_state.get(f"form_{inv['id']}_action")

                if action == "ver":
                    with st.expander("🔎 Detalles de la inversión"):
                        st.write("**Inversión total:** $", inv.get("Inversion_total", 0.0))
                        st.write("**Monto inicial:** $", inv.get("Monto_inicial", 0.0))
                        st.write("**Fianza:** $", inv.get("Fianza", 0.0))
                        st.write("**Muebles:** $", inv.get("Muebles", 0.0))
                        st.write("**Notas:**", inv.get("Notas", "Sin notas"))
                elif action == "editar":
                    st.session_state.edit_id = inv["id"]
                    st.rerun()
                elif action == "eliminar":
                    eliminar_inversion(inv["id"], df_gastos)
                    st.rerun()

def eliminar_inversion(inv_id, df_gastos):
    try:
        db.collection("inversiones").document(inv_id).delete()

        fila_gasto = df_gastos[df_gastos["id"] == inv_id]
        if not fila_gasto.empty:
            propiedad = fila_gasto["Propiedad"].values[0]
            gastos_prop = df_gastos[df_gastos["Propiedad"] == propiedad]
            for _, row in gastos_prop.iterrows():
                db.collection("gastos_fijos").document(row['id']).delete()

        st.success("✅ Inversión eliminada correctamente.")
    except Exception as e:
        st.error(f"❌ Error al eliminar: {e}")