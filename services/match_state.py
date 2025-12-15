MATCH_STATES = {}

def get_state(match_id):
    if match_id not in MATCH_STATES:
        MATCH_STATES[match_id] = {
            "last_minute": None,
            "last_score": None,
            "alerts_sent": set()
        }
    return MATCH_STATES[match_id]
