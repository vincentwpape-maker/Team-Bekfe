import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime as dt
import re
from collections import defaultdict

# -------------------------------------------------------------
#                PAGE CONFIG
# -------------------------------------------------------------
st.set_page_config(
    page_title="Team BekFê Fitness Tracker",
    layout="wide",
)

# -------------------------------------------------------------
#                SOLO-LEVELING THEME CSS
# -------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Global background */
    body {
        background-color: #05070c;
        color: #e5f4ff;
    }

    .main {
        background: radial-gradient(circle at top left, #10243f 0, #05070c 45%, #020309 100%);
    }

    /* Outer APP frame */
    .app-frame {
        border: 4px solid #30c8ff;
        border-radius: 20px;
        padding: 25px 30px 30px 30px;
        margin-top: 10px;
        box-shadow:
            0 0 20px rgba(48, 200, 255, 0.8),
            0 0 45px rgba(15, 115, 210, 0.6);
        background: radial-gradient(circle at top, #08101d 0, #05070c 55%, #020308 100%);
    }

    /* Inner section frame (per tab) */
    .section-frame {
        border: 2px solid #1e6fb5;
        border-radius: 16px;
        padding: 20px 22px 25px 22px;
        margin-top: 10px;
        box-shadow:
            0 0 18px rgba(30, 111, 181, 0.7),
            0 0 28px rgba(0, 0, 0, 0.9) inset;
        background: linear-gradient(135deg, #070b13 0%, #05060b 40%, #090f1b 100%);
    }

    /* Title at very top */
    .main-title {
        font-size: 40px;
        font-weight: 900;
        text-align: center;
        color: #e5f4ff;
        text-shadow:
            0 0 6px #ffffff,
            0 0 16px #3f9dff,
            0 0 32px #00c4ff;
        margin-bottom: 10px;
    }

    /* Section headers */
    .glow-header {
        font-size: 26px;
        font-weight: 800;
        color: #7fd1ff !important;
        text-shadow: 0 0 10px #3f9dff, 0 0 20px #12a5ff;
        border-bottom: 2px solid #2f9dff;
        padding-bottom: 4px;
        display: inline-block;
        margin-bottom: 15px;
    }

    /* Sub headers (like small section headings) */
    .sub-header {
        font-size: 18px;
        font-weight: 700;
        color: #9bd4ff !important;
        text-shadow: 0 0 6px #217ac6;
        margin-top: 15px;
        margin-bottom: 5px;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background: #080c13;
        border-radius: 12px;
        border: 1px solid #1f2a36;
        padding: 4px;
        box-shadow: 0 0 16px rgba(0, 0, 0, 0.9);
    }

    .stTabs [data-baseweb="tab"] {
        color: #9bb8ff;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background: radial-gradient(circle at top, #18446b 0, #07111e 60%);
        color: #ffffff !important;
        border-radius: 9px;
        box-shadow: 0 0 16px rgba(33, 150, 243, 0.9);
        border: 1px solid #34a9ff;
    }

    /* Stat boxes (big blue cards) */
    .stat-box {
        padding: 22px 15px;
        background: radial-gradient(circle at top, #101927 0, #050810 55%, #04060c 100%);
        border: 1px solid #245b8f;
        border-radius: 16px;
        text-align: center;
        box-shadow:
            0 0 20px rgba(22, 113, 194, 0.9),
            0 0 40px rgba(0, 0, 0, 0.8);
        margin-bottom: 18px;
    }

    .stat-value {
        font-size: 40px;
        font-weight: 900;
        color: #7fd1ff;
        text-shadow:
            0 0 8px #79c8ff,
            0 0 18px #19a3ff;
    }

    .stat-label {
        font-size: 15px;
        color: #9bb8d1;
    }

    /* Small stat boxes for profile summary line */
    .summary-line {
        font-size: 14px;
        color: #c3ddff;
        background: rgba(8, 21, 37, 0.85);
        border-radius: 8px;
        padding: 6px 10px;
        border: 1px solid #2f7fd4;
        box-shadow: 0 0 12px rgba(46, 147, 255, 0.6);
        margin-bottom: 10px;
    }

    /* Dataframe tweaks */
    .dataframe tbody tr:hover {
        background-color: rgba(25, 118, 210, 0.25) !important;
    }

    /* Make Plotly charts blend better */
    .js-plotly-plot .plotly {
        background: transparent !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
#                LOAD SHEET VIA CSV
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

    if n in corrections:
        return corrections[n]
    return n.title()

df[col_name] = df[col_name].apply(clean_name)

# -------------------------------------------------------------
#                DURATION PARSER
# -------------------------------------------------------------
def parse_duration(text: str) -> int:
    """Return duration in minutes."""
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

    # Fallbacks for things like "1h30" or "45"
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
#                METRICS & MUSCLE MATRIX
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

# Extra aggregation for plots
df["date"] = df[col_timestamp].dt.date
sessions_per_day = df.groupby("date").size().reset_index(name="sessions")
minutes_per_user = duration.reset_index().rename(columns={col_name: "User"})
overall_muscle_counts = (
    df[col_muscles]
    .astype(str)
    .apply(extract_muscles)
    .explode()
    .value_counts()
    .reset_index()
)
overall_muscle_counts.columns = ["Muscle", "Count"]

# -------------------------------------------------------------
#                APP FRAME START
# -------------------------------------------------------------
st.markdown("<div class='app-frame'>", unsafe_allow_html=True)

st.markdown("<div class='main-title'>⚔️ Team BekFê Fitness Tracker ⚔️</div>", unsafe_allow_html=True)

tab_dash, tab_lb, tab_activity, tab_profile = st.tabs(
    ["Dashboard", "Leaderboards", "Fitness Activity", "Profile"]
)

# -------------------------------------------------------------
#                    DASHBOARD TAB
# -------------------------------------------------------------
with tab_dash:
    st.markdown("<div class='section-frame'>", unsafe_allow_html=True)

    st.markdown("<div class='glow-header'>Dashboard Overview</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(
        f"<div class='stat-box'><div class='stat-value'>{len(df)}</div>"
        "<div class='stat-label'>Form Entries</div></div>",
        unsafe_allow_html=True,
    )
    c2.markdown(
        f"<div class='stat-box'><div class='stat-value'>{df[col_name].nunique()}</div>"
        "<div class='stat-label'>Active Members</div></div>",
        unsafe_allow_html=True,
    )
    c3.markdown(
        f"<div class='stat-box'><div class='stat-value'>{int(sessions.sum())}</div>"
        "<div class='stat-label'>Total Sessions</div></div>",
        unsafe_allow_html=True,
    )
    total_hours = round(duration.sum() / 60, 1)
    c4.markdown(
        f"<div class='stat-box'><div class='stat-value'>{total_hours}</div>"
        "<div class='stat-label'>Total Hours</div></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='sub-header'>🔥 Recent Activity</div>", unsafe_allow_html=True)
    st.dataframe(
        df[[col_timestamp, col_name, col_muscles, col_duration]]
        .sort_values(col_timestamp, ascending=False)
        .head(25),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------
#                    LEADERBOARD TAB
# -------------------------------------------------------------
with tab_lb:
    st.markdown("<div class='section-frame'>", unsafe_allow_html=True)

    st.markdown("<div class='glow-header'>Leaderboard</div>", unsafe_allow_html=True)

    lb = pd.concat([sessions, duration], axis=1).fillna(0).reset_index()
    lb["Hours"] = (lb["total_minutes"] / 60).round(1)
    lb = lb.rename(columns={col_name: "User", "sessions": "Sessions", "total_minutes": "Total Minutes"})
    lb = lb.sort_values("Sessions", ascending=False).reset_index(drop=True)
    lb.index = lb.index + 1
    lb.insert(0, "Rank", lb.index)

    st.dataframe(lb, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------
#                 FITNESS ACTIVITY TAB
# -------------------------------------------------------------
with tab_activity:
    st.markdown("<div class='section-frame'>", unsafe_allow_html=True)

    st.markdown("<div class='glow-header'>Fitness Activity</div>", unsafe_allow_html=True)

    # 1) Sessions over time
    st.markdown("<div class='sub-header'>📆 Sessions Over Time</div>", unsafe_allow_html=True)
    if not sessions_per_day.empty:
        fig_time = px.line(
            sessions_per_day,
            x="date",
            y="sessions",
            markers=True,
            labels={"date": "Date", "sessions": "Sessions"},
        )
        fig_time.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.write("No time-series data yet.")

    # 2) Total minutes per member
    st.markdown("<div class='sub-header'>🧍 Total Minutes per Member</div>", unsafe_allow_html=True)
    if not minutes_per_user.empty:
        fig_minutes = px.bar(
            minutes_per_user.sort_values("total_minutes", ascending=False),
            x="User",
            y="total_minutes",
            labels={"total_minutes": "Total Minutes"},
        )
        fig_minutes.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_minutes, use_container_width=True)

    # 3) Overall muscle usage
    st.markdown("<div class='sub-header'>💪 Overall Muscle Group Distribution</div>", unsafe_allow_html=True)
    if not overall_muscle_counts.empty:
        fig_muscles = px.pie(
            overall_muscle_counts,
            names="Muscle",
            values="Count",
            hole=0.45,
        )
        fig_muscles.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_muscles, use_container_width=True)

    # 4) Raw matrix (optional but useful)
    st.markdown("<div class='sub-header'>📊 User × Muscle Frequency Table</div>", unsafe_allow_html=True)
    st.dataframe(activity_matrix, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------
#                       PROFILE TAB
# -------------------------------------------------------------
with tab_profile:
    st.markdown("<div class='section-frame'>", unsafe_allow_html=True)

    st.markdown("<div class='glow-header'>Profile</div>", unsafe_allow_html=True)

    if not users:
        st.write("No data yet.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        selected = st.selectbox("Select Member", users)

        total_sessions = int(sessions[selected])
        total_minutes_user = int(duration[selected])
        total_hours_user = round(total_minutes_user / 60, 1)

        today = dt.date.today()
        season_year = today.year
        season_end = dt.date(season_year, 12, 31)
        days_left = (season_end - today).days

        # Season summary line
        season_str = (
            f"<div class='summary-line'>"
            f"<b>Season:</b> {season_year} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Current Date:</b> {today.strftime('%m/%d/%Y')} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Season ends in:</b> {days_left} days"
            f"</div>"
        )
        st.markdown(season_str, unsafe_allow_html=True)

        st.markdown(f"<div class='sub-header'>⚔️ {selected} – Status Window</div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.markdown(
            f"<div class='stat-box'><div class='stat-value'>{total_sessions}</div>"
            "<div class='stat-label'>Total Sessions</div></div>",
            unsafe_allow_html=True,
        )
        c2.markdown(
            f"<div class='stat-box'><div class='stat-value'>{total_hours_user}</div>"
            "<div class='stat-label'>Total Hours</div></div>",
            unsafe_allow_html=True,
        )
        c3.markdown(
            f"<div class='stat-box'><div class='stat-value'>{days_left}</div>"
            "<div class='stat-label'>Days Left in Season</div></div>",
            unsafe_allow_html=True,
        )

        st.markdown("<div class='sub-header'>💪 Top Muscles Used</div>", unsafe_allow_html=True)
        mus_series = pd.Series(user_muscle_counts[selected]).sort_values(ascending=False)
        st.write(mus_series.head(5))

        st.markdown("<div class='sub-header'>😴 Least Used Muscles</div>", unsafe_allow_html=True)
        st.write(mus_series.tail(5))

        st.markdown("<div class='sub-header'>📘 Workout Log</div>", unsafe_allow_html=True)
        log = df[df[col_name] == selected][[col_timestamp, col_muscles, col_duration]]
        st.dataframe(
            log.sort_values(col_timestamp, ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------
#                CLOSE APP FRAME
# -------------------------------------------------------------
st.markdown("</div>", unsafe_allow_html=True)
