import time

MATCH_STATE = {}

def get_state(match_id):
    if match_id not in MATCH_STATE:
        MATCH_STATE[match_id] = {
            "created_at": time.time(),
            "last_minute": None,
            "last_score": None,
            "pressure": 0,
            "alerts_sent": set()
        }
    return MATCH_STATE[match_id]
