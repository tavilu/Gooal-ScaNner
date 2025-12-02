# sources/apifootball.py – Smart Polling PRO
import os
import logging
import requests

logger = logging.getLogger("goal_scanner.apifootball")

API_KEY = os.getenv("API_FOOTBALL_KEY")
API_HOST = "v3.football.api-sports.io"
BASE = f"https://{API_HOST}"

HEADERS = {"x-apisports-key": API_KEY} if API_KEY else {}

class APIFootballSource:
    def __init__(self):
        self.session = requests.Session()
        if HEADERS:
            self.session.headers.update(HEADERS)
        self.last_live_count = 0

    def detect_live_games(self):
        try:
            url = f"{BASE}/fixtures?live=all"
            r = self.session.get(url, timeout=10)

            if r.status_code == 429:
                logger.warning("API-Football: RATE LIMIT atingido!")
                return None, True

            if r.status_code != 200:
                logger.error("Erro API-Football: %s - %s", r.status_code, r.text[:200])
                return [], False

            data = r.json().get("response", [])
            return data, False

        except:
            return None, False

    def fetch_live_summary(self):
        live_data, limited = self.detect_live_games()

        if limited:
            # API limit reached → fallback
            return {"__smart": {"has_live": False, "limited": True}}

        if live_data is None:
            return {"__smart": {"has_live": False, "limited": False}}

        has_live = len(live_data) > 0
        summary = {"__smart": {"has_live": has_live, "limited": False}}
        results = []

        for m in live_data:
            try:
                fid = str(m["fixture"]["id"])
                stats = m.get("statistics", [])

                pressure = 0.0
                da = 0
                sot = 0
                xg = 0.0

                # Parse statistics
                try:
                    for block in stats:
                        for s in block.get("statistics", []):
                            t = s.get("type", "").lower()
                            v = s.get("value", 0)

                            if "dangerous attacks" in t:
                                da = max(da, int(v))
                            if "shots on target" in t or "shots on goal" in t:
                                sot = max(sot, int(v))
                            if "xg" in t:
                                try:
                                    xg = max(xg, float(v))
                                except:
                                    pass
                            if "attacks" == t:
                                # pressure heuristic
                                pressure = min(10, float(v) / 10)

                except:
                    pass

                results.append({
                    "fixture_id": fid,
                    "pressure": pressure,
                    "dangerous_attacks": da,
                    "shots_on_target": sot,
                    "xg": xg
                })

            except:
                continue

        summary["data"] = results
        return summary


