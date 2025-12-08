import streamlit as st
import pandas as pd
import plotly.express as px
import datetime as dt
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------
# GOOGLE SHEETS CONNECTION
# ---------------------------------------------
SHEET_ID = "1XQEJH-s0Z6LrutwTTSvS0cYR1e3Tiqi6VqUkGQ-S3Lg"
SHEET_NAME = "Form_Responses1"

def load_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    data = sheet.get_all_records()
    return pd.DataFrame(data), sheet

df, sheet = load_sheet()

# ---------------------------------------------
# NAME CLEANING (MERGE DUPLICATES)
# ---------------------------------------------
df["Please list your name :"] = (
    df["Please list your name :"]
    .str.strip()
    .str.title()
    .replace({
        "Vincemt": "Vincent",
        "Vince": "Vincent",
        "Alian": "Alain",
    })
)

# ---------------------------------------------
# PROCESS DATA
# ---------------------------------------------
df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

# Total sessions = every row where Yes or muscle group logged
df["Session"] = 1

# Extract hours from "25 mins – 2 hours"
def parse_duration(x):
    try:
        x = x.lower()
        if "hour" in x:
            return float(x.split("hour")[0].strip())
        if "min" in x:
            return round(int(x.split("min")[0].strip()) / 60, 2)
    except:
        return 0
    return 0

df["Hours"] = df["How long did you work out for? ( 25 mins - 2hours )"].astype(str).apply(parse_duration)

# Muscle group split
df["Muscle Groups"] = df["What muscle groups did your work on? (Please list all that applies)"].astype(str)


# ---------------------------------------------
# PAGE CONFIG — Solo Leveling UI
# ---------------------------------------------
st.set_page_config(page_title="Team BekFê Fitness Tracker", layout="wide")
st.markdown(
    """
    <style>
    body {
        background-color: #0a0f1a;
        color: #d1e4ff;
    }
    .big-title {
        font-size: 42px;
        font-weight: 900;
        color: #7db3ff;
        text-shadow: 0px 0px 15px #4ea4ff;
    }
    .card {
        background: rgba(20,30,50,0.4);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(120,150,255,0.3);
        text-align: center;
        color: #b8d4ff;
    }
    .highlight {
        font-size: 34px;
        font-weight: 800;
        color: #9cf2ff;
        text-shadow: 0 0 10px #6cdcff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="big-title">⚔️ Team BekFê Fitness Tracker ⚔️</div>', unsafe_allow_html=True)


# ---------------------------------------------
# TABS
# ---------------------------------------------
tab_dash, tab_lb, tab_fitness, tab_profile, tab_add = st.tabs(
    ["Dashboard", "Leaderboards", "Fitness Activity", "Profile", "Add Entry"]
)

# ---------------------------------------------
# DASHBOARD
# ---------------------------------------------
with tab_dash:
    st.subheader("📊 Dashboard Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f"<div class='card'><div class='highlight'>{len(df)}</div>Form Entries</div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='card'><div class='highlight'>{df['Please list your name :'].nunique()}</div>Active Members</div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='card'><div class='highlight'>{df['Session'].sum()}</div>Total Sessions</div>", unsafe_allow_html=True)
    col4.markdown(f"<div class='card'><div class='highlight'>{round(df['Hours'].sum(),1)}</div>Total Hours</div>", unsafe_allow_html=True)

    st.subheader("🔥 Recent Activity")
    st.dataframe(df.sort_values("Timestamp", ascending=False).head(15), use_container_width=True)


# ---------------------------------------------
# LEADERBOARDS
# ---------------------------------------------
with tab_lb:
    st.subheader("🏆 Leaderboard — Total Sessions")

    leaderboard = (
        df.groupby("Please list your name :")["Session"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    leaderboard.columns = ["Name", "Total Sessions"]

    st.dataframe(leaderboard, use_container_width=True)


# ---------------------------------------------
# FITNESS ACTIVITY
# ---------------------------------------------
with tab_fitness:
    st.subheader("💪 Muscle Group Activity by User")

    muscle_counts = (
        df.assign(Muscle=df["Muscle Groups"].str.split(", "))
        .explode("Muscle")
        .groupby(["Please list your name :", "Muscle"])
        .size()
        .reset_index(name="Count")
    )

    st.dataframe(muscle_counts, use_container_width=True)


# ---------------------------------------------
# PROFILE SECTION
# ---------------------------------------------
with tab_profile:
    st.subheader("🧍 Profile Stats")

    user_list = sorted(df["Please list your name :"].unique())
    selected = st.selectbox("Choose a user", user_list)

    user_df = df[df["Please list your name :"] == selected]

    level = len(user_df)
    total_hours = round(user_df["Hours"].sum(), 1)

    st.markdown(
        f"""
        <div class='card'>
            <div class='highlight'>Level {level}</div>
            <strong>Total Hours:</strong> {total_hours}<br>
            <strong>Total Sessions:</strong> {len(user_df)}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------
# ADD ENTRY TAB
# ---------------------------------------------
with tab_add:
    st.subheader("📝 Add a New Workout Entry")

    name = st.text_input("Your Name")
    duration = st.text_input("Workout Duration (ex: 45 mins or 1 hour)")
    did = st.radio("Did you workout today?", ["Yes", "No"])
    muscles = st.multiselect(
        "Muscle Groups",
        [
            "Chest","Back","Biceps","Triceps","Forearms","Shoulders","Hips","Legs",
            "Glutes","Abs","Cardio","Calisthenics (Bodyweight exercises)",
            "Stretching","HIIT (High-Intensity Interval Training)",
            "Sports (Tennis,Soccer..etc)"
        ]
    )

    if st.button("Submit"):
        if name.strip() == "":
            st.error("Name is required.")
        else:
            row = [
                dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                name,
                ", ".join(muscles),
                duration,
                did
            ]
            sheet.append_row(row)
            st.success("Entry added successfully!")

