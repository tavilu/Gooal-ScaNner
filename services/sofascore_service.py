import requests

URL = "https://api.sofascore.com/api/v1/sport/football/events/live"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

def normalize_match(raw):
    return {
        "id": raw["id"],
        "home": raw["homeTeam"]["name"],
        "away": raw["awayTeam"]["name"],
        "minute": raw.get("time", {}).get("currentPeriodStartTimestamp", 0),
        "score": f'{raw["homeScore"]["current"]}-{raw["awayScore"]["current"]}'
    }

def get_live_matches():
    resp = requests.get(URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    data = resp.json()
    events = data.get("events", [])

    return [normalize_match(e) for e in events]
