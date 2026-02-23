import sqlite3
import pandas as pd

# 1. 连上你的真实数据库
db_name = 'lol_analysis.db' 
conn = sqlite3.connect(db_name)

print(f"✅ 成功连接到真实数据库: {db_name}")

# 2. 属于你自己的工业级 SQL 魔法！
# 看到了吗？用 b 代表 B站表，用 r 代表 拳头表
sql_query = """
WITH Latest_Bili_Data AS (
    -- 备菜碗 1：清洗 B 站表，只留最高播放量 (1个剑魔)
    SELECT 
        Champion, 
        MAX(Bili_Top5_Views) AS Max_Views
    FROM bili_hot_champs
    GROUP BY Champion
),
Clean_Riot_Stats AS (
    -- 备菜碗 2：清洗 拳头表，用 DISTINCT 去掉所有重复的爬虫记录 (1个剑魔)
    SELECT DISTINCT 
        Champion, 
        Tags, 
        Difficulty
    FROM riot_stats
)

-- 魔法的主查询：用极其干净的 1 对 1 进行连表！
SELECT 
    v.Champion AS '英雄名字',
    r.Tags AS '职业定位',
    r.Difficulty AS '操作难度',
    v.Max_Views AS 'B站总播放量'
FROM Latest_Bili_Data v
INNER JOIN Clean_Riot_Stats r
    ON v.Champion = r.Champion
ORDER BY v.Max_Views DESC
LIMIT 5;
"""

try:
    # 3. 让 Pandas 执行你的 SQL
    real_data_df = pd.read_sql_query(sql_query, conn)
    
    # 4. 打印出炫酷的结果！
    print("\n🔥 你的专属 LOL 项目：B站顶流英雄揭秘 🔥")
    print("=" * 50)
    print(real_data_df.to_string(index=False)) # to_string(index=False) 是为了让表格更清爽
    print("=" * 50)
    
except Exception as e:
    print("❌ 报错啦：", e)

finally:
    conn.close()