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

def get_headers_from_curl_file(curl_file: str) -> Dict[str, str]:
    with open(curl_file, 'r') as file:
        curl_command = file.read()
    headers = {}
    for line in curl_command.split('\n'):
        if re.match(r'^\s*-H', line):
            header_parts = line.split(':', 1)
            if len(header_parts) == 2:
                key = header_parts[0].replace('-H', '').strip().strip("'")
                value=header_parts[1].strip()
                headers[key] = value
    return headers

def parse_as_cookies(cookie_string: str) -> List[Dict[str, str]]:
    cookies = []
    for item in cookie_string.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookies.append({
                "name": key,
                "value": value,
                "domain": ".amazon.com",  # Add the domain
                "path": "/"  # Add the path
            })
    return cookies


@finic.workflow_entrypoint(input_model=InputSchema)
def main(input: InputSchema):
    query = input.query
    curl_file = input.curl_file
    output_file = input.output_file

    headers = get_headers_from_curl_file(curl_file)
    cookies = parse_as_cookies(headers.get("cookie"))
    
    places = []

    print("Running the Playwright script")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
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
        import pdb; pdb.set_trace()
        
        while len(results) > 0:
            result = results.pop()
            if result.get_attribute("href") in processed_results:
                continue
            # save the url to the results
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

    return {"places": places}
