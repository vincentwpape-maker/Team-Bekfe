import streamlit as st
import streamlit.components.v1 as components
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
#                GLOBAL STYLING (SOLO-LEVELING THEME)
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
        color: #e5f4ff;
        text-shadow: 0 0 12px #3f9dff;
        margin-bottom: 6px;
    }
    .glow-header {
        font-size: 26px;
        font-weight: 800;
        color: #7fd1ff !important;
        text-shadow: 0 0 10px #3f9dff;
        border-bottom: 2px solid #2f9dff;
        padding-bottom: 4px;
        margin-bottom: 15px;
        display: inline-block;
    }
    .sub-header {
        font-size: 18px;
        font-weight: 700;
        color: #9bd4ff !important;
        margin-top: 20px;
        margin-bottom: 6px;
        text-shadow: 0 0 6px #217ac6;
    }
    .stat-box {
        padding: 18px;
        background: radial-gradient(circle at top, #101927 0, #050810 55%);
        border-radius: 14px;
        text-align: center;
        border: 1px solid #245b8f;
        box-shadow: 0 0 24px rgba(0,150,255,0.4);
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
        font-size: 17px;
        color: #ffe8a3;
        background: rgba(34, 22, 6, 0.88);
        border-radius: 10px;
        padding: 10px 14px;
        border: 1px solid #facc15;
        box-shadow: 0 0 14px rgba(250,204,21,0.4);
        margin-bottom: 14px;
    }
    .summary-line {
        background: rgba(10,25,45,0.8);
        padding: 10px 16px;
        border-radius: 8px;
        border: 1px solid #3fa9ff;
        margin-bottom: 12px;
        color: #cce8ff;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------------------
#             LOAD GOOGLE SHEETS DATA
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
#             CLEANING + TRANSFORMATION
# -------------------------------------------------------------
col_timestamp = df.columns[0]
col_name = df.columns[1]
col_muscles = df.columns[3]
col_duration = df.columns[4]

df[col_timestamp] = pd.to_datetime(df[col_timestamp], errors="coerce")

def clean_name(n):
    if not isinstance(n, str): return ""
    n = re.sub(r"[^a-z0-9 ]","", n.lower().strip())
    corrections = {
        "vincent":"Vincent","alain":"Alain","danimix":"Danimix",
        "dani mix":"Danimix","dimitri":"Dimitri","douglas":"Douglas",
        "louis":"Louis","bousik":"Bousik","gregory":"Gregory",
        "mikael":"Mikael","junior":"Junior"
    }
    return corrections.get(n, n.title())

df[col_name] = df[col_name].apply(clean_name)

def parse_duration(t):
    if not isinstance(t,str): return 0
    t = t.lower()
    h = re.search(r"(\d+)\s*(hour|hr|h)", t)
    m = re.search(r"(\d+)\s*(min|m)", t)
    hours = int(h.group(1)) if h else 0
    mins  = int(m.group(1)) if m else 0
    if not h and not m:
        nums = re.findall(r"\d+", t)
        if len(nums)==1: mins = int(nums[0])
        elif len(nums)==2:
            hours = int(nums[0])
            mins = int(nums[1])
    return hours*60 + mins

df["minutes"] = df[col_duration].apply(parse_duration)

# -------------------------------------------------------------
#             MUSCLE EXTRACTION
# -------------------------------------------------------------
def extract_muscles(txt):
    if not isinstance(txt,str): return []
    return [x.split("(")[0].strip() for x in txt.split(",") if x.strip()]

user_muscles = defaultdict(lambda: defaultdict(int))
overall_muscles = defaultdict(int)

for _,row in df.iterrows():
    user = row[col_name]
    muscs = extract_muscles(row[col_muscles])
    for m in muscs:
        user_muscles[user][m] += 1
        overall_muscles[m] += 1

sessions = df.groupby(col_name).size()
duration = df.groupby(col_name)["minutes"].sum()

df["date"] = df[col_timestamp].dt.date
sessions_per_day = df.groupby("date").size().reset_index(name="sessions")
sessions_per_day["7day_avg"] = sessions_per_day["sessions"].rolling(7,1).mean()

mus_df = pd.DataFrame({"Muscle": list(overall_muscles.keys()), "Count": list(overall_muscles.values())})
hours_df = pd.DataFrame({"User": duration.index, "Hours": (duration/60).round(1)}).sort_values("Hours", ascending=False)
users = sorted(df[col_name].unique())

# -------------------------------------------------------------
#               RANK SYSTEM LOGIC
# -------------------------------------------------------------
def get_rank_letter(n):
    if n>=250: return "S"
    if n>=180: return "A"
    if n>=120: return "B"
    if n>=60:  return "C"
    if n>=30:  return "D"
    return "E"

RANK_CONFIG = {
    "S": {"label":"S-Rank Athlete","color":"#e9d5ff","emoji":"👑"},
    "A": {"label":"A-Rank Athlete","color":"#93c5fd","emoji":"💎"},
    "B": {"label":"B-Rank Athlete","color":"#6ee7b7","emoji":"💎"},
    "C": {"label":"C-Rank Athlete","color":"#fde68a","emoji":"💎"},
    "D": {"label":"D-Rank Athlete","color":"#fed7aa","emoji":"💎"},
    "E": {"label":"E-Rank Athlete","color":"#9ca3af","emoji":"💎"},
}

def render_rank_badge(letter):
    cfg = RANK_CONFIG[letter]
    return f"<span style='color:{cfg['color']};font-weight:800;'>{cfg['emoji']} {cfg['label']}</span>"

consistency_map = {u: round((sessions[u]/365)*100,1) for u in sessions.index}
rank_map = {u: get_rank_letter(sessions[u]) for u in sessions.index}

top_user = sessions.idxmax()
top_user_rank_letter = rank_map[top_user]
top_user_sessions = int(sessions[top_user])

# -------------------------------------------------------------
#                HEADER
# -------------------------------------------------------------
st.markdown("<div class='main-title'>Team Bekfè Fitness Tracker</div>", unsafe_allow_html=True)

# -------------------------------------------------------------
#                TABS
# -------------------------------------------------------------
tab_profile, tab_lb, tab_activity, tab_dash, tab_ranks = st.tabs(
    ["Profile","Leaderboards","Fitness Activity","Dashboard","Ranking System"]
)

# -------------------------------------------------------------
#                PROFILE TAB
# -------------------------------------------------------------
with tab_profile:
    st.markdown("<div class='glow-header'>Profile</div>", unsafe_allow_html=True)

    featured_html = render_rank_badge(top_user_rank_letter)
    st.markdown(
        f"<div class='featured-line'>🏆 Featured Athlete: <b>{top_user}</b> – {featured_html} – <b>{top_user_sessions}</b> sessions</div>",
        unsafe_allow_html=True
    )

    selected = st.selectbox("Select Member", users, index=users.index(top_user))

    total_sessions_user = int(sessions[selected])
    total_minutes_user = int(duration[selected])
    total_hours_user = round(total_minutes_user/60,1)
    consistency_user = consistency_map[selected]
    rank_letter_user = rank_map[selected]

    rank_html = render_rank_badge(rank_letter_user)

    today = dt.date.today()
    season_end = dt.date(today.year,12,31)
    days_left = (season_end - today).days

    st.markdown(
        f"<div class='summary-line'><b>Season:</b> {today.year} | "
        f"<b>Date:</b> {today} | <b>Ends in:</b> {days_left} days</div>",
        unsafe_allow_html=True
    )

    st.markdown(f"<div class='sub-header'>{selected} – {rank_html}</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 📉 MONTHLY TRAINING CONSISTENCY (PROFILE ONLY)
    # -------------------------------------------------------------
    st.markdown("<div class='sub-header'>📉 Monthly Training Consistency</div>", unsafe_allow_html=True)

    df_user = df[df[col_name] == selected].copy()
    df_user["month"] = df_user[col_timestamp].dt.month
    df_user["Month"] = df_user[col_timestamp].dt.strftime("%B")

    monthly_sessions = (
        df_user.groupby(["month", "Month"])
        .size()
        .reset_index(name="Sessions")
        .sort_values("month")
    )

    st.plotly_chart(
        px.bar(
            monthly_sessions,
            x="Month",
            y="Sessions",
            text="Sessions"
        ).update_traces(textposition="outside")
         .update_layout(yaxis_title="Sessions", xaxis_title=""),
        use_container_width=True
    )

# -------------------------------------------------------------
#                LEADERBOARD TAB
# -------------------------------------------------------------
with tab_lb:
    st.dataframe(
        pd.DataFrame({
            "User": sessions.index,
            "Sessions": sessions.values,
            "Rank": [rank_map[u] for u in sessions.index]
        }).sort_values("Sessions", ascending=False),
        use_container_width=True
    )

# -------------------------------------------------------------
#                FITNESS ACTIVITY TAB
# -------------------------------------------------------------
with tab_activity:
    st.plotly_chart(px.bar(mus_df, x="Muscle", y="Count"), use_container_width=True)

# -------------------------------------------------------------
#                DASHBOARD TAB
# -------------------------------------------------------------
with tab_dash:
    st.dataframe(df.sort_values(col_timestamp, ascending=False).head(25), use_container_width=True)

# -------------------------------------------------------------
#                RANKING SYSTEM TAB
# -------------------------------------------------------------
with tab_ranks:
    components.html("<h3>Ranking System</h3>", height=200)
