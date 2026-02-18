import pandas as pd
import sqlite3
import random
from datetime import datetime, timedelta

# 1. Connect to Database
conn = sqlite3.connect('lol_analysis.db')
print("🕵️‍♂️ Start: Backfilling historical data...")

# 2. Get today's data as a seed
try:
    # Fetch the latest available data to use as a template
    df_riot_today = pd.read_sql("SELECT * FROM riot_stats WHERE scrape_date = (SELECT MAX(scrape_date) FROM riot_stats)", conn)
    df_bili_today = pd.read_sql("SELECT * FROM bili_hot_champs WHERE scrape_date = (SELECT MAX(scrape_date) FROM bili_hot_champs)", conn)
    
    if df_riot_today.empty or df_bili_today.empty:
        print("❌ Error: Database is empty! Please run 'python update_db.py' first to generate seed data.")
        conn.close()
        exit()

    print(f"✅ Seed data loaded: {len(df_riot_today)} records")

except Exception as e:
    print(f"❌ Database connection error: {e}")
    exit()

# 3. Define configuration (Backfill for past 5 days)
days_to_fake = 5
dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, days_to_fake + 1)]

# 4. Generate Synthetic Data
for date in dates:
    print(f"   ✍️ Generating data for: {date} ...")
    
    # --- A. Backfill Riot Data (Static data, just changing dates) ---
    df_fake_riot = df_riot_today.copy()
    df_fake_riot['scrape_date'] = date
    df_fake_riot.to_sql('riot_stats', conn, if_exists='append', index=False)
    
    # --- B. Backfill Bilibili Data (Add random variance for realism) ---
    df_fake_bili = df_bili_today.copy()
    df_fake_bili['scrape_date'] = date
    
    # Apply random fluctuation between 85% and 115%
    df_fake_bili['Bili_Top5_Views'] = df_fake_bili['Bili_Top5_Views'].apply(lambda x: int(x * random.uniform(0.85, 1.15)))
    
    df_fake_bili.to_sql('bili_hot_champs', conn, if_exists='append', index=False)

print("🎉 Backfill completed! Historical data generated successfully.")
conn.close()