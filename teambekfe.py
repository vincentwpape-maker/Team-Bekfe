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
    page_title="Team Bekfè Fitness Tracker",
    layout="wide",
)

# -------------------------------------------------------------
#                SOLO-LEVELING THEME CSS
# -------------------------------------------------------------
st.markdown(
    """
    <style>
    body {
        background-color: #05070c;
        color: #e5f4ff;
    }

    .main {
        background: radial-gradient(circle at top left, #10243f 0, #05070c 45%, #020309 100%);
    }

    /* Outer APP frame */
    .app-frame {
        border: 3px solid #30c8ff;
        border-radius: 18px;
        padding: 20px 24px 26px 24px;
        margin-top: 10px;
        box-shadow:
            0 0 18px rgba(48, 200, 255, 0.7),
            0 0 40px rgba(15, 115, 210, 0.5);
        background: radial-gradient(circle at top, #08101d 0, #05070c 55%, #020308 100%);
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
        margin-bottom: 6px;
    }

    /* Inner section frame (per tab) */
    .section-frame {
        border: 2px solid #1e6fb5;
        border-radius: 16px;
        padding: 20px 25px;
        margin-top: 12px;
        box-shadow: 0 0 18px rgba(30, 111, 181, 0.6);
        background: linear-gradient(135deg, #070b13 0%, #05060b 40%, #090f1b 100%);
    }

    /* Headers */
    .glow-header {
        font-size: 26px;
        font-weight: 800;
        color: #7fd1ff !important;
        text-shadow: 0 0 10px #3f9dff, 0 0 20px #12a5ff;
        border-bottom: 2px solid #2f9dff;
        padding-bottom: 4px;
        margin-bottom: 15px;
        display: inline-block;
    }

    .sub-header {
        font-size: 18px;
        font-weight: 700;
        color: #9bd4ff !important;
        text-shadow: 0 0 6px #217ac6;
        margin-top: 18px;
        margin-bottom: 6px;
    }

    /* Stat boxes */
    .stat-box {
        padding: 18px;
        background: radial-gradient(circle at top, #101927 0, #050810 55%, #04060c 100%);
        border: 1px solid #245b8f;
        border-radius: 14px;
        text-align: center;
        box-shadow:
            0 0 20px rgba(22, 113, 194, 0.8),
            0 0 30px rgba(0, 0, 0, 0.8);
        margin-bottom: 16px;
    }

    .stat-value {
        font-size: 38px;
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

    /* Season summary line in profile */
    .summary-line {
        font-size: 15px;
        color: #c3ddff;
        background: rgba(8, 21, 37, 0.85);
        border-radius: 8px;
        padding: 8px 12px;
        border: 1px solid #2f7fd4;
        box-shadow: 0 0 12px rgba(46, 147, 255, 0.6);
        margin-bottom: 10px;
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

    /* Dataframe hover */
    .dataframe tbody tr:hover {
        background-color: rgba(25, 118, 210, 0.25) !important;
    }

    /* Plotly background transparent */
    .js-plotly-plot .plotly {
        background: transparent !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
#                LOAD CSV FROM GOOGLE SHEETS
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

# Identify columns based on position
col_timestamp = df.columns[0]
col_name      = df.columns[1]
col_muscles   = df.columns[3]
col_duration  = df.columns[4]

df[col_timestamp] = pd.to_datetime(df[col_timestamp], errors="coerce")

# -------------------------------------------------------------
#                CLEAN USER NAMES
# -------------------------------------------------------------
def clean_name(name):
    if not isinstance(name, str):
        return ""
    n = re.sub(r"[^a-z0-9 ]", "", name.strip().lower())

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
#                PARSE DURATION (SAFE → MINUTES)
# -------------------------------------------------------------
def parse_duration(text):
    if not isinstance(text, str):
        return 0
    s = text.lower()

    hours = 0
    minutes = 0

    h = re.search(r"(\d+)\s*(hour|hours|hr|hrs|h)\b", s)
    m = re.search(r"(\d+)\s*(minute|minutes|min|mins|m)\b", s)

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

    total = hours * 60 + minutes
    return max(total, 0)

df["minutes"] = df[col_duration].apply(parse_duration)

# -------------------------------------------------------------
#                MUSCLE EXTRACTION + COUNTS
# -------------------------------------------------------------
def extract_muscles(txt):
    if not isinstance(txt, str):
        return []
    return [p.split("(")[0].strip() for p in txt.split(",") if p.strip()]

user_muscles = defaultdict(lambda: defaultdict(int))
overall_muscles = defaultdict(int)

for _, row in df.iterrows():
    name = row[col_name]
    muscles = extract_muscles(row[col_muscles])
    for m in muscles:
        user_muscles[name][m] += 1
        overall_muscles[m] += 1

# Sessions + Duration per user
sessions = df.groupby(col_name).size()
duration = df.groupby(col_name)["minutes"].sum()

# Time series for sessions
df["date"] = df[col_timestamp].dt.date
sessions_per_day = df.groupby("date").size().reset_index(name="sessions")
if not sessions_per_day.empty:
    sessions_per_day["7day_avg"] = sessions_per_day["sessions"].rolling(7, min_periods=1).mean()
else:
    sessions_per_day["7day_avg"] = []

# Data for charts
mus_df = pd.DataFrame({
    "Muscle": list(overall_muscles.keys()),
    "Count": list(overall_muscles.values()),
})

hours_df = pd.DataFrame({
    "User": duration.index,
    "Hours": (duration / 60).round(1),
}).sort_values("Hours", ascending=False)

activity_matrix = pd.DataFrame(user_muscles).fillna(0).astype(int).T  # Users rows, muscles columns

users = sorted(df[col_name].unique())

# -------------------------------------------------------------
#                APP FRAME + TITLE
# -------------------------------------------------------------
st.markdown("<div class='app-frame'>", unsafe_allow_html=True)
st.markdown("<div class='main-title'>Team Bekfè Fitness Tracker</div>", unsafe_allow_html=True)

# Tabs in order: Profile, Leaderboards, Fitness Activity, Dashboard
tab_profile, tab_lb, tab_activity, tab_dash = st.tabs(
    ["Profile", "Leaderboards", "Fitness Activity", "Dashboard"]
)

# =============================================================
#                      PROFILE TAB
# =============================================================
with tab_profile:
    st.markdown("<div class='section-frame'>", unsafe_allow_html=True)
    st.markdown("<div class='glow-header'>Profile</div>", unsafe_allow_html=True)

    if not users:
        st.write("No data yet.")
    else:
        selected = st.selectbox("Select Member", users)

        total_sessions_user = int(sessions.get(selected, 0))
        total_minutes_user = int(duration.get(selected, 0))
        total_hours_user = round(total_minutes_user / 60, 1)

        today = dt.date.today()
        season_year = today.year
        season_end = dt.date(season_year, 12, 31)
        days_left = (season_end - today).days

        season_str = (
            f"<div class='summary-line'>"
            f"<b>Season:</b> {season_year} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Current Date:</b> {today.strftime('%m/%d/%Y')} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Season ends in:</b> {days_left} days"
            f"</div>"
        )
        st.markdown(season_str, unsafe_allow_html=True)

        st.markdown(f"<div class='sub-header'>{selected} – Status Window</div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.markdown(
            f"<div class='stat-box'><div class='stat-value'>{total_sessions_user}</div>"
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
        mus_series = pd.Series(user_muscles[selected]).sort_values(ascending=False)
        st.write(mus_series.head(5))

        st.markdown("<div class='sub-header'>📘 Workout Log</div>", unsafe_allow_html=True)
        log = df[df[col_name] == selected][[col_timestamp, col_muscles, col_duration]]
        st.dataframe(
            log.sort_values(col_timestamp, ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

# =============================================================
#                      LEADERBOARD TAB
# =============================================================
with tab_lb:
    st.markdown("<div class='section-frame'>", unsafe_allow_html=True)
    st.markdown("<div class='glow-header'>Leaderboards</div>", unsafe_allow_html=True)

    lb = pd.DataFrame({
        "User": sessions.index,
        "Sessions": sessions.values,
        "Total Minutes": duration.values,
    })
    lb["Hours"] = (lb["Total Minutes"] / 60).round(1)
    lb = lb.sort_values("Sessions", ascending=False).reset_index(drop=True)
    lb.index = lb.index + 1
    lb.insert(0, "Rank", lb.index)

    st.dataframe(lb, hide_index=True, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =============================================================
#                  FITNESS ACTIVITY TAB
# =============================================================
with tab_activity:
    st.markdown("<div class='section-frame'>", unsafe_allow_html=True)
    st.markdown("<div class='glow-header'>Fitness Activity</div>", unsafe_allow_html=True)

    # 1. Most trained muscle group
    st.markdown("<div class='sub-header'>🔥 Most Trained Muscle Groups</div>", unsafe_allow_html=True)
    if not mus_df.empty:
        fig1 = px.bar(
            mus_df.sort_values("Count", ascending=False),
            x="Muscle",
            y="Count",
        )
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.write("No muscle data yet.")

    # 2. Total hours per member (highest → lowest)
    st.markdown("<div class='sub-header'>⏳ Total Hours per Member</div>", unsafe_allow_html=True)
    if not hours_df.empty:
        fig2 = px.bar(
            hours_df,
            x="User",
            y="Hours",
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.write("No duration data yet.")

    # 3. Muscle distribution pie chart
    st.markdown("<div class='sub-header'>💪 Muscle Distribution</div>", unsafe_allow_html=True)
    if not mus_df.empty:
        fig3 = px.pie(
            mus_df,
            names="Muscle",
            values="Count",
            hole=0.45,
        )
        st.plotly_chart(fig3, use_container_width=True)

    # 4. Training frequency (7-day average)
    st.markdown("<div class='sub-header'>📅 Training Frequency (7-Day Avg)</div>", unsafe_allow_html=True)
    if not sessions_per_day.empty:
        fig4 = px.line(
            sessions_per_day,
            x="date",
            y="7day_avg",
            labels={"date": "Date", "7day_avg": "Sessions (7-day avg)"},
        )
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.write("No time-series data yet.")

    # 5. Sessions over time (daily)
    st.markdown("<div class='sub-header'>📈 Sessions Over Time</div>", unsafe_allow_html=True)
    if not sessions_per_day.empty:
        fig5 = px.line(
            sessions_per_day,
            x="date",
            y="sessions",
            labels={"date": "Date", "sessions": "Sessions"},
        )
        st.plotly_chart(fig5, use_container_width=True)

    # 6. User × Muscle frequency table
    st.markdown("<div class='sub-header'>📊 User × Muscle Frequency Table</div>", unsafe_allow_html=True)
    if not activity_matrix.empty:
        st.dataframe(activity_matrix, use_container_width=True)
    else:
        st.write("No muscle breakdown data yet.")

    st.markdown("</div>", unsafe_allow_html=True)

# =============================================================
#                      DASHBOARD TAB
# =============================================================
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
    total_hours_all = round(duration.sum() / 60, 1)
    c4.markdown(
        f"<div class='stat-box'><div class='stat-value'>{total_hours_all}</div>"
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
#                CLOSE APP FRAME
# -------------------------------------------------------------
st.markdown("</div>", unsafe_allow_html=True)
