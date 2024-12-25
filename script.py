from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from time import sleep
import os
import zipfile
from selenium import webdriver
import time
import uuid
from datetime import datetime
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
from selenium.common.exceptions import (
    NoSuchElementException
)
import sys

# Load environment variables from a .env file
load_dotenv()
TWITTER_LOGIN_URL = "https://twitter.com/i/flow/login"

PATH = os.getenv('DRIVER_PATH')
### Connecting to mongoDB

# Get MongoDB credentials
mongo_user = os.getenv('MONGOUSER')
mongo_pass = os.getenv('MONGOPASS')
mongo_appname = os.getenv('MONGOAPPNAME')

# Ensure password is URL-encoded
encoded_password = quote_plus(mongo_pass)

# Construct the URI
uri = f"mongodb+srv://{mongo_user}:{encoded_password}@cluster0.4talj.mongodb.net/?retryWrites=true&w=majority&appName={mongo_appname}"

# Create a new client and connect to the server
try:
    client = MongoClient(uri, server_api=ServerApi('1'))
    client.admin.command('ping')  # Send a ping to confirm a successful connection
    print("Pinged your deployment. You successfully connected to MongoDB!")
    db = client['twitter_trends']  # Database name
    collection = db['trends']      # Collection name
except Exception as e:
    print("Failed to connect to MongoDB:", e)

### Setting up ProxyMesh for selenium
PROXY_HOST = os.getenv('PROXYMESH_HOSTNAME')  # rotating proxy
PROXY_PORT = os.getenv('PROXYMESH_PORT') # port
PROXY_USER = os.getenv("PROXYMESH_USERNAME") # username
PROXY_PASS = os.getenv("PROXYMESH_PASSWORD") # password


manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
"""

background_js = """
var config = {
        mode: "fixed_servers",
        rules: {
          singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
          },
          bypassList: ["localhost"]
        }
      };

chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}

chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)

def serialize_mongo_document(doc):
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

# Setting up chromedriver with proxymesh
def get_chromedriver(use_proxy=False, user_agent=None):
    # Set driver path and service
    s = Service(PATH)
    chrome_options = webdriver.ChromeOptions()
    if use_proxy:
        pluginfile = 'proxy_auth_plugin.zip'

        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        chrome_options.add_extension(pluginfile)
    if user_agent:
        chrome_options.add_argument('--user-agent=%s' % user_agent)
    driver = webdriver.Chrome(
        service=s,
        options=chrome_options)
    return driver

# Input username
def input_username(driver, xusername):
        input_attempt = 0

        while True:
            try:
                username = driver.find_element(
                    "xpath", "//input[@autocomplete='username']"
                )

                username.send_keys(xusername)
                username.send_keys(Keys.RETURN)
                sleep(3)
                break
            except NoSuchElementException:
                input_attempt += 1
                if input_attempt >= 3:
                    print()
                    print(
                        """There was an error inputting the username.

It may be due to the following:
- Internet connection is unstable
- Username is incorrect
- Twitter is experiencing unusual activity"""
                    )
                    driver.quit()
                    sys.exit(1)
                else:
                    print("Re-attempting to input username...")
                    sleep(2)

# Input unusual activity
def input_unusual_activity(driver, usermail):
    input_attempt = 0

    while True:
        try:
            unusual_activity = driver.find_element(
                "xpath", "//input[@data-testid='ocfEnterTextTextInput']"
            )
            unusual_activity.send_keys(usermail)
            unusual_activity.send_keys(Keys.RETURN)
            sleep(3)
            break
        except NoSuchElementException:
            input_attempt += 1
            if input_attempt >= 3:
                break

# Input password
def input_password(driver, xpassword):
    input_attempt = 0

    while True:
        try:
            password = driver.find_element(
                "xpath", "//input[@autocomplete='current-password']"
            )

            password.send_keys(xpassword)
            password.send_keys(Keys.RETURN)
            sleep(3)
            break
        except NoSuchElementException:
            input_attempt += 1
            if input_attempt >= 3:
                print()
                print(
                    """There was an error inputting the password.

It may be due to the following:
- Internet connection is unstable
- Password is incorrect
- Twitter is experiencing unusual activity"""
                )
                driver.quit()
                sys.exit(1)
            else:
                print("Re-attempting to input password...")
                sleep(2)

# Go to user homepage
def go_to_home(driver):
    driver.get("https://twitter.com/home")
    sleep(3)
    pass

# Login to Twitter
def login(driver, username, usermail, password):
    print()
    print("Logging in to Twitter...")

    try:
        driver.maximize_window()
        driver.get(TWITTER_LOGIN_URL)
        sleep(3)

        input_username(driver, username)
        input_unusual_activity(driver, usermail)
        input_password(driver, password)

        cookies = driver.get_cookies()

        auth_token = None

        for cookie in cookies:
            if cookie["name"] == "auth_token":
                auth_token = cookie["value"]
                break

        if auth_token is None:
            raise ValueError(
                """This may be due to the following:

- Internet connection is unstable
- Username is incorrect
- Password is incorrect
"""
            )

        print()
        print("Login Successful")
        print()
    except Exception as e:
        print()
        print(f"Login Failed: {e}")
        sys.exit(1)
    pass

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/run-script', methods=['GET'])
# Main logic
def run_script():
    driver = get_chromedriver(use_proxy=True)
    try:
    # Initializing the webdrive with proxymesh
    # Determine the proxy IP address by visiting an IP-checking service
        driver.get("https://api.ipify.org?format=text")
        time.sleep(3)
        proxy_ip = driver.find_element(By.TAG_NAME, 'body').text
    # Login to Twitter
        login(driver, os.getenv('TWITTER_USER'), os.getenv('TWITTER_USER_MAIL'), os.getenv('TWITTER_PASS'))
    # Go to homepage
        go_to_home(driver)
    # Scrape the trending topics
        # Locate the "What’s Happening" section
        whats_happening_section = driver.find_element(By.XPATH, '//div[contains(@aria-label, "Timeline: Trending now")]')
        # Fetch the top 5 trending topics
        trending_topics = whats_happening_section.find_elements(By.XPATH, './/div[@data-testid="trend"]')[:5]
        topics = [topic.text.split('\n')[1] for topic in trending_topics]
        # Print the trending topics for debugging
        print("Scraped Trending Topics:", topics)
        # Generate a unique ID for this script run
        unique_id = str(uuid.uuid4())
        # Get the current date and time
        current_datetime = datetime.now().isoformat()
        # Create the data to store in MongoDB
        data = {
            "unique_id": unique_id,
            "trend1": topics[0] if len(topics) > 0 else None,
            "trend2": topics[1] if len(topics) > 1 else None,
            "trend3": topics[2] if len(topics) > 2 else None,
            "trend4": topics[3] if len(topics) > 3 else None,
            "trend5": topics[4] if len(topics) > 4 else None,
            "datetime": current_datetime,
            "ip_address": proxy_ip
        }
        # Insert the data into MongoDB
        inserted_id = collection.insert_one(data).inserted_id
        print(f"Data successfully inserted into MongoDB with ID: {inserted_id}")

        # Convert ObjectId to string
        data["_id"] = str(inserted_id)
        
        # data = serialize_mongo_document(collection.find_one({"_id": inserted_id}))

        # Format data for display
        return render_template(
            'result.html',
            datetime=data["datetime"],
            topics=topics,
            ip_address=data["ip_address"],
            json_data=data
        )

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        # Ensure the browser is closed
        if 'driver' in locals():
            driver.quit()
            print("Browser closed")

if __name__ == '__main__':
    app.run(debug=False)