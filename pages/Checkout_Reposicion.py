import streamlit as st

st.set_page_config(page_title="Reposición en Check-out", layout="centered")

# --- ENCABEZADO --- #
st.title("🧹 Reposición en Check-out")
st.markdown("Calculadora automática de insumos utilizados tras una limpieza completa de habitación o apartamento.")

# --- LISTA DE INSUMOS --- #
st.subheader("🧾 Lista de reposición estándar")

insumos = {
    "Papel higiénico (2 unidades)": 1.20,
    "Papel de cocina (1 unidad)": 1.50,
    "Esponja (1 unidad)": 0.80,
    "Secado de lavandería (Dryer)": 6.00
}

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("Estos son los ítems que se reponen en cada check-out:")
with col2:
    st.markdown("💼")

# Mostrar tabla de desglose
st.markdown("""
<style>
    .centered-table thead th {
        text-align: center !important;
    }
    .centered-table td {
        text-align: center !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("### 💰 Coste por limpieza")

# Mostrar tabla formateada
st.table(
    {
        "Producto": list(insumos.keys()),
        "Costo (AUD)": [f"${v:.2f}" for v in insumos.values()]
    }
)

# Calcular total
total = sum(insumos.values())
st.success(f"**Costo total estimado por limpieza:** ${total:.2f} AUD")

# Nota adicional
st.markdown("---")
st.info("Puedes usar esta sección como referencia para automatizar compras, reponer inventario o calcular costos fijos por limpieza en tus reportes.")
