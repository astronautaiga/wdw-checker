import os
import sys
import requests
from bs4 import BeautifulSoup

TARGET_DATE = os.environ.get("TARGET_DATE", "2026-11-29")
PARTY_SIZE = os.environ.get("PARTY_SIZE", "4")
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY")

# 監視したいWDW予約ページのURL
TARGET_URL = f"https://disneyworld.disney.go.com/dining/riviera-resort/topolinos-terrace/booking/?partySize={PARTY_SIZE}&date={TARGET_DATE}"

def send_notification(message):
    if not WEBHOOK_URL:
        print("Webhook URLが設定されていません。")
        return
    payload = {"content": message}
    try:
        requests.post(WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"通知送信エラー: {e}")

def run():
    if not SCRAPER_API_KEY:
        print("エラー: SCRAPER_API_KEY が設定されていません。")
        sys.exit(1)

    print(f"[{TARGET_DATE}] ScraperAPI経由でWDWの空き状況を確認中...")

    # ScraperAPIのエンドポイント設定
    # render=true を指定することでJavaScript実行後の動的要素（時間枠ボタン）を取得します
    payload = {
        'api_key': SCRAPER_API_KEY,
        'url': TARGET_URL,
        'render': 'true',
        'country_code': 'us'  # 米国IPからアクセスしてブロックを回避
    }

    try:
        response = requests.get('http://api.scraperapi.com', params=payload, timeout=90)
        
        if response.status_code != 200:
            print(f"ScraperAPIエラー: ステータスコード {response.status_code}")
            sys.exit(1)

        # BeautifulSoupでHTML解析
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 予約可能時間ボタン要素を抽出
        time_buttons = soup.find_all("button", {"data-testid": "time-slot-button"})
        available_times = [btn.get_text(strip=True) for btn in time_buttons]

        if available_times:
            times_str = ", ".join(available_times)
            msg = f"🎉 【トッポリーノ・テラス】空席が見つかりました！\n日付: {TARGET_DATE}\n人数: {PARTY_SIZE}名\n時間枠: {times_str}\n予約URL: {TARGET_URL}"
            print(msg)
            send_notification(msg)
        else:
            print("現在、空き枠はありません。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
