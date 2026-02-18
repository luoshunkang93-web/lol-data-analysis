import requests
import pandas as pd
import sqlite3
import time
import random
import os
import logging
from datetime import datetime

# ==========================================
# ⚙️ Logging Configuration
# ==========================================
# Configure logging format: Time - Level - Message
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# Initialize Logger
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
        "username": "LoL Data Bot"
    }
    
    try:
        response = requests.post(webhook_url, json=data)
        if response.status_code == 204:
            logger.info("✅ Discord notification sent!")
        else:
            logger.error(f"❌ Failed to send Discord notification: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error sending notification: {e}")

# ==========================================
# 🚀 Main Execution Flow
# ==========================================

logger.info("🚀 [Backend] Starting Data Pipeline...") 

# Initialize Database Connection
conn = sqlite3.connect('lol_analysis.db')

try:
    # --- Part A: Riot Data Pipeline ---
    logger.info("📥 [1/2] Fetching Riot Champion Data...")
    
    VERSION_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
    latest_version = requests.get(VERSION_URL).json()[0]
    
    CHAMP_URL = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/zh_CN/champion.json"
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
    df_riot.to_sql('riot_stats', conn, if_exists='append', index=False)
    logger.info(f"✅ Riot Data Appended! Count: {len(df_riot)}")

    # --- Part B: Bilibili Data Pipeline ---
    logger.info("🕵️‍♂️ [2/2] Fetching Bilibili View Counts...")
    
    demo_champs = target_champs[:10] # For demo purposes, limit to 10
    bili_stats = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Cookie": "buvid3=infoc;" 
    }

    for i, champ in enumerate(demo_champs):
        search_keyword = champ['name']
        # Logging progress (optional, using print for simple progress bar effect)
        print(f"   Searching {i+1}/{len(demo_champs)}: {search_keyword}...", end="\r")
        
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
            logger.warning(f"⚠️ Error fetching {search_keyword}: {e}") 

    if bili_stats:
        df_bili = pd.DataFrame(bili_stats)
        df_bili.to_sql('bili_hot_champs', conn, if_exists='append', index=False)
        logger.info(f"✅ Bilibili Data Appended! Processed {len(df_bili)} champions.")
    
    conn.close()
    
    # Send Success Notification
    success_msg = f"🎉 **Daily Update Success!**\nDate: {today_str}\nRiot Champs: {len(df_riot)}\nBilibili Data: {len(bili_stats)}"
    send_discord_notification(success_msg)
    logger.info("🎉 All Done! Pipeline finished successfully.")

except Exception as e:
    # Send Failure Notification
    error_msg = f"🚨 **Daily Update FAILED!**\nError: {str(e)}"
    send_discord_notification(error_msg)
    logger.error("❌ Critical Pipeline Error", exc_info=True) 
    raise e