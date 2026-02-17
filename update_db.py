import requests
import pandas as pd
import sqlite3
import time
import random
import os  # <--- [新] 用于读取环境变量
from datetime import datetime

# ==========================================
# 🔔 新增功能：发送 Discord 通知
# ==========================================
def send_discord_notification(message):
    webhook_url = os.environ.get("DISCORD_WEBHOOK") # 从环境变量获取秘密
    
    if not webhook_url:
        print("⚠️ No Discord Webhook found. Skipping notification.")
        return

    data = {
        "content": message,
        "username": "LoL Data Bot"
    }
    
    try:
        response = requests.post(webhook_url, json=data)
        if response.status_code == 204:
            print("✅ Discord notification sent!")
        else:
            print(f"❌ Failed to send Discord notification: {response.status_code}")
    except Exception as e:
        print(f"❌ Error sending notification: {e}")

# ==========================================
# 🚀 主程序开始
# ==========================================

# 1. 初始化数据库
conn = sqlite3.connect('lol_analysis.db')
print(f"🚀 [Backend] Starting Data Pipeline at {datetime.now()}...")

try: # <--- [新] 加上大大的 try...except 包裹整个流程，为了捕获错误
    
    # --- Part A: Riot Data ---
    print("\n📥 [1/2] Fetching Riot Champion Data...")
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
    print(f"✅ Riot Data Appended! Count: {len(df_riot)}")

    # --- Part B: Bilibili Data ---
    print("\n🕵️‍♂️ [2/2] Fetching Bilibili View Counts...")
    demo_champs = target_champs[:10] # 依然只跑前10个测试
    bili_stats = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Cookie": "buvid3=infoc;" 
    }

    for i, champ in enumerate(demo_champs):
        search_keyword = champ['name']
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
        except Exception:
            pass 

    if bili_stats:
        df_bili = pd.DataFrame(bili_stats)
        df_bili.to_sql('bili_hot_champs', conn, if_exists='append', index=False)
        print(f"\n✅ Bilibili Data Appended! Processed {len(df_bili)} champions.")
    
    conn.close()
    
    # ✅ 如果走到这里没报错，发送成功消息
    success_msg = f"🎉 **Daily Update Success!**\nDate: {today_str}\nRiot Champs: {len(df_riot)}\nBilibili Data: {len(bili_stats)}"
    send_discord_notification(success_msg)
    print("🎉 All Done!")

except Exception as e:
    # ❌ 如果中间任何地方报错，发送失败消息
    error_msg = f"🚨 **Daily Update FAILED!**\nError: {str(e)}"
    send_discord_notification(error_msg)
    print(f"❌ Critical Error: {e}")
    raise e # 让 GitHub Action 依然显示红色失败