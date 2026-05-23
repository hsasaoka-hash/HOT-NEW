import requests
from bs4 import BeautifulSoup
import time
import os

# 監視対象URL
TARGET_URL = os.getenv("TARGET_URL", "https://beauty.hotpepper.jp/relax/svcSA/macAC/salon/" )
DATA_FILE = "past_shops.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_latest_shops(url):
    try:
        print(f"アクセス中: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        print(f"ステータスコード: {response.status_code}") # 200なら成功
        
        if response.status_code != 200:
            print("アクセスが拒否された可能性があります。")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        shop_list = []
        
        # ページ内のh3タグの数を確認
        h3_tags = soup.find_all('h3')
        print(f"ページ内の見出し(h3)の数: {len(h3_tags)}")

        for h3 in h3_tags:
            a = h3.find('a')
            if a and 'slnH' in a.get('href', ''):
                name = a.text.strip()
                raw_url = a.get('href').split('?')[0]
                full_url = f"https://beauty.hotpepper.jp{raw_url}" if raw_url.startswith('/' ) else raw_url
                shop_list.append({"name": name, "url": full_url})
        
        return shop_list
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return []

def load_past_shops():
    if not os.path.exists(DATA_FILE): return set()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_shops(urls):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for url in sorted(urls): f.write(f"{url}\n")

def main():
    print(f"--- 検索開始 ---")
    current_shops = get_latest_shops(TARGET_URL)
    
    if not current_shops:
        print("店舗が見つかりませんでした。アクセス制限か、URLが正しくない可能性があります。")
        return
    
    past_urls = load_past_shops()
    new_shops = [s for s in current_shops if s['url'] not in past_urls]
    
    if new_shops:
        print(f"★新着店舗が {len(new_shops)} 件見つかりました！")
        for shop in new_shops:
            print(f"店舗名: {shop['name']}\nURL  : {shop['url']}\n---")
        save_shops(past_urls.union(set(s['url'] for s in current_shops)))
    else:
        print("新着店舗はありませんでした（すべてチェック済みです）。")

if __name__ == "__main__":
    main()
