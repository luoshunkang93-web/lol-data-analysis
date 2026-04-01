# app.py
import streamlit as st
import pandas as pd
import snowflake.connector
import numpy as np
from sklearn.linear_model import LinearRegression
from mappings import CHAMPION_DICT

# ====================================================================
# 🚀 Phase 1: Dashboard UI Setup
# ====================================================================
st.title("🔥 League of Legends: Cloud-Native Insights")
st.markdown("Powered by **Snowflake Cloud Data Warehouse** and Advanced SQL Data Modeling.")

# ====================================================================
# 🚀 Phase 2: Cloud Database Connection & Data Extraction
# ====================================================================
# Use Streamlit's caching mechanism to optimize cloud compute costs
@st.cache_resource
def init_snowflake_connection():
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"]
    )

try:
    conn = init_snowflake_connection()
    
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
    )
    SELECT 
        v."Champion" AS "Champion_Name",
        r."Tags" AS "Role_Tags",
        r."Difficulty" AS "Difficulty_Level",
        v.Max_Views AS "Bilibili_Total_Views"
    FROM Latest_Bili_Data v
    INNER JOIN Clean_Riot_Stats r
        ON v."Champion" = r."Champion"
    ORDER BY v.Max_Views DESC
    LIMIT 5;
    """
    
    top5_df = pd.read_sql_query(sql_query, conn)

    # Dictionary Mapping for English Translation
    top5_df['Champion_Name'] = top5_df['Champion_Name'].map(CHAMPION_DICT).fillna(top5_df['Champion_Name'])

    col1, col2 = st.columns(2) 

    with col1:
        st.subheader("🏆 Top 5 Champions Data")
        st.dataframe(top5_df, use_container_width=True) 

    with col2:
        st.subheader("📊 Total Views Bar Chart")
        chart_data = top5_df.set_index('Champion_Name')['Bilibili_Total_Views']
        st.bar_chart(chart_data) 

except Exception as e:
    st.error(f"❌ Failed to connect or fetch data from Snowflake: {e}")

# ====================================================================
# 🚀 Phase 3: Data Science (Machine Learning Prediction)
# ====================================================================
st.divider() 
st.subheader("🤖 Future Trend Prediction (Machine Learning)")
st.markdown("Utilizing a **Linear Regression** model to forecast the top champion's future views based on historical data.")

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
    top_champ_raw_name = pd.read_sql_query(top_champ_query, conn).iloc[0]['Champion']

    # Extract historical timeline for this specific champion
    history_query = f"""
    SELECT "scrape_date", "Bili_Top5_Views" 
    FROM BILI_HOT_CHAMPS 
    WHERE "Champion" = '{top_champ_raw_name}'
    ORDER BY "scrape_date" ASC
    """
    history_df = pd.read_sql_query(history_query, conn)

    top_champ_display_name = CHAMPION_DICT.get(top_champ_raw_name, top_champ_raw_name)

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
            'Predicted_Views': [np.nan] * len(history_df) + y_future_pred.tolist()
        })
        
        plot_data.loc[last_index, 'Predicted_Views'] = plot_data.loc[last_index, 'Actual_Views']

        st.write(f"📈 Predictive Growth Trajectory for **{top_champ_display_name}**")
        st.line_chart(plot_data)
    else:
        st.warning(f"⚠️ Not enough historical data for {top_champ_display_name} to run the ML model.")

except Exception as e:
    st.error(f"❌ ML Model encountered an error: {e}")