# 🎮 League of Legends: End-to-End Data Analytics Pipeline

## 🚀 Project Overview
This project is an automated, end-to-end data pipeline that scrapes, processes, and visualizes the trending League of Legends champions on Bilibili. It perfectly integrates **Data Engineering**, **Data Analytics**, and **Data Science (Machine Learning)** into a unified ecosystem.

## 🛠️ The "Triple-Threat" Architecture

### 1. Data Engineering (DE)
* **Automated Web Scraping:** Python-based scrapers extract real-time viewership data from Bilibili and static champion attributes from Riot Games.
* **Data Modeling:** Designed a Star Schema utilizing SQLite, separating dynamic metrics (Fact Table) and static attributes (Dimension Table).
* **CI/CD Pipeline:** Scheduled via **GitHub Actions** (`daily_update.yml`) to automatically run the scraper and update the database daily.

### 2. Data Analytics (DA)
* **Advanced SQL:** Utilized CTEs (Common Table Expressions), Window Functions, and `JOIN`s to dynamically clean duplicate historical records and aggregate the highest viewership data.
* **Interactive Dashboard:** Built a highly interactive web application using **Streamlit** to display the Top 5 trending champions with visually appealing bar charts.
* **Dynamic Mapping:** Implemented professional Python dictionary mapping (`mappings.py`) to translate Chinese data into an English interface on the fly.

### 3. Data Science (DS)
* **Predictive Modeling:** Integrated `scikit-learn` to apply **Linear Regression**.
* **Trend Forecasting:** The model analyzes historical viewership trajectories and predicts the future popularity trends of the top-ranked champion, providing actionable business insights.

## 💻 Tech Stack
* **Language:** Python 3.12
* **Database:** SQLite3, Advanced SQL
* **Data Processing:** Pandas, NumPy
* **Machine Learning:** Scikit-Learn
* **Frontend:** Streamlit
* **Automation:** GitHub Actions

## ⚙️ How to Run Locally
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the dashboard: `streamlit run app.py`