import random
import threading
import math
import os
from dotenv import load_dotenv
from flask import Flask, request, render_template
from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import NoSuchElementException
import json

# Load environment variables from .env file
load_dotenv()

count = 106
ml = False
tf = False
val = 1
chrome_options = FirefoxOptions()
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--disable-infobars")
# chrome_options.add_argument("--headless")
# chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--start-maximized")
radio_options = "EcW08c"

# Load configuration from environment variables
app = Flask(__name__, template_folder=os.getenv('TEMPLATE_FOLDER', './templates'))
form_link = os.getenv('FORM_LINK', 'https://docs.google.com/forms/....')
driver_path = os.getenv('DRIVER_PATH', '')

# Google authentication (optional)
google_email = os.getenv('GOOGLE_EMAIL', '').strip()
google_password = os.getenv('GOOGLE_PASSWORD', '').strip()
gmail_alias_prefix = os.getenv('GMAIL_ALIAS_PREFIX', '').strip()
requires_login = bool(google_email and google_password)

# Wait time configuration (for speed optimization)
element_wait_timeout = int(os.getenv('ELEMENT_WAIT_TIMEOUT', 5))
form_load_wait = float(os.getenv('FORM_LOAD_WAIT', 1))
submit_wait = float(os.getenv('SUBMIT_WAIT', 1))
between_submissions = float(os.getenv('BETWEEN_SUBMISSIONS', 0.5))

# Parse whitelist submission data (comma-separated entries)
wallet_addresses = [w.strip() for w in os.getenv('WALLET_ADDRESS', '').split(',') if w.strip()]
x_usernames = [x.strip() for x in os.getenv('X_USERNAME', '').split(',') if x.strip()]
x_links = [l.strip() for l in os.getenv('X_LINK', '').split(',') if l.strip()]

# Determine number of entries (max of all provided fields)
num_entries = max(len(wallet_addresses), len(x_usernames), len(x_links)) if (wallet_addresses or x_usernames or x_links) else 0

# Get NUM_RESPONSES from env, default to number of entries
num_responses_env = os.getenv('NUM_RESPONSES', '').strip()
if num_responses_env:
    num_responses = int(num_responses_env)
else:
    num_responses = num_entries

# Create list of whitelist data entries
whitelist_entries = []
for i in range(num_entries):
    entry = {
        'wallet_address': wallet_addresses[i] if i < len(wallet_addresses) else '',
        'x_username': x_usernames[i] if i < len(x_usernames) else '',
        'x_link': x_links[i] if i < len(x_links) else '',
    }
    whitelist_entries.append(entry)

# Helper function to generate email with Gmail alias
def get_email_for_entry(email, alias_prefix, entry_index):
    """Generate unique email using Gmail + alias trick or multiple emails"""
    if not email:
        return None
    
    if ',' in email:
        # Multiple emails provided, cycle through them
        emails = [e.strip() for e in email.split(',')]
        return emails[entry_index % len(emails)]
    elif alias_prefix:
        # Gmail alias: email@gmail.com + prefix+1, prefix+2, etc
        base, domain = email.split('@')
        return f"{base}+{alias_prefix}{entry_index + 1}@{domain}"
    else:
        # Use exact email
        return email

print(f"Loaded {num_entries} whitelist entries. Will submit form {num_responses} times.")
print(f"Wait times - Element: {element_wait_timeout}s, Form load: {form_load_wait}s, Submit: {submit_wait}s, Between: {between_submissions}s")
if requires_login:
    if ',' in google_email:
        emails = [e.strip() for e in google_email.split(',')]
        print(f"Google Login: {len(emails)} accounts available (will cycle through)")
    elif gmail_alias_prefix:
        print(f"Google Login: Gmail aliases enabled (prefix: {gmail_alias_prefix})")
    else:
        print(f"Google Login: {google_email}")
if whitelist_entries:
    for idx, entry in enumerate(whitelist_entries):
        email_for_entry = get_email_for_entry(google_email, gmail_alias_prefix, idx) if requires_login else "N/A"
        print(f"Entry {idx + 1}: {entry['wallet_address']} | {entry['x_username']} | Email: {email_for_entry}")

total = 150
percents = [(34.9, 55.6, 4.5, 5), (22.2, 9.5, 12.7, 6, 7.9, 14.3, 25.4, 2), (73, 11.1, 15.9), (76.2, 15.9, 7.9),
            (11.1, 17.5, 71.4), (12.7, 42.9, 6, 20.6, 5, 9.5, 3.3), (69.8, 23.8, 3, 3.4), (42.9, 46, 11.1),
            (11.1, 14.3, 74.6), (90.5, 9.5), (92.1, 7.9), (4, 41.3, 49.2, 5.5), (71.4, 4.8, 23.8), (45, 35, 20),
            (52.4, 47.6), (76.2, 6.4, 9.5, 7.9), (15.9, 76.2, 7.9), (33.3, 50.8, 15.9), (14.3, 57.1, 17.5, 11.1),
            (74.6, 14.3, 11.1)]  # here goes percentage
persons = {}
response = num_responses  # Number of respondents from env
link = form_link  # Google form link from env


def login_to_google(driver, email, password):
    """
    Authenticate with Google account to bypass sign-in requirement
    Handles both standard emails and Gmail alias variations
    """
    try:
        print(f"Authenticating with: {email}")
        # Wait for email input
        email_input = WebDriverWait(driver, element_wait_timeout).until(
            EC.presence_of_element_located((By.ID, "identifierId"))
        )
        email_input.send_keys(email)
        
        # Click next
        driver.find_element_by_id("identifierNext").click()
        time.sleep(0.5)
        
        # Wait for password input
        password_input = WebDriverWait(driver, element_wait_timeout).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_input.send_keys(password)
        
        # Click next
        driver.find_element_by_id("passwordNext").click()
        time.sleep(1)
        
        print(f"Authentication successful for: {email}")
        return True
    except Exception as e:
        print(f"Google authentication failed for {email}: {e}")
        return False


def fillForm(link_, submission_data, entry_index=0):
    global tf
    global count
    global val
    global ml
    try:
        # Initialize Firefox driver
        if driver_path:
            driver = webdriver.Firefox(executable_path=driver_path, options=chrome_options)
        else:
            driver = webdriver.Firefox(options=chrome_options)
        
        # Handle Google login if required
        if requires_login:
            driver.get("https://accounts.google.com/login")
            # Get the email for this entry (with alias if configured)
            email_for_entry = get_email_for_entry(google_email, gmail_alias_prefix, entry_index)
            if not login_to_google(driver, email_for_entry, google_password):
                print("Failed to authenticate. Proceeding anyway...")
                driver.quit()
                return
            time.sleep(form_load_wait)
            
        if not ml:
            val = 1
        for m in range(val):
            temp = count
            count += 1
            driver.get(link_)
            
            # Wait for form to load - more efficient than fixed sleep
            try:
                WebDriverWait(driver, element_wait_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"], textarea, [role="radiogroup"]'))
                )
            except:
                time.sleep(form_load_wait)
            
            # Fill text input fields (for whitelist submission)
            text_inputs = driver.find_elements_by_css_selector('input[type="text"]')
            for idx, text_input in enumerate(text_inputs):
                try:
                    # Try to identify which field this is based on placeholder
                    placeholder = text_input.get_attribute('placeholder') or text_input.get_attribute('aria-label') or ''
                    
                    if 'wallet' in placeholder.lower() or 'address' in placeholder.lower():
                        if submission_data['wallet_address']:
                            text_input.send_keys(submission_data['wallet_address'])
                    elif 'twitter' in placeholder.lower() or 'x_username' in placeholder.lower() or 'username' in placeholder.lower():
                        if submission_data['x_username']:
                            text_input.send_keys(submission_data['x_username'])
                    elif 'link' in placeholder.lower() or 'url' in placeholder.lower() or 'x' in placeholder.lower() or 'tweet' in placeholder.lower():
                        if submission_data['x_link']:
                            text_input.send_keys(submission_data['x_link'])
                except Exception as e:
                    print(f"Error filling text input {idx}: {e}")
            
            # Fill MCQ questions
            questions = driver.find_elements_by_css_selector('[class="freebirdFormviewerViewNumberedItemContainer"]')
            for question_ in questions:
                try:
                    que = question_.find_element_by_css_selector('[jscontroller="eFy6Rc"]')
                    choices1 = que.find_elements_by_css_selector('[jscontroller="EcW08c"]')
                    num = persons['{}'.format(temp)][questions.index(question_)]
                    choices1[num].click()

                except:
                    que = question_.find_element_by_css_selector('[jscontroller="tjSPQb"]')
                    try:
                        lines = WebDriverWait(que, element_wait_timeout).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,
                                                                                                 '[class="appsMaterialWizToggleRadiogroupGroupContainer exportGroupContainer freebirdFormviewerComponentsQuestionGridRowGroup"]')))
                        for line in lines:
                            choices3 = line.find_elements_by_css_selector('[jscontroller="EcW08c"]')
                            num = persons['{}'.format(temp)][questions.index(question_)]
                            choices3[num].click()
                    except:
                        pass
            #                choices2 = question.find_elements_by_css_selector('[jscontroller="D8e5bc"]')
            
            # Find and click submit button
            try:
                submit_button = WebDriverWait(driver, element_wait_timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Submit')]"))
                )
                submit_button.click()
            except Exception as e:
                print(f"Error clicking submit: {e}")
            
            time.sleep(submit_wait)
        tf = True
        ml = False
        val = 1
        driver.quit()
    except Exception as e:
        print(f"Error in fillForm: {e}")
        tf = True
        ml = False


def multiRun(key1, key2, submission_data, entry_index):
    global tf
    global ml
    global val
    tf = False
    if int(key2) > 4:
        ml = True
        val = math.ceil(int(key2) / 4)
        key2 = 4
    for i in range(int(key2)):
        threading.Thread(target=fillForm, args=(key1, submission_data, entry_index)).start()
        time.sleep(between_submissions)
    time.sleep(0.5)


def formFill(key1, key2, submission_data, entry_index):
    try:
        multiRun(key1, key2, submission_data, entry_index)
        while True:
            if tf:
                print(f'{key2} times form fill done.')
                break
    except Exception as e:
        print(e)
        print('Error in filling your form, your form might contain questions other than MCQ or have email verification')


for n in range(total):
    a_d = {f"{(n + 1)}": []}
    persons.update(a_d)

mno = 1
for question in percents:
    for option in question:
        rispondant = (math.floor(option * 1.5))
        for ko in range(rispondant):
            persons['{}'.format(mno)].append(question.index(option))
            mno += 1

    mno = 1

# Submit form for each whitelist entry
if whitelist_entries:
    print(f"\nStarting form submissions for {len(whitelist_entries)} entries...\n")
    for idx, entry in enumerate(whitelist_entries):
        print(f"Submitting entry {idx + 1}/{len(whitelist_entries)}: {entry['wallet_address']}")
        formFill(link, num_responses, entry, idx)
        print(f"Completed entry {idx + 1}\n")
    print("All entries submitted successfully!")
else:
    print("No whitelist entries found in .env file!")
    print("Please add WALLET_ADDRESS, X_USERNAME, or X_LINK to .env")
