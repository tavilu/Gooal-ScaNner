import os, httpx, asyncio
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")

async def send_telegram_message(text: str):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram not configured, skipping send")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, json=payload)
            if r.status_code != 200:
                print("Telegram send failed:", r.status_code, r.text[:200])
    except Exception as e:
        print("Telegram service exception:", e)