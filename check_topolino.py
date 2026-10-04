import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright

TARGET_DATE = os.environ.get("TARGET_DATE", "2026-11-29")
PARTY_SIZE = os.environ.get("PARTY_SIZE", "4")
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
        # HTTP/2エラー回避のための引数を追加
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-http2",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        print(f"[{TARGET_DATE}] 空き状況を確認中...")
        try:
            # 読み込み完了条件を domcontentloaded に変更してエラーを抑止
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(7)  # 動的コンテンツの読み込み待ち

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
