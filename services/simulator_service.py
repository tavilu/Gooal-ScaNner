import random
import time

# jogos simulados fixos
_MATCHES = {
    1: {"home": "Flamengo", "away": "Palmeiras"},
    2: {"home": "Real Madrid", "away": "Barcelona"},
    3: {"home": "Manchester City", "away": "Arsenal"},
}

# estado interno da simulação
_STATE = {}

def _init_match(match_id):
    _STATE[match_id] = {
        "minute": 0,
        "home_goals": 0,
        "away_goals": 0,
        "last_update": time.time()
    }

def get_live_matches():
    matches = []

    for match_id, teams in _MATCHES.items():
        if match_id not in _STATE:
            _init_match(match_id)

        state = _STATE[match_id]

        # avança tempo a cada chamada
        if time.time() - state["last_update"] > 20:
            state["minute"] += random.randint(1, 3)
            state["last_update"] = time.time()

            # chance de gol
            if random.random() < 0.15:
                if random.random() < 0.5:
                    state["home_goals"] += 1
                else:
                    state["away_goals"] += 1

        matches.append({
            "id": match_id,
            "home": teams["home"],
            "away": teams["away"],
            "minute": state["minute"],
            "score": f'{state["home_goals"]}-{state["away_goals"]}'
        })

    return matches
