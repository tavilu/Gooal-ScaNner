def has_changed(match, state):
    return (
        state["last_minute"] != match["minute"] or
        state["last_score"] != match["score"]
    )
