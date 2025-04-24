import streamlit as st
import pandas as pd
import datetime
import altair as alt
from firebase_config import db

st.set_page_config(page_title="Dashboard", layout="wide")
st.markdown("""
<style>
.big-title {
font-size: 36px;
font-weight: 600;
}
.big-number {
font-size: 48px;
color: #e60073;
font-weight: bold;
}
.upcoming {
color: grey;
margin-bottom: 20px;
}
.box-summary {
border: 1px solid #ddd;
border-radius: 10px;
padding: 20px;
background-color: #fff;
}
</style>
""", unsafe_allow_html=True)

# ---------- FUNCIONES PARA FIRESTORE ----------

def obtener_datos_bookings():
bookings_ref = db.collection("bookings")
docs = bookings_ref.stream()
data = []
for doc in docs:
d = doc.to_dict()
d["id"] = doc.id
data.append(d)
df = pd.DataFrame(data)
if not df.empty:
df["Check-in"] = pd.to_datetime(df.get("Check-in"), errors="coerce")
df["Mes"] = df["Check-in"].dt.to_period("M").dt.to_timestamp()
df["Check-out"] = pd.to_datetime(df.get("Check-out"), errors="coerce")
df["Fecha"] = pd.to_datetime(df.get("Fecha"), errors="coerce")
df["Precio"] = pd.to_numeric(df.get("Precio"), errors="coerce").fillna(0)
df["Huespedes"] = pd.to_numeric(df.get("Huespedes"), errors="coerce").fillna(0).astype(int)
df["Noches"] = pd.to_numeric(df.get("Noches"), errors="coerce").fillna(0).astype(int)
return df

# ---------- CARGAR DATOS ----------

df = obtener_datos_bookings()
hoy = datetime.date.today()
mes_actual = pd.to_datetime(hoy).to_period("M").to_timestamp()

# ---------- INGRESOS Y GRÁFICO PRINCIPAL ----------

st.markdown("## Earnings")
ingresos_mes = df[df["Mes"] == mes_actual]["Precio"].sum()
upcoming = df[df["Check-in"] > pd.to_datetime(hoy)]["Precio"].sum()

# Crear rango completo de meses

meses_completos = pd.date_range(start="2024-10-01", end=hoy, freq="MS")
df_meses = pd.DataFrame({"Mes": meses_completos})

# Agrupar ingresos y unir con rango completo

ingresos_por_mes = df.groupby("Mes")["Precio"].sum().reset_index()
ingresos_por_mes = df_meses.merge(ingresos_por_mes, on="Mes", how="left").fillna(0)
ingresos_por_mes["Mes"] = ingresos_por_mes["Mes"].dt.strftime("%b")

col_main, col_side = st.columns([3, 1])
with col_main:
st.markdown(f"<div class='big-title'>You’ve made</div>", unsafe_allow_html=True)
st.markdown(f"<div class='big-number'>${ingresos_mes:,.2f} AUD</div>", unsafe_allow_html=True)
st.markdown(f"<div class='upcoming'>Upcoming ${upcoming:,.2f} AUD</div>", unsafe_allow_html=True)

    chart = alt.Chart(ingresos_por_mes).mark_bar(
        cornerRadiusTopLeft=8, cornerRadiusTopRight=8, color="#e60073"
    ).encode(
        x=alt.X("Mes", sort=list(ingresos_por_mes["Mes"])),
        y=alt.Y("Precio", title="$ AUD"),
        tooltip=["Mes", "Precio"]
    ).properties(height=300)

    st.altair_chart(chart, use_container_width=True)

with col_side:
total = df["Precio"].sum()
fee = total \* 0.03
neto = total - fee
st.markdown(f"""
<div class='box-summary'>
<h4>Year-to-date summary</h4>
<p style='margin-bottom: 5px;'>1 Jan – {hoy:%d %b %Y}</p>
<p><strong>Gross earnings</strong><br/>${total:,.2f} AUD</p>
        <p><strong>Airbnb service fee (3%)</strong><br/>-${fee:,.2f} AUD</p>
<p><strong>Tax withheld</strong><br/>$0.00 AUD</p>
        <hr/>
        <p><strong>Total (AUD)</strong><br/><b>${neto:,.2f} AUD</b></p>
</div>
""", unsafe_allow_html=True)
