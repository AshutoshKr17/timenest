from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta 

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


import os
import time


# Configuration
EMAIL = str(os.getenv('EMAIL_TEST', ''))
PASSWORD = str(os.getenv('PASS_TEST', ''))


# Configuration
CALENDLY_LOGIN_URL = "https://calendly.com/login"
DATA_DELETION_URL = "https://calendly.com/app/admin/security/data_deletion"

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
    chrome_options.add_argument("--headless=new")  # Run without a GUI
    chrome_options.add_argument("--no-sandbox")    # Required for GitHub
    chrome_options.add_argument("--disable-dev-shm-usage")  # Prevents crashes
    chrome_options.add_argument("--window-size=1920,1080")  # Sets window size

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    wait = WebDriverWait(driver, 20)  # Increased timeout
    try:
        driver.get(CALENDLY_LOGIN_URL)
        
        # Wait for page to fully load
        time.sleep(2)
        
        # Enter email
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "[data-testid='email-input'] input")
        )).send_keys(EMAIL)
        
        # Click continue button
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.button-primary")
        )).click()

        # Wait for password page transition with longer timeout
        time.sleep(3)
        
        # Try multiple selectors for password field
        password_field = None
        selectors = [
            "input[type='password']",
            "input[placeholder*='password']",
            "input[name='password']",
            "[data-testid='password-input'] input",
            "input[autocomplete='current-password']"
        ]
        
        for selector in selectors:
            try:
                password_field = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, selector)
                ))
                logging.info(f"Found password field with selector: {selector}")
                break
            except:
                continue
        
        if not password_field:
            raise Exception("Could not locate password field with any selector")
            
        # Wait for field to be interactable
        wait.until(EC.element_to_be_clickable(password_field))
        password_field.clear()
        password_field.send_keys(PASSWORD)
        
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[type='submit']")
        )).click()

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
