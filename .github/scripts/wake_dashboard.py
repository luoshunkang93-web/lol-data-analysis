import logging
import sys
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ==========================================
# ⚙️ Configuration
# ==========================================
APP_URL = "https://lol-insights-boston.streamlit.app/"
WAKE_BUTTON = (By.XPATH, "//button[contains(., 'get this app back up')]")
STAY_SECONDS = 45

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ==========================================
# 🌐 Visit the dashboard like a real user
# ==========================================
# A plain curl only fetches the Streamlit Cloud wrapper page and does not count
# as app traffic. A real browser session does, which resets the 12-hour idle
# timer. If the app is already asleep, click the wake-up button first.
def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(APP_URL)
        try:
            button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(WAKE_BUTTON))
            logger.info("😴 Dashboard is asleep. Clicking the wake-up button...")
            button.click()
            WebDriverWait(driver, 120).until(EC.invisibility_of_element_located(WAKE_BUTTON))
            logger.info("✅ Wake-up accepted.")
        except TimeoutException:
            if driver.find_elements(*WAKE_BUTTON):
                logger.error("❌ Wake-up button is still showing.")
                sys.exit(1)
            logger.info("✅ Dashboard is awake.")

        # Stay on the page so the app session connects and registers as a visit.
        time.sleep(STAY_SECONDS)
        logger.info("👋 Visit finished.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
