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
st.set_page_config(page_title="Team BekFê Fitness Tracker", layout="wide")

# -------------------------------------------------------------
#                SOLO-LEVELING THEME CSS
# -------------------------------------------------------------
st.markdown("""
<style>
body { background-color: #05070c; color: #e5f4ff; }
.main { background: radial-gradient(circle at top left, #10243f 0, #05070c 45%, #020309 100%); }

/* Title */
.main-title {
    font-size: 40px; font-weight: 900; text-align: center;
    color: #e5f4ff;
    text-shadow: 0 0 6px #ffffff, 0 0 16px #3f9dff, 0 0 32px #00c4ff;
    margin-bottom: 5px;
}

/* Section frame */
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
    font-size: 26px; font-weight: 800;
    color: #7fd1ff !important;
    text-shadow: 0 0 10px #3f9dff;
    border-bottom: 2px solid #2f9dff;
    padding-bottom: 4px;
    margin-bottom: 15px;
    display: inline-block;
}

.sub-header {
    font-size: 18px; font-weight: 700;
    color: #9bd4ff !important;
    text-shadow: 0 0 6px #217ac6;
    margin-top: 15px;
}

/* Stat boxes */
.stat-box {
    padding: 18px;
    background: #101927;
    border: 1px solid #245b8f;
    border-radius: 14px;
    text-align: center;
    box-shadow: 0 0 20px rgba(22,113,194,.7);
}

.stat-value {
    font-size: 38px;
    font-weight: 900;
    color: #7fd1ff;
    text-shadow: 0 0 12px #19a3ff;
}

.summary-line {
    font-size: 15px; color: #c3ddff;
    background: rgba(8,21,37,.8);
    border-radius: 8px;
    padding: 8px 12px;
    border: 1px solid #2f7fd4;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
#                LOAD CSV FROM GOOGLE SHEETS
# -------------------------------------------------------------
CSV_URL = "https://docs.google.com/spreadsheets/d/1XQEJH-s0Z6LrutwTTSvS0cYR1e3Tiqi6VqUkGQ-S3Lg/export?format=csv&gid=2121731071"

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = [c.strip() for c in df.columns]
    return df

df = load_data()

# Identify columns
col_timestamp = df.columns[0]
col_name = df.columns[1]
col_muscles = df.columns[3]
col_duration = df.columns[4]

df[col_timestamp] = pd.to_datetime(df[col_timestamp], errors="coerce")

# -------------------------------------------------------------
#                CLEAN USER NAMES
# -------------------------------------------------------------
def clean_name(name):
    if not isinstance(name, str):
        return ""
    n = re.sub(r"[^a-z0-9 ]", "", name.strip().lower())
    corrections = {
        "vincent": "Vincent", "alain": "Alain", "danimix": "Danimix",
        "dani mix": "Danimix", "dimitri": "Dimitri", "douglas": "Douglas",
        "louis": "Louis", "bousik": "Bousik", "gregory": "Gregory",
        "mikael": "Mikael", "junior": "Junior"
    }
    return corrections.get(n, n.title())

df[col_name] = df[col_name].apply(clean_name)

# -------------------------------------------------------------
#                PARSE DURATION (SAFE)
# -------------------------------------------------------------
def parse_duration(text):
    if not isinstance(text, str):
        return 0
    s = text.lower()
    h = re.search(r"(\d+)\s*(hour|hr|h)", s)
    m = re.search(r"(\d+)\s*(min|minute|m)", s)
    hours = int(h.group(1)) if h else 0
    minutes = int(m.group(1)) if m else 0
    if not h and not m:
        nums = re.findall(r"\d+", s)
        if len(nums) == 1: minutes = int(nums[0])
        if len(nums) == 2: hours, minutes = int(nums[0]), int(nums[1])
    return hours * 60 + minutes

df["minutes"] = df[col_duration].apply(parse_duration)

# -------------------------------------------------------------
#                MUSCLE EXTRACTION + COUNTS
# -------------------------------------------------------------
def extract_muscles(txt):
    if not isinstance(txt, str): return []
    return [p.split("(")[0].strip() for p in txt.split(",") if p.strip()]

user_muscles = defaultdict(lambda: defaultdict(int))
overall_muscles = defaultdict(int)

for _, r in df.iterrows():
    muscles = extract_muscles(r[col_muscles])
    for m in muscles:
        user_muscles[r[col_name]][m] += 1
        overall_muscles[m] += 1

# Sessions + Duration per user
sessions = df.groupby(col_name).size()
duration = df.groupby(col_name)["minutes"].sum()

# Time series
df["date"] = df[col_timestamp].dt.date
sessions_per_day = df.groupby("date").size().reset_index(name="sessions")
sessions_per_day["7day_avg"] = sessions_per_day["sessions"].rolling(7).mean()

# -------------------------------------------------------------
#                TOP TITLE
# -------------------------------------------------------------
st.markdown("<div class='main-title'>⚔️ Team BekFê Fitness Tracker ⚔️</div>", unsafe_allow_html=True)

# Tabs
tab_dash, tab_lb, tab_activity, tab_profile = st.tabs(
    ["Dashboard", "Leaderboards", "Fitness Activity", "Profile"]
)

# =============================================================
#                      DASHBOARD
# =============================================================
with tab_dash:
    st.markdown("<div class='section-frame'>", unsafe_allow_html=True)
    st.markdown("<div class='glow-header'>Dashboard Overview</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='stat-box'><div class='stat-value'>{len(df)}</div>Entries</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='stat-box'><div class='stat-value'>{df[col_name].nunique()}</div>Members</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='stat-box'><div class='stat-value'>{sessions.sum()}</div>Sessions</div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='stat-box'><div class='stat-value'>{round(duration.sum()/60,1)}</div>Hours</div>", unsafe_allow_html=True)

    st.dataframe(df[[col_timestamp, col_name, col_muscles, col_duration]].sort_values(col_timestamp, ascending=False), hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =============================================================
#                      LEADERBOARDS
# =============================================================
with tab_lb:
    st.markdown("<div class='section-frame'>", unsafe_allow_html=True)
    st.markdown("<div class='glow-header'>Leaderboard</div>", unsafe_allow_html=True)

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
#                      FITNESS ACTIVITY
# =============================================================
with tab_activity:
    st.markdown("<div class='section-frame'>", unsafe_allow_html=True)
    st.markdown("<div class='glow-header'>Fitness Activity</div>", unsafe_allow_html=True)

    # 1 — Most Trained Muscle Group
    st.markdown("<div class='sub-header'>🔥 Most Trained Muscle Groups</div>", unsafe_allow_html=True)
    mus_df = pd.DataFrame({"Muscle": list(overall_muscles.keys()), "Count": list(overall_muscles.values())})
    fig1 = px.bar(mus_df.sort_values("Count", ascending=False), x="Muscle", y="Count")
    st.plotly_chart(fig1, use_container_width=True)

    # 2 — Total Hours per Member (sorted highest → lowest)
    st.markdown("<div class='sub-header'>⏳ Total Hours per Member</div>", unsafe_allow_html=True)
    hours_df = (duration/60).round(1).reset_index().rename(columns={col_name:"User", 0:"Hours"})
    hours_df = hours_df.sort_values("minutes", ascending=False)
    hours_df = pd.DataFrame({"User": duration.index, "Hours": (duration/60).round(1)})
    hours_df = hours_df.sort_values("Hours", ascending=False)
    fig2 = px.bar(hours_df, x="User", y="Hours")
    st.plotly_chart(fig2, use_container_width=True)

    # 3 — Muscle Distribution
    st.markdown("<div class='sub-header'>💪 Muscle Distribution</div>", unsafe_allow_html=True)
    fig3 = px.pie(mus_df, names="Muscle", values="Count", hole=.45)
    st.plotly_chart(fig3, use_container_width=True)

    # 4 — Training Frequency 7-day average
    st.markdown("<div class='sub-header'>📅 Training Frequency (7-Day Avg)</div>", unsafe_allow_html=True)
    fig4 = px.line(sessions_per_day, x="date", y="7day_avg")
    st.plotly_chart(fig4, use_container_width=True)

    # 5 — Sessions Over Time
    st.markdown("<div class='sub-header'>📈 Sessions Over Time</div>", unsafe_allow_html=True)
    fig5 = px.line(sessions_per_day, x="date", y="sessions")
    st.plotly_chart(fig5, use_container_width=True)

    # 6 — User × Muscle Frequency Table
    st.markdown("<div class='sub-header'>📊 User × Muscle Frequency Table</div>", unsafe_allow_html=True)
    full_mat = pd.DataFrame(user_muscles).fillna(0).astype(int)
    st.dataframe(full_mat, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =============================================================
#                      PROFILE TAB
# =============================================================
with tab_profile:
    st.markdown("<div class='section-frame'>", unsafe_allow_html=True)
    st.markdown("<div class='glow-header'>Profile</div>", unsafe_allow_html=True)

    users = sorted(df[col_name].unique())
    selected = st.selectbox("Select Member", users)

    total_sessions = sessions[selected]
    mins = duration[selected]
    hrs = round(mins / 60, 1)

    today = dt.date.today()
    season_end = dt.date(today.year, 12, 31)
    days_left = (season_end - today).days

    st.markdown(
        f"<div class='summary-line'><b>Season:</b> {today.year} | "
        f"<b>Today:</b> {today} | "
        f"<b>Days left:</b> {days_left}</div>",
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='stat-box'><div class='stat-value'>{total_sessions}</div>Sessions</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='stat-box'><div class='stat-value'>{hrs}</div>Hours</div>", unsafe_allow_html=True)

    st.markdown("<div class='sub-header'>💪 Top Muscles Used</div>", unsafe_allow_html=True)
    mus_series = pd.Series(user_muscles[selected]).sort_values(ascending=False)
    st.write(mus_series.head(5))

    st.markdown("<div class='sub-header'>📘 Workout Log</div>", unsafe_allow_html=True)
    log = df[df[col_name] == selected][[col_timestamp, col_muscles, col_duration]]
    st.dataframe(log.sort_values(col_timestamp, ascending=False), hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)
