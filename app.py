# app.py
import streamlit as st
import pandas as pd
import numpy as np
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
    # Note: Double quotes are used for column names to handle case-sensitivity from Pandas export
    sql_query = """
        WITH Latest_Bili_Data AS (
        SELECT "Champion", MAX("Bili_Top5_Views") AS Max_Views
        FROM BILI_HOT_CHAMPS
        GROUP BY "Champion"
    ),
    Clean_Riot_Stats AS (
        SELECT DISTINCT "Champion", "Tags", "Difficulty"
        FROM RIOT_STATS
    ),
    Ranked_Champions AS (
        SELECT
            v."Champion" AS "Champion_Name",
            r."Tags" AS "Role_Tags",
            r."Difficulty" AS "Difficulty_Level",
            v.Max_Views AS "Bilibili_Total_Views",
            DENSE_RANK() OVER(ORDER BY v.Max_Views DESC) AS view_rank
        FROM Latest_Bili_Data v
        INNER JOIN Clean_Riot_Stats r
            ON v."Champion" = r."Champion"
    )
    SELECT "Champion_Name", "Role_Tags", "Difficulty_Level", "Bilibili_Total_Views"
    FROM Ranked_Champions
    WHERE view_rank <= 5;
    """

    top5_df = conn.query(sql_query, ttl=600)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 5 Tracked Champions by Bilibili Views")
        st.dataframe(top5_df, use_container_width=True)

    with col2:
        st.subheader("Bilibili Views (sum of top 5 search results)")
        chart_data = top5_df.set_index('Champion_Name')['Bilibili_Total_Views']
        st.bar_chart(chart_data)

except Exception as e:
    st.error(f"❌ Failed to connect or fetch data from Snowflake: {e}")

# ====================================================================
# 🚀 Phase 3: Simple Linear Trend Line
# ====================================================================
st.divider()
st.subheader("Trend Line for the Top Champion")
st.markdown("A straight line fitted with linear regression to the top champion's recorded views, extended 3 data points ahead. It shows the overall direction only and is not a forecasting model.")

try:
    # Identify the #1 champion based on all-time highest views
    top_champ_query = """
    SELECT "Champion"
    FROM BILI_HOT_CHAMPS
    GROUP BY "Champion"
    HAVING COUNT("scrape_date") > 1
    ORDER BY MAX("Bili_Top5_Views") DESC
    LIMIT 1
    """
    top_champ_raw_name = conn.query(top_champ_query, ttl=600).iloc[0]['Champion']

    # Parametrized query prevents SQL injection from champion name
    history_query = """
    SELECT "scrape_date", "Bili_Top5_Views"
    FROM BILI_HOT_CHAMPS
    WHERE "Champion" = ?
    ORDER BY "scrape_date" ASC
    """
    history_df = conn.query(history_query, ttl=600, params=[top_champ_raw_name])

    top_champ_display_name = top_champ_raw_name

    if len(history_df) > 1:
        history_df['Time_Index'] = range(len(history_df))
        X_train = history_df[['Time_Index']]
        y_train = history_df['Bili_Top5_Views']

        model = LinearRegression()
        model.fit(X_train, y_train)

        future_steps = 3
        last_index = len(history_df) - 1
        X_future = pd.DataFrame({'Time_Index': range(last_index + 1, last_index + 1 + future_steps)})
        y_future_pred = model.predict(X_future)

        plot_data = pd.DataFrame({
            'Actual_Views': y_train.tolist() + [np.nan] * future_steps,
            'Trend_Line': [np.nan] * len(history_df) + y_future_pred.tolist()
        })

        plot_data.loc[last_index, 'Trend_Line'] = plot_data.loc[last_index, 'Actual_Views']

        st.write(f"Recorded views and linear trend for **{top_champ_display_name}**")
        st.line_chart(plot_data, use_container_width=True)
    else:
        st.warning(f"⚠️ Not enough historical data for {top_champ_display_name} to draw a trend line.")

except Exception as e:
    st.error(f"❌ Trend line could not be drawn: {e}")
