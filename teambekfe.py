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
import base64
import json

def img_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# Decide gender by name (edit anytime)
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
    # Add female names here later if needed:
    # "Sophie": "female",
}

# Map your Google Form muscle labels -> overlay buckets
# (Add aliases so your exact text matches)
MUSCLE_ALIASES = {
    "Upper Body": "UPPER_BODY",
    "Lower Body": "LOWER_BODY",
    "Core": "CORE",
    "Grips": "GRIPS",
    "Forearms": "FOREARMS",

    "Chest": "CHEST",
    "Back": "BACK",
    "Shoulders": "SHOULDERS",
    "Arms": "ARMS",
    "Legs": "LEGS",
    "Glutes": "GLUTES",
    "Glutes & Legs": "GLUTES",
}

OVERLAY_BUCKETS = ["CHEST","BACK","SHOULDERS","ARMS","FOREARMS","GRIPS","CORE","UPPER_BODY","LOWER_BODY","LEGS","GLUTES"]

def bucket_counts_for_user(selected_user: str) -> dict:
    raw = user_muscles.get(selected_user, {})
    out = {k: 0 for k in OVERLAY_BUCKETS}

    for k, v in raw.items():
        key = str(k).strip()
        bucket = MUSCLE_ALIASES.get(key)

        # loose matching fallback
        if not bucket:
            lk = key.lower()
            if "upper" in lk: bucket = "UPPER_BODY"
            elif "lower" in lk: bucket = "LOWER_BODY"
            elif "core" in lk or "abs" in lk: bucket = "CORE"
            elif "grip" in lk: bucket = "GRIPS"
            elif "forearm" in lk: bucket = "FOREARMS"
            elif "chest" in lk or "pec" in lk: bucket = "CHEST"
            elif "back" in lk or "lat" in lk or "trap" in lk: bucket = "BACK"
            elif "shoulder" in lk or "delt" in lk: bucket = "SHOULDERS"
            elif "arm" in lk or "bicep" in lk or "tricep" in lk: bucket = "ARMS"
            elif "glute" in lk or "ham" in lk: bucket = "GLUTES"
            elif "leg" in lk or "quad" in lk or "calf" in lk: bucket = "LEGS"

        if bucket:
            out[bucket] += int(v)

    return out


def render_game_avatar_with_overlay(selected_user: str, gender: str, buckets: dict) -> str:
    """
    Game avatar PNG as background + transparent SVG muscle overlay + numbers.
    NOTE: Muscle shapes are positioned for a generic front-facing avatar.
          You can tweak the rectangles/polygons later to align perfectly to your art.
    """
    avatar_path = "assets/male.png" if gender == "male" else "assets/female.png"
    avatar_b64 = img_to_base64(avatar_path)

    # Color intensity by relative usage
    maxv = max(buckets.values()) if buckets else 1
    maxv = max(maxv, 1)

    def tier(v):
        r = v / maxv
        if v <= 0: return ("rgba(80,160,255,0.08)", "rgba(120,200,255,0.20)")
        if r >= 0.75: return ("rgba(250,204,21,0.55)", "rgba(250,204,21,0.85)")   # high = gold
        if r >= 0.35: return ("rgba(34,211,238,0.45)", "rgba(34,211,238,0.80)")   # mid = cyan
        return ("rgba(59,130,246,0.35)", "rgba(59,130,246,0.70)")                 # low = blue

    # Define overlay regions (simple but readable)
    # You’ll adjust these positions once to match your avatar art.
    regions = [
        # id, label, SVG shape (x,y,w,h), label position (lx, ly)
        ("CHEST",      "CHEST",      ("rect",  120, 160, 110,  70), (175, 205)),
        ("SHOULDERS",  "SHOULDERS",  ("rect",  105, 135, 140,  35), (175, 155)),
        ("ARMS",       "ARMS",       ("rect",   75, 165,  55, 120), (102, 225)),
        ("ARMS_R",     "ARMS",       ("rect",  240, 165,  55, 120), (267, 225)),
        ("CORE",       "CORE",       ("rect",  135, 235,  80,  90), (175, 285)),
        ("FOREARMS",   "FOREARMS",   ("rect",   70, 285,  60,  80), (100, 330)),
        ("FOREARMS_R", "FOREARMS",   ("rect",  240, 285,  60,  80), (270, 330)),
        ("LEGS",       "LEGS",       ("rect",  130, 335,  90, 160), (175, 420)),
        ("GLUTES",     "GLUTES",     ("rect",  135, 315,  80,  35), (175, 338)),
    ]

    # Build SVG with colored regions + numbers
    svg_parts = []
    labels_parts = []

    # Choose what value to display for each region id
    # (ARMS_R uses ARMS, FOREARMS_R uses FOREARMS)
    def get_value(region_id):
        if region_id in ("ARMS_R",): return buckets.get("ARMS", 0)
        if region_id in ("FOREARMS_R",): return buckets.get("FOREARMS", 0)
        return buckets.get(region_id, 0)

    for rid, text, (shape, x, y, w, h), (lx, ly) in regions:
        v = int(get_value(rid))
        fill, stroke = tier(v)

        svg_parts.append(
            f"""<rect id="{rid}" x="{x}" y="{y}" width="{w}" height="{h}"
                 rx="14" ry="14"
                 fill="{fill}" stroke="{stroke}" stroke-width="2"
                 filter="url(#glow)" />"""
        )

        # Always display number; if you want blanks on 0, change to: ("" if v==0 else str(v))
        labels_parts.append(
            f"""<text x="{lx}" y="{ly}" class="lbl">{text} {v}</text>"""
        )

    regions_json = json.dumps([{"id": rid, "label": lab, "value": int(get_value(rid))} for rid, lab, *_ in regions])

    html = f"""
    <style>
      .avatar-wrap {{
        position: relative;
        width: 100%;
        max-width: 520px;
        margin: 0 auto;
        border-radius: 16px;
        border: 1px solid rgba(63,169,255,0.55);
        box-shadow: 0 0 22px rgba(0,150,255,0.18);
        overflow: hidden;
        background: radial-gradient(circle at top, rgba(20,40,70,0.55) 0%, rgba(5,8,16,0.92) 55%);
      }}
      .avatar-bg {{
        width: 100%;
        display: block;
        user-select: none;
        -webkit-user-drag: none;
      }}
      .overlay {{
        position: absolute;
        inset: 0;
      }}
      .lbl {{
        fill: #e5f4ff;
        font-weight: 900;
        font-size: 14px;
        text-anchor: middle;
        paint-order: stroke;
        stroke: rgba(0,0,0,0.75);
        stroke-width: 3px;
      }}
      .title {{
        font-family: system-ui, -apple-system, Segoe UI, Roboto;
        color: #cce8ff;
        font-weight: 900;
        margin: 0 0 10px 2px;
        text-align: center;
      }}
      .legend {{
        display:flex; gap:10px; justify-content:center; flex-wrap:wrap;
        padding: 10px 0 12px 0;
        font-family: system-ui, -apple-system, Segoe UI, Roboto;
        color:#9bd4ff; font-weight:800;
      }}
      .chip {{ padding:6px 10px; border-radius:999px; border:1px solid rgba(63,169,255,0.35); background: rgba(5,8,16,0.55); }}
      .low {{ color:#3b82f6; }}
      .mid {{ color:#22d3ee; }}
      .high {{ color:#facc15; }}
      #tip {{
        position:absolute;
        display:none;
        padding:8px 10px;
        border-radius: 10px;
        background: rgba(5,8,16,0.9);
        border: 1px solid rgba(63,169,255,0.45);
        color: #cce8ff;
        font-family: system-ui, -apple-system, Segoe UI, Roboto;
        font-weight: 900;
        box-shadow: 0 0 18px rgba(0,150,255,0.18);
        pointer-events:none;
        z-index: 10;
      }}
    </style>

    <div class="title">{selected_user} — Avatar Muscle Targets</div>

    <div class="avatar-wrap" id="wrap">
      <img class="avatar-bg" src="data:image/png;base64,{avatar_b64}" />

      <svg class="overlay" viewBox="0 0 370 560" preserveAspectRatio="xMidYMid meet">
        <defs>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="blur"/>
            <feMerge>
              <feMergeNode in="blur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {''.join(svg_parts)}
        {''.join(labels_parts)}
      </svg>

      <div id="tip"></div>
    </div>

    <div class="legend">
      <span class="chip"><span class="low">Low</span></span>
      <span class="chip"><span class="mid">Medium</span></span>
      <span class="chip"><span class="high">High</span></span>
    </div>

    <script>
      const regions = {regions_json};
      const wrap = document.getElementById("wrap");
      const tip = document.getElementById("tip");

      function showTip(text, x, y) {{
        tip.style.display = "block";
        tip.innerText = text;
        const rect = wrap.getBoundingClientRect();
        tip.style.left = (x - rect.left + 12) + "px";
        tip.style.top  = (y - rect.top  + 12) + "px";
      }}

      function hideTip() {{
        tip.style.display = "none";
      }}

      // Hover tooltips on rectangles
      regions.forEach(r => {{
        const el = document.getElementById(r.id);
        if (!el) return;
        el.addEventListener("mousemove", (e) => {{
          showTip(`${{r.label}} — ${{r.value}}`, e.clientX, e.clientY);
        }});
        el.addEventListener("mouseleave", hideTip);
      }});
    </script>
    """
    return html

import base64
import json

def img_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# Decide gender by name (edit anytime)
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
    # Add female names here later if needed:
    # "Sophie": "female",
}

# Map your Google Form muscle labels -> overlay buckets
# (Add aliases so your exact text matches)
MUSCLE_ALIASES = {
    "Upper Body": "UPPER_BODY",
    "Lower Body": "LOWER_BODY",
    "Core": "CORE",
    "Grips": "GRIPS",
    "Forearms": "FOREARMS",

    "Chest": "CHEST",
    "Back": "BACK",
    "Shoulders": "SHOULDERS",
    "Arms": "ARMS",
    "Legs": "LEGS",
    "Glutes": "GLUTES",
    "Glutes & Legs": "GLUTES",
}

OVERLAY_BUCKETS = ["CHEST","BACK","SHOULDERS","ARMS","FOREARMS","GRIPS","CORE","UPPER_BODY","LOWER_BODY","LEGS","GLUTES"]

def bucket_counts_for_user(selected_user: str) -> dict:
    raw = user_muscles.get(selected_user, {})
    out = {k: 0 for k in OVERLAY_BUCKETS}

    for k, v in raw.items():
        key = str(k).strip()
        bucket = MUSCLE_ALIASES.get(key)

        # loose matching fallback
        if not bucket:
            lk = key.lower()
            if "upper" in lk: bucket = "UPPER_BODY"
            elif "lower" in lk: bucket = "LOWER_BODY"
            elif "core" in lk or "abs" in lk: bucket = "CORE"
            elif "grip" in lk: bucket = "GRIPS"
            elif "forearm" in lk: bucket = "FOREARMS"
            elif "chest" in lk or "pec" in lk: bucket = "CHEST"
            elif "back" in lk or "lat" in lk or "trap" in lk: bucket = "BACK"
            elif "shoulder" in lk or "delt" in lk: bucket = "SHOULDERS"
            elif "arm" in lk or "bicep" in lk or "tricep" in lk: bucket = "ARMS"
            elif "glute" in lk or "ham" in lk: bucket = "GLUTES"
            elif "leg" in lk or "quad" in lk or "calf" in lk: bucket = "LEGS"

        if bucket:
            out[bucket] += int(v)

    return out


def render_game_avatar_with_overlay(selected_user: str, gender: str, buckets: dict) -> str:
    """
    Game avatar PNG as background + transparent SVG muscle overlay + numbers.
    NOTE: Muscle shapes are positioned for a generic front-facing avatar.
          You can tweak the rectangles/polygons later to align perfectly to your art.
    """
    avatar_path = "assets/male.png" if gender == "male" else "assets/female.png"
    avatar_b64 = img_to_base64(avatar_path)

    # Color intensity by relative usage
    maxv = max(buckets.values()) if buckets else 1
    maxv = max(maxv, 1)

    def tier(v):
        r = v / maxv
        if v <= 0: return ("rgba(80,160,255,0.08)", "rgba(120,200,255,0.20)")
        if r >= 0.75: return ("rgba(250,204,21,0.55)", "rgba(250,204,21,0.85)")   # high = gold
        if r >= 0.35: return ("rgba(34,211,238,0.45)", "rgba(34,211,238,0.80)")   # mid = cyan
        return ("rgba(59,130,246,0.35)", "rgba(59,130,246,0.70)")                 # low = blue

    # Define overlay regions (simple but readable)
    # You’ll adjust these positions once to match your avatar art.
    regions = [
        # id, label, SVG shape (x,y,w,h), label position (lx, ly)
        ("CHEST",      "CHEST",      ("rect",  120, 160, 110,  70), (175, 205)),
        ("SHOULDERS",  "SHOULDERS",  ("rect",  105, 135, 140,  35), (175, 155)),
        ("ARMS",       "ARMS",       ("rect",   75, 165,  55, 120), (102, 225)),
        ("ARMS_R",     "ARMS",       ("rect",  240, 165,  55, 120), (267, 225)),
        ("CORE",       "CORE",       ("rect",  135, 235,  80,  90), (175, 285)),
        ("FOREARMS",   "FOREARMS",   ("rect",   70, 285,  60,  80), (100, 330)),
        ("FOREARMS_R", "FOREARMS",   ("rect",  240, 285,  60,  80), (270, 330)),
        ("LEGS",       "LEGS",       ("rect",  130, 335,  90, 160), (175, 420)),
        ("GLUTES",     "GLUTES",     ("rect",  135, 315,  80,  35), (175, 338)),
    ]

    # Build SVG with colored regions + numbers
    svg_parts = []
    labels_parts = []

    # Choose what value to display for each region id
    # (ARMS_R uses ARMS, FOREARMS_R uses FOREARMS)
    def get_value(region_id):
        if region_id in ("ARMS_R",): return buckets.get("ARMS", 0)
        if region_id in ("FOREARMS_R",): return buckets.get("FOREARMS", 0)
        return buckets.get(region_id, 0)

    for rid, text, (shape, x, y, w, h), (lx, ly) in regions:
        v = int(get_value(rid))
        fill, stroke = tier(v)

        svg_parts.append(
            f"""<rect id="{rid}" x="{x}" y="{y}" width="{w}" height="{h}"
                 rx="14" ry="14"
                 fill="{fill}" stroke="{stroke}" stroke-width="2"
                 filter="url(#glow)" />"""
        )

        # Always display number; if you want blanks on 0, change to: ("" if v==0 else str(v))
        labels_parts.append(
            f"""<text x="{lx}" y="{ly}" class="lbl">{text} {v}</text>"""
        )

    regions_json = json.dumps([{"id": rid, "label": lab, "value": int(get_value(rid))} for rid, lab, *_ in regions])

    html = f"""
    <style>
      .avatar-wrap {{
        position: relative;
        width: 100%;
        max-width: 520px;
        margin: 0 auto;
        border-radius: 16px;
        border: 1px solid rgba(63,169,255,0.55);
        box-shadow: 0 0 22px rgba(0,150,255,0.18);
        overflow: hidden;
        background: radial-gradient(circle at top, rgba(20,40,70,0.55) 0%, rgba(5,8,16,0.92) 55%);
      }}
      .avatar-bg {{
        width: 100%;
        display: block;
        user-select: none;
        -webkit-user-drag: none;
      }}
      .overlay {{
        position: absolute;
        inset: 0;
      }}
      .lbl {{
        fill: #e5f4ff;
        font-weight: 900;
        font-size: 14px;
        text-anchor: middle;
        paint-order: stroke;
        stroke: rgba(0,0,0,0.75);
        stroke-width: 3px;
      }}
      .title {{
        font-family: system-ui, -apple-system, Segoe UI, Roboto;
        color: #cce8ff;
        font-weight: 900;
        margin: 0 0 10px 2px;
        text-align: center;
      }}
      .legend {{
        display:flex; gap:10px; justify-content:center; flex-wrap:wrap;
        padding: 10px 0 12px 0;
        font-family: system-ui, -apple-system, Segoe UI, Roboto;
        color:#9bd4ff; font-weight:800;
      }}
      .chip {{ padding:6px 10px; border-radius:999px; border:1px solid rgba(63,169,255,0.35); background: rgba(5,8,16,0.55); }}
      .low {{ color:#3b82f6; }}
      .mid {{ color:#22d3ee; }}
      .high {{ color:#facc15; }}
      #tip {{
        position:absolute;
        display:none;
        padding:8px 10px;
        border-radius: 10px;
        background: rgba(5,8,16,0.9);
        border: 1px solid rgba(63,169,255,0.45);
        color: #cce8ff;
        font-family: system-ui, -apple-system, Segoe UI, Roboto;
        font-weight: 900;
        box-shadow: 0 0 18px rgba(0,150,255,0.18);
        pointer-events:none;
        z-index: 10;
      }}
    </style>

    <div class="title">{selected_user} — Avatar Muscle Targets</div>

    <div class="avatar-wrap" id="wrap">
      <img class="avatar-bg" src="data:image/png;base64,{avatar_b64}" />

      <svg class="overlay" viewBox="0 0 370 560" preserveAspectRatio="xMidYMid meet">
        <defs>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="blur"/>
            <feMerge>
              <feMergeNode in="blur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {''.join(svg_parts)}
        {''.join(labels_parts)}
      </svg>

      <div id="tip"></div>
    </div>

    <div class="legend">
      <span class="chip"><span class="low">Low</span></span>
      <span class="chip"><span class="mid">Medium</span></span>
      <span class="chip"><span class="high">High</span></span>
    </div>

    <script>
      const regions = {regions_json};
      const wrap = document.getElementById("wrap");
      const tip = document.getElementById("tip");

      function showTip(text, x, y) {{
        tip.style.display = "block";
        tip.innerText = text;
        const rect = wrap.getBoundingClientRect();
        tip.style.left = (x - rect.left + 12) + "px";
        tip.style.top  = (y - rect.top  + 12) + "px";
      }}

      function hideTip() {{
        tip.style.display = "none";
      }}

      // Hover tooltips on rectangles
      regions.forEach(r => {{
        const el = document.getElementById(r.id);
        if (!el) return;
        el.addEventListener("mousemove", (e) => {{
          showTip(`${{r.label}} — ${{r.value}}`, e.clientX, e.clientY);
        }});
        el.addEventListener("mouseleave", hideTip);
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
