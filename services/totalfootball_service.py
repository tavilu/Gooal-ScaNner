def normalize_match(raw):
    return {
        "id": raw["id"],
        "home": raw["homeTeam"]["name"],
        "away": raw["awayTeam"]["name"],
        "minute": raw.get("minute", 0),
        "score": f'{raw["score"]["home"]}-{raw["score"]["away"]}'
    }
