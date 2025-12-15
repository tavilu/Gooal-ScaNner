import asyncio
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


async def poll_matches():
    while True:
        try:
            matches = get_live_matches()
        except Exception as e:
            print("Erro ao buscar partidas:", e)
            await asyncio.sleep(600)  # backoff pesado
            continue

        for match in matches:
            try:
                state = get_state(match["id"])

                if has_changed(match, state):
                    alerts = analyze(match, state)

                    for alert in alerts:
                        send_telegram_message(alert["message"])
                        state["alerts_sent"].add(alert["key"])

                    state["last_minute"] = match.get("minute")
                    state["last_score"] = match.get("score")

            except Exception as e:
                print(f"Erro ao processar partida {match.get('id')}: {e}")

        await asyncio.sleep(600)  # 10 minutos (economia total)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(poll_matches())


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

