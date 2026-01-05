# services/simulator_service.py
import random

# estado único do simulador (memória)
_matches = {
    1: {
        "id": 1,
        "home": "Time A",
        "away": "Time B",
        "minute": 0,
        "score": "0-0"
    }
}

def get_live_matches():
    match = _matches[1]

    # avança o minuto (1 a 3 por ciclo)
    match["minute"] += random.randint(1, 3)

    # chance de gol (25%)
    if random.random() < 0.25:
        home, away = map(int, match["score"].split("-"))
        if random.random() > 0.5:
            home += 1
        else:
            away += 1
        match["score"] = f"{home}-{away}"

    return [match]

