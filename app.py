from services.match_state import get_state
from services.change_detector import has_changed
from services.analyzer import analyze
from services.telegram_service import send_telegram_message

async def poll_matches():
    while True:
        matches = get_live_matches()  # TotalFootball (leve)

        for match in matches:
            state = get_state(match["id"])

            if has_changed(match, state):
                alerts = analyze(match, state)

                for alert in alerts:
                    send_telegram_message(alert["message"])
                    state["alerts_sent"].add(alert["key"])

                state["last_minute"] = match["minute"]
                state["last_score"] = match["score"]

        await asyncio.sleep(300)  # 5 minutos
