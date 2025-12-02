# sources/bet365.py
import os
import logging
import requests
import time

logger = logging.getLogger("goal_scanner.bet365")

# Prefer using an odds provider (TheOddsAPI) for market moves.
# If you really want to read Bet365 live UI, use Playwright/Selenium with a residential proxy
# and emulate human browser. Implementing that here is possible but operationally heavy.

THEODDS_KEY = os.getenv("ODDS_API_KEY")
THEODDS_REGION = os.getenv("ODDS_REGION", "eu")
THEODDS_MARKETS = os.getenv("ODDS_MARKETS", "h2h,totals")

class Bet365Source:
    """
    Bet365Source tries to get market-movement signals.
    Implementation strategy:
      1) Try to get from TheOddsAPI (recommended)
      2) If not available and you request, switch to a headless browser implementation
    """
    def __init__(self):
        self.cache = {}
        self.session = requests.Session()

    def _fetch_from_theodds(self):
        if not THEODDS_KEY:
            return []
        url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds?regions={THEODDS_REGION}&markets={THEODDS_MARKETS}&apiKey={THEODDS_KEY}"
        try:
            r = self.session.get(url, timeout=10)
            if r.status_code != 200:
                logger.debug("TheOdds fetch error %s", r.status_code)
                return []
            data = r.json()
            result = []
            for m in data:
                fid = str(m.get("id") or (m.get("home_team","")+m.get("away_team","")))
                # compute an odds_delta similar to OddsSource (normalized 0-10)
                bookmakers = m.get("bookmakers",[])
                if not bookmakers:
                    continue
                b = bookmakers[0]
                markets = b.get("markets",[])
                total_m = next((x for x in markets if x.get("key")=="totals"), None)
                if not total_m: continue
                outcomes = total_m.get("outcomes",[])
                over = next((o for o in outcomes if o.get("name","").lower()=="over"), None)
                if not over: continue
                cur = float(over["price"])
                prev = self.cache.get(fid, cur)
                delta = max(0, prev - cur)
                normalized = min(10, delta*5) if delta>0 else 0
                self.cache[fid] = cur
                result.append({"fixture_id": fid, "odds_delta": normalized})
            return result
        except Exception:
            logger.exception("Bet365/TheOdds fetch failed")
            return []

    def fetch_live_summary(self):
        # Prefer TheOdds provider
        data = self._fetch_from_theodds()
        # Map to analyzer expected shape: we'll return items with odds_delta under key 'odds_delta'
        mapped = []
        for it in data:
            mapped.append({
                "fixture_id": it["fixture_id"],
                "odds_delta": it["odds_delta"]
            })
        return mapped
