<img width="2559" height="1398" alt="image" src="https://github.com/user-attachments/assets/295bd641-9369-449a-93a6-d8b9ed4beefb" />

# 🎮 League of Legends: End-to-End Data Analytics Pipeline

**Live dashboard:** https://lol-insights-boston.streamlit.app/ *(hosted on a free cloud tier, first load may take 30-60 seconds)*

## 🚀 Project Overview
This project is an automated, end-to-end data pipeline that scrapes, processes, and visualizes the trending League of Legends champions on Bilibili. It integrates **Data Engineering**, **Data Analytics**, and **Data Science (Machine Learning)** into a unified ecosystem.

## 🛠️ The "Triple-Threat" Architecture

### 1. Data Engineering (DE)
* **Automated Ingestion:** Python scrapers pull daily champion attributes from the Riot Games Data Dragon API and viewership metrics from the Bilibili search API.
* **Cloud Data Warehouse:** A Star Schema on **Snowflake** separates dynamic metrics (fact table) from champion attributes (dimension table). The project started on local SQLite and was later migrated to Snowflake for a storage-compute separated architecture (`migrate_to_cloud.py`).
* **CI/CD Automation:** **GitHub Actions** (`daily_update.yml`) runs the pipeline daily with credentials injected from GitHub Secrets. Success and failure notifications are pushed to **Discord** via webhook. A second workflow (`keep_alive.yml`) pings the dashboard to prevent free-tier hibernation.

### 2. Data Analytics (DA)
* **Advanced SQL:** CTEs deduplicate the daily-snapshot tables, and a `DENSE_RANK` window function ranks champions so ties are kept instead of being arbitrarily dropped.
* **Interactive Dashboard:** A **Streamlit** app reads directly from Snowflake via `st.connection` and displays the Top 5 trending champions.

### 3. Data Science (DS)
* **Predictive Modeling:** Integrated `scikit-learn` to apply **Linear Regression**.
* **Trend Forecasting:** The model analyzes historical viewership trajectories and predicts the future popularity trend of the top-ranked champion, plotted against actual values on the dashboard.

## 💻 Tech Stack
* **Language:** Python 3.12
* **Data Warehouse:** Snowflake (migrated from SQLite)
* **Data Processing:** Pandas, NumPy
* **Machine Learning:** Scikit-Learn
* **Frontend:** Streamlit
* **Automation:** GitHub Actions, Discord Webhooks

## ⚙️ How to Run Locally
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Add your Snowflake credentials to `.streamlit/secrets.toml` *(see the Streamlit `st.connection` docs)*.
4. Run the dashboard: `streamlit run app.py`
