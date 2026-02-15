import streamlit as st
import pandas as pd
import sqlite3

conn = sqlite3.connect("lol_analysis.db")

sql_query = "SELECT r.Champion, r.Difficulty, COALESCE(b.Bili_Top5_Views, 0) AS Views FROM riot_stats r LEFT JOIN bili_hot_champs b ON r.champion = b.champion "
df = pd.read_sql(sql_query, conn)

st.title("🏆 LOL Data Dashboard")
st.write("欢迎来到我的数据看板！这里将展示英雄联盟的数据分析结果。")

# 只要像写 Markdown 一样写 Python 字符串，它就会显示在网页上
st.markdown("---") 
st.success("环境配置成功！Ready to go! 🚀")



st.sidebar.header("🔍 筛选器")

min_diff = st.sidebar.slider("选择最低难度 (Minimum Difficulty)", 0, 10, 0)

df_filtered = df[df["Difficulty"] >= min_diff]

df_sorted = df_filtered.sort_values(by = "Views",  ascending=False)

top_hero = df_sorted.iloc[0]

st.header("🏆 谁是流量之王？")

st.metric(
    label="当前难度下最火的英雄",
    value=top_hero["Champion"],
    delta=f"播放量: {int(top_hero['Views']):,}"
)

st.header("📈 难度 vs 播放量分析")

st.write("让我们看看英雄难度和播放量是否有关系：")

st.scatter_chart(data=df_filtered, x="Difficulty", y = "Views")
st.dataframe(df_filtered)

