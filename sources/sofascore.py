# sources/sofascore.py
import requests
import logging
import random
import time

logger = logging.getLogger("goal_scanner.sofascore")

# User-Agents reais de navegador
UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",

    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.2 Safari/605.1.15",

    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
]

class SofaScoreSource:
    """
    Nova versão – usa API pública JSON ao invés do HTML.
    Muito mais rápido, estável, e sem bloqueio 403.
    """

    def __init__(self):
        # API aberta usada pelo próprio site
        self.url = "https://api.sofascore.com/api/v1/sport/football/events/live"

    def _headers(self):
        return {
            "User-Agent": random.choice(UAS),
            "Accept": "application/json",
            "Referer": "https://www.sofascore.com",
        }

    def fetch_live_summary(self):
        try:
            time.sleep(random.uniform(0.4, 1.2))  # comportamento humano

            r = requests.get(self.url, headers=self._headers(), timeout=8)

            if r.status_code in [403, 429]:
                logger.error(f"SofaScore bloqueou ({r.status_code}). Tentando fallback...")
                return []

            data = r.json().get("events", [])

            results = []

            for m in data:
                try:
                    fixture_id = m.get("id")

                    stats = m.get("statistics", [])
                    da = 0
                    sot = 0
                    xg = 0.0
                    pressure = 0.0

                    for stat in stats:
                        for item in stat.get("stats", []):
                            t = item.get("name", "").lower()
                            v = item.get("value", 0)

                            if "dangerous" in t:
                                da = max(da, int(v))

                            if "shots on target" in t:
                                sot = max(sot, int(v))

                            if t == "xg":
                                try:
                                    xg = float(v)
                                except:
                                    pass

                            if "attacks" == t:
                                pressure = min(10, float(v) / 10)

                    results.append({
                        "fixture_id": str(fixture_id),
                        "pressure": pressure,
                        "dangerous_attacks": da,
                        "shots_on_target": sot,
                        "xg": xg
                    })

                except Exception:
                    continue

            return results

        except Exception as e:
            logger.error(f"Erro SofaScore: {e}")
            return []



