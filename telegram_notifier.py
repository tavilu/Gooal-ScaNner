import os
import logging
import requests

logger = logging.getLogger("goal_scanner.telegram_notifier")

class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not self.token or not self.chat_id:
            logger.warning("Telegram BOT_TOKEN ou CHAT_ID não configurados!")

    def send(self, alerts):
        if not self.token or not self.chat_id:
            logger.warning("Telegram credentials missing, skipping notification.")
            return

        for alert in alerts:
            text = (
                f"⚽️ *Goal Scanner Alert*\n"
                f"Fixture: {alert.get('fixture_id', 'N/A')}\n"
                f"Score: {alert.get('score', 'N/A')}\n"
                f"Details: {alert.get('data', {})}"
            )
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            try:
                resp = requests.post(url, json=payload, timeout=10)
                if resp.status_code != 200:
                    logger.error(f"Telegram send failed: {resp.status_code} {resp.text}")
                else:
                    logger.info("Telegram notification sent")
            except Exception as e:
                logger.exception(f"Telegram send exception: {e}")

