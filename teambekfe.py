import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
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

    /* Headings */
    h1, h2, h3, h4 {
        color: #67c1ff;
        text-shadow: 0px 0px 10px #0e639c;
        font-weight: 700 !important;
    }

    /* Tabs */
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

    /* Stat Panels */
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
#                LOAD GOOGLE SHEET DATA
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
#                NAME NORMALIZATION + MERGING
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

    if n in corrections:
        return corrections[n]
    return n.title()

df[col_name] = df[col_name].apply(clean_name)

# -------------------------------------------------------------
#                DURATION PARSER
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
#                BUILD SESSIONS + MUSCLE TABLE
# -------------------------------------------------------------
sessions = df.groupby(col_name).size().rename("sessions")
duration = df.groupby(col_name)["minutes"].sum().rename("total_minutes")

def extract_muscles(cell):
    if not isinstance(cell, str):
        return []
    parts = [p.split("(")[0].strip() for p in cell.split(",")]
    return [p for p in parts if p]

user_muscle_counts = defaultdict(lambda: defaultdict(int))
all_muscles = set()

for _, row in df.iterrows():
    name = row[col_name]
    muscles = extract_muscles(row[col_muscles])
    for m in muscles:
        user_muscle_counts[name][m] += 1
        all_muscles.add(m)

users = sorted(sessions.index.tolist())
all_muscles = sorted(all_muscles)

activity_matrix = pd.DataFrame(0, index=all_muscles, columns=users)

for user, mus_dict in user_muscle_counts.items():
    for m, v in mus_dict.items():
        activity_matrix.loc[m, user] = v


# -------------------------------------------------------------
#                          UI TABS
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

    c1, c2, c3, c4 = st.columns(4)
    
    c1.markdown(f"<div class='stat-box'><div class='stat-value'>{len(df)}</div><div class='stat-label'>Form Entries</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='stat-box'><div class='stat-value'>{df[col_name].nunique()}</div><div class='stat-label'>Active Members</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='stat-box'><div class='stat-value'>{int(sessions.sum())}</div><div class='stat-label'>Total Sessions</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='stat-box'><div class='stat-value'>{round(duration.sum()/60,1)}</div><div class='stat-label'>Total Hours</div></div>", unsafe_allow_html=True)

    st.markdown("### 🔥 Recent Activity")
    st.dataframe(
        df[[col_timestamp, col_name, col_muscles, col_duration]].sort_values(
            col_timestamp, ascending=False
        ),
        use_container_width=True
    )

# -------------------------------------------------------------
#                    LEADERBOARD TAB
# -------------------------------------------------------------
with tab_lb:
    st.header("🏆 Leaderboard – Total Sessions")

    lb = pd.concat([sessions, duration], axis=1).fillna(0).reset_index()
    lb["hours"] = (lb["total_minutes"] / 60).round(1)
    lb = lb.rename(columns={col_name: "User"})
    lb = lb.sort_values("sessions", ascending=False).reset_index(drop=True)
    lb.index = lb.index + 1
    lb.insert(0, "Rank", lb.index)

    st.dataframe(lb, use_container_width=True)

# -------------------------------------------------------------
#                 FITNESS ACTIVITY TAB
# -------------------------------------------------------------
with tab_activity:
    st.header("💠 Muscle Activity Heatmap")

    heat_df = (
        activity_matrix.reset_index()
        .melt(id_vars="index", var_name="User", value_name="Count")
        .rename(columns={"index": "Muscle"})
    )

    chart = alt.Chart(heat_df).mark_rect().encode(
        x=alt.X("User:O", title="User"),
        y=alt.Y("Muscle:O", title="Muscle Group"),
        color=alt.Color("Count:Q", scale=alt.Scale(scheme="blues")),
        tooltip=["User", "Muscle", "Count"]
    )

    st.altair_chart(chart, use_container_width=True)

    st.markdown("### Raw Table")
    st.dataframe(activity_matrix, use_container_width=True)

# -------------------------------------------------------------
#                       PROFILE TAB
# -------------------------------------------------------------
with tab_profile:
    st.header("🧍 Solo Leveling Profile Panel")

    selected = st.selectbox("Select Member", users)

    total_sessions = sessions[selected]
    total_minutes = duration[selected]
    total_hours = round(total_minutes / 60, 1)

    today = dt.date.today()
    season_end = dt.date(today.year, 12, 31)
    days_left = (season_end - today).days

    st.markdown(f"## ⚔️ {selected} – Status Window")

    c1, c2, c3 = st.columns(3)

    c1.markdown(f"<div class='stat-box'><div class='stat-value'>{total_sessions}</div><div class='stat-label'>Fitness Days</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='stat-box'><div class='stat-value'>{total_hours}</div><div class='stat-label'>Total Hours</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='stat-box'><div class='stat-value'>{days_left}</div><div class='stat-label'>Days Left in Season</div></div>", unsafe_allow_html=True)

    st.markdown("### 💪 Top Muscles Used")
    mus = pd.Series(user_muscle_counts[selected]).sort_values(ascending=False)
    st.write(mus.head(5))

    st.markdown("### 💤 Least Used Muscles")
    st.write(mus.tail(5))

    st.markdown("### 📘 Workout Log")
    log = df[df[col_name] == selected][[col_timestamp, col_muscles, col_duration]]
    st.dataframe(log.sort_values(col_timestamp, ascending=False), use_container_width=True)
