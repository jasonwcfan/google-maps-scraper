from models import InputSchema
from playwright.sync_api import sync_playwright, Playwright, Page
import os
from finicapi import Finic
from dotenv import load_dotenv
from typing import List, Dict
import json
import re

load_dotenv(override=True)
FINIC_API_KEY = os.getenv("FINIC_API_KEY")
finic = Finic(
    api_key=FINIC_API_KEY,
)

@finic.workflow_entrypoint(input_model=InputSchema)
def main(input: InputSchema):
    query = input.query
    output_file = input.output_file
    
    places = []

    print("Running the Playwright script")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # context = browser.new_context()
        page = browser.new_page()

        # context.add_cookies(cookies)

        # Navigate to the orders page.
        page.goto("https://www.google.com/maps/@43.6500418,-79.3916043,3508m")

        # Wait for the page to load
        page.wait_for_load_state("domcontentloaded")

        search_box = page.query_selector("input.searchboxinput")
        search_box.fill(query)
        search_box.press('Enter')

        # Wait for the network to be idle
        page.wait_for_load_state("networkidle")

        # Find all a elements with a href attribute that includes "google.com/maps/place"
        results_section = page.query_selector("div[aria-label^='Results']")
        results = page.query_selector_all("a[href*='google.com/maps/place']")
        processed_results = []
        
        while len(results) > 0:
            result = results.pop()
            if result.get_attribute("href") in processed_results:
                continue

            places.append(result.get_attribute("href"))
            processed_results.append(page.url)

            if len(processed_results) > 50:
                break

            if len(results) == 0:
                #scroll down the max possible amount in the results section
                results_section.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_load_state("networkidle")
                results = page.query_selector_all("a[href*='google.com/maps/place']")
        
        browser.close()

        with open(output_file, "w") as file:
            json.dump(places, file)

    return {"places": places}
