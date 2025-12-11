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
    }
    .stat-label {
        font-size: 15px;
        color: #9bb8d1;
    }

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

    .featured-line {
        font-size: 16px;
        color: #ffe8a3;
        background: rgba(34, 22, 6, 0.9);
        border-radius: 8px;
        padding: 8px 12px;
        border: 1px solid #facc15;
        box-shadow: 0 0 14px rgba(250, 204, 21, 0.7);
        margin-bottom: 14px;
    }

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

# Column IDs
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
        "vincent": "Vincent", "alain": "Alain", "danimix": "Danimix",
        "dani mix": "Danimix", "dimitri": "Dimitri", "douglas": "Douglas",
        "louis": "Louis", "bousik": "Bousik", "gregory": "Gregory",
        "mikael": "Mikael", "junior": "Junior"
    }
    return corrections.get(n, n.title())

df[col_name] = df[col_name].apply(clean_name)

# -------------------------------------------------------------
#                PARSE DURATION (MINUTES)
# -------------------------------------------------------------
def parse_duration(text):
    if not isinstance(text, str):
        return 0
    s = text.lower()

    hours = minutes = 0
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

    return max(hours * 60 + minutes, 0)

df["minutes"] = df[col_duration].apply(parse_duration)

# -------------------------------------------------------------
#                MUSCLE EXTRACTION
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

sessions = df.groupby(col_name).size()
duration = df.groupby(col_name)["minutes"].sum()

df["date"] = df[col_timestamp].dt.date
sessions_per_day = df.groupby("date").size().reset_index(name="sessions")
sessions_per_day["7day_avg"] = sessions_per_day["sessions"].rolling(7, min_periods=1).mean()

mus_df = pd.DataFrame(
    {"Muscle": list(overall_muscles.keys()), "Count": list(overall_muscles.values())}
)
hours_df = pd.DataFrame(
    {"User": duration.index, "Hours": (duration / 60).round(1)}
).sort_values("Hours", ascending=False)
activity_matrix = pd.DataFrame(user_muscles).fillna(0).astype(int).T
users = sorted(df[col_name].unique())

# -------------------------------------------------------------
#                CONSISTENCY RANK SYSTEM (S–E RANK ATHLETE)
# -------------------------------------------------------------
# Realistic thresholds based on sessions in a 365-day season
def get_rank_letter(sessions_count: int) -> str:
    if sessions_count >= 250:
        return "S"
    elif sessions_count >= 180:
        return "A"
    elif sessions_count >= 120:
        return "B"
    elif sessions_count >= 60:
        return "C"
    elif sessions_count >= 30:
        return "D"
    else:
        return "E"

RANK_CONFIG = {
    "S": {
        "label": "S-Rank Athlete",
        "color": "#e9d5ff",  # light purple
        "emoji": "👑",
    },
    "A": {
        "label": "A-Rank Athlete",
        "color": "#93c5fd",  # blue
        "emoji": "💎",
    },
    "B": {
        "label": "B-Rank Athlete",
        "color": "#6ee7b7",  # green
        "emoji": "💎",
    },
    "C": {
        "label": "C-Rank Athlete",
        "color": "#fde68a",  # yellow
        "emoji": "💎",
    },
    "D": {
        "label": "D-Rank Athlete",
        "color": "#fed7aa",  # orange
        "emoji": "💎",
    },
    "E": {
        "label": "E-Rank Athlete",
        "color": "#9ca3af",  # grey
        "emoji": "💎",
    },
}

def render_rank_badge(rank_letter: str, consistency: float | None = None) -> str:
    cfg = RANK_CONFIG.get(rank_letter, RANK_CONFIG["E"])
    label = cfg["label"]
    color = cfg["color"]
    emoji = cfg["emoji"]
    if consistency is not None:
        return (
            f"<span style='color:{color}; font-weight:800;'>"
            f"{emoji} {label} • {consistency:.1f}%"
            f"</span>"
        )
    else:
        return (
            f"<span style='color:{color}; font-weight:800;'>"
            f"{emoji} {label}"
            f"</span>"
        )

# Maps for each user
consistency_map = {}
rank_map = {}

for user in sessions.index:
    s_count = int(sessions.get(user, 0))
    consistency_pct = (s_count / 365) * 100
    consistency_map[user] = round(consistency_pct, 1)
    rank_letter = get_rank_letter(s_count)
    rank_map[user] = rank_letter

# Featured athlete = most sessions
top_user = sessions.idxmax()
top_user_sessions = int(sessions[top_user])
top_user_consistency = consistency_map.get(top_user, 0.0)
top_user_rank_letter = rank_map.get(top_user, "E")

# -------------------------------------------------------------
#                TOP BUTTON (GOOGLE FORM)
# -------------------------------------------------------------
st.markdown("""
### Log Your Fitness Sessions
<a href="https://docs.google.com/forms/d/1JqTx8Fd5la2BGv4h5s1506KZMVQUqHL2U0pNvKs0KTo/edit" target="_blank"
   style="
       background:#0d1b2a;
       padding:10px 20px;
       border-radius:8px;
       border:1px solid #3ecbff;
       color:#aee6ff;
       font-size:16px;
       text-decoration:none;
       box-shadow:0 0 10px #23b0ff;
   ">
   ➤ Submit Entry
</a>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>Team Bekfè Fitness Tracker</div>", unsafe_allow_html=True)

# -------------------------------------------------------------
#                TAB ORDER
# -------------------------------------------------------------
tab_profile, tab_lb, tab_activity, tab_dash, tab_ranks = st.tabs(
    ["Profile", "Leaderboards", "Fitness Activity", "Dashboard", "Ranking System"]
)

# =============================================================
#                      PROFILE TAB
# =============================================================
with tab_profile:
    st.markdown("<div class='glow-header'>Profile</div>", unsafe_allow_html=True)

    # Featured Athlete banner (highest sessions)
    featured_badge_html = render_rank_badge(top_user_rank_letter, top_user_consistency)
    st.markdown(
        f"<div class='featured-line'>🏆 Featured Athlete: <b>{top_user}</b> – "
        f"{featured_badge_html} – <b>{top_user_sessions}</b> sessions</div>",
        unsafe_allow_html=True
    )

    # Default selection = top user
    selected = st.selectbox(
        "Select Member",
        users,
        index=users.index(top_user) if top_user in users else 0
    )

    total_sessions_user = int(sessions.get(selected, 0))
    total_minutes_user = int(duration.get(selected, 0))
    total_hours_user = round(total_minutes_user / 60, 1)
    consistency_user = consistency_map.get(selected, 0.0)
    rank_letter_user = rank_map.get(selected, "E")
    rank_badge_html = render_rank_badge(rank_letter_user, consistency_user)

    today = dt.date.today()
    season_year = today.year
    season_end = dt.date(season_year, 12, 31)
    days_left = (season_end - today).days

    st.markdown(
        f"<div class='summary-line'><b>Season:</b> {season_year} | "
        f"<b>Current Date:</b> {today.strftime('%m/%d/%Y')} | "
        f"<b>Season ends in:</b> {days_left} days</div>",
        unsafe_allow_html=True
    )

    # Name + Rank in header
    st.markdown(
        f"<div class='sub-header'>{selected} – {rank_badge_html}</div>",
        unsafe_allow_html=True
    )

    # --- STAT BOXES ------------------------------------------
    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(
        f"<div class='stat-box'>"
        f"<div class='stat-value'>{total_sessions_user}</div>"
        f"<div class='stat-label'>Total Sessions</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    c2.markdown(
        f"<div class='stat-box'>"
        f"<div class='stat-value'>{total_hours_user}</div>"
        f"<div class='stat-label'>Total Hours</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    c3.markdown(
        f"<div class='stat-box'>"
        f"<div class='stat-value'>{days_left}</div>"
        f"<div class='stat-label'>Days Left</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    c4.markdown(
        f"<div class='stat-box'>"
        f"<div class='stat-value'>{consistency_user:.1f}%</div>"
        f"<div class='stat-label'>Season Consistency</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    st.markdown("<div class='sub-header'>💪 Top Muscles Used</div>", unsafe_allow_html=True)
    mus_series = pd.Series(user_muscles[selected]).sort_values(ascending=False)
    st.dataframe(mus_series.head(5), use_container_width=True)

    st.markdown("<div class='sub-header'>📘 Workout Log</div>", unsafe_allow_html=True)
    log = df[df[col_name] == selected][[col_timestamp, col_muscles, col_duration]]
    st.dataframe(
        log.sort_values(col_timestamp, ascending=False),
        use_container_width=True,
        hide_index=True
    )

# =============================================================
#                      LEADERBOARD TAB
# =============================================================
with tab_lb:
    st.markdown("<div class='glow-header'>Leaderboards</div>", unsafe_allow_html=True)

    lb = pd.DataFrame({
        "User": sessions.index,
        "Sessions": sessions.values,
        "Total Minutes": duration.values,
    })
    lb["Hours"] = (lb["Total Minutes"] / 60).round(1)
    lb["Consistency %"] = [consistency_map[u] for u in lb["User"]]
    lb["Rank Letter"] = [rank_map[u] for u in lb["User"]]
    lb["Rank Title"] = [RANK_CONFIG[r]["label"] for r in lb["Rank Letter"]]
    lb["Icon"] = [RANK_CONFIG[r]["emoji"] for r in lb["Rank Letter"]]

    # Sort by Sessions (highest first)
    lb = lb.sort_values("Sessions", ascending=False).reset_index(drop=True)
    lb.index = lb.index + 1
    lb.insert(0, "Position", lb.index)

    lb_display = lb[["Position", "User", "Icon", "Rank Title", "Consistency %", "Sessions", "Hours"]]

    st.dataframe(lb_display, hide_index=True, use_container_width=True)

# =============================================================
#                  FITNESS ACTIVITY TAB
# =============================================================
with tab_activity:
    st.markdown("<div class='glow-header'>Fitness Activity</div>", unsafe_allow_html=True)

    st.markdown("<div class='sub-header'>🔥 Most Trained Muscle Groups</div>", unsafe_allow_html=True)
    st.plotly_chart(
        px.bar(mus_df.sort_values("Count", ascending=False), x="Muscle", y="Count"),
        use_container_width=True
    )

    st.markdown("<div class='sub-header'>⏳ Total Hours per Member</div>", unsafe_allow_html=True)
    st.plotly_chart(
        px.bar(hours_df, x="User", y="Hours"),
        use_container_width=True
    )

    st.markdown("<div class='sub-header'>💪 Muscle Distribution</div>", unsafe_allow_html=True)
    st.plotly_chart(
        px.pie(mus_df, names="Muscle", values="Count", hole=0.45),
        use_container_width=True
    )

    st.markdown("<div class='sub-header'>📅 Training Frequency (7-Day Avg)</div>", unsafe_allow_html=True)
    st.plotly_chart(
        px.line(sessions_per_day, x="date", y="7day_avg"),
        use_container_width=True
    )

    st.markdown("<div class='sub-header'>📈 Sessions Over Time</div>", unsafe_allow_html=True)
    st.plotly_chart(
        px.line(sessions_per_day, x="date", y="sessions"),
        use_container_width=True
    )

    st.markdown("<div class='sub-header'>📊 User × Muscle Frequency Table</div>", unsafe_allow_html=True)
    st.dataframe(activity_matrix, use_container_width=True)

# =============================================================
#                      DASHBOARD TAB
# =============================================================
with tab_dash:
    st.markdown("<div class='glow-header'>Dashboard Overview</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        f"<div class='stat-box'>"
        f"<div class='stat-value'>{len(df)}</div>"
        f"<div class='stat-label'>Form Entries</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    c2.markdown(
        f"<div class='stat-box'>"
        f"<div class='stat-value'>{df[col_name].nunique()}</div>"
        f"<div class='stat-label'>Active Members</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    c3.markdown(
        f"<div class='stat-box'>"
        f"<div class='stat-value'>{int(sessions.sum())}</div>"
        f"<div class='stat-label'>Total Sessions</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    c4.markdown(
        f"<div class='stat-box'>"
        f"<div class='stat-value'>{round(duration.sum()/60,1)}</div>"
        f"<div class='stat-label'>Total Hours</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    st.markdown("<div class='sub-header'>🔥 Recent Activity</div>", unsafe_allow_html=True)
    st.dataframe(
        df.sort_values(col_timestamp, ascending=False).head(25),
        use_container_width=True,
        hide_index=True
    )

# =============================================================
#                      RANKING SYSTEM TAB
# =============================================================
with tab_ranks:
    st.markdown("<div class='glow-header'>Ranking System</div>", unsafe_allow_html=True)
    st.markdown(
        "Season = 365 days. Ranks are based on how many sessions you log in the season.",
        unsafe_allow_html=True,
    )

    rank_table = pd.DataFrame([
        {"Rank": "S-Rank Athlete", "Letter": "S", "Sessions Range": "250 – 365", "Approx Consistency": "68% – 100%"},
        {"Rank": "A-Rank Athlete", "Letter": "A", "Sessions Range": "180 – 249", "Approx Consistency": "49% – 68%"},
        {"Rank": "B-Rank Athlete", "Letter": "B", "Sessions Range": "120 – 179", "Approx Consistency": "33% – 49%"},
        {"Rank": "C-Rank Athlete", "Letter": "C", "Sessions Range": "60 – 119",  "Approx Consistency": "16% – 33%"},
        {"Rank": "D-Rank Athlete", "Letter": "D", "Sessions Range": "30 – 59",   "Approx Consistency": "8% – 16%"},
        {"Rank": "E-Rank Athlete", "Letter": "E", "Sessions Range": "0 – 29",    "Approx Consistency": "0% – 8%"},
    ])

    st.markdown("<div class='sub-header'>📜 Tier Breakdown</div>", unsafe_allow_html=True)
    st.dataframe(rank_table, use_container_width=True, hide_index=True)
