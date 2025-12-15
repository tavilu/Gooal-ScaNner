def send_alerts(alerts, state):
    for alert in alerts:
        send_telegram_message(alert["message"])
        state["alerts_sent"].add(alert["key"])
