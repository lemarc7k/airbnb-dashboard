import streamlit as st
st.set_page_config(page_title="dashboard | KM Ventures", layout="wide")
import pandas as pd
import datetime
import altair as alt
from firebase_config import db

try:
    # tu lógica aquí
    st.write("✅ Página cargada correctamente")
except Exception as e:
    st.error(f"❌ Error cargando página: {e}")


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

# ---------- FIREBASE FUNCTION ---------- #
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

# ---------- LOAD DATA ---------- #
df = obtener_datos_bookings()
hoy = datetime.date.today()
mes_actual = pd.to_datetime(hoy).to_period("M").to_timestamp()

# ---------- MES RANGE ÚLTIMOS 12 MESES ---------- #
anio_actual = hoy.year
meses_completos = pd.date_range(start=f"{anio_actual}-01-01", end=f"{anio_actual}-12-01", freq="MS")
df_meses = pd.DataFrame({"Mes": meses_completos})

# ---------- CALCULOS Y GRÁFICO ---------- #
st.markdown("## Earnings")
ingresos_mes = df[df["Mes"] == mes_actual]["Precio"].sum()
upcoming = df[df["Check-in"] > pd.to_datetime(hoy)]["Precio"].sum()

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
    fee = total * 0.03
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





# ---------- CALCULAR PAGOS UPCOMING Y PAID ---------- #
df["Fecha de pago"] = df["Check-in"] + pd.Timedelta(days=2)

pagos_upcoming = df[df["Fecha de pago"] > pd.to_datetime(hoy)]
pagos_paid = df[df["Fecha de pago"] <= pd.to_datetime(hoy)]

# ---------- PAGOS FUTUROS (UPCOMING) ---------- #
st.markdown("---")
st.markdown("### 📆 Upcoming")

# Calcular fecha estimada de pago = 2 días después del check-in
df["Payout Date"] = df["Check-in"] + pd.Timedelta(days=2)
upcoming_df = df[df["Payout Date"] > pd.to_datetime(hoy)].copy()
upcoming_df = upcoming_df.sort_values("Payout Date")

if not upcoming_df.empty:
    tabla_upcoming = pd.DataFrame({
        "Status": ["Scheduled"] * len(upcoming_df),
        "Date": upcoming_df["Payout Date"].dt.strftime("%d %b"),
        "Amount": upcoming_df["Precio"].map("${:,.2f} AUD".format),
        "Payout method": ["Kevin Mera Vera, Checking\n••••1476 (AUD)"] * len(upcoming_df),
        "Type": ["Reservation"] * len(upcoming_df)
    })

    st.dataframe(tabla_upcoming, hide_index=True, use_container_width=True)
    st.button("View all upcoming", key="btn_upcoming")

else:
    st.info("No upcoming payouts scheduled.")

# ---------- PAGOS ENVIADOS (PAID) ---------- #
st.markdown("---")
st.markdown("### 💰 Paid")

paid_df = df[df["Payout Date"] <= pd.to_datetime(hoy)].copy()
paid_df = paid_df.sort_values("Payout Date", ascending=False)

if not paid_df.empty:
    tabla_paid = pd.DataFrame({
        "Status": ["Sent"] * len(paid_df),
        "Date": paid_df["Payout Date"].dt.strftime("%d %b"),
        "Paid out": paid_df["Precio"].map("${:,.2f} AUD".format),
        "Payout method": ["Kevin Mera Vera, Checking\n••••1476 (AUD)"] * len(paid_df),
        "Transactions": [1] * len(paid_df)
    })

    st.dataframe(tabla_paid, hide_index=True, use_container_width=True)
    st.button("View all paid", key="btn_paid")

else:
    st.info("No past payouts yet.")
