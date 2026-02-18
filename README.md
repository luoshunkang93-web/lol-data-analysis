# 🏆 LoL Champion Data Pipeline & Analytics

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://luo-lol-dashboard.streamlit.app)
![Python](https://img.shields.io/badge/Python-3.9-blue)
![Status](https://img.shields.io/badge/Pipeline-Automated-green)

An automated End-to-End Data Engineering project that analyzes the correlation between **League of Legends** champion difficulty (Riot API) and their popularity on Bilibili (Video Views).

## 🚀 Live Demo
👉 **[Click here to view the Interactive Dashboard](https://luo-lol-dashboard.streamlit.app)**

---

## 🏗️ Architecture

This project implements a complete ETL pipeline:

1.  **Extraction (Extract)**: 
    - Scrapes champion metadata from official **Riot Games API**.
    - Scrapes video view counts from **Bilibili API**.
2.  **Transformation (Transform)**:
    - Cleans and merges data using **Pandas**.
    - Adds timestamps and source tags.
3.  **Loading (Load)**:
    - Stores structured data into a **SQLite** database (`lol_analysis.db`).
4.  **Automation & Monitoring**:
    - **GitHub Actions**: Runs the pipeline automatically every day at 00:00 UTC.
    - **Discord Webhook**: Sends real-time success/failure alerts to my device.
5.  **Visualization**:
    - Built with **Streamlit** to visualize Correlation (Scatter Plot) and Trend (Time Series).

---

## 🛠️ Tech Stack

* **Language**: Python 3.9
* **Data Processing**: Pandas, Requests
* **Database**: SQLite
* **Frontend**: Streamlit (Cloud Deployed)
* **DevOps**: GitHub Actions (CI/CD), Discord Webhook (Alerting)
* **Logs**: Python Logging Module (Production-grade observability)

---

## 📂 Project Structure

```text
├── .github/workflows  # CI/CD Configuration
├── app.py             # Frontend Dashboard (Streamlit)
├── update_db.py       # Backend ETL Script (The Crawler)
├── backfill.py        # Utility script for generating mock history
├── requirements.txt   # Python Dependencies
└── README.md          # Project Documentation