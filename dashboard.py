# dashboard.py
import streamlit as st, pandas as pd

st.title("Exploitation-Validated Prioritization")
df = pd.read_csv("results.csv")

st.metric("CVE ทั้งหมด", len(df))
st.metric("โจมตีได้จริง", int(df["exploited"].sum()))
st.metric("แก้สำเร็จ", int(df["fixed"].sum()))
st.dataframe(df[["cve", "predicted", "exploited", "fixed"]])

# เปิดเว็บที่ http://localhost:8501
# รันด้วยคำสั่ง: streamlit run dashboard.py
