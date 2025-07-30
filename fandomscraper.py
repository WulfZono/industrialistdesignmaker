import requests
from bs4 import BeautifulSoup
import time
import json
import argparse

BASE_URL = "https://industrialist.fandom.com"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

CATEGORY_URLS = {
    "machines": "https://industrialist.fandom.com/wiki/Category:Machines",
    "items": "https://industrialist.fandom.com/wiki/Category:Items"
}

def get_soup(url):
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        return BeautifulSoup(res.text, 'html.parser')
    return None

def get_category_links(category_url):
    soup = get_soup(category_url)
    links = []
    if not soup:
        return links

    for a in soup.select('div.category-page__members a.category-page__member-link'):
        href = a.get('href')
        if href:
            full_url = BASE_URL + href
            links.append(full_url)
    return links

def parse_machine_page(url):
    soup = get_soup(url)

    data = {
        "url": url,
        "name": "",
        "input_energy": "",
        "capacity": "",
        "pollution": "",
        "size": "",
        "cost": "",
        "recipe": []
    }

    title = soup.find("h1", {"id": "firstHeading"})
    if title:
        data["name"] = title.text.strip()

    content = soup.select_one("div.mw-parser-output")
    if not content:
        return data

    # Find energy requirements
    for info_div in content.find_all("div", class_="information"):
        prev = info_div.find_previous(string=True)
        if prev and "Power" in prev:
            text = info_div.get_text(strip=True)
            if text.startswith("Input"):
                text = text[5:].lstrip(": \u00A0")  
            data["input_energy"] = text
            break 
    # Find capacity
    for info_div in content.find_all("div", class_="information bordertop"):
        if "Capacity" in info_div.get_text(strip=True):
            text = info_div.get_text(strip=True)
            if text.startswith("Capacity"):
            # Remove "Capacity" and any following colon or whitespace
                text = text[len("Capacity"):].lstrip(": \u00A0")  
             
            data["capacity"] = text
            break
    # Find pollution
    for info_div in content.find_all("div", class_="information bordertop"):
        if "Pollution" in info_div.get_text(strip=True):
            text = info_div.get_text(strip=True)
            if text.startswith("Pollution"):
                text = text[len("Pollution"):].lstrip(": \u00A0")
            
            data["pollution"] = text
            break
    # Find size
    for info_div in content.find_all("div", class_="information bordertop"):
        if "Size" in info_div.get_text(strip=True):
            text = info_div.get_text(strip=True)
            if text.startswith("Size"):
                text = text[len("Size"):].lstrip(": \u00A0")
             
            data["size"] = text
            break
    # Find cost
    for info_div in content.find_all("div", class_="information"):
        if "Cost" in info_div.get_text(strip=True):
            text = info_div.get_text(strip=True)
            if text.startswith("Cost"):
                text = text[len("Cost"):].lstrip(": \u00A0")
             
            data["cost"] = text
            break
    
    # Recipes
    for table in content.find_all("table"):
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if all(cell.name == "th" for cell in cells):
                continue
            if len(cells) >= 3:
                material = cells[0].get_text(strip=True)
                qty = cells[1].get_text(strip=True)
                output = cells[2].get_text(strip=True)
                if material and qty and output and "Power" != qty:
                    data["recipe"].append({"material": material, "quantity": qty, "output": output})
                elif not material and qty and output and "Power" != qty:
                    material = ""
                    data["recipe"].append({"material": material, "quantity": qty, "output": output})
    return data

def parse_item_page(url):
    soup = get_soup(url)

    data = {
        "url": url,
        "name": "",
        "value": ""
    }

    title = soup.find("h1", {"id": "firstHeading"})
    if title:
        data["name"] = title.text.strip()

    content = soup.select_one("div.mw-parser-output")
    if not content:
        return data

    # Find item value
    value_div = content.find_all("div", class_="pi-data-value pi-font")
    for div in value_div:
        if "$" in div.get_text(strip=True):
            data["value"] = div.get_text(strip=True)
            break
    return data


def main():
    parser = argparse.ArgumentParser(description="Industrialist Wiki Scraper")
    parser.add_argument('--scrape', choices=['machines', 'items', 'both'], default='both', help='Which data to scrape')
    parser.add_argument('--max-machines', type=int, default=None, help='Max number of machine pages to scrape')
    parser.add_argument('--max-items', type=int, default=None, help='Max number of item pages to scrape')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests in seconds')
    args = parser.parse_args()

    machine_data = []
    item_data = []

    if args.scrape in ['machines', 'both']:
        machine_links = get_category_links(CATEGORY_URLS["machines"])
        if args.max_machines:
            machine_links = machine_links[:args.max_machines]
        print(f"Found {len(machine_links)} machine pages")
        for idx, link in enumerate(machine_links):
            print(f"[{idx+1}/{len(machine_links)}] Scraping machine: {link}")
            item = parse_machine_page(link)
            if item:
                machine_data.append(item)
            time.sleep(args.delay)
        with open("industrialist_machines.json", "w") as f:
            json.dump(machine_data, f, indent=2)
        print("Done. Saved data to 'industrialist_machines.json'.")

    if args.scrape in ['items', 'both']:
        item_links = get_category_links(CATEGORY_URLS["items"])
        if args.max_items:
            item_links = item_links[:args.max_items]
        print(f"Found {len(item_links)} item pages")
        for idx, link in enumerate(item_links):
            print(f"[{idx+1}/{len(item_links)}] Scraping item: {link}")
            item = parse_item_page(link)
            if item:
                item_data.append(item)
            time.sleep(args.delay)
        with open("industrialist_items.json", "w") as f:
            json.dump(item_data, f, indent=2)
        print("Done. Saved data to 'industrialist_items.json'.")

if __name__ == "__main__":
    main()
