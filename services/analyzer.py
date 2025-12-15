def analyze(match, state):
    minute = match["minute"]

    # pressão fictícia baseada no tempo
    if minute > 55:
        state["pressure"] += 1

    alerts = []

    # jogo travado
    if (
        minute >= 70 and
        match["score"] == "0-0" and
        "stalled_game" not in state["alerts_sent"]
    ):
        alerts.append({
            "key": "stalled_game",
            "message": f"⏱ {minute}' — {match['home']} x {match['away']}\nJogo travado até agora."
        })

    # pressão final
    if (
        minute >= 78 and
        state["pressure"] >= 5 and
        "late_pressure" not in state["alerts_sent"]
    ):
        alerts.append({
            "key": "late_pressure",
            "message": f"🔥 {minute}' — {match['home']} pressiona forte no fim."
        })

    return alerts
