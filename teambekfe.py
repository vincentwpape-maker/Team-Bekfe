import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.express as px
import datetime as dt
import re
from collections import defaultdict
import base64
import json

# -------------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------------
st.set_page_config(page_title="Team Bekfè Fitness Tracker", layout="wide")

# -------------------------------------------------------------
# GLOBAL STYLING (SOLO-LEVELING THEME)
# -------------------------------------------------------------
st.markdown("""
<style>
body { background-color:#05070c; color:#e5f4ff; }
.main-title { font-size:40px; font-weight:900; text-align:center; text-shadow:0 0 12px #3f9dff; }
.glow-header { font-size:26px; font-weight:800; color:#7fd1ff; border-bottom:2px solid #2f9dff; }
.sub-header { font-size:18px; font-weight:700; color:#9bd4ff; margin-top:20px; }
.stat-box { padding:18px; background:#050810; border-radius:14px; text-align:center; border:1px solid #245b8f; }
.stat-value { font-size:38px; font-weight:900; color:#7fd1ff; }
.stat-label { font-size:14px; color:#9bb8d1; }
.featured-line { background:rgba(34,22,6,.88); padding:10px 14px; border-radius:10px; border:1px solid #facc15; }
.summary-line { background:rgba(10,25,45,.8); padding:10px 16px; border-radius:8px; border:1px solid #3fa9ff; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# LOAD DATA
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

col_timestamp, col_name, col_muscles, col_duration = df.columns[0], df.columns[1], df.columns[3], df.columns[4]
df[col_timestamp] = pd.to_datetime(df[col_timestamp], errors="coerce")

# -------------------------------------------------------------
# CLEANING
# -------------------------------------------------------------
def clean_name(n):
    if not isinstance(n,str): return ""
    n = re.sub(r"[^a-z0-9 ]","", n.lower())
    return n.title()

df[col_name] = df[col_name].apply(clean_name)

def parse_duration(t):
    if not isinstance(t,str): return 0
    nums = list(map(int, re.findall(r"\d+", t)))
    return nums[0]*60 + (nums[1] if len(nums)>1 else 0)

df["minutes"] = df[col_duration].apply(parse_duration)

# -------------------------------------------------------------
# MUSCLE EXTRACTION
# -------------------------------------------------------------
def extract_muscles(txt):
    if not isinstance(txt,str): return []
    return [x.split("(")[0].strip() for x in txt.split(",")]

user_muscles = defaultdict(lambda: defaultdict(int))
for _,r in df.iterrows():
    for m in extract_muscles(r[col_muscles]):
        user_muscles[r[col_name]][m] += 1

sessions = df.groupby(col_name).size()
duration = df.groupby(col_name)["minutes"].sum()
users = sorted(sessions.index)

# -------------------------------------------------------------
# RANK LOGIC
# -------------------------------------------------------------
def get_rank(n):
    return "S" if n>=250 else "A" if n>=180 else "B" if n>=120 else "C" if n>=60 else "D" if n>=30 else "E"

rank_map = {u:get_rank(sessions[u]) for u in sessions.index}
consistency_map = {u:round(sessions[u]/365*100,1) for u in sessions.index}

# -------------------------------------------------------------
# AVATAR LOGIC
# -------------------------------------------------------------
def img_to_base64(path):
    with open(path,"rb") as f:
        return base64.b64encode(f.read()).decode()

GENDER_MAP = {u:"male" for u in users}

MUSCLE_ALIASES = {
    "Chest":"CHEST","Back":"BACK","Shoulders":"SHOULDERS","Arms":"ARMS",
    "Forearms":"FOREARMS","Core":"CORE","Legs":"LEGS","Glutes":"GLUTES"
}

def bucket_counts_for_user(user):
    out = defaultdict(int)
    for k,v in user_muscles[user].items():
        for key,val in MUSCLE_ALIASES.items():
            if key.lower() in k.lower():
                out[val]+=v
    return out

def render_avatar(user, buckets):
    avatar = img_to_base64("assets/male.png")
    maxv = max(buckets.values()) if buckets else 1

    def color(v):
        r=v/maxv
        return "#facc15" if r>0.7 else "#22d3ee" if r>0.3 else "#3b82f6"

    blocks=""
    y=150
    for k,v in buckets.items():
        blocks+=f"<rect x='140' y='{y}' width='90' height='32' rx='8' fill='{color(v)}'/><text x='185' y='{y+22}' text-anchor='middle' fill='white'>{k} {v}</text>"
        y+=40

    return f"""
    <div style='text-align:center'>
      <img src='data:image/png;base64,{avatar}' width='360'/>
      <svg viewBox='0 0 360 600' style='position:absolute;top:0;left:0'>
        {blocks}
      </svg>
    </div>
    """

# -------------------------------------------------------------
# HEADER
# -------------------------------------------------------------
st.markdown("<div class='main-title'>Team Bekfè Fitness Tracker</div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# TABS
# -------------------------------------------------------------
tab_profile, tab_lb, tab_activity, tab_dash, tab_ranks = st.tabs(
    ["Profile","Leaderboards","Fitness Activity","Dashboard","Ranking System"]
)

# -------------------------------------------------------------
# PROFILE TAB
# -------------------------------------------------------------
with tab_profile:
    selected = st.selectbox("Select Member", users)

    st.markdown(f"<div class='sub-header'>{selected} — Rank {rank_map[selected]}</div>", unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    c1.markdown(f"<div class='stat-box'><div class='stat-value'>{sessions[selected]}</div><div class='stat-label'>Sessions</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='stat-box'><div class='stat-value'>{round(duration[selected]/60,1)}</div><div class='stat-label'>Hours</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='stat-box'><div class='stat-value'>{consistency_map[selected]}%</div><div class='stat-label'>Consistency</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='sub-header'>🧍 Avatar Muscle Targets</div>", unsafe_allow_html=True)
    components.html(render_avatar(selected, bucket_counts_for_user(selected)), height=600)

    st.markdown("<div class='sub-header'>📉 Monthly Training Consistency</div>", unsafe_allow_html=True)
    df_user=df[df[col_name]==selected].copy()
    df_user["Month"]=df_user[col_timestamp].dt.strftime("%B")
    st.plotly_chart(df_user.groupby("Month").size().reset_index(name="Sessions"), use_container_width=True)

# -------------------------------------------------------------
# LEADERBOARD
# -------------------------------------------------------------
with tab_lb:
    st.dataframe(pd.DataFrame({
        "User":sessions.index,
        "Sessions":sessions.values,
        "Rank":[rank_map[u] for u in sessions.index]
    }).sort_values("Sessions",ascending=False), use_container_width=True)

# -------------------------------------------------------------
# ACTIVITY
# -------------------------------------------------------------
with tab_activity:
    st.plotly_chart(px.bar(df.groupby(col_muscles).size().reset_index(name="Count"),
                            x=col_muscles,y="Count"), use_container_width=True)

# -------------------------------------------------------------
# DASHBOARD
# -------------------------------------------------------------
with tab_dash:
    st.dataframe(df.sort_values(col_timestamp,ascending=False).head(25), use_container_width=True)

# -------------------------------------------------------------
# RANKS
# -------------------------------------------------------------
with tab_ranks:
    st.write("Ranks: E → S based on yearly sessions")
