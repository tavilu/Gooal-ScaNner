from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncio, os, time
from services.totalfootball_service import get_live_matches
from services.telegram_service import send_telegram_message

app = FastAPI()
templates = Jinja2Templates(directory="templates")

LAST_NOTIFIED = {}

def format_msg(match: dict) -> str:
    minute = match.get("minute") or match.get("time") or "-"
    return (f"⚽ POSSÍVEL OPORTUNIDADE - Jogo ao vivo\n"
            f"{match.get('home_name')} x {match.get('away_name')}\n"
            f"Placar: {match.get('home_score')} - {match.get('away_score')}\n"
            f"Minuto: {minute}")

async def polling_task():
    await asyncio.sleep(3)
    print("🚀 Polling background task started (TotalFootball)")
    while True:
        try:
            matches = await get_live_matches()
            print(f"🔄 {len(matches)} jogos ao vivo recebidos (TotalFootball)")
            for m in matches:
                match_id = str(m.get("id"))
                total_goals = int(m.get("home_score") or 0) + int(m.get("away_score") or 0)
                if total_goals >= 1 and match_id not in LAST_NOTIFIED:
                    msg = format_msg(m)
                    await send_telegram_message(msg)
                    LAST_NOTIFIED[match_id] = time.time()
        except Exception as e:
            print("Error in polling_task:", e)
        await asyncio.sleep(15)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(polling_task())
    print("✔ Background polling task scheduled (TotalFootball)")

@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get('/health')
def health():
    return {"status":"ok", "service":"gooal-scanner-totalfootball"}