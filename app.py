from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncio
import requests
import time

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ================================
# TELEGRAM
# ================================
TELEGRAM_BOT_TOKEN = "8263777761:AAH9mlZyc3eswgxxhpC6WGT-gQuqzXuEFOI"
CHAT_ID = 233304451

def send_telegram(msg: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print("Erro ao enviar Telegram:", e)


# ================================
# API-FOOTBALL CONFIG
# ================================
API_KEY = "fb4b9c6f7a7cf10833165326d348d357"

def fetch_live_matches():
    """Chamada síncrona — usada dentro de task assíncrona."""
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    headers = {"x-apisports-key": API_KEY}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()

        # debug opcional:
        print("STATUS:", r.status_code)
        print("RAW:", str(data)[:200])

        return data.get("response", [])

    except Exception as e:
        print("Erro ao buscar jogos ao vivo:", e)
        return []


# ================================
# MONITORAMENTO / ALERTAS
# ================================
last_alert = {}

def analyze_match(match):
    global last_alert

    fixture = match["fixture"]
    teams = match["teams"]
    goals = match["goals"]

    event_id = fixture["id"]
    home = teams["home"]["name"]
    away = teams["away"]["name"]
    score = (goals["home"], goals["away"])

    now = time.time()

    # evita spam
    if event_id not in last_alert or now - last_alert[event_id] > 180:
        msg = (
            f"⚽ Jogo ao vivo:\n"
            f"{home} x {away}\n"
            f"Placar: {score[0]} - {score[1]}"
        )
        send_telegram(msg)
        last_alert[event_id] = now


# ================================
# BACKGROUND TASK ASSÍNCRONA
# ================================
async def polling_loop():
    await asyncio.sleep(5)  # espera o servidor subir totalmente

    print("🚀 Background task iniciada...")

    while True:
        matches = fetch_live_matches()

        print(f"🔄 {len(matches)} jogos ao vivo monitorados")

        for match in matches:
            analyze_match(match)

        await asyncio.sleep(15)  # pausa sem travar o servidor


@app.on_event("startup")
async def start_background():
    asyncio.create_task(polling_loop())
    print("✔ Background task registrada com sucesso!")


# ================================
# ROTAS
# ================================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "gooal-scanner"}


# ================================
# TELEGRAM WEBHOOK (opcional)
# ================================
@app.post(f"/webhook/{TELEGRAM_BOT_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    print("Mensagem do Telegram:", data)
    return {"ok": True}


