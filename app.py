import streamlit as st
import pandas as pd
import sqlite3
from mappings import CHAMPION_DICT

# 1. Set up the dashboard title and description
st.title("🔥 League of Legends: Bilibili Trending Insights")
st.markdown("Powered by real web-scraped data and advanced SQL data modeling.")

# 2. Connect to the database and execute the advanced SQL query
conn = sqlite3.connect('lol_analysis.db')
sql_query = """
WITH Latest_Bili_Data AS (
    -- CTE 1: Clean Bilibili facts table
    SELECT Champion, MAX(Bili_Top5_Views) AS Max_Views
    FROM bili_hot_champs
    GROUP BY Champion
),
Clean_Riot_Stats AS (
    -- CTE 2: Clean Riot dimension table
    SELECT DISTINCT Champion, Tags, Difficulty
    FROM riot_stats
)
SELECT 
    v.Champion AS 'Champion_Name',
    r.Tags AS 'Role_Tags',
    r.Difficulty AS 'Difficulty_Level',
    v.Max_Views AS 'Bilibili_Total_Views'
FROM Latest_Bili_Data v
INNER JOIN Clean_Riot_Stats r
    ON v.Champion = r.Champion
ORDER BY v.Max_Views DESC
LIMIT 5;
"""

# 3. Fetch the cleaned DataFrame
top5_df = pd.read_sql_query(sql_query, conn)
conn.close()

top5_df['Champion_Name'] = top5_df['Champion_Name'].map(CHAMPION_DICT).fillna(top5_df['Champion_Name'])

# 4. Core DA Task: Data Visualization!
# Split the layout into two columns for better UI
col1, col2 = st.columns(2) 

with col1:
    st.subheader("🏆 Top 5 Champions Data")
    # Display the raw cleaned data
    st.dataframe(top5_df, use_container_width=True) 

with col2:
    st.subheader("📊 Total Views Bar Chart")
    # Prepare data for the bar chart by setting the index to Champion_Name (X-axis)
    chart_data = top5_df.set_index('Champion_Name')['Bilibili_Total_Views']
    # Render the bar chart in one line of code!
    st.bar_chart(chart_data)

# ====================================================================
# 🚀 Phase 3: Data Science (Machine Learning Prediction)
# ====================================================================
import numpy as np
from sklearn.linear_model import LinearRegression

st.divider() 
st.subheader("🤖 Future Trend Prediction (Machine Learning)")
st.markdown("Utilizing a **Linear Regression** model to forecast the top champion's future views based on historical scraped data.")

# 1. Re-establish database connection to fetch historical data
conn = sqlite3.connect('lol_analysis.db')

# Identify the #1 champion based on all-time highest views
top_champ_query = """
SELECT Champion 
FROM bili_hot_champs 
GROUP BY Champion 
ORDER BY MAX(Bili_Top5_Views) DESC 
LIMIT 1
"""
# Fetch the Chinese name for database querying
top_champ_raw_name = pd.read_sql_query(top_champ_query, conn).iloc[0]['Champion']

# 2. Extract historical timeline for this specific champion
history_query = f"""
SELECT scrape_date, Bili_Top5_Views 
FROM bili_hot_champs 
WHERE Champion = '{top_champ_raw_name}'
ORDER BY scrape_date ASC
"""
history_df = pd.read_sql_query(history_query, conn)
conn.close()

# Map the champion name to English for UI presentation
top_champ_display_name = CHAMPION_DICT.get(top_champ_raw_name, top_champ_raw_name)

# 3. Proceed with Machine Learning ONLY if we have enough historical data points
if len(history_df) > 1:
    # Prepare features (X) and target (y) for the model
    # X-axis: Time sequence (0, 1, 2, 3...)
    history_df['Time_Index'] = range(len(history_df))
    X_train = history_df[['Time_Index']]
    y_train = history_df['Bili_Top5_Views']

    # Initialize and train the Linear Regression model
    model = LinearRegression()
    model.fit(X_train, y_train)

    # 4. Forecast the trend for the next 3 intervals
    future_steps = 3
    last_index = len(history_df) - 1
    X_future = pd.DataFrame({'Time_Index': range(last_index + 1, last_index + 1 + future_steps)})
    y_future_pred = model.predict(X_future)

    # 5. Construct a consolidated DataFrame for visualization
    plot_data = pd.DataFrame({
        'Actual_Views': y_train.tolist() + [np.nan] * future_steps,
        'Predicted_Views': [np.nan] * len(history_df) + y_future_pred.tolist()
    })
    
    # Bridge the gap: connect the last actual point to the first predicted point
    plot_data.loc[last_index, 'Predicted_Views'] = plot_data.loc[last_index, 'Actual_Views']

    # 6. Render the predictive line chart
    st.write(f"📈 Predictive Growth Trajectory for **{top_champ_display_name}**")
    st.line_chart(plot_data)

else:
    st.warning(f"⚠️ Not enough historical data for {top_champ_display_name} to run the ML model. Keep the scraper running for a few more days!")