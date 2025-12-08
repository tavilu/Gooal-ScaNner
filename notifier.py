import os
import logging
import requests
from notifier.telegram_notifier import TelegramNotifier  # importa seu telegram notifier

logger = logging.getLogger("goal_scanner.notifier")

ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID")
ONESIGNAL_API_KEY = os.getenv("ONESIGNAL_API_KEY")

class Notifier:
    def __init__(self):
        self.telegram = TelegramNotifier()

    def notify_level(self, alert):
        level = alert["level"]
        title = f"[{level}] Goal Scanner"
        msg = f"Fixture {alert['fixture']} — Level {level} — GPI {alert['gpi']:.1f}"

        if ONESIGNAL_API_KEY and ONESIGNAL_APP_ID:
            payload = {
                "app_id": ONESIGNAL_APP_ID,
                "included_segments": ["Subscribed Users"],
                "headings": {"en": title},
                "contents": {"en": msg},
                "data": {"type": "level_alert", "payload": alert}
            }
            try:
                r = requests.post(
                    "https://onesignal.com/api/v1/notifications",
                    headers={"Authorization": f"Basic {ONESIGNAL_API_KEY}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=10
                )
                logger.info("OneSignal %s -> %s", r.status_code, r.text)
            except Exception as e:
                logger.exception("OneSignal failed: %s", e)
        else:
            # Se OneSignal não está configurado, envia via Telegram
            try:
                self.telegram.send([alert])
                logger.info("Telegram notification sent")
            except Exception as e:
                logger.exception("Telegram notification failed: %s", e)

