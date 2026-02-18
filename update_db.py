import requests
import pandas as pd
import sqlite3
import time
import random
import os
import logging  # <--- [新] 引入日志库
from datetime import datetime

# ==========================================
# ⚙️ 配置日志 (Logging Setup) - 核心部分！
# ==========================================
# 1. 设置日志格式：时间 - 级别 - 消息
# 2. level=logging.INFO 意味着：只要是 INFO 及以上的消息都记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__) # 获取一个记录器

# ==========================================
# 🔔 Discord 通知函数 (保持不变)
# ==========================================
def send_discord_notification(message):
    webhook_url = os.environ.get("DISCORD_WEBHOOK")
    
    if not webhook_url:
        logger.warning("⚠️ No Discord Webhook found. Skipping notification.") # [修改] print -> logger.warning
        return

    data = {
        "content": message,
        "username": "LoL Data Bot"
    }
    
    try:
        response = requests.post(webhook_url, json=data)
        if response.status_code == 204:
            logger.info("✅ Discord notification sent!") # [修改] print -> logger.info
        else:
            logger.error(f"❌ Failed to send Discord notification: {response.status_code}") # [修改] print -> logger.error
    except Exception as e:
        logger.error(f"❌ Error sending notification: {e}")

# ==========================================
# 🚀 主程序
# ==========================================

# 1. 初始化
# 这里的 logs 会自动带上时间戳，不用你自己写 datetime.now() 了
logger.info("🚀 [Backend] Starting Data Pipeline...") 

conn = sqlite3.connect('lol_analysis.db')

try:
    # --- Part A: Riot Data ---
    logger.info("📥 [1/2] Fetching Riot Champion Data...") # [修改]
    
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
    logger.info(f"✅ Riot Data Appended! Count: {len(df_riot)}") # [修改]

    # --- Part B: Bilibili Data ---
    logger.info("🕵️‍♂️ [2/2] Fetching Bilibili View Counts...") # [修改]
    
    demo_champs = target_champs[:10]
    bili_stats = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Cookie": "buvid3=infoc;" 
    }

    for i, champ in enumerate(demo_champs):
        search_keyword = champ['name']
        # 注意：这里我们只打印 DEBUG 级别的信息，或者为了简洁，可以不打印进度条，或者每10个打印一次
        # 为了演示，我们先保留 print (logging 也可以混用，但最好统一)
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
            # 这里的 exc_info=True 是专业细节！它会把具体的报错行号也打印出来
            logger.warning(f"⚠️ Error fetching {search_keyword}: {e}", exc_info=False) 

    if bili_stats:
        df_bili = pd.DataFrame(bili_stats)
        df_bili.to_sql('bili_hot_champs', conn, if_exists='append', index=False)
        logger.info(f"✅ Bilibili Data Appended! Processed {len(df_bili)} champions.") # [修改]
    
    conn.close()
    
    success_msg = f"🎉 **Daily Update Success!**\nDate: {today_str}\nRiot Champs: {len(df_riot)}\nBilibili Data: {len(bili_stats)}"
    send_discord_notification(success_msg)
    logger.info("🎉 All Done! Pipeline finished successfully.") # [修改]

except Exception as e:
    error_msg = f"🚨 **Daily Update FAILED!**\nError: {str(e)}"
    send_discord_notification(error_msg)
    # exc_info=True 会打印出非常详细的错误堆栈，方便你找 Bug
    logger.error("❌ Critical Pipeline Error", exc_info=True) 
    raise e