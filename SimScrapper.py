
import importlib
import sys
import csv
import subprocess
import time
import re
# Check if Selenium is installed
try:
    importlib.import_module("selenium")
except ImportError:
    print("Selenium is not installed. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "selenium"])

# Check if BeautifulSoup is installed
try:
    importlib.import_module("bs4")
except ImportError:
    print("BeautifulSoup is not installed. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "beautifulsoup4"])

try:
    importlib.import_module("pandas")
except ImportError:
    print("pandas is not installed. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pandas"])

# Now you can import the libraries safely
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
from bs4 import BeautifulSoup

def read_credentials_from_file():
    with open("credentials.txt", "r") as file:
        lines = file.readlines()
        username = lines[0].strip()  # Removing trailing newline
        password = lines[1].strip()  # Removing trailing newline
    return username, password

login_url = 'https://www.simultrain.swiss/smt12/admin/index.php/Login/checkLogin'
#table_url = 'https://www.simultrain.swiss/smt12/admin/index.php/Trainer'

def main():


    browser_number = input("What is the browser used: 1 for chrome , 2 for firefox : -> ")

    if int(browser_number) == 1:
        options = webdriver.ChromeOptions()
          # Run Chrome in headless mode (without GUI)
        options.add_argument('--headless')  # Run Chrome in headless mode (without GUI)
        driver = webdriver.Chrome(options=options)

    elif int(browser_number) == 2:
        options = webdriver.FirefoxOptions()

        driver = webdriver.Firefox(options=options, service=None, keep_alive=False)
    else:
        print("Not a valid number, exiting the program.")
        sys.exit()


    if not driver:
        print("Could not open the browser, exiting the program.")
        sys.exit()

    driver.get(login_url)

    username, password = read_credentials_from_file()

    #wait for the username field to appear
    try:
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
    except TimeoutException:
        print('Login unsuccessful. Unable to find username field, Exiting...')
        sys.exit()

    # Find login elements and input credentials
    username_input = driver.find_element(By.ID, "username")
    username_input.send_keys(username)

    #wait for the password field to appear
    try:
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        print('Login successful. Accessing table...')
    except TimeoutException:
        print('Login unsuccessful. Unable to find password field, Exiting...')
        sys.exit()


    password_input = driver.find_element(By.ID, "password")
    password_input.send_keys(password)


    # Find the button using XPath (by class and text)
    login_button = driver.find_element(By.XPATH, "//button[contains(@class, 'MuiButton-containedPrimary') and contains(text(), 'Log In')]")
    login_button.click()

    print('Logging in...')

    time.sleep(3)

    try:
        def dismiss_backdrop():
            """ Removes the Material-UI backdrop if it exists """
            try:
                backdrop = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "MuiBackdrop-root"))
                )
                driver.execute_script("arguments[0].remove();", backdrop)
                print("Backdrop removed.")
                time.sleep(1)  # Wait before clicking again
            except TimeoutException:
                print("No backdrop found, proceeding.")

        def open_dropdown():
            """ Opens the dropdown menu again if it's closed """
            try:
                dismiss_backdrop()  # Ensure backdrop is gone

                dropdown_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'MuiIconButton-root')]//p[contains(text(), 'Session')]"))
                )
                driver.execute_script("arguments[0].click();", dropdown_button)  # Force click
                print("Dropdown menu opened.")

                # Ensure dropdown remains open
                WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "MuiMenu-paper"))
                )
                time.sleep(1)  # Ensure menu opens fully
            except TimeoutException:
                print("Dropdown menu did not open.")

        open_dropdown()  # Open dropdown for the first time

        def get_sessions():
            """ Retrieves all valid session elements between first and last divider """
            try:
                menu_items = driver.find_elements(By.XPATH, "//li[contains(@class, 'MuiMenuItem-root')] | //hr[contains(@class, 'MuiDivider-root')]")
                session_elements = []
                found_first_divider = False
                found_second_divider = False

                for item in menu_items:
                    if "MuiDivider-root" in item.get_attribute("class"):
                        if not found_first_divider:
                            found_first_divider = True
                            continue
                        elif found_first_divider and not found_second_divider:
                            found_second_divider = True
                            break

                    if found_first_divider and not found_second_divider:
                        session_elements.append(item)

                return session_elements
            except StaleElementReferenceException:
                print("Stale element detected, retrying session collection...")
                return get_sessions()  # Retry fetching sessions
            
        def extract_table_data():
            """ Extracts the table data from the currently opened session """
            try:
                # Locate the table
                table = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'MuiTable-root')]"))
                )

                # Extract column headers
                headers = [th.text.strip() for th in table.find_elements(By.XPATH, ".//thead/tr/th")]
                
                # Extract table rows
                rows = []
                for row in table.find_elements(By.XPATH, ".//tbody/tr"):
                    cells = [td.text.strip() for td in row.find_elements(By.XPATH, ".//td")]
                    rows.append(cells)

                return headers, rows

            except TimeoutException:
                print("Table not found for this session.")
                return [], []

        sessions = get_sessions()
        print(f"Found {len(sessions)} clickable sessions.")

        all_data = []
        extracted_headers = None  # Will store headers after first table extraction

        for i in range(len(sessions)):
            open_dropdown()  # Reopen dropdown before each click
            sessions = get_sessions()  # Refresh session list

            session = sessions[i]
            session_text = session.text.strip()
            print(f"Clicking session: {session_text}")

            try:
                # Ensure session is clickable before clicking
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(session)
                )

                # Use JavaScript for guaranteed click action
                driver.execute_script("arguments[0].click();", session)
                time.sleep(2)  # Allow time for session change

                # Extract table data
                headers, table_data = extract_table_data()

                # Store the headers from the first table only
                if extracted_headers is None and headers:
                    extracted_headers = headers

                # Store data for all sessions
                for row in table_data:
                    all_data.append([session_text] + row)

            except (ElementClickInterceptedException, StaleElementReferenceException):
                print(f"Click issue detected for {session_text}, retrying...")
                driver.execute_script("arguments[0].click();", session)  # JavaScript click fallback


        # Convert to DataFrame and process the data
        if all_data:

            # Add session column and headers
            df_raw = pd.DataFrame(all_data, columns=["Session"] + extracted_headers)

            # Save raw data before any filtering or sorting
            df_raw.to_csv("raw_session_data.csv", index=False)
            print("Raw data saved to raw_session_data.csv")

            # Create a copy to process for the cleaned version
            df = df_raw.copy()            

            # Keep only the required fields
            required_fields = ['Team', 'CPI', 'SPI', 'QPI', 'MOTIV', 'RMI', 'SCORE']
            df = df[[col for col in required_fields if col in df.columns]]

            # Convert 'Team' column to numeric for sorting (extracts numbers)
            df['Team'] = df['Team'].str.extract('(\d+)').astype(float)

            # Sort by Team number
            df = df.sort_values(by='Team', ascending=True)

            # Save to CSV
            df.to_csv("sorted_session_data.csv", index=False)
            print("Data saved to sorted_session_data.csv")

    except Exception as e:
        print(f"Error: {e}")

    driver.quit()

if __name__ == "__main__":
    main()


