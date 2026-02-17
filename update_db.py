import requests
import pandas as pd
import sqlite3
import time
import random
from datetime import datetime  # <--- [变化1] 引入时间库

# 1. 初始化数据库
conn = sqlite3.connect('lol_analysis.db')
print(f"🚀 [Backend] Starting Data Pipeline at {datetime.now()}...")

# ==========================================
# 📦 步骤 A: 获取 Riot 英雄数据 (主表)
# ==========================================
print("\n📥 [1/2] Fetching Riot Champion Data...")
try:
    # 获取最新版本号
    VERSION_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
    latest_version = requests.get(VERSION_URL).json()[0]
    
    # 获取英雄数据
    CHAMP_URL = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/zh_CN/champion.json"
    response = requests.get(CHAMP_URL)
    champ_data = response.json()['data']

    difficulty_list = []
    target_champs = [] 
    
    # 获取今天的日期字符串，例如 "2024-02-18"
    today_str = datetime.now().strftime("%Y-%m-%d")

    for en_name, data in champ_data.items():
        difficulty_list.append({
            "Champion": data['name'],
            "Difficulty": data['info']['difficulty'],
            "Tags": ",".join(data['tags']),
            "source": "riot",
            "scrape_date": today_str # <--- [变化2] 给数据打上时间戳
        })
        target_champs.append({"name": data['name']})

    # 存入 riot_stats 表
    df_riot = pd.DataFrame(difficulty_list)
    
    # <--- [变化3] 关键修改：改成 'append' (追加模式)
    df_riot.to_sql('riot_stats', conn, if_exists='append', index=False)
    print(f"✅ Riot Data Appended! Total Champions: {len(df_riot)}")

except Exception as e:
    print(f"❌ Riot Error: {e}")

# ==========================================
# 📺 步骤 B: 获取 Bilibili 播放数据 (副表)
# ==========================================
print("\n🕵️‍♂️ [2/2] Fetching Bilibili View Counts...")

# 这里的逻辑和之前一样，暂时跑前10个做测试
demo_champs = target_champs[:10] 

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
        params = {
            "keyword": f"LOL {search_keyword}", 
            "search_type": "video", 
            "order": "click"
        }
        
        resp = requests.get(url, headers=headers, params=params, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            total_views = 0
            if data['code'] == 0 and 'result' in data['data']:
                video_list = data['data']['result']
                for v in video_list[:5]:
                    views = v.get('play') if 'play' in v else v.get('stat', {}).get('view', 0)
                    total_views += int(views)
            
            bili_stats.append({
                "Champion": champ['name'],
                "Bili_Top5_Views": total_views,
                "scrape_date": today_str # <--- [变化4] B站数据也要打时间戳
            })
            
    except Exception as e:
        print(f"\n   ⚠️ Error fetching {search_keyword}: {e}")

# 存入 bili_hot_champs 表
if bili_stats:
    df_bili = pd.DataFrame(bili_stats)
    # <--- [变化5] 关键修改：改成 'append'
    df_bili.to_sql('bili_hot_champs', conn, if_exists='append', index=False)
    print(f"\n✅ Bilibili Data Appended! Processed {len(df_bili)} champions.")
else:
    print("\n⚠️ No Bilibili data fetched.")

conn.close()
print("🎉 All Done! History preserved.")