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
df["month"] = df[col_timestamp].dt.month
df["month_name"] = df[col_timestamp].dt.strftime("%B")


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
activity_matrix = pd.DataFrame(user_muscles).fillna(0).astype(int).T
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

st.markdown("""
### Log Your Fitness Sessions  
<a href="https://docs.google.com/forms/d/1JqTx8Fd5la2BGv4h5s1506KZMVQUqHL2U0pNvKs0KTo/edit"
target="_blank"
style="background:#0d1b2a;padding:10px 20px;border-radius:8px;
border:1px solid #3ecbff;color:#aee6ff;font-size:16px;text-decoration:none;">
➤ Submit Entry
</a>
""", unsafe_allow_html=True)

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

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f"<div class='stat-box'><div class='stat-value'>{total_sessions_user}</div><div class='stat-label'>Total Sessions</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='stat-box'><div class='stat-value'>{total_hours_user}</div><div class='stat-label'>Total Hours</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='stat-box'><div class='stat-value'>{days_left}</div><div class='stat-label'>Days Left</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='stat-box'><div class='stat-value'>{consistency_user}%</div><div class='stat-label'>Season Consistency</div></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 🔵 PROGRESS BAR → Next Rank (Mana Surge Animation)
    # -------------------------------------------------------------
    st.markdown("<div class='sub-header'>📈 Progress to Next Rank</div>", unsafe_allow_html=True)

    rank_thresholds = {"S":250,"A":180,"B":120,"C":60,"D":30,"E":0}
    order = ["E","D","C","B","A","S"]

    current_rank = rank_letter_user
    current_count = total_sessions_user

    if current_rank == "S":
        next_rank = None
        next_threshold = 365
    else:
        next_rank = order[order.index(current_rank)+1]
        next_threshold = rank_thresholds[next_rank]

    current_threshold = rank_thresholds[current_rank]

    progress = (current_count - current_threshold) / (next_threshold - current_threshold)
    progress = max(0, min(progress, 1))

    st.markdown(f"""
        <style>
        @keyframes manaFill {{
            from {{ width: 0%; }}
            to {{ width: {progress*100}%; }}
        }}
        .mana-bar {{
            width: 100%;
            height: 20px;
            background: #0a0f1a;
            border-radius: 10px;
            border: 1px solid #3fa9ff;
            overflow: hidden;
            margin-bottom: 12px;
        }}
        .mana-fill {{
            height: 100%;
            background: linear-gradient(90deg, #1e90ff, #00e1ff);
            animation: manaFill 1.8s ease-out forwards;
        }}
        </style>

        <div class="mana-bar">
            <div class="mana-fill"></div>
        </div>
    """, unsafe_allow_html=True)

    st.write(f"**{current_count} / {next_threshold} sessions to reach {next_rank or 'MAX'} Rank**")

    # Top Muscles
    st.markdown("<div class='sub-header'>💪 Top Muscles Used</div>", unsafe_allow_html=True)
    top_df = pd.Series(user_muscles[selected]).sort_values(ascending=False).head(5)
    st.dataframe(top_df.reset_index().rename(columns={"index":"Muscle",0:"Count"}), hide_index=True)

    # Least Muscles
    st.markdown("<div class='sub-header'>🩶 Least Used Muscles</div>", unsafe_allow_html=True)
    least_df = pd.Series(user_muscles[selected]).sort_values(ascending=True).head(5)
    st.dataframe(least_df.reset_index().rename(columns={"index":"Muscle",0:"Count"}), hide_index=True)

    # Workout Log
    st.markdown("<div class='sub-header'>📘 Workout Log</div>", unsafe_allow_html=True)
    log = df[df[col_name]==selected][[col_timestamp,col_muscles,col_duration]]
    st.dataframe(log.sort_values(col_timestamp, ascending=False), hide_index=True)

# -------------------------------------------------------------
# 📅 Monthly Session Breakdown (Ranked by Performance)
# -------------------------------------------------------------
st.markdown("<div class='sub-header'>📅 Monthly Session Performance</div>", unsafe_allow_html=True)

monthly_sessions = (
    df[df[col_name] == selected]
    .groupby(["month", "month_name"])
    .size()
    .reset_index(name="Sessions")
    .sort_values("Sessions", ascending=False)
)

# Ensure months with 0 sessions still show (optional but nice)
all_months = pd.DataFrame({
    "month": range(1, 13),
    "month_name": [dt.date(1900, m, 1).strftime("%B") for m in range(1, 13)]
})

monthly_sessions = (
    all_months
    .merge(monthly_sessions, on=["month", "month_name"], how="left")
    .fillna(0)
)

monthly_sessions["Sessions"] = monthly_sessions["Sessions"].astype(int)

st.dataframe(
    monthly_sessions[["month_name", "Sessions"]],
    hide_index=True,
    use_container_width=True
)


# -------------------------------------------------------------
#                LEADERBOARD TAB
# -------------------------------------------------------------
with tab_lb:
    st.markdown("<div class='glow-header'>Leaderboards</div>", unsafe_allow_html=True)

    lb = pd.DataFrame({
        "User": sessions.index,
        "Sessions": sessions.values,
        "Hours": (duration.values/60).round(1),
        "Consistency %": [consistency_map[u] for u in sessions.index],
        "Rank": [rank_map[u] for u in sessions.index]
    }).sort_values("Sessions",ascending=False).reset_index(drop=True)

    lb.insert(0,"Position", lb.index+1)
    st.dataframe(lb, hide_index=True, use_container_width=True)

# -------------------------------------------------------------
#                FITNESS ACTIVITY TAB
# -------------------------------------------------------------
with tab_activity:
    st.markdown("<div class='glow-header'>Fitness Activity</div>", unsafe_allow_html=True)

    st.markdown("<div class='sub-header'>🔥 Most Trained Muscle Groups</div>", unsafe_allow_html=True)
    st.plotly_chart(px.bar(mus_df.sort_values("Count",ascending=False), x="Muscle", y="Count"), use_container_width=True)

    st.markdown("<div class='sub-header'>⏳ Total Hours per Member</div>", unsafe_allow_html=True)
    st.plotly_chart(px.bar(hours_df, x="User", y="Hours"), use_container_width=True)

    st.markdown("<div class='sub-header'>💪 Muscle Distribution</div>", unsafe_allow_html=True)
    st.plotly_chart(px.pie(mus_df, names="Muscle", values="Count", hole=0.45), use_container_width=True)

    st.markdown("<div class='sub-header'>📅 Training Frequency (7-Day Avg)</div>", unsafe_allow_html=True)
    st.plotly_chart(px.line(sessions_per_day, x="date", y="7day_avg"), use_container_width=True)

# -------------------------------------------------------------
#                DASHBOARD TAB
# -------------------------------------------------------------
with tab_dash:
    st.markdown("<div class='glow-header'>Dashboard Overview</div>", unsafe_allow_html=True)
    st.dataframe(df.sort_values(col_timestamp, ascending=False).head(25), hide_index=True, use_container_width=True)

# -------------------------------------------------------------
#                RANKING SYSTEM TAB
# -------------------------------------------------------------
with tab_ranks:
    st.markdown("<div class='glow-header'>Ranking System</div>", unsafe_allow_html=True)

    rank_html = """
    <style>
    .rank-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }
    .rank-table th, .rank-table td {
        padding: 12px;
        text-align: center;
        font-size: 16px;
        border: 1px solid #1e293b;
    }
    .s-rank { background: linear-gradient(90deg,#5b21b6,#facc15); color:white; }
    .a-rank { background: rgba(59,130,246,0.55); color:white; }
    .b-rank { background: rgba(16,185,129,0.55); color:white; }
    .c-rank { background: rgba(234,179,8,0.55); color:black; }
    .d-rank { background: rgba(249,115,22,0.55); color:black; }
    .e-rank { background: rgba(156,163,175,0.45); color:white; }
    </style>

    <table class="rank-table">
        <tr><th>Rank</th><th>Letter</th><th>Sessions Range</th><th>Consistency %</th></tr>
        <tr class="s-rank"><td>S-Rank Athlete</td><td>S</td><td>250–365</td><td>68–100%</td></tr>
        <tr class="a-rank"><td>A-Rank Athlete</td><td>A</td><td>180–249</td><td>49–68%</td></tr>
        <tr class="b-rank"><td>B-Rank Athlete</td><td>B</td><td>120–179</td><td>33–49%</td></tr>
        <tr class="c-rank"><td>C-Rank Athlete</td><td>C</td><td>60–119</td><td>16–33%</td></tr>
        <tr class="d-rank"><td>D-Rank Athlete</td><td>D</td><td>30–59</td><td>8–16%</td></tr>
        <tr class="e-rank"><td>E-Rank Athlete</td><td>E</td><td>0–29</td><td>0–8%</td></tr>
    </table>
    """

    components.html(rank_html, height=500, scrolling=False)
