import streamlit as st
import pandas as pd
import sqlite3

# ==========================================
# 1. Database Connection & Data Loading
# ==========================================
def load_data():
    conn = sqlite3.connect('lol_analysis.db')
    
    # Query: Join Riot data (difficulty) with Bilibili data (views)
    # We use the latest scrape date to show the current snapshot
    query = """
    SELECT 
        r.Champion, 
        r.Difficulty, 
        r.Tags, 
        b.Bili_Top5_Views as Views,
        r.scrape_date
    FROM riot_stats r
    JOIN bili_hot_champs b ON r.Champion = b.Champion AND r.scrape_date = b.scrape_date
    WHERE r.scrape_date = (SELECT MAX(scrape_date) FROM riot_stats)
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Load data
try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# ==========================================
# 2. Sidebar Configuration (Filters)
# ==========================================
st.sidebar.header("🔍 Filters")
min_diff = st.sidebar.slider("Minimum Difficulty Level", 0, 10, 0)

# Filter the dataframe based on user input
filtered_df = df[df['Difficulty'] >= min_diff]

# ==========================================
# 3. Main Dashboard UI
# ==========================================
st.title("🏆 LoL Champion Data Dashboard")
st.markdown(f"**Data Last Updated:** {df['scrape_date'].iloc[0]}")

# --- Section 1: The "Traffic King" ---
st.header("👑 The Traffic King")
st.write("The most popular champion matching your criteria:")

if not filtered_df.empty:
    # Find the champion with max views
    top_champ = filtered_df.loc[filtered_df['Views'].idxmax()]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Champion Name", value=top_champ['Champion'])
    with col2:
        st.metric(label="Total Views (Top 5 Videos)", value=f"{top_champ['Views']:,}")
else:
    st.warning("No champions found matching the criteria.")

# --- Section 2: Scatter Plot Analysis ---
st.markdown("---")
st.header("📊 Correlation: Difficulty vs. Popularity")
st.write("Does a harder champion lead to more views? Let's find out.")

if not filtered_df.empty:
    st.scatter_chart(
        filtered_df,
        x="Difficulty",
        y="Views",
        color="Difficulty", 
        size="Views" 
    )

# --- Section 3: Raw Data Table ---
with st.expander("📂 View Detailed Dataset"):
    st.dataframe(filtered_df)

# ==========================================
# 4. Trend Analysis (Time Series)
# ==========================================
st.markdown("---")
st.header("📈 Trend Analysis (Time Series)")
st.write("Track the popularity trend of a specific champion over the last few days.")

# Connect to DB again for historical query
conn = sqlite3.connect('lol_analysis.db')
unique_champs = df["Champion"].unique()
selected_champ = st.selectbox("Select a Champion to Analyze:", unique_champs)

if selected_champ:
    # Query historical data for the selected champion
    sql_trend = f"""
    SELECT 
        r.scrape_date,
        COALESCE(b.Bili_Top5_Views, 0) AS Views
    FROM riot_stats r
    LEFT JOIN bili_hot_champs b 
        ON r.Champion = b.Champion 
        AND r.scrape_date = b.scrape_date 
    WHERE r.Champion = '{selected_champ}'
    ORDER BY r.scrape_date ASC
    """
    
    try:
        df_trend = pd.read_sql(sql_trend, conn)
        
        if not df_trend.empty:
            # Render Line Chart
            st.line_chart(df_trend, x="scrape_date", y="Views")
            
            # Calculate Growth Rate
            if len(df_trend) >= 2:
                newest_views = df_trend.iloc[-1]['Views']
                oldest_views = df_trend.iloc[0]['Views']
                if oldest_views > 0:
                    growth = ((newest_views - oldest_views) / oldest_views) * 100
                    st.metric(label="Recent Growth Rate", value=f"{growth:.1f}%")
        else:
            st.warning("No historical data available for this champion.")
            
    except Exception as e:
        st.error(f"Query Error: {e}")
    finally:
        conn.close()