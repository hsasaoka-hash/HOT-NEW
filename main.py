import requests
from bs4 import BeautifulSoup
import time
import os

# 監視したいURLのリスト（ここに追加・削除が可能です）
TARGET_URLS = [
    "https://beauty.hotpepper.jp/svcSA/newShopList/",        # ヘア（関東 ）
    "https://beauty.hotpepper.jp/relax/svcSA/newShopList/",  # リラク（関東 ）
    "https://beauty.hotpepper.jp/kr/svcSA/newShopList/",     # エステ・ネイル・まつげ（関東 ）
]

DATA_FILE = "past_shops.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Referer": "https://beauty.hotpepper.jp/",
}

def get_latest_shops(url ):
    try:
        print(f"チェック中: {url}")
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            print(f"アクセス失敗 (Code: {response.status_code})")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        shop_list = []
        
        # 新着一覧ページの構造に合わせて抽出
        # 通常の店舗一覧と新着一覧ではタグが異なる場合があるため広めに探す
        items = soup.select('h3.salonCassette__title a, h3.salonName a, .shopName a')
        
        if not items:
            items = [a for a in soup.find_all('a') if 'slnH' in a.get('href', '')]

        for a in items:
            name = a.text.strip()
            if not name or len(name) < 2: continue
            
            raw_url = a.get('href').split('?')[0]
            if 'slnH' not in raw_url: continue
            
            full_url = f"https://beauty.hotpepper.jp{raw_url}" if raw_url.startswith('/' ) else raw_url
            
            if not any(s['url'] == full_url for s in shop_list):
                shop_list.append({"name": name, "url": full_url})
        
        print(f"-> {len(shop_list)} 件の店舗を確認")
        return shop_list
    except Exception as e:
        print(f"エラー: {e}")
        return []

def load_past_shops():
    if not os.path.exists(DATA_FILE): return set()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_shops(urls):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for url in sorted(urls): f.write(f"{url}\n")

def main():
    print("--- 全エリア・カテゴリ巡回開始 ---")
    all_current_shops = []
    
    for url in TARGET_URLS:
        shops = get_latest_shops(url)
        all_current_shops.extend(shops)
        time.sleep(2) # サーバー負荷軽減のため間隔を空ける
    
    if not all_current_shops:
        print("店舗が一つも見つかりませんでした。アクセス制限の可能性があります。")
        return
    
    past_urls = load_past_shops()
    new_shops = []
    seen_urls = set()
    
    for shop in all_current_shops:
        if shop['url'] not in past_urls and shop['url'] not in seen_urls:
            new_shops.append(shop)
            seen_urls.add(shop['url'])
    
    if new_shops:
        print(f"\n★合計 {len(new_shops)} 件の新着店舗が見つかりました！")
        print("="*40)
        for shop in new_shops:
            print(f"店舗名: {shop['name']}")
            print(f"URL  : {shop['url']}")
            print("-" * 20)
        
        # 全てのURLを保存
        updated_urls = past_urls.union(set(s['url'] for s in all_current_shops))
        save_shops(updated_urls)
    else:
        print("\n新着店舗はありませんでした。")

if __name__ == "__main__":
    main()
