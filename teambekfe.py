import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="Team BekFê Fitness Tracker",
    layout="wide",
)

# -----------------------------
# SOLO LEVELING UI THEME
# -----------------------------
st.markdown("""
<style>
body {
    background-color: #0a0f1a;
}
header, .stTabs [role="tablist"] button {
    font-size: 20px;
}
.block-container {
    background-color: #0a0f1a;
    padding-top: 2rem;
}
h1, h2, h3, h4, h5, h6, p, label {
    font-family: 'Roboto', sans-serif;
    color: #e0e6f1 !important;
}
.stat-card {
    background: rgba(25, 35, 60, 0.85);
    padding: 25px;
    border-radius: 12px;
    border: 1px solid #3a4a6a;
    text-align: center;
    box-shadow: 0px 0px 12px rgba(0, 255, 255, 0.15);
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# GOOGLE SHEETS CONFIG
# -----------------------------
SHEET_ID = "1XQEJH-s0Z6LrutwTTSvS0cYR1e3Tiqi6VqUkGQ-S3Lg"
SHEET_NAME = "Data"   # ← IMPORTANT: using your new “Data” tab

# -----------------------------
# LOAD GOOGLE SHEET
# -----------------------------
@st.cache_data(ttl=60)
def load_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )
    client = gspread.authorize(creds)

    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    df = pd.DataFrame(sheet.get_all_records())

    # Clean name issues: trim, lowercase, unify spelling
    if "Please list your name :" in df.columns:
        df["Please list your name :"] = (
            df["Please list your name :"]
            .astype(str)
            .str.strip()
            .str.title()
        )

    return df, sheet


df, sheet = load_sheet()


# -----------------------------
# NAVIGATION TABS
# -----------------------------
tabs = st.tabs(["🏠 Dashboard", "🥇 Leaderboards", "🔥 Fitness Activity", "👤 Profile"])


# -----------------------------
# TAB 1 — DASHBOARD
# -----------------------------
with tabs[0]:
    st.markdown("<h1>🗡️ Team BekFê Fitness Tracker ⚔️</h1>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown('<div class="stat-card"><h2>262</h2><p>Form Entries</p></div>', unsafe_allow_html=True)

    with col2:
        active_members = df["Please list your name :"].nunique()
        st.markdown(f'<div class="stat-card"><h2>{active_members}</h2><p>Active Members</p></div>', unsafe_allow_html=True)

    with col3:
        st.markdown(f'<div class="stat-card"><h2>{len(df)}</h2><p>Total Sessions</p></div>', unsafe_allow_html=True)

    with col4:
        def convert_time(t):
            try:
                t = str(t).lower().replace("mins", "min").replace("hrs", "hour")
                if "hour" in t:
                    h = float(t.split("hour")[0].strip())
                    return h * 60
                if "min" in t:
                    return float(t.split("min")[0].strip())
            except:
                return 0
            return 0

        total_minutes = df["How long did you work out for?  ( 25 mins  - 2hours )"].apply(convert_time).sum()
        total_hours = round(total_minutes / 60, 1)

        st.markdown(f'<div class="stat-card"><h2>{total_hours}</h2><p>Total Hours</p></div>', unsafe_allow_html=True)

    st.markdown("### 🔥 Recent Activity")
    st.dataframe(df.tail(20), use_container_width=True)


# -----------------------------
# TAB 2 — LEADERBOARDS
# -----------------------------
with tabs[1]:
    st.header("🥇 Weekly Leaderboards")

    leaderboard = (
        df.groupby("Please list your name :")
        .size()
        .reset_index(name="Sessions")
        .sort_values("Sessions", ascending=False)
    )

    st.dataframe(leaderboard, use_container_width=True)


# -----------------------------
# TAB 3 — FITNESS ACTIVITY
# -----------------------------
with tabs[2]:
    st.header("🔥 Workout Breakdown")

    activity_counts = (
        df["What muscle groups did your work on? (Please list all that applies)"]
        .astype(str)
        .str.split(",")
        .explode()
        .str.strip()
        .value_counts()
    )

    st.bar_chart(activity_counts)


# -----------------------------
# TAB 4 — PROFILE + ADD ENTRY
# -----------------------------
with tabs[3]:
    st.header("👤 Submit New Workout Entry")

    with st.form("add_entry"):
        name = st.text_input("Name")
        duration = st.text_input("Workout Duration (e.g., 30 mins)")
        muscle_groups = st.text_area("Muscle Groups Worked")
        submitted = st.form_submit_button("Submit Entry")

        if submitted:
            new_row = [pd.Timestamp.now(), name, "Yes", muscle_groups, duration]
            sheet.append_row(new_row)
            st.success("Entry added successfully! Refresh to see it.")





