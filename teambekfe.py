import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime as dt
import re
from collections import defaultdict

# -------------------------------------------------------------
#                SOLO LEVELING THEME (GLOBAL CSS)
# -------------------------------------------------------------
st.markdown(
    """
    <style>
    body {
        background-color: #0a0d12;
        color: #e5f4ff;
    }

    .main {
        background-color: #0a0d12;
    }

    h1, h2, h3, h4 {
        color: #67c1ff;
        text-shadow: 0px 0px 10px #0e639c;
        font-weight: 700 !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: #0f141b;
        border-radius: 10px;
        border: 1px solid #1f2a36;
        padding: 5px;
    }

    .stTabs [data-baseweb="tab"] {
        color: #a8c7ff;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background: #11324d;
        color: #ffffff !important;
        border-radius: 8px;
        box-shadow: 0 0 8px #0e5b99;
    }

    .stat-box {
        padding: 20px;
        background: #11161f;
        border: 1px solid #1d2b3c;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 0 12px #0e5b99;
        margin-bottom: 15px;
    }

    .stat-value {
        font-size: 38px;
        font-weight: 800;
        color: #67c1ff;
        text-shadow: 0px 0px 15px #0e639c;
    }

    .stat-label {
        font-size: 15px;
        color: #9bb8d1;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------------------
#                LOAD GOOGLE SHEET VIA CSV
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
#                NAME NORMALIZATION
# -------------------------------------------------------------
def clean_name(name):
    if not isinstance(name, str):
        return ""
    n = name.strip().lower()
    n = re.sub(r"[^a-z0-9 ]", "", n)
    n = re.sub(r"\s+", " ", n)

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

# -------------------------------------------------------------
#                PARSE WORKOUT DURATION
# -------------------------------------------------------------
def parse_duration(text):
    if not isinstance(text, str):
        return 0
    s = text.lower()
    hours = 0
    minutes = 0

    h = re.search(r"(\d+)\s*(hour|hr|h)", s)
    m = re.search(r"(\d+)\s*(minute|min|m)", s)

    if h:
        hours = int(h.group(1))
    if m:
        minutes = int(m.group(1))

    if not h and not m:
        nums = re.findall(r"\d+", s)
        if len(nums) == 1:
            minutes = int(nums[0])
        elif len(nums) == 2:
            hours = int(nums[0])
            minutes = int(nums[1])

    return hours * 60 + minutes

df["minutes"] = df[col_duration].apply(parse_duration)

# -------------------------------------------------------------
#                MUSCLE COUNT PER USER
# -------------------------------------------------------------
def extract_muscles(text):
    if not isinstance(text, str):
        return []
    parts = [p.split("(")[0].strip() for p in text.split(",")]
    return [p for p in parts if p]

user_muscles = defaultdict(lambda: defaultdict(int))
muscle_popularity = defaultdict(int)

for _, row in df.iterrows():
    name = row[col_name]
    muscles = extract_muscles(row[col_muscles])
    for m in muscles:
        user_muscles[name][m] += 1
        muscle_popularity[m] += 1

# -------------------------------------------------------------
#                BUILD APPLICATION UI
# -------------------------------------------------------------
st.title("⚔️ Team BekFe Fitness Tracker ⚔️")

tab_dash, tab_lb, tab_activity, tab_profile = st.tabs(
    ["Dashboard", "Leaderboards", "Fitness Activity", "Profile"]
)

# -------------------------------------------------------------
#                    DASHBOARD TAB
# -------------------------------------------------------------
with tab_dash:
    st.header("📊 Dashboard Overview")

    sessions = df.groupby(col_name).size().rename("sessions")
    duration = df.groupby(col_name)["minutes"].sum().rename("total_minutes")

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='stat-box'><div class='stat-value'>{len(df)}</div><div class='stat-label'>Form Entries</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='stat-box'><div class='stat-value'>{df[col_name].nunique()}</div><div class='stat-label'>Active Members</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='stat-box'><div class='stat-value'>{sessions.sum()}</div><div class='stat-label'>Total Sessions</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='stat-box'><div class='stat-value'>{round(duration.sum()/60,1)}</div><div class='stat-label'>Total Hours</div></div>", unsafe_allow_html=True)

    st.markdown("### 🔥 Recent Activity")
    st.dataframe(df[[col_timestamp, col_name, col_muscles, col_duration]].sort_values(col_timestamp, ascending=False))

# -------------------------------------------------------------
#                    LEADERBOARD TAB
# -------------------------------------------------------------
with tab_lb:
    st.header("🏆 Leaderboard")

    lb = pd.DataFrame({
        "User": sessions.index,
        "Sessions": sessions.values,
        "Total Minutes": duration.values
    })
    lb["Hours"] = (lb["Total Minutes"] / 60).round(1)
    lb = lb.sort_values("Sessions", ascending=False).reset_index(drop=True)

    st.dataframe(lb)

# -------------------------------------------------------------
#                FITNESS ACTIVITY (NEW VISUALS)
# -------------------------------------------------------------
with tab_activity:
    st.header("🔥 Fitness Activity Dashboard")

    # 1. Total popularity of each muscle group
    pop_df = pd.DataFrame({
        "Muscle Group": list(muscle_popularity.keys()),
        "Count": list(muscle_popularity.values())
    }).sort_values("Count", ascending=False)

    st.subheader("🏋️ Most Trained Muscle Groups")
    fig1 = px.bar(pop_df, x="Muscle Group", y="Count",
                  color="Count", color_continuous_scale="Blues")
    st.plotly_chart(fig1, use_container_width=True)

    # 2. Pie chart breakdown
    st.subheader("🥧 Muscle Distribution")
    fig2 = px.pie(pop_df, names="Muscle Group", values="Count")
    st.plotly_chart(fig2, use_container_width=True)

    # 3. Sessions over time
    st.subheader("📅 Training Frequency Over Time")
    time_df = df.groupby(df[col_timestamp].dt.date).size().reset_index(name="Sessions")
    fig3 = px.line(time_df, x=col_timestamp, y="Sessions")
    st.plotly_chart(fig3, use_container_width=True)

# -------------------------------------------------------------
#                       PROFILE TAB
# -------------------------------------------------------------
with tab_profile:
    st.header("🧍 Solo Leveling Profile")

    users = sorted(df[col_name].unique())
    selected = st.selectbox("Select Member", users)

    total_sessions = sessions[selected]
    total_minutes = duration[selected]
    total_hours = round(total_minutes / 60, 1)

    st.markdown(f"## ⚔️ {selected} – Status Panel")

    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='stat-box'><div class='stat-value'>{total_sessions}</div><div class='stat-label'>Total Sessions</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='stat-box'><div class='stat-value'>{total_hours}</div><div class='stat-label'>Total Hours</div></div>", unsafe_allow_html=True)

    st.subheader("💪 Top Muscles")
    mus = pd.Series(user_muscles[selected]).sort_values(ascending=False)
    st.write(mus.head(5))

    st.subheader("📘 Workout Log")
    log = df[df[col_name] == selected][[col_timestamp, col_muscles, col_duration]]
    st.dataframe(log.sort_values(col_timestamp, ascending=False))
