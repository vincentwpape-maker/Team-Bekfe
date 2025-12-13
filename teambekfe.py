import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import datetime as dt
import re
from collections import defaultdict

# -------------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------------
st.set_page_config(
    page_title="Team Bekfè Fitness Tracker",
    layout="wide",
)

# -------------------------------------------------------------
# GLOBAL STYLING (SOLO-LEVELING THEME)
# -------------------------------------------------------------
st.markdown(
    """
    <style>
    body {
        background-color: #05070c;
        color: #e5f4ff;
    }
    .main-title {
        font-size: 40px;
        font-weight: 900;
        text-align: center;
        text-shadow: 0 0 12px #3f9dff;
        margin-bottom: 6px;
    }
    .glow-header {
        font-size: 26px;
        font-weight: 800;
        color: #7fd1ff;
        border-bottom: 2px solid #2f9dff;
        margin-bottom: 15px;
        display: inline-block;
    }
    .sub-header {
        font-size: 18px;
        font-weight: 700;
        color: #9bd4ff;
        margin-top: 20px;
        margin-bottom: 6px;
    }
    .stat-box {
        padding: 18px;
        border-radius: 14px;
        text-align: center;
        background: #101927;
        border: 1px solid #245b8f;
    }
    .stat-value {
        font-size: 38px;
        font-weight: 900;
        color: #7fd1ff;
    }
    .stat-label {
        font-size: 14px;
        color: #9bb8d1;
    }
    .featured-line {
        background: rgba(34,22,6,.88);
        border: 1px solid #facc15;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 14px;
    }
    .summary-line {
        background: #0a1930;
        border: 1px solid #3fa9ff;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# LOAD GOOGLE SHEETS DATA
# -------------------------------------------------------------
CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1XQEJH-s0Z6LrutwTTSvS0cYR1e3Tiqi6VqUkGQ-S3Lg/export"
    "?format=csv&gid=2121731071"
)

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = [c.strip() for c in df.columns]
    return df

df = load_data()

# -------------------------------------------------------------
# COLUMN SETUP
# -------------------------------------------------------------
col_timestamp = df.columns[0]
col_name = df.columns[1]
col_muscles = df.columns[3]
col_duration = df.columns[4]

df[col_timestamp] = pd.to_datetime(df[col_timestamp], errors="coerce")

df["month"] = df[col_timestamp].dt.month
df["month_name"] = df[col_timestamp].dt.strftime("%B")

# -------------------------------------------------------------
# CLEANING
# -------------------------------------------------------------
def clean_name(n):
    if not isinstance(n, str):
        return ""
    n = re.sub(r"[^a-z0-9 ]", "", n.lower().strip())
    corrections = {
        "vincent": "Vincent",
        "alain": "Alain",
        "danimix": "Danimix",
        "dani mix": "Danimix",
        "dimitri": "Dimitri",
        "douglas": "Douglas",
        "louis": "Louis",
        "bousik": "Bousik",
        "gregory": "Gregory",
        "mikael": "Mikael",
        "junior": "Junior",
    }
    return corrections.get(n, n.title())

df[col_name] = df[col_name].apply(clean_name)

def parse_duration(t):
    if not isinstance(t, str):
        return 0
    nums = list(map(int, re.findall(r"\d+", t)))
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    elif len(nums) == 1:
        return nums[0]
    return 0

df["minutes"] = df[col_duration].apply(parse_duration)

# -------------------------------------------------------------
# MUSCLE EXTRACTION
# -------------------------------------------------------------
def extract_muscles(txt):
    if not isinstance(txt, str):
        return []
    return [x.split("(")[0].strip() for x in txt.split(",") if x.strip()]

user_muscles = defaultdict(lambda: defaultdict(int))
overall_muscles = defaultdict(int)

for _, row in df.iterrows():
    for m in extract_muscles(row[col_muscles]):
        user_muscles[row[col_name]][m] += 1
        overall_muscles[m] += 1

sessions = df.groupby(col_name).size()
duration = df.groupby(col_name)["minutes"].sum()
users = sorted(df[col_name].unique())

# -------------------------------------------------------------
# RANK SYSTEM
# -------------------------------------------------------------
def get_rank_letter(n):
    if n >= 250: return "S"
    if n >= 180: return "A"
    if n >= 120: return "B"
    if n >= 60:  return "C"
    if n >= 30:  return "D"
    return "E"

rank_map = {u: get_rank_letter(sessions[u]) for u in sessions.index}
consistency_map = {u: round(sessions[u] / 365 * 100, 1) for u in sessions.index}

# -------------------------------------------------------------
# HEADER
# -------------------------------------------------------------
st.markdown("<div class='main-title'>Team Bekfè Fitness Tracker</div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# TABS
# -------------------------------------------------------------
tab_profile, tab_lb, tab_activity, tab_dash, tab_ranks = st.tabs(
    ["Profile", "Leaderboards", "Fitness Activity", "Dashboard", "Ranking System"]
)

# -------------------------------------------------------------
# PROFILE TAB
# -------------------------------------------------------------
with tab_profile:
    selected = st.selectbox("Select Athlete", users)

    st.markdown("<div class='glow-header'>Profile</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='stat-box'><div class='stat-value'>{sessions[selected]}</div><div class='stat-label'>Sessions</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='stat-box'><div class='stat-value'>{round(duration[selected]/60,1)}</div><div class='stat-label'>Hours</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='stat-box'><div class='stat-value'>{rank_map[selected]}</div><div class='stat-label'>Rank</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='stat-box'><div class='stat-value'>{consistency_map[selected]}%</div><div class='stat-label'>Consistency</div></div>", unsafe_allow_html=True)

    # Monthly breakdown
    st.markdown("<div class='sub-header'>📅 Monthly Session Performance</div>", unsafe_allow_html=True)

    monthly = (
        df[df[col_name] == selected]
        .groupby(["month", "month_name"])
        .size()
        .reset_index(name="Sessions")
        .sort_values("Sessions", ascending=False)
    )

    all_months = pd.DataFrame({
        "month": range(1, 13),
        "month_name": [dt.date(1900, m, 1).strftime("%B") for m in range(1, 13)]
    })

    monthly = all_months.merge(monthly, on=["month", "month_name"], how="left").fillna(0)
    monthly["Sessions"] = monthly["Sessions"].astype(int)

    st.dataframe(monthly[["month_name", "Sessions"]], hide_index=True, use_container_width=True)

# -------------------------------------------------------------
# LEADERBOARD TAB
# -------------------------------------------------------------
with tab_lb:
    lb = pd.DataFrame({
        "User": sessions.index,
        "Sessions": sessions.values,
        "Rank": [rank_map[u] for u in sessions.index],
        "Consistency %": [consistency_map[u] for u in sessions.index],
    }).sort_values("Sessions", ascending=False)

    st.dataframe(lb, hide_index=True, use_container_width=True)

# -------------------------------------------------------------
# RANKING SYSTEM TAB
# -------------------------------------------------------------
with tab_ranks:
    components.html("""
    <table style="width:100%;border-collapse:collapse;">
        <tr><th>Rank</th><th>Sessions</th></tr>
        <tr><td>S</td><td>250–365</td></tr>
        <tr><td>A</td><td>180–249</td></tr>
        <tr><td>B</td><td>120–179</td></tr>
        <tr><td>C</td><td>60–119</td></tr>
        <tr><td>D</td><td>30–59</td></tr>
        <tr><td>E</td><td>0–29</td></tr>
    </table>
    """, height=300)
