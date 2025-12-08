import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import datetime as dt
import re
from collections import defaultdict

# -------------------------------------------------------------
#                SOLO LEVELING / NEON BLUE THEME
# -------------------------------------------------------------
st.set_page_config(page_title="Team BekFê Fitness Tracker", layout="wide")

st.markdown(
    """
    <style>
    body {
        background-color: #070b10;
        color: #d7ecff;
    }

    .main {
        background-color: #070b10;
    }

    /* MAIN TITLE */
    .main-title {
        text-align: center;
        font-size: 50px;
        font-weight: 900;
        color: #ffffff;
        margin-top: -25px;
        margin-bottom: 10px;
        text-shadow: 0 0 20px #4fc3ff, 0 0 40px #0077ff;
    }

    /* TAB STYLE */
    .stTabs [data-baseweb="tab-list"] {
        background: #0d1219;
        border-radius: 8px;
        border: 1px solid #1c2b3a;
        padding: 6px;
        margin-bottom: 15px;
    }

    .stTabs [data-baseweb="tab"] {
        color: #a8c7ff;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background: #11324d;
        border-radius: 6px;
        color: white !important;
        box-shadow: 0 0 10px #4fc3ff;
    }

    /* SECTION WRAPPER */
    .section-frame {
        background: #0c1117;
        padding: 20px 25px;
        border-radius: 12px;
        border: 1px solid #1c2b3a;
        box-shadow: 0 0 18px #004c73 inset;
        margin-top: 10px;
        margin-bottom: 20px;
    }

    /* STAT CARDS */
    .stat-card {
        background: #0c1117;
        padding: 25px;
        text-align: center;
        border-radius: 15px;
        border: 1px solid #123047;
        box-shadow: 0 0 20px #006699;
    }

    .stat-value {
        font-size: 42px;
        font-weight: 800;
        color: #73caff;
        text-shadow: 0 0 15px #4fc3ff;
    }

    .stat-label {
        color: #9bb8d1;
        font-size: 16px;
        font-weight: 500;
    }

    /* HEADERS */
    .section-header {
        font-size: 30px;
        font-weight: 700;
        color: #73caff;
        text-shadow: 0 0 15px #4fc3ff;
        margin-bottom: 10px;
    }

    .sub-header {
        font-size: 22px;
        font-weight: 600;
        color: #9bd3ff;
        margin-top: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
#                MAIN TITLE
# -------------------------------------------------------------
st.markdown("<div class='main-title'>⚔️ Team BekFê Fitness Tracker ⚔️</div>", unsafe_allow_html=True)


# -------------------------------------------------------------
#                LOAD SHEET AS CSV
# -------------------------------------------------------------
CSV_URL = "https://docs.google.com/spreadsheets/d/1XQEJH-s0Z6LrutwTTSvS0cYR1e3Tiqi6VqUkGQ-S3Lg/export?format=csv&gid=2121731071"

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = [c.strip() for c in df.columns]
    return df

df = load_data()

col_timestamp = df.columns[0]
col_name = df.columns[1]
col_muscles = df.columns[3]
col_duration = df.columns[4]

df[col_timestamp] = pd.to_datetime(df[col_timestamp], errors="coerce")


# -------------------------------------------------------------
#                CLEAN NAMES
# -------------------------------------------------------------
def clean_name(name):
    if not isinstance(name, str): return ""
    n = re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()
    corrections = {
        "vincent": "Vincent", "alain": "Alain", "danimix": "Danimix",
        "dimitri": "Dimitri", "douglas": "Douglas", "louis": "Louis",
        "gregory": "Gregory", "mikael": "Mikael", "bousik": "Bousik",
        "agusto": "Agusto",
    }
    return corrections.get(n, n.title())

df[col_name] = df[col_name].apply(clean_name)


# -------------------------------------------------------------
#                PARSE DURATIONS
# -------------------------------------------------------------
def parse_duration(text):
    if not isinstance(text, str): return 0
    s = text.lower()
    hours = sum(int(x) for x in re.findall(r"(\d+)\s*(hour|hr|h)", s))
    minutes = sum(int(x) for x in re.findall(r"(\d+)\s*(minute|min|m)", s))
    if hours == 0 and minutes == 0:
        nums = re.findall(r"\d+", s)
        if len(nums) == 1: minutes = int(nums[0])
    return hours * 60 + minutes

df["minutes"] = df[col_duration].apply(parse_duration)


# -------------------------------------------------------------
#                SESSION + MUSCLE DATA
# -------------------------------------------------------------
sessions = df.groupby(col_name).size().rename("Sessions")
duration = df.groupby(col_name)["minutes"].sum().rename("Total Minutes")

def extract_muscles(x):
    if not isinstance(x, str): return []
    return [p.split("(")[0].strip() for p in x.split(",")]

user_muscle_counts = defaultdict(lambda: defaultdict(int))
all_muscles = set()

for _, row in df.iterrows():
    muscles = extract_muscles(row[col_muscles])
    for m in muscles:
        user_muscle_counts[row[col_name]][m] += 1
        all_muscles.add(m)


# -------------------------------------------------------------
#                UI TABS
# -------------------------------------------------------------
tab_dash, tab_lb, tab_activity, tab_profile = st.tabs(
    ["Dashboard", "Leaderboards", "Fitness Activity", "Profile"]
)


# -------------------------------------------------------------
#                DASHBOARD
# -------------------------------------------------------------
with tab_dash:
    st.markdown("<div class='section-frame'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>📊 Dashboard Overview</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(f"<div class='stat-card'><div class='stat-value'>{len(df)}</div><div class='stat-label'>Form Entries</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='stat-card'><div class='stat-value'>{df[col_name].nunique()}</div><div class='stat-label'>Active Members</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='stat-card'><div class='stat-value'>{int(sessions.sum())}</div><div class='stat-label'>Total Sessions</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='stat-card'><div class='stat-value'>{round(duration.sum()/60,1)}</div><div class='stat-label'>Total Hours</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='sub-header'>🔥 Recent Activity</div>", unsafe_allow_html=True)
    st.dataframe(df[[col_timestamp, col_name, col_muscles, col_duration]].sort_values(col_timestamp, ascending=False), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# -------------------------------------------------------------
#                LEADERBOARD
# -------------------------------------------------------------
with tab_lb:
    st.markdown("<div class='section-frame'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>🏆 Leaderboard</div>", unsafe_allow_html=True)

    lb = pd.concat([sessions, duration], axis=1).reset_index()
    lb["Hours"] = (lb["Total Minutes"] / 60).round(1)
    lb = lb.rename(columns={col_name: "User"})
    lb = lb.sort_values("Sessions", ascending=False).reset_index(drop=True)
    lb.index = lb.index + 1
    lb.insert(0, "Rank", lb.index)

    st.dataframe(lb, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# -------------------------------------------------------------
#                FITNESS ACTIVITY
# -------------------------------------------------------------
with tab_activity:
    st.markdown("<div class='section-frame'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>💠 Muscle Activity Breakdown</div>", unsafe_allow_html=True)

    muscle_totals = (
        df[col_muscles]
        .astype(str)
        .apply(lambda x: extract_muscles(x))
        .explode()
        .value_counts()
        .reset_index()
    )
    muscle_totals.columns = ["Muscle Group", "Count"]

    fig = alt.Chart(muscle_totals).mark_bar(color="#4fc3ff").encode(
        x=alt.X("Muscle Group", sort="-y"),
        y="Count",
        tooltip=["Muscle Group", "Count"]
    )

    st.altair_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# -------------------------------------------------------------
#                PROFILE
# -------------------------------------------------------------
with tab_profile:
    st.markdown("<div class='section-frame'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>🧍 Profile</div>", unsafe_allow_html=True)

    users = sorted(sessions.index.tolist())
    selected = st.selectbox("Choose member", users)

    total_sessions = sessions[selected]
    total_minutes = duration[selected]
    total_hours = round(total_minutes / 60, 1)

    today = dt.date.today()
    season_end = dt.date(today.year, 12, 31)
    days_left = (season_end - today).days

    st.markdown(f"""
        <div class='sub-header'>Season: {today.year}</div>
        <div class='sub-header'>Current Date: {today.strftime('%B %d, %Y')}</div>
        <div class='sub-header'>Season ends in: {days_left} Days</div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='stat-card'><div class='stat-value'>{total_sessions}</div><div class='stat-label'>Total Sessions</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='stat-card'><div class='stat-value'>{total_hours}</div><div class='stat-label'>Total Hours</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='sub-header'>💪 Top Muscles</div>", unsafe_allow_html=True)
    mus = pd.Series(user_muscle_counts[selected]).sort_values(ascending=False)
    st.write(mus.head(5))

    st.markdown("<div class='sub-header'>😴 Least Used Muscles</div>", unsafe_allow_html=True)
    st.write(mus.tail(5))

    st.markdown("<div class='sub-header'>📘 Workout History</div>", unsafe_allow_html=True)
    st.dataframe(df[df[col_name] == selected][[col_timestamp, col_muscles, col_duration]].sort_values(col_timestamp, ascending=False), use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

