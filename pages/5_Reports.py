import streamlit as st
import pandas as pd

st.header("📊 Reportes Semanales")

df = pd.read_csv("data/reports.csv")
st.dataframe(df)
