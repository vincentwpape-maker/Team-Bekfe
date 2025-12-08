with tab_activity:
    st.header("💠 Fitness Activity Dashboard")

    # -----------------------------------
    # 1️⃣ MUSCLE GROUP POPULARITY (BAR CHART)
    # -----------------------------------
    st.subheader("🔥 Most Trained Muscle Groups")

    muscle_totals = (
        df[col_muscles]
        .fillna("")
        .apply(lambda x: [m.strip() for m in str(x).split(",") if m.strip()])
        .explode()
        .value_counts()
        .reset_index()
    )
    muscle_totals.columns = ["Muscle Group", "Count"]

    chart1 = alt.Chart(muscle_totals).mark_bar().encode(
        x=alt.X("Count:Q"),
        y=alt.Y("Muscle Group:N", sort='-x'),
        color=alt.Color("Count:Q", scale=alt.Scale(scheme="blues")),
        tooltip=["Muscle Group", "Count"]
    ).properties(height=450)

    st.altair_chart(chart1, use_container_width=True)

    # -----------------------------------
    # 2️⃣ MUSCLE BREAKDOWN PER USER (STACKED BAR)
    # -----------------------------------
    st.subheader("🧍‍♂️ Muscle Breakdown by User (Stacked Bar)")

    stacked_df = (
        activity_matrix.reset_index()
        .melt(id_vars="index", var_name="User", value_name="Count")
        .rename(columns={"index": "Muscle"})
    )

    chart2 = alt.Chart(stacked_df).mark_bar().encode(
        x=alt.X("User:N", title="User"),
        y=alt.Y("Count:Q", title="Muscle Count"),
        color=alt.Color("Muscle:N", scale=alt.Scale(scheme="tableau10")),
        tooltip=["User", "Muscle", "Count"]
    ).properties(height=500)

    st.altair_chart(chart2, use_container_width=True)

    # -----------------------------------
    # 3️⃣ SESSION TIMELINE (AREA CHART)
    # -----------------------------------
    st.subheader("📅 Activity Timeline")

    timeline_df = (
        df[[col_timestamp, col_name]]
        .groupby(df[col_timestamp].dt.date)
        .size()
        .reset_index(name="Sessions")
    )

    chart3 = alt.Chart(timeline_df).mark_area(opacity=0.7).encode(
        x=alt.X("Timestamp:T", title="Date"),
        y=alt.Y("Sessions:Q"),
        color=alt.value("#4fa3f7"),
        tooltip=["Timestamp", "Sessions"]
    ).properties(height=300)

    st.altair_chart(chart3, use_container_width=True)

    # -----------------------------------
    # 4️⃣ WORKOUT DURATION DISTRIBUTION (HISTOGRAM)
    # -----------------------------------
    st.subheader("⏱ Workout Duration Distribution")

    chart4 = alt.Chart(df).mark_bar().encode(
        x=alt.X("minutes:Q", bin=alt.Bin(maxbins=20), title="Workout Minutes"),
        y=alt.Y("count():Q", title="Number of Sessions"),
        color=alt.value("#67c1ff"),
        tooltip=["count()", "minutes"]
    ).properties(height=300)

    st.altair_chart(chart4, use_container_width=True)
