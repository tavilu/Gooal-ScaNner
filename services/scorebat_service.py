import requests

URL = "https://www.scorebat.com/video-api/v3/"

def normalize_match(raw):
    return {
        "id": raw["competition"]["id"] + "_" + raw["title"],
        "home": raw["side1"]["name"],
        "away": raw["side2"]["name"],
        "minute": 0,  # ScoreBat não fornece minuto
        "score": raw.get("score", "0-0")
    }

def get_live_matches():
    resp = requests.get(URL, timeout=20)
    resp.raise_for_status()

    data = resp.json()
    games = data.get("response", [])

    return [normalize_match(g) for g in games]
