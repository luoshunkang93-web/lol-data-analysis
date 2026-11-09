# app.py
import streamlit as st
import pandas as pd
from sklearn.linear_model import LinearRegression

st.set_page_config(layout="wide")

# ====================================================================
# 🚀 Phase 1: Dashboard UI Setup
# ====================================================================
st.title("League of Legends Champion Popularity Dashboard")
st.markdown("Daily Bilibili video views for a 10-champion demo set, stored in **Snowflake** and queried with SQL. Views are used as a rough proxy for player interest.")

# ====================================================================
# 🚀 Phase 2: Cloud Database Connection & Data Extraction
# ====================================================================
# st.connection auto-handles token refresh and reconnection on expiry
conn = st.connection("snowflake")

try:
    # Each tracked champion's most recent snapshot. Early rows (Feb 2026) used Chinese
    # champion names and are excluded so the dashboard shows the current daily data.
    # Note: Double quotes are used for column names to handle case-sensitivity from Pandas export
    sql_query = """
    WITH Latest_Bili_Data AS (
        SELECT "Champion", "scrape_date" AS Snapshot_Date, "Bili_Top5_Views" AS Views
        FROM BILI_HOT_CHAMPS
        WHERE REGEXP_LIKE("Champion", '.*[A-Za-z].*')
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY "Champion" ORDER BY "scrape_date" DESC, "Bili_Top5_Views" DESC
        ) = 1
    ),
    Clean_Riot_Stats AS (
        SELECT "Champion", "Tags", "Difficulty"
        FROM RIOT_STATS
        QUALIFY ROW_NUMBER() OVER (PARTITION BY "Champion" ORDER BY "scrape_date" DESC) = 1
    ),
    Ranked_Champions AS (
        SELECT
            v."Champion" AS "Champion_Name",
            r."Tags" AS "Role_Tags",
            r."Difficulty" AS "Difficulty_Level",
            v.Views AS "Bilibili_Views",
            v.Snapshot_Date AS "Snapshot_Date",
            DENSE_RANK() OVER (ORDER BY v.Views DESC) AS view_rank
        FROM Latest_Bili_Data v
        INNER JOIN Clean_Riot_Stats r
            ON v."Champion" = r."Champion"
    )
    SELECT "Champion_Name", "Role_Tags", "Difficulty_Level", "Bilibili_Views", "Snapshot_Date"
    FROM Ranked_Champions
    WHERE view_rank <= 5
    ORDER BY view_rank;
    """

    top5_df = conn.query(sql_query, ttl=600)
    top_champ_raw_name = top5_df.iloc[0]['Champion_Name'] if len(top5_df) else None

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 5 Tracked Champions by Bilibili Views")
        st.dataframe(top5_df, use_container_width=True)
        if len(top5_df):
            st.caption(f"Each champion's most recent snapshot; latest data: {top5_df['Snapshot_Date'].max()}")

    with col2:
        st.subheader("Bilibili Views (sum of top 5 search results)")
        chart_data = top5_df.set_index('Champion_Name')['Bilibili_Views']
        st.bar_chart(chart_data)

except Exception as e:
    st.error(f"❌ Failed to connect or fetch data from Snowflake: {e}")

# ====================================================================
# 🚀 Phase 3: Simple Linear Trend Line
# ====================================================================
st.divider()
st.subheader("Trend Line for the Top Champion")
st.markdown("A straight line fitted with linear regression to the top champion's recorded daily views, extended 3 days past the latest snapshot. It shows the overall direction only and is not a forecasting model.")

try:
    if not top_champ_raw_name:
        raise ValueError("no current data for the top 5 table")

    # Parametrized query prevents SQL injection from champion name; one value per day
    history_query = """
    SELECT "scrape_date", MAX("Bili_Top5_Views") AS "Bili_Top5_Views"
    FROM BILI_HOT_CHAMPS
    WHERE "Champion" = ?
    GROUP BY "scrape_date"
    ORDER BY "scrape_date" ASC
    """
    history_df = conn.query(history_query, ttl=600, params=[top_champ_raw_name])

    top_champ_display_name = top_champ_raw_name

    if len(history_df) > 1:
        history_df['Date'] = pd.to_datetime(history_df['scrape_date'])
        first_day = history_df['Date'].min()
        history_df['Day'] = (history_df['Date'] - first_day).dt.days
        X_train = history_df[['Day']]
        y_train = history_df['Bili_Top5_Views']

        model = LinearRegression()
        model.fit(X_train, y_train)

        # Trend values on each recorded day, plus 3 days past the last snapshot
        last_day = int(history_df['Day'].max())
        future_df = pd.DataFrame({'Day': [last_day + i for i in range(1, 4)]})
        future_df['Date'] = first_day + pd.to_timedelta(future_df['Day'], unit='D')
        line_df = pd.concat([history_df[['Day', 'Date']], future_df], ignore_index=True)
        line_df['Trend_Line'] = model.predict(line_df[['Day']])

        plot_data = line_df.set_index('Date')[['Trend_Line']].join(
            history_df.set_index('Date')[['Bili_Top5_Views']].rename(columns={'Bili_Top5_Views': 'Actual_Views'})
        )

        st.write(f"Recorded views and linear trend for **{top_champ_display_name}**")
        st.line_chart(plot_data[['Actual_Views', 'Trend_Line']], use_container_width=True)
    else:
        st.warning(f"⚠️ Not enough historical data for {top_champ_display_name} to draw a trend line.")

except Exception as e:
    st.error(f"❌ Trend line could not be drawn: {e}")
