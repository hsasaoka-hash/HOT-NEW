import requests
from bs4 import BeautifulSoup
import time
import os
import json

# --- 設定 ---
# ターゲットURL（リラクゼーションカテゴリの特定エリア一覧ページ）
# ユーザーが後で変更しやすいように環境変数または直接書き換え可能にする
TARGET_URL = os.getenv("TARGET_URL", "https://beauty.hotpepper.jp/relax/svcSA/macAC/salon/")
DATA_FILE = "past_shops.txt"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "") # 通知先のWebhook URL

# User-Agentの設定（サーバー負荷軽減とアクセス拒否回避のため）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_latest_shops(url):
    """ターゲットURLから店舗名とURLのリストを取得する"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        # 負荷軽減のための待機
        time.sleep(1)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        shop_list = []
        
        # 店舗名とURLが含まれる要素を抽出
        # 調査結果に基づき、h3タグ内のaタグでslnHを含むものを対象とする
        for h3 in soup.find_all('h3'):
            a = h3.find('a')
            if a and 'slnH' in a.get('href', ''):
                name = a.text.strip()
                # URLからクエリパラメータを除去して正規化（重複検知の精度向上のため）
                raw_url = a.get('href').split('?')[0]
                if raw_url.startswith('/'):
                    full_url = f"https://beauty.hotpepper.jp{raw_url}"
                else:
                    full_url = raw_url
                
                shop_list.append({"name": name, "url": full_url})
        
        return shop_list
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

def load_past_shops():
    """過去に検知した店舗URLをファイルから読み込む"""
    if not os.path.exists(DATA_FILE):
        return set()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_shops(urls):
    """最新の店舗URLリストをファイルに保存する"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for url in sorted(urls):
            f.write(f"{url}\n")

def send_notification(new_shops):
    """新着店舗を通知する（Webhook）"""
    if not WEBHOOK_URL:
        print("Webhook URL is not set. Skipping notification.")
        for shop in new_shops:
            print(f"New Shop Found: {shop['name']} - {shop['url']}")
        return

    message_content = "【ホットペッパービューティー新着掲載通知】\n"
    for shop in new_shops:
        message_content += f"・{shop['name']}\n  {shop['url']}\n"

    # Discord/Slack/LINE Notify 共通で使えるシンプルなJSON形式（必要に応じて調整）
    payload = {"content": message_content, "text": message_content}
    
    try:
        res = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        res.raise_for_status()
        print("Notification sent successfully.")
    except Exception as e:
        print(f"Failed to send notification: {e}")

def main():
    print(f"Checking for new shops at: {TARGET_URL}")
    
    # 1. 最新の店舗リストを取得
    current_shops = get_latest_shops(TARGET_URL)
    if not current_shops:
        print("No shops found or error occurred.")
        return

    # 2. 過去のデータを読み込み
    past_urls = load_past_shops()
    
    # 3. 差分（新着店舗）を抽出
    new_shops = []
    for shop in current_shops:
        if shop['url'] not in past_urls:
            new_shops.append(shop)
    
    # 4. 通知とデータ更新
    if new_shops:
        print(f"Found {len(new_shops)} new shops!")
        send_notification(new_shops)
        
        # 全てのURLをマージして保存
        all_urls = past_urls.union(set(shop['url'] for shop in current_shops))
        save_shops(all_urls)
    else:
        print("No new shops found.")

if __name__ == "__main__":
    main()
