import json
import os
from pprint import pprint

import arrow
import gspread
import pandas as pd
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from playwright.sync_api import sync_playwright

load_dotenv()

url = "https://f1tv.formula1.com/page/1724/inside-story"  # Replace with your target URL


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        headless=False
    )  # Launch browser in headless mode
    page = browser.new_page()  # Create a new page
    page.goto(url)  # Navigate to the target URL

    # Wait for the div to load
    page.wait_for_selector(
        "#app > div > div.content > main > div:nth-child(4) > div > div > div"
    )
    list_items = page.query_selector_all('div[role="listitem"]')

    scraped_data = []
    for item in list_items:
        if item.inner_text():
            parsed = item.inner_text().strip().replace(" | Documentary", "")
            title, time = parsed.split("\n")
            scraped_data.append({"title": title, "length": time})
    pprint(scraped_data)

    browser.close()  # Close the browser

scopes = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_info(
    json.loads(os.getenv("GS_CREDS")),
    scopes=scopes,
)

gc = gspread.authorize(creds)

sht1 = gc.open_by_key("1So6jvb1UDu8QjlQfjylT07oOJfEM9oRySB4YaXbHnWY").sheet1

sheet_data = sht1.get_all_values()
new = pd.DataFrame(scraped_data)
seen = pd.DataFrame(sheet_data[1:], columns=sheet_data[0])
time_now = arrow.now("US/Eastern").isoformat()
new["time_scraped"] = time_now


for idx, row in new.iterrows():
    if row["title"] not in list(seen["title"]):
        sht1.append_row(list(row), table_range="A1:B1")
