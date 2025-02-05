import asyncio
import re
import json
import os
import random
from selenium_driverless import webdriver
from selenium_driverless.types.by import By
from selenium_driverless.types.options import Options

# Load existing links from a text file
def load_existing_links(file_path):
    try:
        with open(file_path, "r") as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

# Load existing JSON data to avoid overwriting
def load_existing_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return []
    return []

# Extracts fragrance notes, avoiding duplicates and empty values
async def extract_notes(driver, elements):
    notes = set()  # Using a set to avoid duplicates
    for el in elements:
        text = await driver.execute_script(
            "return arguments[0].childNodes[arguments[0].childNodes.length - 1].textContent.trim();", el
        )
        if text:
            notes.add(text)
    return list(notes)  # Convert to a list after removing duplicates

async def main():
    json_file = "fragrances.json"
    links = load_existing_links("link.txt")  
    existing_data = load_existing_json(json_file)

    # Extract existing fragrance names to avoid duplicates
    existing_titles = {item["title"].strip().lower() for item in existing_data}

    # Find the last used ID and increment it
    last_id = max((item.get("id", 0) for item in existing_data), default=0)

    # Configure the browser with a random User-Agent
    options = Options()

    async with webdriver.Chrome(options=options) as driver:
        for link in links:
            await driver.get(link, wait_load=True)

            # Simulate a real session by adding cookies
            cookies = {
                "name": "session",
                "value": "random_session_value",
                "domain": ".fragrantica.com"
            }
            await driver.add_cookie(cookies)
            await asyncio.sleep(2)  # Wait to simulate human behavior

            # Extract fragrance title
            try:
                titleElement = await driver.find_element(By.CSS_SELECTOR, '#toptop > h1')
                title = await driver.execute_script("return arguments[0].textContent;", titleElement)
            except:
                print(f"⚠️ Skipping: Could not retrieve title for {link}")
                continue  # Skip this fragrance if the title is missing

            # Skip if the fragrance already exists in the JSON
            if title.lower() in existing_titles:
                print(f"⚠️ Skipping: '{title}' already exists in the dataset.")
                continue

            # Extract brand name
            try:
                brandElement = await driver.find_element(By.CSS_SELECTOR, "#main-content div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > p > a > span")
                brand = await brandElement.text
            except:
                brand = "Unknown brand"

            # Extract image URL
            try:
                imageElement = await driver.find_element(By.CSS_SELECTOR, "img[itemprop='image']")
                image_url = await driver.execute_script("return arguments[0].src;", imageElement)
            except:
                image_url = "No image available"

            # Extract accords
            accords = await driver.find_elements(By.CSS_SELECTOR, ".accord-bar")
            accords_data = []
            for accord in accords:
                text = await accord.text
                style = await driver.execute_script("return arguments[0].getAttribute('style');", accord)
                width_match = re.search(r'width:\s*([\d\.]+)%', style)
                width = width_match.group(1) if width_match else "0"
                accords_data.append({"name": text, "width": width})

            # Extract notes
            topNotes = await driver.find_elements(By.CSS_SELECTOR, "#pyramid div:nth-child(4) div")
            middleNotes = await driver.find_elements(By.CSS_SELECTOR, "#pyramid div:nth-child(6) div")
            baseNotes = await driver.find_elements(By.CSS_SELECTOR, "#pyramid div:nth-child(8) div")

            top_notes_data = await extract_notes(driver, topNotes)
            middle_notes_data = await extract_notes(driver, middleNotes)
            base_notes_data = await extract_notes(driver, baseNotes)

            # Increment the ID
            last_id += 1  

            # Store fragrance information in a dictionary
            fragrance_data = {
                "id": last_id,
                "title": title,
                "brand": brand,
                "image": image_url,
                "accords": accords_data,
                "top_notes": top_notes_data,
                "middle_notes": middle_notes_data,
                "base_notes": base_notes_data,
                "link": link
            }

            # Add new fragrance to the dataset
            existing_data.append(fragrance_data)
            existing_titles.add(title.lower())  # Update the set to prevent duplicates

            # Save updated data to JSON file
            with open(json_file, "w", encoding="utf-8") as file:
                json.dump(existing_data, file, ensure_ascii=False, indent=4)

            print(f"✅ Saved: {title} - {brand} (ID: {last_id})")

            await asyncio.sleep(random.randint(3, 5))  # Random pause to avoid detection

asyncio.run(main())
