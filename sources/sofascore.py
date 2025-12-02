# sources/sofascore.py
import requests
import logging
from bs4 import BeautifulSoup
import random
import time

logger = logging.getLogger("goal_scanner.sofascore")

# Headers reais de navegador para evitar 403
HEADERS = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/121.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.google.com"
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.google.com"
    }
]


class SofaScoreSource:
    def __init__(self):
        self.url = "https://www.sofascore.com/football/live"

    def fetch_live_summary(self):
        """
        Retorna eventos básicos para o analisador.
        Formato:
        [
            {
                "fixture_id": "ID",
                "pressure": float,
                "dangerous_attacks": int,
                "shots_on_target": int,
                "xg": float
            }
        ]
        """

        header = random.choice(HEADERS)

        try:
            r = requests.get(self.url, headers=header, timeout=10)
            if r.status_code == 403:
                logger.error("Sofascore bloqueou (403). Trocando headers...")
                time.sleep(1)
                return []

            soup = BeautifulSoup(r.text, "lxml")

            matches = []

            # Seletores melhorados
            games = soup.select(".event-row, .sc-hLBbgP")
            for g in games:
                try:
                    team_home = g.select_one(".team-home, .sc-kpOJdI")
                    team_away = g.select_one(".team-away, .sc-fBWQRz")
                    attack = g.select_one(".dangerous-attacks, .sc-hKwDqJ")
                    pressure = g.select_one(".attack-momentum, .sc-bYEvPH")
                    shots = g.select_one(".shots-on-target, .sc-hiCbrj")

                    fixture = (
                        (team_home.text.strip() if team_home else "") +
                        (team_away.text.strip() if team_away else "")
                    )

                    matches.append({
                        "fixture_id": fixture or str(random.random()),
                        "pressure": float(pressure.text.replace("%", "")) if pressure else 0.0,
                        "dangerous_attacks": int(attack.text or 0) if attack else 0,
                        "shots_on_target": int(shots.text or 0) if shots else 0,
                        "xg": 0.0
                    })
                except:
                    continue

            return matches

        except Exception as e:
            logger.error(f"Erro SofaScore: {e}")
            return []


