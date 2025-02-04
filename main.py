from selenium_driverless import webdriver
from selenium_driverless.types.by import By
import asyncio
import os

def load_existing_links(file_path):
    if not os.path.exists(file_path):
        return set()
    with open(file_path, "r") as file:
        return set(line.strip() for line in file.readlines())

def save_link(file_path, link):
    with open(file_path, "a") as file:
        file.write(f"{link}\n")

async def main():
    file_path = "link.txt"
    startDate = 1900
    endDate = 1900
    step = 1
    categories = ["male", "female", "unisex"]

    existing_links = load_existing_links(file_path)
    print(f"{len(existing_links)} liens déjà présents dans {file_path}")

    async with webdriver.Chrome() as driver:
        while startDate <= 2025:
            for category in categories:
                url = f"https://www.fragrantica.fr/search/?godina={startDate}%3A{endDate}&spol={category}"
                await driver.get(url, wait_load=True)
                await driver.sleep(3)

                extracted_links = set()
                print(f"\n🔍 Scraping {category.upper()} ({startDate}-{endDate})...")

                while True:
                    grid_items = await driver.find_elements(By.CLASS_NAME, "cell card fr-news-box")
                    print(f"📌 {len(grid_items)} fragrances find")

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
                            print(f"⚠️ Error while scrapping fragrance: {e}")

                    if new_links == 0:
                        print("✅ Did not find new fragrance on this page.")

                    try:
                        button = await driver.find_element(By.CLASS_NAME, "button")
                        
                        status = await button.get_property('disabled')

                        if not status:
                            print("➡ Clicked on button to show more results")
                            await button.click(move_to=True)
                            await driver.sleep(2)
                            continue
                        else:
                            print(f"⏩ Ended scrapping {category.upper()}, going to the next one.")
                            break

                    except Exception:
                        print(f"⚠️ Can't find 'see more' button {category.upper()}.")
                        break

            print(f"🔄 Finished running {startDate}-{endDate}, going to the next year.")
            startDate += step
            endDate += step

asyncio.run(main())
