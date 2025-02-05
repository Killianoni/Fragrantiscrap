import asyncio
from selenium_driverless import webdriver
from selenium_driverless.types.by import By

# Load existing links from a file to avoid duplicates
def load_existing_links(file_path):
    try:
        with open(file_path, "r") as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

# Save new links to a file
def save_link(file_path, link):
    with open(file_path, "a") as file:
        file.write(f"{link}\n")

async def main():
    file_path = "link.txt"
    start_year = 2008
    end_year = 2008
    step = 1  # Year increment step
    categories = ["male", "female", "unisex"]  # Fragrance types
    countries = [
        "United States", "France", "Italy", "United Kingdom", "Brazil", 
        "United Arab Emirates", "Spain", "Russia", "Germany", "Sweden"
    ]  # Countries (as used in Fragrantica)

    existing_links = load_existing_links(file_path)
    print(f"{len(existing_links)} links already exist in {file_path}")

    async with webdriver.Chrome() as driver:
        while start_year <= 2025:
            for category in categories:
                for country in countries:
                    url = f"https://www.fragrantica.fr/search/?godina={start_year}%3A{end_year}&spol={category}&country={country}"
                    await driver.get(url, wait_load=True)
                    await driver.sleep(3)
                    
                    extracted_links = set()
                    print(f"\n🔍 Scraping {category.upper()} ({start_year}-{end_year}) - Country: {country}")
                    
                    while True:
                        grid_items = await driver.find_elements(By.CLASS_NAME, "cell card fr-news-box")
                        print(f"📌 {len(grid_items)} fragrances found for {country}")

                        new_links = 0
                        for item in grid_items:
                            try:
                                title_element = await item.find_element(By.TAG_NAME, "a")
                                href_link = await title_element.get_attribute("href")

                                if href_link not in extracted_links and href_link not in existing_links:
                                    extracted_links.add(href_link)
                                    existing_links.add(href_link)
                                    save_link(file_path, href_link)
                                    new_links += 1
                            except Exception as e:
                                print(f"⚠️ Error extracting an element: {e}")

                        if new_links == 0:
                            print("✅ No new fragrances found on this page.")

                        try:
                            button = await driver.find_element(By.CLASS_NAME, "button")
                            status = await button.get_property('disabled')

                            if not status:
                                print("➡️ Clicking 'See More' to load more results...")
                                await button.click(move_to=True)
                                await driver.sleep(2)
                                continue
                            else:
                                print(f"⏩ Scraping completed for {category.upper()} ({start_year}-{end_year}) - Country: {country}")
                                break
                        except Exception:
                            print("⚠️ 'See More' button not found, moving to the next country.")
                            break
            
            print(f"🔄 Completed year {start_year}-{end_year}, moving to the next year.")
            start_year += step
            end_year += step

# Run the script
asyncio.run(main())
