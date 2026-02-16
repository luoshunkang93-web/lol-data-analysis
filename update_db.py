import requests
import pandas as pd
import sqlite3
import time
import random

# 1. 初始化数据库
conn = sqlite3.connect('lol_analysis.db')
print("🚀 [Backend] Starting Data Pipeline...")

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
    
    for en_name, data in champ_data.items():
        # 这里有一步很重要：提取我们需要的数据
        difficulty_list.append({
            "Champion": data['name'],
            "Difficulty": data['info']['difficulty'],
            "Tags": ",".join(data['tags'])
        })
        # 准备给 B 站爬虫用的名单
        target_champs.append({"name": data['name']})

    # 存入 riot_stats 表
    df_riot = pd.DataFrame(difficulty_list)
    df_riot.to_sql('riot_stats', conn, if_exists='replace', index=False)
    print(f"✅ Riot Data Updated! Total Champions: {len(df_riot)}")

except Exception as e:
    print(f"❌ Riot Error: {e}")

# ==========================================
# 📺 步骤 B: 获取 Bilibili 播放数据 (副表)
# ==========================================
print("\n🕵️‍♂️ [2/2] Fetching Bilibili View Counts...")

# ⚠️ 关键修改：我们要跑全量数据了！
# 为了防止被封 IP，我们还是先只跑前 10 个测试一下自动化流程
# 等以后确定没问题了，再把 [:10] 去掉
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
        # 随机休眠 0.5~1.5 秒，模拟人类行为
        time.sleep(random.uniform(0.5, 1.5))
        
        url = "https://api.bilibili.com/x/web-interface/search/type"
        params = {
            "keyword": f"LOL {search_keyword}", 
            "search_type": "video", 
            "order": "click" # 按点击量排序
        }
        
        resp = requests.get(url, headers=headers, params=params, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            total_views = 0
            # 只取前 5 个视频的播放量总和
            if data['code'] == 0 and 'result' in data['data']:
                video_list = data['data']['result']
                for v in video_list[:5]:
                    # B站API有时候返回 'play' 有时候返回 'view'
                    views = v.get('play') if 'play' in v else v.get('stat', {}).get('view', 0)
                    total_views += int(views)
            
            bili_stats.append({
                "Champion": champ['name'],
                "Bili_Top5_Views": total_views
            })
            
    except Exception as e:
        print(f"\n   ⚠️ Error fetching {search_keyword}: {e}")

# 存入 bili_hot_champs 表
df_bili = pd.DataFrame(bili_stats)
# 注意：这里用 'replace' 会覆盖旧数据，这正是我们想要的“更新”
df_bili.to_sql('bili_hot_champs', conn, if_exists='replace', index=False)

print(f"\n✅ Bilibili Data Updated! Processed {len(df_bili)} champions.")

conn.close()
print("🎉 All Done! Database is fresh.")