import sqlite3
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import getpass

print("🚀 Starting Cloud Migration Process...")

# ==========================================
# STEP 1: EXTRACT (Read from local SQLite)
# ==========================================
print("\n📦 Extracting data from local SQLite database...")
sqlite_conn = sqlite3.connect('lol_analysis.db')

# Extract the Fact Table
df_bili = pd.read_sql_query("SELECT * FROM bili_hot_champs", sqlite_conn)
# Extract the Dimension Table
df_riot = pd.read_sql_query("SELECT * FROM riot_stats", sqlite_conn)

sqlite_conn.close()
print(f"✅ Extracted {len(df_bili)} rows from Bilibili table.")
print(f"✅ Extracted {len(df_riot)} rows from Riot table.")

# ==========================================
# STEP 2: CONNECT (Authenticate to Snowflake)
# ==========================================
print("\n🔑 Connecting to Snowflake Cloud...")
user_password = getpass.getpass("Enter your Snowflake password: ")

try:
    sf_conn = snowflake.connector.connect(
        user='kksnow',             # <-- Replace with your Snowflake username
        password=user_password,           
        account='JKNNMCM-ORC24346',       # <-- Your unique account identifier
        warehouse='LOL_WH',
        database='LOL_CLOUD_DB',
        schema='PUBLIC'
    )
    print("✅ Connected to Snowflake successfully!")

    # ==========================================
    # STEP 3: LOAD (Write DataFrames to Cloud)
    # ==========================================
    print("\n☁️ Uploading data to Snowflake... Please wait.")
    
    # Upload Fact Table (auto_create_table=True will create the table automatically in Snowflake)
    success_bili, nchunks_bili, nrows_bili, _ = write_pandas(
        sf_conn, 
        df_bili, 
        'BILI_HOT_CHAMPS', 
        auto_create_table=True
    )
    
    # Upload Dimension Table
    success_riot, nchunks_riot, nrows_riot, _ = write_pandas(
        sf_conn, 
        df_riot, 
        'RIOT_STATS', 
        auto_create_table=True
    )

    if success_bili and success_riot:
        print("\n🎉 MIGRATION COMPLETE!")
        print(f"⬆️ Successfully loaded {nrows_bili} rows into BILI_HOT_CHAMPS.")
        print(f"⬆️ Successfully loaded {nrows_riot} rows into RIOT_STATS.")

except Exception as e:
    print("\n❌ AN ERROR OCCURRED DURING MIGRATION:")
    print(e)

finally:
    if 'sf_conn' in locals() and sf_conn:
        sf_conn.close()
        print("\n🔒 Snowflake connection closed safely.")