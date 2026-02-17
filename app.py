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

# ==========================================
# 📈 新增功能：趋势分析 (Trend Analysis)
# ==========================================
st.markdown("---")
st.header("📈 英雄热度趋势 (Time Series)")
st.write("查看某个英雄在过去几天的热度变化：")

# 1. 既然要选英雄，我们得先有个下拉框
# 获取所有英雄的名字，去重
unique_champs = df["Champion"].unique()
selected_champ = st.selectbox("选择一个英雄 (Select Champion):", unique_champs)

# 2. 如果用户选了英雄，我们就去数据库查它的“族谱”（历史记录）
if selected_champ:
    # SQL 解释：查这个英雄，并且按时间顺序排好
    sql_trend = f"""
    SELECT 
        r.scrape_date,
        COALESCE(b.Bili_Top5_Views, 0) AS Views
    FROM riot_stats r
    LEFT JOIN bili_hot_champs b 
        ON r.Champion = b.Champion 
        AND r.scrape_date = b.scrape_date 
    WHERE r.Champion = '{selected_champ}'
    ORDER BY r.scrape_date ASC
    """
    
    try:
        df_trend = pd.read_sql(sql_trend, conn)
        
        # 3. 只有数据超过 1 条，画图才有意义
        if not df_trend.empty:
            # 画折线图！x轴是日期，y轴是播放量
            st.line_chart(df_trend, x="scrape_date", y="Views")
            
            # 算个“涨跌幅”装得更专业一点
            if len(df_trend) >= 2:
                newest_views = df_trend.iloc[-1]['Views']
                oldest_views = df_trend.iloc[0]['Views']
                if oldest_views > 0:
                    growth = ((newest_views - oldest_views) / oldest_views) * 100
                    color = "normal"
                    if growth > 0: color = "normal" # Streamlit metric 自动标绿
                    st.metric(label="近期热度增长率", value=f"{growth:.1f}%")
        else:
            st.warning("暂无该英雄的历史数据。")
            
    except Exception as e:
        st.error(f"查询出错: {e}")