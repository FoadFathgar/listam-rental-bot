import os
import json
import time
import requests
from bs4 import BeautifulSoup

# Embedded Credentials
TELEGRAM_BOT_TOKEN = "8610585425:AAHjm3VY6lsCislJG2ys7d1QQyrMlJST9S8"
TELEGRAM_CHAT_ID = "8321605132"
LIST_AM_URL = os.environ.get("LIST_AM_URL")

STATE_FILE = "seen_ids.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def load_seen_ids():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_seen_ids(seen_ids):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen_ids), f)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")

def check_list_am():
    if not LIST_AM_URL:
        print("Error: LIST_AM_URL environment variable is missing.")
        return

    print("Checking List.am for new listings...")
    try:
        response = requests.get(LIST_AM_URL, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"Failed to fetch page. Status code: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("a", href=True)
        
        seen_ids = load_seen_ids()
        new_seen_ids = set(seen_ids)
        new_items_found = []

        for item in items:
            href = item["href"]
            if "/item/" in href:
                item_id = href.split("/item/")[1].split("?")[0]
                if item_id not in seen_ids:
                    title = item.get_text(strip=True) or "New House/Apartment Listing"
                    full_link = f"https://www.list.am{href}" if href.startswith("/") else href
                    
                    if item_id not in new_seen_ids:
                        new_items_found.append((item_id, title, full_link))
                        new_seen_ids.add(item_id)

        # First run: cache all active IDs without spamming your Telegram
        if not seen_ids and new_items_found:
            print(f"Initial run completed: Cached {len(new_items_found)} listings. Future matches will trigger alerts.")
            save_seen_ids(new_seen_ids)
            return

        if new_items_found:
            for item_id, title, full_link in reversed(new_items_found):
                msg = f"🏠 <b>New List.am Rental Listing!</b>\n\n{title}\n\n🔗 <a href='{full_link}'>View Listing</a>"
                send_telegram_message(msg)
                time.sleep(1)
            save_seen_ids(new_seen_ids)
            print(f"Sent alerts for {len(new_items_found)} new listing(s).")
        else:
            print("No new listings found.")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    check_list_am()
