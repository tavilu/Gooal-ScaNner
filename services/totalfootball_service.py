import os, httpx, asyncio

RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "totalfootball-api.p.rapidapi.com")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")

BASE_URL = f"https://{RAPIDAPI_HOST}/api/match/living/stream"

async def get_live_matches():
    if not RAPIDAPI_KEY:
        print("TotalFootball service: RAPIDAPI_KEY not set in env, returning []")
        return []

    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(BASE_URL, headers=headers)
            print("TotalFootball status:", r.status_code)
            text = r.text[:500]
            print("TotalFootball raw:", text)
            r.raise_for_status()
            data = r.json()
            matches = []
            # Find candidate list in response
            candidates = []
            if isinstance(data, dict):
                for key in ("result","matches","data","response"):
                    v = data.get(key)
                    if v:
                        candidates = v if isinstance(v, list) else v.get("matches", []) or v
                        break
            if not candidates and isinstance(data, list):
                candidates = data
            for item in candidates:
                try:
                    match_id = item.get("id") or item.get("match_id") or item.get("fixture_id")
                    home = (item.get("home") or {}).get("name") or item.get("home_name") or (item.get("teams") or {}).get("home")
                    away = (item.get("away") or {}).get("name") or item.get("away_name") or (item.get("teams") or {}).get("away")
                    home_score = (item.get("scores") or {}).get("home") or item.get("home_score") or (item.get("goals") or {}).get("home") or 0
                    away_score = (item.get("scores") or {}).get("away") or item.get("away_score") or (item.get("goals") or {}).get("away") or 0
                    minute = item.get("minute") or item.get("time") or (item.get("status") or {}).get("minute")
                    matches.append({
                        "id": match_id,
                        "home_name": home,
                        "away_name": away,
                        "home_score": home_score,
                        "away_score": away_score,
                        "minute": minute
                    })
                except Exception:
                    continue
            return matches
    except httpx.HTTPStatusError as he:
        print("TotalFootball HTTP error:", he.response.status_code, he.response.text[:300])
    except Exception as e:
        print("TotalFootball error:", e)
    return []