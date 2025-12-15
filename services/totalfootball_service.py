import os
import time
import requests

API_KEY = os.getenv("RAPIDAPI_KEY")
API_HOST = "totalfootball-api.p.rapidapi.com"

LAST_429 = None
BLOCK_TIME = 60 * 60  # 1 hora


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
        print("⛔ TotalFootball bloqueado temporariamente (429)")
        return []

    url = "https://totalfootball-api.p.rapidapi.com/matches/live"

    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": API_HOST
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 429:
            LAST_429 = time.time()
            print("🚫 Cota excedida — pausando chamadas por 1h")
            return []

        response.raise_for_status()

        data = response.json()
        matches = data.get("response", [])

        normalized = [normalize_match(m) for m in matches]
        print(f"🔄 {len(normalized)} jogos ao vivo recuperados")

        return normalized

    except Exception as
