# sources/apifootball.py
import os
import logging
import httpx


logger = logging.getLogger("goal_scanner.apifootball")
API_KEY = os.getenv("APIFOOTBALL_KEY")
BASE = "https://api-football-v1.p.rapidapi.com/v3"


class APIFootballSource:
def __init__(self):
self.headers = {
"x-rapidapi-host": "api-football-v1.p.rapidapi.com",
"x-rapidapi-key": API_KEY,
}


def detect_live_games(self):
"""Retorna (live_data, limited_flag)"""
if not API_KEY:
logger.warning("APIFOOTBALL_KEY ausente")
return ([], True)


try:
with httpx.Client(timeout=10) as c:
r = c.get(f"{BASE}/fixtures?live=all", headers=self.headers)
if r.status_code == 429:
logger.warning("API-Football: limit reached")
return ([], True)
if r.status_code != 200:
logger.error("API-Football erro %s", r.status_code)
return ([], True)


data = r.json().get("response", [])
return (data, False)
except Exception as e:
logger.error(f"Erro APIFootball: {e}")
return ([], True)


def fetch_stats_for_fixture(self, fixture_id):
try:
with httpx.Client(timeout=10) as c:
r = c.get(f"{BASE}/fixtures/statistics?h2h=false&fixture={fixture_id}", headers=self.headers)
if r.status_code != 200:
return None
return r.json().get("response", [])
except Exception as e:
logger.error(f"Erro APIFootball stats: {e}")
return None

