# League of Legends Champion Popularity Tracker

**Live dashboard:** https://lol-insights-boston.streamlit.app/ *(hosted on a free cloud tier, first load may take 30-60 seconds)*

## Overview
A small personal project that tracks how much attention League of Legends champions get on Bilibili, a Chinese video platform. A scheduled Python job collects data every day, stores it in Snowflake, and a Streamlit dashboard shows the results. Bilibili video views are used as a rough proxy for player interest.

## How It Works

### 1. Daily data collection
* Pulls role tags and difficulty for every champion (about 170) from Riot's Data Dragon API.
* Searches Bilibili for a 10-champion demo set and records the sum of views of the top 5 search results for each champion.
* Runs once a day as a scheduled **GitHub Actions** job (`daily_update.yml`). Snowflake credentials are kept in GitHub Secrets, and a **Discord** webhook message reports each run's success (with row counts) or failure.
* The job extracts and loads raw data. Cleaning and joining happen in the dashboard's SQL.

### 2. Storage
* Started on local SQLite and was migrated to **Snowflake** (`migrate_to_cloud.py`).
* Two tables in a simple star schema: a champion attribute table (dimension) and a daily Bilibili views table (fact).

### 3. SQL and dashboard
* Three CTEs pick each champion's most recent snapshot (`QUALIFY ROW_NUMBER()`), take the latest attributes, and join them. A `DENSE_RANK` window function ranks champions by views so ties are kept.
* A parameterized query pulls the top champion's history, one value per day.
* The **Streamlit** app reads from Snowflake via `st.connection` and shows the top 5 tracked champions as a table and a bar chart.
* A straight-line trend (scikit-learn linear regression on days since the first snapshot) is drawn for the top champion and extended 3 days past the latest snapshot. It shows direction only; it is not a forecasting model.
* A second workflow (`keep_alive.yml`) opens the dashboard in a headless browser every 4 hours so the free tier does not put it to sleep.

## Known Limitations
* **Demo scope:** Bilibili views cover only 10 champions, the first 10 alphabetically (Aatrox to Aphelios), so "top 5" means the top 5 of those 10.
* **Synthetic cold-start data:** `backfill.py` generated 5 days of history (Feb 12-16, 2026) with random noise so the trend chart had something to show at launch. Those rows are still in the table but use Chinese names, so the dashboard no longer shows them (see below).
* **Gaps:** No data for March 2026 and most of April 2026 (account move and re-migration), and none from Sep 7 to 23, 2026 (GitHub paused the scheduled workflow after 60 days without repository activity). The job has run daily since May 2026 apart from that September gap.
* **Failed requests:** About half of the daily Bilibili requests fail, and failed requests are not logged yet. A row-count check is the planned fix.
* **Early Chinese-name rows:** Data from Feb 2026 stored champion names in Chinese, and Chinese-name searches return far higher view counts. Until Nov 2026 the dashboard ranked champions by all-time highest views, so it kept showing those February rows. It now uses each champion's most recent English-name snapshot only. The old rows remain in the tables.
* **AI assistance:** Most of the code was drafted with generative AI coding assistants (Gemini, later Claude for maintenance). I designed the steps, checked the outputs and can explain each part.

## Tech Stack
* **Language:** Python 3.12 (Pandas, NumPy, scikit-learn, requests)
* **Database:** Snowflake (migrated from SQLite)
* **Dashboard:** Streamlit
* **Automation:** GitHub Actions, Discord webhooks

## How to Run Locally
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Add your Snowflake credentials to `.streamlit/secrets.toml` *(see the Streamlit `st.connection` docs)*.
4. Run the dashboard: `streamlit run app.py`
