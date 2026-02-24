import requests
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import time
import random
import os
import logging
from datetime import datetime

# ==========================================
# ⚙️ Logging Configuration
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ==========================================
# 🔔 Discord Notification Helper
# ==========================================
def send_discord_notification(message):
    webhook_url = os.environ.get("DISCORD_WEBHOOK")
    
    if not webhook_url:
        logger.warning("⚠️ No Discord Webhook found. Skipping notification.")
        return

    data = {
        "content": message,
        "username": "LoL Cloud Data Bot"
    }
    
    try:
        response = requests.post(webhook_url, json=data)
        if response.status_code == 204:
            logger.info("✅ Discord notification sent successfully!")
        else:
            logger.error(f"❌ Failed to send Discord notification. HTTP Status: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error sending Discord notification: {e}")

# ==========================================
# 🚀 Main Cloud Execution Flow
# ==========================================
logger.info("🚀 [Cloud Backend] Starting Automated Data Pipeline...") 

try:
    # --- STEP 1: Fetch External API Data ---
    logger.info("📥 [1/3] Fetching Riot Games Champion Data...")
    
    VERSION_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
    latest_version = requests.get(VERSION_URL).json()[0]
    
    CHAMP_URL = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/champion.json"
    champ_data = requests.get(CHAMP_URL).json()['data']

    difficulty_list = []
    target_champs = [] 
    today_str = datetime.now().strftime("%Y-%m-%d")

    for en_name, data in champ_data.items():
        difficulty_list.append({
            "Champion": data['name'],
            "Difficulty": data['info']['difficulty'],
            "Tags": ",".join(data['tags']),
            "source": "riot",
            "scrape_date": today_str
        })
        target_champs.append({"name": data['name']})

    df_riot = pd.DataFrame(difficulty_list)
    logger.info(f"✅ Riot Data Extracted. Total Champions: {len(df_riot)}")

    logger.info("🕵️‍♂️ [2/3] Fetching Bilibili Viewership Metrics...")
    
    demo_champs = target_champs[:10] # Limitation for demo purposes
    bili_stats = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Cookie": "buvid3=infoc;" 
    }

    for i, champ in enumerate(demo_champs):
        search_keyword = champ['name']
        logger.info(f"   Scraping {i+1}/{len(demo_champs)}: {search_keyword}...")
        
        try:
            time.sleep(random.uniform(0.5, 1.5))
            url = "https://api.bilibili.com/x/web-interface/search/type"
            params = {"keyword": f"LOL {search_keyword}", "search_type": "video", "order": "click"}
            resp = requests.get(url, headers=headers, params=params, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                total_views = 0
                if data['code'] == 0 and 'result' in data['data']:
                    video_list = data['data']['result']
                    for v in video_list[:5]:
                        views = v.get('play') or v.get('stat', {}).get('view') or 0
                        total_views += int(views)
                
                bili_stats.append({
                    "Champion": champ['name'],
                    "Bili_Top5_Views": total_views,
                    "scrape_date": today_str
                })
        except Exception as e:
            logger.warning(f"⚠️ Error fetching metrics for {search_keyword}: {e}") 

    df_bili = pd.DataFrame(bili_stats)
    logger.info(f"✅ Bilibili Data Extracted. Processed {len(df_bili)} records.")

    # --- STEP 2: Authenticate to Snowflake ---
    logger.info("🔑 [3/3] Connecting to Snowflake Cloud Data Warehouse...")
    
    sf_user = os.environ.get("SNOWFLAKE_USER")
    sf_password = os.environ.get("SNOWFLAKE_PASSWORD")
    sf_account = os.environ.get("SNOWFLAKE_ACCOUNT")

    if not all([sf_user, sf_password, sf_account]):
        raise ValueError("Critical Security Error: Missing Snowflake credentials in environment variables.")

    sf_conn = snowflake.connector.connect(
        user=sf_user,
        password=sf_password,
        account=sf_account,
        warehouse='LOL_WH',
        database='LOL_CLOUD_DB',
        schema='PUBLIC'
    )
    logger.info("✅ Successfully connected to Snowflake.")

    # --- STEP 3: Load Data into Snowflake ---
    logger.info("☁️ Uploading DataFrames to Snowflake...")
    
    # Write Riot Dimension Table
    success_riot, nchunks_riot, nrows_riot, _ = write_pandas(
        sf_conn, df_riot, 'RIOT_STATS', auto_create_table=True
    )
    
    # Write Bilibili Fact Table
    success_bili, nchunks_bili, nrows_bili, _ = write_pandas(
        sf_conn, df_bili, 'BILI_HOT_CHAMPS', auto_create_table=True
    )

    sf_conn.close()
    
    # Send Success Notification
    success_msg = f"🎉 **Cloud Data Pipeline Success!**\nDate: {today_str}\nLoaded {nrows_riot} rows to RIOT_STATS.\nLoaded {nrows_bili} rows to BILI_HOT_CHAMPS."
    send_discord_notification(success_msg)
    logger.info("🎉 Pipeline execution completed successfully. Connection closed.")

except Exception as e:
    # Send Failure Notification
    error_msg = f"🚨 **Cloud Pipeline FAILED!**\nError details: {str(e)}"
    send_discord_notification(error_msg)
    logger.error("❌ Critical Pipeline Error Encountered", exc_info=True) 
    raise e