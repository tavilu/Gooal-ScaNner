# sources/odds.py
import os
import logging
import requests
from datetime import datetime

logger = logging.getLogger("goal_scanner.odds")

API_KEY = os.getenv("ODDS_API_KEY")
REGION = "eu"
MARKETS = "h2h,totals"


class OddsSource:
    """
    Versão ultra estável.
    Nunca trava o app e nunca polui o log com erro repetitivo
    (401, 403, limite estourado etc).
    """
    def __init__(self):
        self.enabled = bool(API_KEY)
        self.cache = {}

        if not API_KEY:
            logger.warning("OddsAPI desativada (ODDS_API_KEY ausente).")

    def fetch_live_summary(self):
        # Odds desativado → retorna vazio sem log
        if not self.enabled:
            return []

        url = (
            f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds"
            f"?regions={REGION}&markets={MARKETS}&apiKey={API_KEY}"
        )

        try:
            r = requests.get(url, timeout=6)

            # Erros mais comuns tratados silenciosamente
            if r.status_code == 401:
                logger.warning("OddsAPI: API KEY inválida ou créditos esgotados. Odds desativado.")
                self.enabled = False
                return []

            if r.status_code in (402, 403, 429):
                logger.warning(f"OddsAPI bloqueou/limitou ({r.status_code}). Desativando até próximo reboot.")
                self.enabled = False
                return []

            if r.status_code != 200:
                logger.error(f"OddsAPI retorno inesperado {r.status_code}: {r.text[:120]}")
                return []

            data = r.json()
            results = []

            for match in data:
                fixture_id = str(
                    match.get("id")
                    or (match.get("home_team", "") + match.get("away_team", ""))
                )

                bookmakers = match.get("bookmakers", [])
                if not bookmakers:
                    continue

                casa = bookmakers[0]
                markets = casa.get("markets", [])

                total_market = next((m for m in markets if m["key"] == "totals"), None)
                if not total_market:
                    continue

                outcomes = total_market.get("outcomes", [])
                if not outcomes:
                    continue

                over = next((o for o in outcomes if o["name"].lower() == "over"), None)
                if not over:
                    continue

                current_odd = float(over["price"])
                previous_odd = self.cache.get(fixture_id, current_odd)

                delta = previous_odd - current_odd

                # normalização para 0–10
                normalized = max(0, min(10, delta * 5))

                self.cache[fixture_id] = current_odd

                results.append({
                    "fixture_id": fixture_id,
                    "odds_delta": normalized,
                })

            return results

        except Exception as e:
            logger.error(f"OddsAPI falhou: {e}")
            return []

        
        
