from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from services.simulator_service import get_live_matches
from services.match_state import get_state
from services.change_detector import has_changed
from services.analyzer import analyze
from services.telegram_service import send_telegram_message

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/run-scan")
def run_scan():
    try:
        matches = get_live_matches()
    except Exception as e:
        return {"status": "error", "detail": str(e)}

    alerts_sent = 0

    for match in matches:
        try:
            state = get_state(match["id"])

            if has_changed(match, state):
                alerts = analyze(match, state)

                for alert in alerts:
                    send_telegram_message(alert["message"])
                    state["alerts_sent"].add(alert["key"])
                    alerts_sent += 1

                state["last_minute"] = match.get("minute")
                state["last_score"] = match.get("score")

        except Exception as e:
            print(f"Erro na partida {match.get('id')}: {e}")

    return {
        "status": "ok",
        "matches": len(matches),
        "alerts_sent": alerts_sent
    }


@app.get("/test-telegram")
def test_telegram():
    send_telegram_message("🚀 Gooal Scanner conectado com sucesso!")
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

