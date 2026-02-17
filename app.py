import streamlit as st
import pandas as pd
import sqlite3

# 连接数据库
conn = sqlite3.connect("lol_analysis.db")

# SQL 查询升级：只获取最新日期的快照
sql_query = """
SELECT 
    r.Champion, 
    r.Difficulty, 
    COALESCE(b.Bili_Top5_Views, 0) AS Views,
    r.scrape_date
FROM riot_stats r
LEFT JOIN bili_hot_champs b 
    ON r.Champion = b.Champion 
    AND r.scrape_date = b.scrape_date 
WHERE r.scrape_date = (SELECT MAX(scrape_date) FROM riot_stats)
"""

df = pd.read_sql(sql_query, conn)

# 页面布局
st.title("🏆 LOL Data Dashboard")
# 这一行就是之前报错的地方，现在它是独立的了
st.caption(f"📅 数据最后更新于: {df['scrape_date'].iloc[0] if not df.empty else 'N/A'}")

# 侧边栏筛选
st.sidebar.header("🔍 筛选器")
min_diff = st.sidebar.slider("选择最低难度 (Minimum Difficulty)", 0, 10, 0)

# 数据筛选与排序
df_filtered = df[df["Difficulty"] >= min_diff]
df_sorted = df_filtered.sort_values(by="Views", ascending=False)

# 核心指标 (KPI)
st.header("🏆 谁是流量之王？")
if not df_sorted.empty:
    top_hero = df_sorted.iloc[0]
    st.metric(
        label="当前难度下最火的英雄",
        value=top_hero["Champion"],
        delta=f"播放量: {int(top_hero['Views']):,}"
    )
else:
    st.warning("暂无数据")

# 图表分析
st.header("📈 难度 vs 播放量分析")
st.write("让我们看看英雄难度和播放量是否有关系：")

st.scatter_chart(data=df_filtered, x="Difficulty", y="Views", color="Difficulty")

# 数据明细
with st.expander("查看详细数据表"):
    st.dataframe(df_filtered)