import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import re
from collections import defaultdict

# ---------- CONFIG ----------
CSV_URL = "https://docs.google.com/spreadsheets/d/1XQEJH-s0Z6LrutwTTSvS0cYR1e3Tiqi6VqUkGQ-S3Lg/export?format=csv&gid=2121731071"
SEASON_END_MONTH = 12   # December
SEASON_END_DAY = 31     # 31st

st.set_page_config(
    page_title="Team BekFe Fitness",
    layout="wide",
    page_icon="💪"
)

# ---------- HELPERS ----------

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(CSV_URL)
    # Try to normalize column names a bit
    df.columns = [c.strip() for c in df.columns]

    # Identify columns by partial name (handles small edits in the form)
    def find_col(pattern):
        for c in df.columns:
            if pattern.lower() in c.lower():
                return c
        raise ValueError(f"Column with pattern '{pattern}' not found")

    cols = {
        "timestamp": find_col("timestamp"),
        "name": find_col("please list your name"),
        "did_exercise": find_col("did you engage"),
        "muscles": find_col("muscle"),
        "duration": find_col("how long did you work out")
    }

    # Convert timestamp
    df[cols["timestamp"]] = pd.to_datetime(df[cols["timestamp"]], errors="coerce")

    return df, cols


def parse_duration_to_minutes(text: str) -> float:
    """
    Convert messy duration text to minutes.
    Handles things like:
    - '2 hours'
    - '1 hour 30 minutes'
    - '45 mins'
    - '1h'
    - '1h 15'
    - '1 hour of hit cardio, p90x style'
    """
    if not isinstance(text, str):
        return np.nan

    s = text.lower().strip()

    # Replace commas with spaces for easier matching
    s = s.replace(",", " ")

    # Patterns for hours and minutes
    hour_pattern = r"(\d+)\s*(hour|hours|hr|hrs|h)\b"
    minute_pattern = r"(\d+)\s*(minute|minutes|min|mins|m)\b"

    hours = 0
    minutes = 0

    # Find all explicit hour & minute mentions
    h_match = re.search(hour_pattern, s)
    m_match = re.search(minute_pattern, s)

    if h_match:
        hours = int(h_match.group(1))
    if m_match:
        minutes = int(m_match.group(1))

    # If we still have nothing, try a bare number
    if not h_match and not m_match:
        nums = re.findall(r"\d+", s)
        if len(nums) == 1:
            # Assume minutes if e.g. '45'
            minutes = int(nums[0])
        elif len(nums) == 2:
            # Assume H:M like '1 30'
            hours = int(nums[0])
            minutes = int(nums[1])

    total_minutes = hours * 60 + minutes
    if total_minutes == 0:
        return np.nan
    return total_minutes


def build_user_stats(df, cols):
    # Filter only "Yes" days just in case
    df_yes = df[df[cols["did_exercise"]].astype(str).str.lower() == "yes"].copy()

    # Sessions per user
    sessions = df_yes.groupby(cols["name"]).size().rename("sessions")

    # Duration
    df_yes["minutes"] = df_yes[cols["duration"]].apply(parse_duration_to_minutes)
    duration = df_yes.groupby(cols["name"])["minutes"].sum().rename("total_minutes")

    # Muscles per user
    user_muscle_counts = defaultdict(lambda: defaultdict(int))
    all_muscles = set()

    for _, row in df_yes.iterrows():
        name = str(row[cols["name"]]).strip()
        cell = str(row[cols["muscles"]])
        parts = [p.strip() for p in cell.split(",") if p.strip()]
        for p in parts:
            # Remove text in parentheses so
            # "Calisthenics (Bodyweight exercises)" -> "Calisthenics"
            base = p.split("(")[0].strip()
            if not base:
                continue
            all_muscles.add(base)
            user_muscle_counts[name][base] += 1

    all_muscles = sorted(all_muscles)
    users = sorted(sessions.index.tolist())

    # Muscle activity table (rows = muscle, cols = user)
    muscle_table = pd.DataFrame(0, index=all_muscles, columns=users, dtype=int)
    for user, mus_dict in user_muscle_counts.items():
        for m, count in mus_dict.items():
            if m in muscle_table.index and user in muscle_table.columns:
                muscle_table.loc[m, user] = count

    return sessions, duration, muscle_table, user_muscle_counts


# ---------- MAIN APP ----------

df, cols = load_data()
sessions, duration, muscle_table, user_muscle_counts = build_user_stats(df, cols)

st.title("🏛️ Team BekFe Fitness Tracker")

tab_dashboard, tab_leaderboard, tab_activity, tab_profile = st.tabs(
    ["🏠 Dashboard", "🏆 Leaderboards", "📊 Fitness Activity", "🧍 Profile"]
)

# ---------- DASHBOARD ----------
with tab_dashboard:
    st.subheader("Overview")

    total_entries = len(df)
    total_users = df[cols["name"]].nunique()
    total_sessions = int(sessions.sum())
    total_minutes_all = float(duration.sum())
    total_hours_all = round(total_minutes_all / 60.0, 1)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Form Entries", total_entries)
    c2.metric("Active Members", total_users)
    c3.metric("Total Sessions", total_sessions)
    c4.metric("Total Hours (approx.)", total_hours_all)

    st.markdown("---")
    st.subheader("Recent Activity")
    df_display = df[[cols["timestamp"], cols["name"], cols["muscles"], cols["duration"]]].sort_values(
        by=cols["timestamp"], ascending=False
    )
    st.dataframe(df_display.head(25), use_container_width=True)

# ---------- LEADERBOARD ----------
with tab_leaderboard:
    st.subheader("🏆 Leaderboard – Total Fitness Sessions")

    lb = (
        pd.concat([sessions, duration], axis=1)
        .fillna(0)
        .reset_index()
        .rename(columns={
            cols["name"]: "Username",
            "sessions": "Total Fitness Sessions",
            "total_minutes": "Total Minutes"
        })
    )

    lb["Total Hours"] = (lb["Total Minutes"] / 60).round(1)
    lb = lb.sort_values(by="Total Fitness Sessions", ascending=False).reset_index(drop=True)
    lb.index = lb.index + 1  # Rank starting at 1
    lb.insert(0, "Rank", lb.index)

    st.dataframe(
        lb[["Rank", "Username", "Total Fitness Sessions", "Total Hours"]],
        use_container_width=True,
        height=400
    )

# ---------- FITNESS ACTIVITY ----------
with tab_activity:
    st.subheader("📊 Muscle Group Activity by User")

    # Add a "Total" row
    activity = muscle_table.copy()
    activity.loc["Total"] = activity.sum(axis=0)

    st.write("Counts = number of sessions where that muscle group was logged.")
    st.dataframe(
        activity.style.background_gradient(axis=None),
        use_container_width=True
    )

# ---------- PROFILE ----------
with tab_profile:
    st.subheader("🧍 Member Profile")

    all_users = sorted(sessions.index.tolist())
    default_index = all_users.index("Vincent") if "Vincent" in all_users else 0
    selected_user = st.selectbox("Select a user", all_users, index=default_index)

    st.markdown(f"### ⚔️ {selected_user}'s Profile")

    user_sessions = int(sessions.get(selected_user, 0))
    user_minutes = float(duration.get(selected_user, 0.0))
    user_hours = round(user_minutes / 60.0, 1)

    today = dt.date.today()
    season_year = today.year
    season_end = dt.date(season_year, SEASON_END_MONTH, SEASON_END_DAY)
    days_left = (season_end - today).days

    c1, c2, c3 = st.columns(3)
    c1.metric("Fitness Days (Sessions)", user_sessions)
    c2.metric("Total Hours (approx.)", user_hours)
    c3.metric("Season Ends In", f"{max(days_left,0)} days")

    # Favorite / least worked muscles
    mus_dict = user_muscle_counts.get(selected_user, {})
    mus_series = pd.Series(mus_dict).sort_values(ascending=False)

    st.markdown("#### 💪 Favorite Muscle Groups")
    if len(mus_series) == 0:
        st.write("No muscle data yet for this user.")
    else:
        fav = mus_series.head(3)
        for m, v in fav.items():
            st.write(f"- **{m}** – {v} sessions")

    st.markdown("#### 💤 Least Worked Muscle Groups")
    if len(mus_series) > 0:
        # muscles with the lowest non-zero counts
        least = mus_series.sort_values(ascending=True).head(3)
        for m, v in least.items():
            st.write(f"- **{m}** – {v} sessions")

    st.markdown("---")
    st.markdown("#### Raw Log for this User")
    user_log = df[df[cols["name"]] == selected_user]
    st.dataframe(
        user_log[[cols["timestamp"], cols["muscles"], cols["duration"]]].sort_values(
            by=cols["timestamp"], ascending=False
        ),
        use_container_width=True,
        height=300
    )

