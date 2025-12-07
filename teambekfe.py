import streamlit as st
import pandas as pd

st.title("Team BekFe – Workout Tracker")

csv_url = "https://docs.google.com/spreadsheets/d/1XQEJH-s0Z6LrutwTTSvS0cYR1e3Tiqi6VqUkGQ-S3Lg/export?format=csv&gid=2121731071"

df = pd.read_csv(csv_url)

st.subheader("Raw Data")
st.dataframe(df)

st.subheader("Summary")
st.write("Total entries:", len(df))
