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
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-http2",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US"
        )
        page = context.new_page()

        print(f"[{TARGET_DATE}] 空き状況を確認中...")
        
        # アクセス成功するまで最大3回試行
        success = False
        for attempt in range(1, 4):
            try:
                print(f"アクセス試行 {attempt} 回目...")
                # wait_until="commit" で最速でレスポンスを受け取る
                page.goto(URL, wait_until="commit", timeout=40000)
                time.sleep(10)  # 画面上の要素がレンダリングされるのを待つ
                success = True
                break
            except Exception as e:
                print(f"試行 {attempt} 失敗: {e}")
                time.sleep(5)

        if not success:
            print("3回の試行すべてでアクセスに失敗しました。")
            browser.close()
            sys.exit(1)

        try:
            # 予約可能時間ボタン要素のテキストを取得
            available_times = page.locator("button[data-testid='time-slot-button']").all_text_contents()

            if available_times:
                times_str = ", ".join(available_times)
                msg = f"🎉 【トッポリーノ・テラス】空席が見つかりました！\n日付: {TARGET_DATE}\n人数: {PARTY_SIZE}名\n時間枠: {times_str}\n予約URL: {URL}"
                print(msg)
                send_notification(msg)
            else:
                print("現在、空き枠はありません（またはまだ読み込み中）。")
        except Exception as e:
            print(f"要素取得時のエラー: {e}")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    run()
