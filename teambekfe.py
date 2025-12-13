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

import json

# -------------------------------------------------------------
# AVATAR: Gender mapping (edit names anytime)
# -------------------------------------------------------------
GENDER_MAP = {
    "Vincent": "male",
    "Alain": "male",
    "Douglas": "male",
    "Dimitri": "male",
    "Mikael": "male",
    "Junior": "male",
    "Danimix": "male",
    "Bousik": "male",
    "Gregory": "male",
    "Louis": "male",
}

# -------------------------------------------------------------
# AVATAR: Map your raw muscle strings -> buckets we visualize
# (Add/adjust aliases to match your Google Form muscle labels)
# -------------------------------------------------------------
MUSCLE_ALIASES = {
    "Upper Body": "UPPER_BODY",
    "Lower Body": "LOWER_BODY",
    "Core": "CORE",
    "Grips": "GRIPS",
    "Grip": "GRIPS",
    "Forearms": "FOREARMS",
    "Forearm": "FOREARMS",

    "Chest": "CHEST",
    "Back": "BACK",
    "Shoulders": "SHOULDERS",
    "Arms": "ARMS",
    "Biceps": "ARMS",
    "Triceps": "ARMS",

    "Legs": "LEGS",
    "Glutes": "GLUTES_LEGS",
    "Glutes & Legs": "GLUTES_LEGS",
    "Hamstrings": "GLUTES_LEGS",
    "Quads": "LEGS",
    "Calves": "LEGS",
}

DEFAULT_BUCKETS = ["UPPER_BODY", "LOWER_BODY", "CORE", "GRIPS", "FOREARMS", "CHEST", "BACK", "SHOULDERS", "ARMS", "LEGS", "GLUTES_LEGS"]

def bucket_counts_for_user(selected_user: str):
    """Convert your user_muscles[selected] dict into stable avatar buckets."""
    raw = user_muscles.get(selected_user, {})
    out = {b: 0 for b in DEFAULT_BUCKETS}

    for k, v in raw.items():
        key = str(k).strip()
        bucket = MUSCLE_ALIASES.get(key)
        if not bucket:
            # try loose matching
            lk = key.lower()
            if "upper" in lk: bucket = "UPPER_BODY"
            elif "lower" in lk: bucket = "LOWER_BODY"
            elif "core" in lk or "abs" in lk: bucket = "CORE"
            elif "grip" in lk: bucket = "GRIPS"
            elif "forearm" in lk: bucket = "FOREARMS"
            elif "chest" in lk or "pec" in lk: bucket = "CHEST"
            elif "back" in lk or "lat" in lk: bucket = "BACK"
            elif "shoulder" in lk or "delt" in lk: bucket = "SHOULDERS"
            elif "arm" in lk or "bicep" in lk or "tricep" in lk: bucket = "ARMS"
            elif "glute" in lk or "ham" in lk: bucket = "GLUTES_LEGS"
            elif "leg" in lk or "quad" in lk or "calf" in lk: bucket = "LEGS"

        if bucket:
            out[bucket] += int(v)

    return out

def render_avatar_html(gender: str, buckets: dict, title: str = ""):
    """
    2D neon silhouette + constellation points.
    gender: "male" or "female"
    buckets: dict {BUCKET: count}
    """
    # Points are in % of the avatar canvas (0-100)
    # You can tweak positions later without touching the logic.
    points_male = {
        "UPPER_BODY":  (30, 18),
        "LOWER_BODY":  (30, 62),
        "CORE":        (70, 38),
        "GRIPS":       (80, 18),
        "FOREARMS":    (78, 44),
        "CHEST":       (52, 28),
        "BACK":        (52, 30),
        "SHOULDERS":   (50, 20),
        "ARMS":        (60, 28),
        "LEGS":        (55, 70),
        "GLUTES_LEGS": (70, 64),
    }

    points_female = {
        "UPPER_BODY":  (28, 20),
        "LOWER_BODY":  (28, 64),
        "CORE":        (78, 34),
        "GRIPS":       (78, 20),
        "FOREARMS":    (78, 46),
        "CHEST":       (50, 28),
        "BACK":        (50, 30),
        "SHOULDERS":   (48, 20),
        "ARMS":        (60, 30),
        "LEGS":        (55, 74),
        "GLUTES_LEGS": (22, 66),
    }

    pts = points_male if gender == "male" else points_female

    data = {k: int(buckets.get(k, 0)) for k in pts.keys()}
    maxv = max(data.values()) if data else 1
    maxv = max(maxv, 1)

    # simple neon color scaling
    # low = blue, mid = cyan, high = gold
    def color_for(v):
        r = v / maxv
        if r >= 0.75: return "#facc15"
        if r >= 0.35: return "#22d3ee"
        if r > 0:     return "#3b82f6"
        return "rgba(59,130,246,0.12)"

    nodes = []
    labels = []
    for name, (x, y) in pts.items():
        v = data.get(name, 0)
        c = color_for(v)
        glow = 0.25 + 0.85 * (v / maxv)  # glow intensity
        radius = 5 + 6 * (v / maxv)      # bigger dot when more trained

        nodes.append({
            "name": name.replace("_", " "),
            "x": x, "y": y,
            "v": v,
            "c": c,
            "glow": glow,
            "r": radius
        })

    nodes_json = json.dumps(nodes)

    # Simple silhouette (stylized outline) using SVG paths (no external assets)
    # Looks "neon blueprint" which matches Solo-Leveling.
    # You can later swap this with a custom SVG silhouette without changing node logic.
    silhouette_path_male = """
      <path d="M150 60
               C135 60 125 72 125 88
               C125 105 137 118 150 118
               C163 118 175 105 175 88
               C175 72 165 60 150 60Z"
            fill="none" stroke="rgba(160,220,255,0.85)" stroke-width="2"/>
      <path d="M115 140
               C120 118 135 110 150 110
               C165 110 180 118 185 140
               C205 150 214 170 212 190
               C208 220 198 250 195 275
               C192 300 196 330 198 350
               C200 370 195 395 185 410
               C175 426 165 440 150 440
               C135 440 125 426 115 410
               C105 395 100 370 102 350
               C104 330 108 300 105 275
               C102 250 92 220 88 190
               C86 170 95 150 115 140Z"
            fill="none" stroke="rgba(160,220,255,0.65)" stroke-width="2"/>
      <path d="M105 190 C85 215 78 240 80 270 C82 295 95 320 110 338"
            fill="none" stroke="rgba(120,200,255,0.35)" stroke-width="2"/>
      <path d="M195 190 C215 215 222 240 220 270 C218 295 205 320 190 338"
            fill="none" stroke="rgba(120,200,255,0.35)" stroke-width="2"/>
      <path d="M135 440 C125 475 120 515 125 540
               M165 440 C175 475 180 515 175 540"
            fill="none" stroke="rgba(160,220,255,0.55)" stroke-width="2"/>
    """

    silhouette_path_female = """
      <path d="M150 60
               C136 60 125 73 125 90
               C125 106 137 120 150 120
               C163 120 175 106 175 90
               C175 73 164 60 150 60Z"
            fill="none" stroke="rgba(160,220,255,0.85)" stroke-width="2"/>
      <path d="M118 142
               C124 118 138 110 150 110
               C162 110 176 118 182 142
               C198 156 206 176 204 196
               C200 230 194 256 190 278
               C184 310 188 336 195 360
               C202 384 198 406 186 422
               C174 438 164 452 150 452
               C136 452 126 438 114 422
               C102 406 98 384 105 360
               C112 336 116 310 110 278
               C106 256 100 230 96 196
               C94 176 102 156 118 142Z"
            fill="none" stroke="rgba(160,220,255,0.65)" stroke-width="2"/>
      <path d="M132 452 C124 486 120 520 124 544
               M168 452 C176 486 180 520 176 544"
            fill="none" stroke="rgba(160,220,255,0.55)" stroke-width="2"/>
    """

    silhouette = silhouette_path_male if gender == "male" else silhouette_path_female

    # Build HTML
    html = f"""
    <div style="width:100%; padding: 8px 6px;">
      <div style="font-family: system-ui, -apple-system, Segoe UI, Roboto; color:#cce8ff; font-weight:800; margin: 0 0 10px 2px;">
        {title}
      </div>

      <div style="position:relative; width:100%; max-width: 720px; margin: 0 auto;
                  background: radial-gradient(circle at top, rgba(20,40,70,0.55) 0%, rgba(5,8,16,0.92) 55%);
                  border: 1px solid rgba(63,169,255,0.55);
                  border-radius: 14px;
                  box-shadow: 0 0 22px rgba(0,150,255,0.20);
                  padding: 14px;">
        <svg viewBox="0 0 300 560" width="100%" height="560" style="display:block;">
          <defs>
            <filter id="softGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3.5" result="blur"/>
              <feMerge>
                <feMergeNode in="blur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>

            <filter id="hardGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="7" result="blur"/>
              <feColorMatrix in="blur" type="matrix"
                values="1 0 0 0 0
                        0 1 0 0 0
                        0 0 1 0 0
                        0 0 0 1 0" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>

            <linearGradient id="silGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="rgba(80,170,255,0.95)" />
              <stop offset="100%" stop-color="rgba(0,225,255,0.55)" />
            </linearGradient>
          </defs>

          <!-- Background stars -->
          <g opacity="0.35">
            <circle cx="40" cy="40" r="1.5" fill="#7fd1ff"/>
            <circle cx="260" cy="70" r="1.2" fill="#7fd1ff"/>
            <circle cx="220" cy="30" r="1.0" fill="#7fd1ff"/>
            <circle cx="70" cy="120" r="1.1" fill="#7fd1ff"/>
            <circle cx="270" cy="150" r="1.3" fill="#7fd1ff"/>
            <circle cx="40" cy="220" r="1.0" fill="#7fd1ff"/>
            <circle cx="260" cy="260" r="1.2" fill="#7fd1ff"/>
            <circle cx="60" cy="330" r="1.1" fill="#7fd1ff"/>
            <circle cx="250" cy="380" r="1.0" fill="#7fd1ff"/>
          </g>

          <!-- Silhouette -->
          <g filter="url(#softGlow)" stroke="url(#silGrad)">
            {silhouette}
          </g>

          <!-- Nodes -->
          <g id="nodes"></g>
        </svg>

        <div id="tip" style="
          position:absolute; left: 14px; top: 14px;
          padding: 8px 10px; border-radius: 10px;
          border: 1px solid rgba(63,169,255,0.45);
          background: rgba(5,8,16,0.85);
          color: #cce8ff;
          font-weight: 800;
          box-shadow: 0 0 18px rgba(0,150,255,0.18);
          display:none;
          pointer-events:none;
          font-family: system-ui, -apple-system, Segoe UI, Roboto;
          font-size: 14px;
        "></div>

        <div style="margin-top: 10px; display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
          <div style="color:#9bd4ff; font-weight:700;">Legend:</div>
          <div style="color:#3b82f6; font-weight:800;">Low</div>
          <div style="color:#22d3ee; font-weight:800;">Medium</div>
          <div style="color:#facc15; font-weight:900;">High</div>
        </div>
      </div>
    </div>

    <script>
      const nodes = {nodes_json};
      const svg = document.querySelector("svg");
      const g = document.getElementById("nodes");
      const tip = document.getElementById("tip");

      function pctToSvg(xPct, yPct) {{
        // xPct/yPct are 0-100; map to viewBox 0..300, 0..560
        return [ (xPct/100)*300, (yPct/100)*560 ];
      }}

      function showTip(text, clientX, clientY) {{
        tip.style.display = "block";
        tip.innerText = text;
        const rect = svg.getBoundingClientRect();
        tip.style.left = (clientX - rect.left + 14) + "px";
        tip.style.top  = (clientY - rect.top  + 14) + "px";
      }}

      function hideTip() {{
        tip.style.display = "none";
      }}

      // Optional: connect points with faint lines (constellation vibe)
      // We'll connect a curated chain so it looks intentional.
      const connectOrder = ["UPPER BODY","CHEST","CORE","LOWER BODY","GLUTES LEGS","LEGS","FOREARMS","GRIPS","ARMS","SHOULDERS","BACK"];
      const idx = Object.fromEntries(nodes.map(n => [n.name, n]));

      function drawLine(a, b) {{
        if (!a || !b) return;
        const [ax, ay] = pctToSvg(a.x, a.y);
        const [bx, by] = pctToSvg(b.x, b.y);
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", ax); line.setAttribute("y1", ay);
        line.setAttribute("x2", bx); line.setAttribute("y2", by);
        line.setAttribute("stroke", "rgba(127,209,255,0.18)");
        line.setAttribute("stroke-width", "2");
        g.appendChild(line);
      }}

      for (let i=0; i<connectOrder.length-1; i++) {{
        drawLine(idx[connectOrder[i]], idx[connectOrder[i+1]]);
      }}

      // Draw nodes on top
      nodes.forEach(n => {{
        const [cx, cy] = pctToSvg(n.x, n.y);

        // Outer glow
        const glow = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        glow.setAttribute("cx", cx); glow.setAttribute("cy", cy);
        glow.setAttribute("r", Math.max(10, n.r*2.2));
        glow.setAttribute("fill", n.c);
        glow.setAttribute("opacity", n.glow.toFixed(2));
        glow.setAttribute("filter", "url(#hardGlow)");
        g.appendChild(glow);

        // Core dot
        const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        dot.setAttribute("cx", cx); dot.setAttribute("cy", cy);
        dot.setAttribute("r", Math.max(4, n.r));
        dot.setAttribute("fill", n.c);
        dot.setAttribute("stroke", "rgba(255,255,255,0.55)");
        dot.setAttribute("stroke-width", "1");
        dot.style.cursor = "default";

        dot.addEventListener("mousemove", (e) => {{
          const label = `${{n.name}} — ${{n.v}}`;
          showTip(label, e.clientX, e.clientY);
        }});
        dot.addEventListener("mouseleave", hideTip);

        g.appendChild(dot);
      }});
    </script>
    """
    return html

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
# 📉 MONTHLY TRAINING CONSISTENCY
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
        text="Sessions",
        title=None
    ).update_traces(textposition="outside")
     .update_layout(yaxis_title="Sessions", xaxis_title=""),
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
