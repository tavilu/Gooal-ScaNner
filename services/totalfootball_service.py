import os
import requests

API_URL = "https://totalfootball-api.p.rapidapi.com/fixtures"

HEADERS = {
    "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
    "X-RapidAPI-Host": "totalfootball-api.p.rapidapi.com"
}

def normalize_match(raw):
    return {
        "id": raw["id"],
        "home": raw["homeTeam"]["name"],
        "away": raw["awayTeam"]["name"],
        "minute": raw.get("minute", 0),
        "score": f'{raw["score"]["home"]}-{raw["score"]["away"]}'
    }

def get_live_matches():
    try:
        response = requests.get(
            API_URL,
            headers=HEADERS,
            params={"live": "all"},
            timeout=15
        )
        response.raise_for_status()

        data = response.json()
        return [normalize_match(m) for m in data.get("response", [])]

    except Exception as e:
        print(f"Erro TotalFootball: {e}")
        return []

    
