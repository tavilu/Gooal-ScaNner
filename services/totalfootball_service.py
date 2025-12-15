import os
import time
import requests

API_KEY = os.getenv("RAPIDAPI_KEY")
API_HOST = "totalfootball-api.p.rapidapi.com"

LAST_429 = None
BLOCK_TIME = 60 * 60


def normalize_match(raw):
    return {
        "id": raw.get("id"),
        "home": raw["homeTeam"]["name"],
        "away": raw["awayTeam"]["name"],
        "minute": raw.get("minute", 0),
        "score": f'{raw["score"]["home"]}-{raw["score"]["away"]}'
    }


def can_call_api():
    global LAST_429
    if LAST_429 is None:
        return True
    return (time.time() - LAST_429) > BLOCK_TIME


def get_live_matches():
    global LAST_429

    if not can_call_api():
        print("⛔ API bloqueada temporariamente")
        return []

    url = "https://totalfootball-api.p.rapidapi.com/matches/live"

    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": API_HOST
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)

        if r.status_code == 429:
            LAST_429 = time.time()
            print("🚫 Cota excedida")
            return []

        r.raise_for_status()
        data = r.json()

        matches = data.get("response", [])
        return [normalize_match(m) for m in matches]

    except Exception as e:
        print("Erro TotalFootball:", e)
        return []
