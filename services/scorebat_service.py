import requests
import os

API_KEY = os.getenv("SCOREBAT_API_KEY")

URL = f"https://www.scorebat.com/video-api/v3/feed/?token={API_KEY}"

def get_live_matches():
    try:
        resp = requests.get(URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        matches = []
        for item in data.get("response", []):
            if item.get("competition") and item.get("videos"):
                matches.append({
                    "id": item["title"],
                    "home": item["side1"]["name"],
                    "away": item["side2"]["name"],
                    "minute": None,
                    "score": None
                })

        return matches

    except Exception as e:
        print("Erro Scorebat:", e)
        return []
