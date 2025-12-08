import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime as dt
import re
from collections import defaultdict

# ---------- CONFIG ----------
CSV_URL = "https://docs.google.com/spreadsheets/d/1XQEJH-s0Z6LrutwTTSvS0cYR1e3Tiqi6VqUkGQ-S3Lg/export?format=csv&gid=2121731071"

st.set_page_config(page_title="Team BekFe Fitness", layout="wide")

# ---------- HELPERS ----------

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = [c.strip() for c in df.columns]
    return df


def parse_duration(text):
    if not isinstance(text, str):
        return 0
    s = text.lower()
    hours = 0
    minutes = 0

    h = re.search(r"(\d+)\s*(hour|hr|h)", s)
    m = re.search(r"(\d+)\s*(minute|min|m)", s)

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

    return hours * 60 + minutes


def extract_muscles(cell):
    if not isinstance(cell, str):
        return []
    parts = [p.split("(")[0].strip() for p in cell.split(",")]
    return [p for p in parts if p]


# ---------- LOAD DATA ----------
df = load_data()

col_timestamp = df.columns[0]
col_name = df.columns[1]
col_muscles = df.columns[3]
col_duration = df.columns[4]

df[col_timestamp] = pd.to_datetime(df[col_timestamp], errors="coerce")
df["minutes"] = df[col_duration].apply(parse_duration)

# 1 session = 1 timestamp row
sessions = df.groupby(col_name).size().rename("sessions")

# total minutes per user
duration = df.groupby(col_name)["minutes"].sum().rename("total_minutes")

# ---------- MUSCLE STATS ----------
user_muscle_counts = defaultdict(lambda: defaultdict(int))
all_muscles = set()

for _, row in df.iterrows():
    name = row[col_name]
    muscles = extract_muscles(row[col_muscles])
    for m in muscles:
        user_muscle_counts[name][m] += 1
        all_muscles.add(m)

users = sorted(sessions.index.tolist())
all_muscles = sorted(all_muscles)

activity_matrix = pd.DataFrame(0, index=all_muscles, columns=users)

for user, mus_dict in user_muscle_counts.items():
    for m, v in mus_dict.items():
        activity_matrix.loc[m, user] = v


# ---------- UI ----------
st.title("🏛️ Team BekFe Fitness Tracker")

tab_dashboard, tab_leaderboard, tab_activity, tab_profile = st.tabs(
    ["🏠 Dashboard", "🏆 Leaderboards", "📊 Fitness Activity", "🧍 Profile"]
)

# ------------------- DASHBOARD -------------------
with tab_dashboard:
    st.subheader("Overview")
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Form Entries", len(df))
    c2.metric("Active Members", df[col_name].nunique())
    c3.metric("Total Sessions", int(sessions.sum()))
    c4.metric("Total Hours", round(duration.sum() / 60, 1))

    st.markdown("### Recent Activity")
    st.dataframe(
        df[[col_timestamp, col_name, col_muscles, col_duration]].sort_values(
            col_timestamp, ascending=False
        ),
        use_container_width=True
    )


# ------------------- LEADERBOARD -------------------
with tab_leaderboard:
    st.subheader("🏆 Leaderboard – Total Fitness Sessions")

    lb = pd.concat([sessions, duration], axis=1).fillna(0).reset_index()
    lb["hours"] = (lb["total_minutes"] / 60).round(1)
    lb = lb.rename(columns={col_name: "Username"})
    lb = lb.sort_values("sessions", ascending=False).reset_index(drop=True)
    lb.index = lb.index + 1
    lb.insert(0, "Rank", lb.index)

    st.dataframe(lb, use_container_width=True)


# ------------------- FITNESS ACTIVITY -------------------
with tab_activity:
    st.subheader("📊 Muscle Group Activity by User")

    # Convert to long format for plotly
    heat_df = activity_matrix.reset_index().melt(id_vars="index")
    heat_df.columns = ["Muscle", "User", "Count"]

    fig = px.imshow(
        activity_matrix,
        labels=dict(x="User", y="Muscle", color="Count"),
        color_continuous_scale="Reds",
        aspect="auto",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Raw Activity Table")
    st.dataframe(activity_matrix, use_container_width=True)


# ------------------- PROFILE -------------------
with tab_profile:
    st.subheader("🧍 Member Profile")

    user_list = sorted(users)
    default_user = user_list.index("Vincent") if "Vincent" in user_list else 0
    selected = st.selectbox("Select Member", user_list, index=default_user)

    total_sessions = sessions[selected]
    total_minutes = duration[selected]
    total_hours = round(total_minutes / 60, 1)

    today = dt.date.today()
    season_end = dt.date(today.year, 12, 31)
    days_left = (season_end - today).days

    st.markdown(f"## ⚔️ {selected}'s Stats")

    c1, c2, c3 = st.columns(3)
    c1.metric("Fitness Days", total_sessions)
    c2.metric("Total Hours", total_hours)
    c3.metric("Season Ends In", f"{days_left} days")

    # Favorite muscles
    st.markdown("### 💪 Favorite Muscle Groups")
    mus_dict = user_muscle_counts[selected]
    mus_series = pd.Series(mus_dict).sort_values(ascending=False)

    if len(mus_series) > 0:
        st.write(mus_series.head(3))
    else:
        st.write("No muscle data.")

    st.markdown("### 😴 Least Worked Groups")
    if len(mus_series) > 0:
        st.write(mus_series.tail(3))


    st.markdown("### 📘 Workout Log")
    user_df = df[df[col_name] == selected][
        [col_timestamp, col_muscles, col_duration]
    ].sort_values(col_timestamp, ascending=False)

    st.dataframe(user_df, use_container_width=True)
