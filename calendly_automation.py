from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
import time
import subprocess
import re
import logging
import os
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Configuration
CALENDLY_LOGIN_URL = "https://calendly.com/login"
DATA_DELETION_URL = "https://calendly.com/app/admin/security/data_deletion"

# Configuration
EMAIL = os.getenv('EMAIL_TEST')  or "akushwaha@digitalocean.com"
PASSWORD = os.getenv('PASS_TEST')  or "Ashutosh@170902"

def calculate_dates():
    today = datetime.now()
    logging.info("Calculating date range for cleanup")
    
    first_of_this_month = today.replace(day=1)
    last_month_end = first_of_this_month - timedelta(days=1)
    first_of_last_month = last_month_end.replace(day=1)
    month_before_last_end = first_of_last_month - timedelta(days=1)
    month_before_last_start = month_before_last_end.replace(day=1)
    
    logging.info(
        "Selected date range: %s to %s", 
        month_before_last_start.strftime("%Y-%m-%d"),
        month_before_last_end.strftime("%Y-%m-%d")
    )
    return month_before_last_start, month_before_last_end
    
def select_date_in_calendar(driver, wait, date_to_select):
    """
    Helper function to select a specific date in the Calendly calendar.
    """
    month_year_str = date_to_select.strftime("%B %Y")
    day_str = date_to_select.strftime("%-d")
    
    logging.debug("Attempting to select date: %s %s", month_year_str, day_str)
    
    date_locator = (
        f"//table[@aria-label='{month_year_str}']"
        f"//div[@role='button' and text()='{day_str}' and not(@data-outside-month)]"
    )
    
    try:
        logging.info("Selecting date: %s", date_to_select.strftime("%Y-%m-%d"))
        date_element = wait.until(EC.element_to_be_clickable((By.XPATH, date_locator)))
        date_element.click()
        logging.debug("Successfully clicked date element")
    except Exception as e:
        logging.error(
            "Failed to select date %s. Locator used: %s",
            date_to_select.strftime("%Y-%m-%d"),
            date_locator,
            exc_info=True
        )
        raise e

def automate_calendly_cleanup():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    chrome_service = Service(executable_path='/usr/bin/google-chrome')
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    wait = WebDriverWait(driver, 5)
    
    try:
        # Login
        driver.get(CALENDLY_LOGIN_URL)
        email_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='email-input'] input")))
        email_input.send_keys(EMAIL)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.button-primary"))).click()

        password_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password'][placeholder='password']")))
        password_field.send_keys(PASSWORD)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()

        wait.until(EC.url_contains("event_types"))

        
        driver.get(DATA_DELETION_URL)
        wait.until(EC.url_contains("/admin/security/data_deletion"))

        try:
            logging.info("Starting date selection process")
            start_date, end_date = calculate_dates()
            
            logging.debug("Clicking date range input")
            date_range_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='data_requests_date_range']")))
            date_range_input.click()
            time.sleep(1)

            current_month_header = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".c14v74yl h2"))).text
            logging.info("Current calendar display: %s", current_month_header)
            
            current_calendar_date = datetime.strptime(current_month_header, "%B %Y")
            months_diff = (current_calendar_date.year - start_date.year) * 12 + current_calendar_date.month - start_date.month

            if months_diff > 0:
                logging.info("Navigating back %s months", months_diff)
                prev_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Go to previous month']")))
                for i in range(months_diff):
                    prev_btn.click()
                    time.sleep(0.3)
                    logging.debug("Month navigation click %s/%s", i+1, months_diff)

            logging.info("Selecting start date")
            select_date_in_calendar(driver, wait, start_date)
            logging.info("Selecting end date")
            select_date_in_calendar(driver, wait, end_date)

            logging.debug("Clicking apply button")
            apply_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Apply']]")))
            apply_button.click()
            time.sleep(1)
            
            logging.info("Successfully applied date range: %s to %s",
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d"))

        except Exception as e:
            logging.error("Date selection failed: %s", str(e), exc_info=True)
            raise

        try:
            logging.warning("Initiating data deletion for range %s-%s", 
                          start_date.strftime("%Y-%m-%d"), 
                          end_date.strftime("%Y-%m-%d"))
            
            delete_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@class, 'uvkj3lh') and contains(@class, 'l15h8fme') and contains(@class, 'bzua8jl') and contains(@class, 'dulxlhf') and not(contains(@class, 's19wokei'))]")
            ))
            delete_button.click()
            logging.debug("Clicked primary delete button")
            
            logging.info("Confirming deletion")
            confirm_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@class, 'uvkj3lh') and contains(@class, 'l15h8fme') and contains(@class, 'bzua8jl') and contains(@class, 'dulxlhf')]//span[contains(text(),'Yes')]")
            ))
            confirm_button.click()
            
            logging.info("Successfully deleted data from %s to %s", 
                          start_date.strftime("%Y-%m-%d"), 
                          end_date.strftime("%Y-%m-%d"))
            time.sleep(20)
            
        except Exception as e:
            logging.error("Data deletion failed at confirmation step: %s", str(e), exc_info=True)
            raise
        
    except Exception as e:
        logging.error("Workflow failed: %s", str(e), exc_info=True)
    finally:
        logging.info("Browser session ended")
        driver.quit()

if __name__ == "__main__":
    automate_calendly_cleanup()
