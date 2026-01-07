import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import datetime as dt
import re
from collections import defaultdict

# OPTIONAL (only needed if you want to truly SAVE steps to Google Sheets)
# If you don't set Streamlit secrets, the Steps tab will still work (preview + manual),
# but it will show an error when you click "Save Steps".
import gspread
from google.oauth2.service_account import Credentials

# -------------------------------------------------------------
#                PAGE CONFIG
# -------------------------------------------------------------
st.set_page_config(
    page_title="Level Fit",
    layout="wide",
)

# -------------------------------------------------------------
#                GLOBAL STYLING (SOLO-LEVELING THEME)
# -------------------------------------------------------------
st.markdown(
    """
    <style>
    body { background-color: #05070c; color: #e5f4ff; }

    .main-title {
        font-size: 40px; font-weight: 900; text-align: center;
        color: #e5f4ff; text-shadow: 0 0 12px #3f9dff; margin-bottom: 6px;
    }
    .glow-header {
        font-size: 26px; font-weight: 800; color: #7fd1ff !important;
        text-shadow: 0 0 10px #3f9dff; border-bottom: 2px solid #2f9dff;
        padding-bottom: 4px; margin-bottom: 15px; display: inline-block;
    }
    .sub-header {
        font-size: 18px; font-weight: 700; color: #9bd4ff !important;
        margin-top: 20px; margin-bottom: 6px; text-shadow: 0 0 6px #217ac6;
    }
    .stat-box {
        padding: 18px;
        background: radial-gradient(circle at top, #101927 0, #050810 55%);
        border-radius: 14px; text-align: center;
        border: 1px solid #245b8f;
        box-shadow: 0 0 24px rgba(0,150,255,0.4);
    }
    .stat-value { font-size: 38px; font-weight: 900; color: #7fd1ff; }
    .stat-label { font-size: 14px; color: #9bb8d1; }

    .featured-line {
        font-size: 17px; color: #ffe8a3;
        background: rgba(34, 22, 6, 0.88);
        border-radius: 10px; padding: 10px 14px;
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

    /* Season buttons look */
    .season-wrap label { font-weight: 800 !important; color: #cce8ff !important; }
    div[role="radiogroup"] > label {
        border: 1px solid #3fa9ff !important;
        border-radius: 10px !important;
        padding: 8px 16px !important;
        margin-right: 10px !important;
        background: rgba(10,25,45,0.55) !important;
        box-shadow: 0 0 10px rgba(63,169,255,0.15);
        cursor: pointer;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------------------
#             GOOGLE SHEETS - WORKOUT DATA (READ)
# -------------------------------------------------------------
CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1XQEJH-s0Z6LrutwTTSvS0cYR1e3Tiqi6VqUkGQ-S3Lg/export"
    "?format=csv&gid=2121731071"
)

@st.cache_data(ttl=300)
def load_data():
    _df = pd.read_csv(CSV_URL)
    _df.columns = [c.strip() for c in _df.columns]
    return _df

df = load_data()

# -------------------------------------------------------------
#             OPTIONAL: GOOGLE SHEETS - STEPS (WRITE)
# -------------------------------------------------------------
def get_gspread_client():
    """
    Optional: configure Streamlit secrets to enable saving steps:
    - st.secrets["gcp_service_account"]  (service account json dict)
    - st.secrets["steps_sheet_id"]       (Google Sheet ID where you want a "Steps" tab)
    """
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )
        return gspread.authorize(creds)
    except Exception:
        return None

def ensure_steps_worksheet(sh, title="Steps"):
    try:
        return sh.worksheet(title)
    except Exception:
        ws = sh.add_worksheet(title=title, rows="2000", cols="10")
        ws.append_row(["timestamp", "user", "date", "steps", "note"])
        return ws

# -------------------------------------------------------------
#             COLUMN SETUP
# -------------------------------------------------------------
col_timestamp = df.columns[0]
col_name      = df.columns[1]
col_muscles   = df.columns[3]
col_duration  = df.columns[4]

# -------------------------------------------------------------
#             ROBUST DATE PARSE (2-PASS)
# -------------------------------------------------------------
def robust_to_datetime(series: pd.Series) -> pd.Series:
    s1 = pd.to_datetime(series, errors="coerce", infer_datetime_format=True)
    if s1.isna().mean() > 0.20:
        s2 = pd.to_datetime(series, errors="coerce", dayfirst=True)
        if s2.notna().sum() > s1.notna().sum():
            return s2
    return s1

df[col_timestamp] = robust_to_datetime(df[col_timestamp])
df["year"] = df[col_timestamp].dt.year

# -------------------------------------------------------------
#             CLEAN NAME + DURATION
# -------------------------------------------------------------
def clean_name(n):
    if not isinstance(n, str):
        return ""
    n = re.sub(r"[^a-z0-9 ]", "", n.lower().strip())
    corrections = {
        "vincent":"Vincent","alain":"Alain","danimix":"Danimix",
        "dani mix":"Danimix","dimitri":"Dimitri","douglas":"Douglas",
        "louis":"Louis","bousik":"Bousik","gregory":"Gregory",
        "mikael":"Mikael","junior":"Junior"
    }
    return corrections.get(n, n.title())

df[col_name] = df[col_name].apply(clean_name)

def parse_duration(t):
    if not isinstance(t, str):
        return 0
    t = t.lower()
    h = re.search(r"(\d+)\s*(hour|hr|h)", t)
    m = re.search(r"(\d+)\s*(min|m)", t)
    hours = int(h.group(1)) if h else 0
    mins  = int(m.group(1)) if m else 0

    if not h and not m:
        nums = re.findall(r"\d+", t)
        if len(nums) == 1:
            mins = int(nums[0])
        elif len(nums) == 2:
            hours = int(nums[0])
            mins = int(nums[1])
    return hours * 60 + mins

df["minutes"] = df[col_duration].apply(parse_duration)

# -------------------------------------------------------------
#             SEASON SELECTOR (ALWAYS SHOW 2025 + 2026)
# -------------------------------------------------------------
FORCE_YEARS = [2025, 2026]
available_years = sorted({int(y) for y in df["year"].dropna().unique()} | set(FORCE_YEARS))
today = dt.date.today()
default_year = today.year if today.year in available_years else max(available_years)

# -------------------------------------------------------------
#                HEADER
# -------------------------------------------------------------
st.markdown("<div class='main-title'>Level Fit</div>", unsafe_allow_html=True)

st.markdown("""
### Log Your Fitness Sessions  
<a href="https://docs.google.com/forms/d/1JqTx8Fd5la2BGv4h5s1506KZMVQUqHL2U0pNvKs0KTo/edit"
target="_blank"
style="background:#0d1b2a;padding:10px 20px;border-radius:8px;
border:1px solid #3ecbff;color:#aee6ff;font-size:16px;text-decoration:none;">
➤ Submit Entry
</a>
""", unsafe_allow_html=True)

st.markdown("<div class='sub-header season-wrap'>📅 Select Season</div>", unsafe_allow_html=True)
season_year = st.radio(
    "Select Season",
    available_years,
    index=available_years.index(default_year),
    horizontal=True,
    key="season_year"
)

df_season = df[df["year"] == season_year].copy()

# -------------------------------------------------------------
#             MUSCLE EXTRACTION
# -------------------------------------------------------------
def extract_muscles(txt):
    if not isinstance(txt, str):
        return []
    return [x.split("(")[0].strip() for x in txt.split(",") if x.strip()]

user_muscles = defaultdict(lambda: defaultdict(int))
overall_muscles = defaultdict(int)

for _, row in df_season.iterrows():
    user = row[col_name]
    muscs = extract_muscles(row[col_muscles])
    for m in muscs:
        user_muscles[user][m] += 1
        overall_muscles[m] += 1

# -------------------------------------------------------------
#             METRICS (SAFE IF EMPTY)
# -------------------------------------------------------------
if len(df_season) > 0:
    sessions = df_season.groupby(col_name).size()
    duration = df_season.groupby(col_name)["minutes"].sum()

    df_season["date"] = df_season[col_timestamp].dt.date
    sessions_per_day = df_season.groupby("date").size().reset_index(name="sessions")
    sessions_per_day["7day_avg"] = sessions_per_day["sessions"].rolling(7, 1).mean()

    users = sorted(df_season[col_name].dropna().unique())
else:
    sessions = pd.Series(dtype=int)
    duration = pd.Series(dtype=int)
    sessions_per_day = pd.DataFrame({"date": [], "sessions": [], "7day_avg": []})
    users = []

mus_df = pd.DataFrame({"Muscle": list(overall_muscles.keys()), "Count": list(overall_muscles.values())})
hours_df = (
    pd.DataFrame({"User": duration.index, "Hours": (duration/60).round(1)})
    .sort_values("Hours", ascending=False)
    if len(duration) else pd.DataFrame({"User": [], "Hours": []})
)

# -------------------------------------------------------------
#               RANK SYSTEM LOGIC
# -------------------------------------------------------------
def get_rank_letter(n):
    if n >= 250: return "S"
    if n >= 180: return "A"
    if n >= 120: return "B"
    if n >= 60:  return "C"
    if n >= 30:  return "D"
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

if len(sessions) > 0:
    consistency_map = {u: round((int(sessions[u]) / 365) * 100, 1) for u in sessions.index}
    rank_map = {u: get_rank_letter(int(sessions[u])) for u in sessions.index}
    top_user = sessions.idxmax()
    top_user_rank_letter = rank_map[top_user]
    top_user_sessions = int(sessions[top_user])
else:
    consistency_map = {}
    rank_map = {}
    top_user = None
    top_user_rank_letter = "E"
    top_user_sessions = 0

# -------------------------------------------------------------
#                TABS
# -------------------------------------------------------------
tab_profile, tab_steps, tab_lb, tab_activity, tab_dash, tab_ranks = st.tabs(
    ["Profile", "Steps", "Leaderboards", "Fitness Activity", "Dashboard", "Ranking System"]
)

# -------------------------------------------------------------
#                PROFILE TAB
# -------------------------------------------------------------
with tab_profile:
    st.markdown("<div class='glow-header'>Profile</div>", unsafe_allow_html=True)

    if len(df_season) == 0:
        st.warning(f"No data for {season_year} yet. Add sessions with {season_year} timestamps to populate this season.")
    else:
        featured_html = render_rank_badge(top_user_rank_letter)
        st.markdown(
            f"<div class='featured-line'>🏆 Featured Athlete: <b>{top_user}</b> – {featured_html} – <b>{top_user_sessions}</b> sessions</div>",
            unsafe_allow_html=True
        )

        selected = st.selectbox("Select Member", users, index=users.index(top_user))

        total_sessions_user = int(sessions[selected])
        total_minutes_user = int(duration[selected])
        total_hours_user = round(total_minutes_user / 60, 1)
        consistency_user = consistency_map.get(selected, 0)
        rank_letter_user = rank_map.get(selected, "E")
        rank_html = render_rank_badge(rank_letter_user)

        # Season summary
        if season_year == today.year:
            season_date = today
            season_end = dt.date(season_year, 12, 31)
            days_left = (season_end - season_date).days
            season_status = f"Ends in: {days_left} days"
        else:
            season_date = dt.date(season_year, 12, 31)
            days_left = 0
            season_status = "Season complete ✅"

        st.markdown(
            f"<div class='summary-line'><b>Season:</b> {season_year} | "
            f"<b>Date:</b> {season_date} | <b>{season_status}</b></div>",
            unsafe_allow_html=True
        )

        st.markdown(f"<div class='sub-header'>{selected} – {rank_html}</div>", unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='stat-box'><div class='stat-value'>{total_sessions_user}</div><div class='stat-label'>Total Sessions</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='stat-box'><div class='stat-value'>{total_hours_user}</div><div class='stat-label'>Total Hours</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='stat-box'><div class='stat-value'>{days_left}</div><div class='stat-label'>Days Left</div></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='stat-box'><div class='stat-value'>{consistency_user}%</div><div class='stat-label'>Season Consistency</div></div>", unsafe_allow_html=True)

        # Progress bar
        st.markdown("<div class='sub-header'>📈 Progress to Next Rank</div>", unsafe_allow_html=True)

        rank_thresholds = {"S":250, "A":180, "B":120, "C":60, "D":30, "E":0}
        order = ["E", "D", "C", "B", "A", "S"]

        current_rank = rank_letter_user
        current_count = total_sessions_user

        if current_rank == "S":
            next_rank = None
            next_threshold = 365
        else:
            next_rank = order[order.index(current_rank) + 1]
            next_threshold = rank_thresholds[next_rank]

        current_threshold = rank_thresholds[current_rank]
        denom = (next_threshold - current_threshold) if (next_threshold - current_threshold) != 0 else 1
        progress = (current_count - current_threshold) / denom
        progress = max(0, min(progress, 1))

        st.markdown(f"""
            <style>
            @keyframes manaFill {{
                from {{ width: 0%; }}
                to {{ width: {progress*100}%; }}
            }}
            .mana-bar {{
                width: 100%; height: 20px; background: #0a0f1a;
                border-radius: 10px; border: 1px solid #3fa9ff;
                overflow: hidden; margin-bottom: 12px;
            }}
            .mana-fill {{
                height: 100%;
                background: linear-gradient(90deg, #1e90ff, #00e1ff);
                animation: manaFill 1.8s ease-out forwards;
            }}
            </style>

            <div class="mana-bar"><div class="mana-fill"></div></div>
        """, unsafe_allow_html=True)

        st.write(f"**{current_count} / {next_threshold} sessions to reach {next_rank or 'MAX'} Rank**")

        # Muscles + Log
        st.markdown("<div class='sub-header'>💪 Top Muscles Used</div>", unsafe_allow_html=True)
        top_df = pd.Series(user_muscles[selected]).sort_values(ascending=False).head(5)
        st.dataframe(top_df.reset_index().rename(columns={"index":"Muscle", 0:"Count"}), hide_index=True)

        st.markdown("<div class='sub-header'>📘 Workout Log</div>", unsafe_allow_html=True)
        log = df_season[df_season[col_name] == selected][[col_timestamp, col_muscles, col_duration]]
        st.dataframe(log.sort_values(col_timestamp, ascending=False), hide_index=True)

        # Monthly consistency
        st.markdown("<div class='sub-header'>📉 Monthly Training Consistency</div>", unsafe_allow_html=True)
        df_user = df_season[df_season[col_name] == selected].copy()
        df_user["month"] = df_user[col_timestamp].dt.month
        df_user["Month"] = df_user[col_timestamp].dt.strftime("%B")
        monthly_sessions = (
            df_user.groupby(["month", "Month"]).size().reset_index(name="Sessions").sort_values("month")
        )

        if len(monthly_sessions) == 0:
            st.info("No monthly data for this user in this season yet.")
        else:
            st.plotly_chart(
                px.bar(monthly_sessions, x="Month", y="Sessions", text="Sessions", title=None)
                .update_traces(textposition="outside")
                .update_layout(yaxis_title="Sessions", xaxis_title=""),
                use_container_width=True
            )

# -------------------------------------------------------------
#                STEPS TAB (OPTION C1: PREVIEW ONLY)
# -------------------------------------------------------------
with tab_steps:
    st.markdown("<div class='glow-header'>Steps</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>📸 Log Steps (Screenshot Preview Only)</div>", unsafe_allow_html=True)

    if len(users) == 0:
        st.warning("No users available for this season yet.")
    else:
        steps_user = st.selectbox("Select Member", users, key="steps_user")

        img = st.file_uploader(
            "Upload your steps screenshot (optional). This will NOT be stored.",
            type=["png", "jpg", "jpeg", "webp"],
            key="steps_img"
        )
        if img is not None:
            st.image(img, caption="Preview (not saved)", use_container_width=True)

        steps_date = st.date_input("Date", value=dt.date.today(), key="steps_date")
        steps_value = st.number_input("Steps", min_value=0, step=100, value=0, key="steps_value")
        note = st.text_input("Note (optional)", value="", key="steps_note")

        if st.button("✅ Save Steps", use_container_width=True):
            gc = get_gspread_client()
            if gc is None:
                st.error(
                    "Steps logging is not connected to Google Sheets yet.\n\n"
                    "To enable saving, add Streamlit secrets:\n"
                    "- gcp_service_account\n"
                    "- steps_sheet_id\n\n"
                    "Until then: screenshot preview + manual entry works, but cannot save."
                )
            else:
                try:
                    sh = gc.open_by_key(st.secrets["steps_sheet_id"])
                    ws = ensure_steps_worksheet(sh, "Steps")
                    ws.append_row([
                        dt.datetime.now().isoformat(),
                        steps_user,
                        steps_date.isoformat(),
                        int(steps_value),
                        note
                    ])
                    st.success(f"Saved ✅ {steps_user} • {steps_value:,} steps • {steps_date}")
                    st.info("Screenshot was previewed only and NOT stored (C1).")
                except Exception as e:
                    st.error(f"Failed to save steps: {e}")

# -------------------------------------------------------------
#                LEADERBOARD TAB
# -------------------------------------------------------------
with tab_lb:
    st.markdown("<div class='glow-header'>Leaderboards</div>", unsafe_allow_html=True)

    if len(sessions) == 0:
        st.info(f"No leaderboard data for season {season_year} yet.")
    else:
        lb = pd.DataFrame({
            "User": sessions.index,
            "Sessions": sessions.values,
            "Hours": (duration.values/60).round(1),
            "Consistency %": [consistency_map.get(u, 0) for u in sessions.index],
            "Rank": [rank_map.get(u, "E") for u in sessions.index]
        }).sort_values("Sessions", ascending=False).reset_index(drop=True)
        lb.insert(0, "Position", lb.index + 1)
        st.dataframe(lb, hide_index=True, use_container_width=True)

# -------------------------------------------------------------
#                FITNESS ACTIVITY TAB
# -------------------------------------------------------------
with tab_activity:
    st.markdown("<div class='glow-header'>Fitness Activity</div>", unsafe_allow_html=True)

    st.markdown("<div class='sub-header'>🔥 Most Trained Muscle Groups</div>", unsafe_allow_html=True)
    if len(mus_df) == 0:
        st.info("No muscle data for this season.")
    else:
        st.plotly_chart(px.bar(mus_df.sort_values("Count", ascending=False), x="Muscle", y="Count"), use_container_width=True)

    st.markdown("<div class='sub-header'>⏳ Total Hours per Member</div>", unsafe_allow_html=True)
    if len(hours_df) == 0:
        st.info("No duration data for this season.")
    else:
        st.plotly_chart(px.bar(hours_df, x="User", y="Hours"), use_container_width=True)

    st.markdown("<div class='sub-header'>💪 Muscle Distribution</div>", unsafe_allow_html=True)
    if len(mus_df) == 0:
        st.info("No muscle distribution for this season.")
    else:
        st.plotly_chart(px.pie(mus_df, names="Muscle", values="Count", hole=0.45), use_container_width=True)

    st.markdown("<div class='sub-header'>📅 Training Frequency (7-Day Avg)</div>", unsafe_allow_html=True)
    if len(sessions_per_day) == 0:
        st.info("No daily frequency data for this season.")
    else:
        st.plotly_chart(px.line(sessions_per_day, x="date", y="7day_avg"), use_container_width=True)

# -------------------------------------------------------------
#                DASHBOARD TAB
# -------------------------------------------------------------
with tab_dash:
    st.markdown("<div class='glow-header'>Dashboard Overview</div>", unsafe_allow_html=True)
    st.dataframe(df_season.sort_values(col_timestamp, ascending=False).head(25), hide_index=True, use_container_width=True)

# -------------------------------------------------------------
#                RANKING SYSTEM TAB
# -------------------------------------------------------------
with tab_ranks:
    st.markdown("<div class='glow-header'>Ranking System</div>", unsafe_allow_html=True)

    rank_html = """
    <style>
    .rank-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    .rank-table th, .rank-table td {
        padding: 12px; text-align: center; font-size: 16px; border: 1px solid #1e293b;
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
