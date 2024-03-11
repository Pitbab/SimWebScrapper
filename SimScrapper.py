
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

# Now you can import the libraries safely
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

def read_credentials_from_file():
    with open("credentials.txt", "r") as file:
        lines = file.readlines()
        username = lines[0].strip()  # Removing trailing newline
        password = lines[1].strip()  # Removing trailing newline
    return username, password


fields = ['team','CPI', 'SPI', 'QPI', 'Motiv', 'RMI', 'Score']
data_row = []
needed_fields = [5, 6, 7, 8, 9, 10]

login_url = 'https://www.simultrain.swiss/smt12/admin/index.php/Login/checkLogin'
table_url = 'https://www.simultrain.swiss/smt12/admin/index.php/Trainer'

def main():


    browser_number = input("What is the browser used: 1 for chrome , 2 for firefox : -> ")

    if int(browser_number) == 1:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run Chrome in headless mode (without GUI)
        driver = webdriver.Chrome(options=options)

    elif int(browser_number) == 2:
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')  # Run Firefox in headless mode (without GUI)
        driver = webdriver.Firefox(options=options, service=None, keep_alive=False)
    else:
        print("Not a valid number, exiting the program.")
        sys.exit()


    if not driver:
        print("Could not open the browser, exiting the program.")
        sys.exit()

    driver.get(login_url)

    # Find login elements and input credentials
    username_input = driver.find_element(By.NAME, "username")
    password_input = driver.find_element(By.NAME, "password")
    login_button = driver.find_element(By.NAME, "submit")


    username, password = read_credentials_from_file()

    username_input.send_keys(username)
    password_input.send_keys(password)
    login_button.click()

    print('Logging in...')

    # Wait for either successful login or error message
    try:
        # Check for a successful login by waiting for the table to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "table"))
        )
        print('Login successful. Accessing table...')
    except TimeoutException:
        print('Login unsuccessful. Exiting...')
        sys.exit()

    driver.get(table_url)
    time.sleep(3)

    #find sessions id dropdown 
    dropdown_menu = driver.find_element(By.ID, "session_list")


    #get all the sub buttons after the dropdown header
    session_name = dropdown_menu.find_elements(By.XPATH, "//li[@class='dropdown-header']/following-sibling::li")
    session_ids = []
    for name in session_name:
        button = name.find_element(By.TAG_NAME, "a")
        on_click_value = button.get_attribute("onclick")
        session_ids.append(on_click_value)


    print('Copying tables... (more teams = more time to copy the data)')

    initialContent = ""

    for session_id in session_ids:

        driver.execute_script(session_id)
        
        while True:
            try:
                lookedContent = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#table tbody tr:first-child td:first-child"))).text

                if lookedContent != initialContent:
                    break
            except:
                pass

        initialContent = lookedContent

        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')


        table = soup.find('table', {'id': 'table'})

        rows = table.find_all('tr')



        for row in rows:
            columns = row.find_all('td')
            temp = []
            for index, column in enumerate(columns):
                if index == 1:
                    team_number = int(''.join(filter(str.isdigit, column.get_text())))
                    temp.append(team_number)

                if index in needed_fields:
                    temp.append(column.get_text())

            if temp:
                data_row.append(temp)

    sorted_rows = sorted(data_row, key=lambda x: x[0])

    driver.quit()
    print('Creating csv file... (the file sould be in the same folder as this program)')

    # write the csv
    with open('data.csv', 'w', encoding="utf-8") as f:
        write = csv.writer(f)
        write.writerow(fields)
        write.writerows(sorted_rows)

if __name__ == "__main__":
    main()


