from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configuration
OM_USER = "fakeemail@gmail.com"  # Replace with your email
OM_PASS = 'your_password'          # Replace with your password


def delete_all_leads():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=chrome_options
    )
    wait = WebDriverWait(driver, 5)
    try:
        # Login
        driver.get("https://app.optinmonster.com/login")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "login"))).send_keys(OM_USER)
        driver.find_element(By.ID, "password").send_keys(OM_PASS)
        login_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'input.button-blue[type="submit"][value="Log In"]'))
        )
        login_btn.click()

        # Navigate to Leads
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.LINK_TEXT, "Leads"))).click()
        
        # Select Monster Leads™ from dropdown
        monster_leads_option = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//li[contains(@class, "monster-leads")]/a[@href="/leads/"]')
            )
        )
        monster_leads_option.click()
        # Handle pagination and deletion
        while True:
            # Delete all leads on current page
            delete_buttons = driver.find_elements(By.CSS_SELECTOR, 'i.fa-trash')
            if not delete_buttons:
                print("No leads found on this page")
                break
                
            for _ in range(len(delete_buttons)):
                try:
                    # Delete lead
                    driver.find_element(By.CSS_SELECTOR, 'i.fa-trash').click()
                    
                    # Confirm deletion
                    WebDriverWait(driver, 1).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, '//button[contains(., "Yes, I\'m Sure")]')
                        )
                    ).click()
                    
                    # Wait for deletion to complete
                    WebDriverWait(driver, 1).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, 'i.fa-trash'))
                    )
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error deleting lead: {str(e)}")
                    break

            # # Check for next page
            # try:
            #     next_button = WebDriverWait(driver, 10).until(
            #         EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.button-icon i.fa-chevron-right'))
            #     )
            #     next_button.click()
            #     time.sleep(3)  # Wait for page load
            # except:
            #     print("No more pages")
            #     break

    finally:
        driver.quit()

if __name__ == "__main__":
    delete_all_leads()