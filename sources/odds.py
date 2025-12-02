# sources/odds.py
import os
import logging
import requests
from datetime import datetime

logger = logging.getLogger("goal_scanner.odds")

API_KEY = os.getenv("ODDS_API_KEY")
REGION = "eu"  # regiões suportadas: eu, uk, us, au
MARKETS = "h2h,totals"  # buscamos odds + over/under

class OddsSource:
    def __init__(self):
        if not API_KEY:
            logger.warning("ODDS_API_KEY não configurada!")
        self.cache = {}  # armazenar odds anteriores por jogo
        
    def fetch_live_summary(self):
        """
        Retorna lista de objetos no formato:
        {
            "fixture_id": "ID_JOGO",
            "odds_delta": float (0-10)
        }
        
        odds_delta = quanto caiu a odd de OVER → maior = gol iminente
        """
        if not API_KEY:
            return []
        
        url = (
            f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds"
            f"?regions={REGION}&markets={MARKETS}&apiKey={API_KEY}"
        )
        
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                logger.error("Erro OddsAPI: %s %s", r.status_code, r.text)
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

                casa = bookmakers[0]  # primeira casa disponível
                mercados = casa.get("markets", [])
                
                total_market = next((m for m in mercados if m["key"] == "totals"), None)
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

                # queda = mercado prevendo gol → delta positivo
                delta = previous_odd - current_odd

                # normalização para a escala 0–10
                if delta <= 0:
                    normalized = 0
                else:
                    normalized = min(10, delta * 5)

                self.cache[fixture_id] = current_odd

                results.append({
                    "fixture_id": fixture_id,
                    "odds_delta": normalized
                })
            
            return results
        
        except Exception as e:
            logger.exception("Falha OddsAPI: %s", e)
            return []

