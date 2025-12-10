from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import threading
import time
import requests

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# =====================================================
# CONFIGURAÇÕES DO TELEGRAM
# =====================================================

TELEGRAM_BOT_TOKEN = "8263777761:AAH9mlZyc3eswgxxhpC6WGT-gQuqzXuEFOI"
CHAT_ID = 233304451

def send_telegram(msg: str):
    """Envia mensagem para o Telegram."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print("Erro ao enviar Telegram:", e)

# =====================================================
# CONFIGURAÇÕES DA API-FOOTBALL
# =====================================================

API_KEY = "fb4b9c6f7a7cf10833165326d348d357" 

def get_live_matches():
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    headers = {
        "fb4b9c6f7a7cf10833165326d348d357": API_KEY
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("response", [])
    except Exception as e:
        print("Erro ao buscar jogos ao vivo:", e)
        return []

# =====================================================
# LÓGICA DE ALERTA
# =====================================================

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
    if event_id not in last_alert or now - last_alert[event_id] > 180:
        msg = (
            f"⚽ Jogo ao vivo:\n"
            f"{home} x {away}\n"
            f"Placar: {score[0]} - {score[1]}"
        )
        send_telegram(msg)
        last_alert[event_id] = now

# =====================================================
# THREAD DE POLLING
# =====================================================

def polling_loop():
    while True:
        matches = get_live_matches()
        print(f"🔄 {len(matches)} jogos ao vivo monitorados")
        for match in matches:
            analyze_match(match)
        time.sleep(15)

@app.on_event("startup")
def start_thread():
    thread = threading.Thread(target=polling_loop, daemon=True)
    thread.start()
    print("🚀 Polling iniciado...")

# =====================================================
# ROTAS FASTAPI
# =====================================================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
def health():
    return {"status": "ok", "service": "gooal-scanner"}

# =====================================================
# WEBHOOK DO TELEGRAM (opcional)
# =====================================================

@app.post(f"/webhook/{TELEGRAM_BOT_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    print("Mensagem do Telegram:", data)
    return {"ok": True}

