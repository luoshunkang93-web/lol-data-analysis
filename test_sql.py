import sqlite3
import pandas as pd

# 1. Connect to the local SQLite database
db_name = 'lol_analysis.db' 
conn = sqlite3.connect(db_name)

print(f"✅ Successfully connected to the database: {db_name}")

# 2. Define the advanced SQL query with double CTEs for data deduplication
sql_query = """
WITH Latest_Bili_Data AS (
    -- CTE 1: Clean Bilibili facts table, keeping only the max views per champion
    SELECT 
        Champion, 
        MAX(Bili_Top5_Views) AS Max_Views
    FROM bili_hot_champs
    GROUP BY Champion
),
Clean_Riot_Stats AS (
    -- CTE 2: Clean Riot dimension table, removing duplicated scraped records
    SELECT DISTINCT 
        Champion, 
        Tags, 
        Difficulty
    FROM riot_stats
)

-- Main Query: Join the cleaned tables to generate the final top 5 ranking
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

try:
    # 3. Execute the SQL query using Pandas
    real_data_df = pd.read_sql_query(sql_query, conn)
    
    # 4. Display the formatted results
    print("\n🔥 Bilibili LOL Trending Champions: Top 5 🔥")
    print("=" * 60)
    print(real_data_df.to_string(index=False))
    print("=" * 60)
    
except Exception as e:
    # Catch and print any execution errors gracefully
    print("❌ An error occurred during execution:")
    print(e)

finally:
    # 5. Ensure the database connection is closed safely
    conn.close()
    print("\n🔒 Database connection closed safely.")