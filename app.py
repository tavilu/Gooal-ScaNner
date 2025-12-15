import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from services.sofascore_service import get_live_matches
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
        matches = get_live_matches()

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


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(poll_matches())


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )
