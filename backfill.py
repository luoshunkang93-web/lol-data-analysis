import pandas as pd
import sqlite3
import random
from datetime import datetime, timedelta

# 1. 连接数据库
conn = sqlite3.connect('lol_analysis.db')
print("🕵️‍♂️ 启动：正在伪造历史数据 (Backfilling Operation)...")

# 2. 获取今天的日期作为基准
# 我们需要先看看数据库里有没有数据。如果没有，这个脚本会报错。
# 假设你刚刚已经运行过 update_db.py 了
try:
    df_riot_today = pd.read_sql("SELECT * FROM riot_stats WHERE scrape_date = (SELECT MAX(scrape_date) FROM riot_stats)", conn)
    df_bili_today = pd.read_sql("SELECT * FROM bili_hot_champs WHERE scrape_date = (SELECT MAX(scrape_date) FROM bili_hot_champs)", conn)
    
    if df_riot_today.empty or df_bili_today.empty:
        print("❌ 错误：数据库是空的！请先运行 'python update_db.py' 抓取一次今天的数据作为种子。")
        conn.close()
        exit()

    print(f"✅以此为种子数据: {len(df_riot_today)} 条记录")

except Exception as e:
    print(f"❌ 读取数据库失败: {e}")
    exit()

# 3. 定义我们要伪造多少天（比如过去 5 天）
days_to_fake = 5
# 生成一个日期列表，例如: ['2026-02-16', '2026-02-15', ...]
dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, days_to_fake + 1)]

# 4. 开始循环造假
for date in dates:
    print(f"   ✍️ 正在伪造日期: {date} ...")
    
    # --- A. 伪造 Riot 数据 (比较简单，难度一般不变，只改日期) ---
    df_fake_riot = df_riot_today.copy()
    df_fake_riot['scrape_date'] = date
    # 存入数据库
    df_fake_riot.to_sql('riot_stats', conn, if_exists='append', index=False)
    
    # --- B. 伪造 B站 数据 (关键！要有随机波动才真实) ---
    df_fake_bili = df_bili_today.copy()
    df_fake_bili['scrape_date'] = date
    
    # 魔法函数：让播放量在 85% 到 115% 之间随机波动
    # 比如今天的播放量是 100万，昨天的可能就是 95万
    df_fake_bili['Bili_Top5_Views'] = df_fake_bili['Bili_Top5_Views'].apply(lambda x: int(x * random.uniform(0.85, 1.15)))
    
    # 存入数据库
    df_fake_bili.to_sql('bili_hot_champs', conn, if_exists='append', index=False)

print("🎉 任务完成！你现在拥有了 5 天的“历史数据”。")
conn.close()