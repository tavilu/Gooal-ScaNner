import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from services.simulator_service import get_live_matches
from services.match_state import get_state
from services.change_detector import has_changed
from services.analyzer import analyze
from services.telegram_service import send_telegram_message


# 🔹 APP PRIMEIRO (OBRIGATÓRIO)
app = FastAPI()
templates = Jinja2Templates(directory="templates")


# 🔹 HEALTHCHECK (Render)
@app.get("/health")
def health():
    return {"status": "ok"}


# 🔹 LOOP PRINCIPAL
async def poll_matches():
    print("🔥 Loop de simulação iniciado")

    while True:
        try:
            matches = get_live_matches()
        except Exception as e:
            print("Erro ao buscar partidas:", e)
            await asyncio.sleep(10)
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
                print(f"Erro na partida {match.get('id')}: {e}")

        await asyncio.sleep(30)


# 🔹 STARTUP EVENT (AGORA NO LUGAR CERTO)
@app.on_event("startup")
async def startup_event():
    print("🚀 Gooal Scanner iniciado (startup)")
    asyncio.create_task(poll_matches())


# 🔹 TESTE TELEGRAM
@app.get("/test-telegram")
def test_telegram():
    send_telegram_message("🚀 Gooal Scanner conectado com sucesso!")
    return {"ok": True}


# 🔹 FRONT
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

