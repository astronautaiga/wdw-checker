import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright

TARGET_DATE = os.environ.get("TARGET_DATE", "2026-11-15")
PARTY_SIZE = os.environ.get("PARTY_SIZE", "2")
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

URL = f"https://disneyworld.disney.go.com/dining/riviera-resort/topolinos-terrace/booking/?partySize={PARTY_SIZE}&date={TARGET_DATE}"

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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print(f"[{TARGET_DATE}] 空き状況を確認中...")
        try:
            page.goto(URL, wait_until="networkidle", timeout=60000)
            time.sleep(5)

            available_times = page.locator("button[data-testid='time-slot-button']").all_text_contents()

            if available_times:
                times_str = ", ".join(available_times)
                msg = f"🎉 【トッポリーノ・テラス】空席が見つかりました！\n日付: {TARGET_DATE}\n人数: {PARTY_SIZE}名\n時間枠: {times_str}\n予約URL: {URL}"
                print(msg)
                send_notification(msg)
            else:
                print("現在、空き枠はありません。")
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    run()
