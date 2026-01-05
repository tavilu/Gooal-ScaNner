# services/match_state.py

STATES = {}

def get_state(match_id):
    if match_id not in STATES:
        STATES[match_id] = {
            "last_minute": None,
            "last_score": None,
            "alerts_sent": set()
        }
    return STATES[match_id]
