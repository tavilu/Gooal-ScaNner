from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import threading
import time
import requests

# =============================================================
# FASTAPI INIT
# =============================================================
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# =============================================================
# CONFIG TELEGRAM
# =============================================================
TELEGRAM_BOT_TOKEN = "8263777761:AAH9mlZyc3eswgxxhpC6WGT-gQuqzXuEFOI"
CHAT_ID = 233304451

def send_telegram(msg: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print("❌ Erro ao enviar mensagem no Telegram:", e)

# =============================================================
# CONFIG API-FOOTBALL
# =============================================================
API_KEY = "fb4b9c6f7a7cf10833165326d348d357"

def get_live_matches():
    url = "https://v3.football.api-sports.io/fixtures?live=all"

    headers = {
        "x-apisports-key": API_KEY,
        "x-apisports-host": "v3.football.api-sports.io"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        # Debug avançado
        print("STATUS:", response.status_code)
        print("RESPONSE HEADERS:", response.headers)
        print("RAW RESPONSE:", response.text[:300])

        response.raise_for_status()

        data = response.json()
        return data.get("response", [])

    except Exception as e:
        print("🔥 ERRO AO BUSCAR JOGOS AO VIVO:", e)
        return []

# =============================================================
# ANÁLISE E ALERTAS
# =============================================================
last_alert = {}  # Guarda timestamp do último alerta por jogo

def analyze_match(match):
    global last_alert

    fixture = match["fixture"]
    teams = match["teams"]
    goals = match["goals"]

    event_id = fixture["id"]
    home = teams["home"]["name"]
    away = teams["away"]["name"]
    score_home = goals["home"]
    score_away = goals["away"]

    now = time.time()

    # Evita alertas repetidos
    if event_id not in last_alert or now - last_alert[event_id] > 180:

        msg = (
            f"⚽ Jogo ao vivo:\n"
            f"{home} x {away}\n"
            f"Placar: {score_home} - {score_away}"
        )

        send_telegram(msg)
        last_alert[event_id] = now

# =============================================================
# LOOP DE POLLING
# =============================================================
def polling_loop():
    while True:
        matches = get_live_matches()
        print(f"🔄 {len(matches)} jogos ao vivo monitorados")

        for match in matches:
            analyze_match(match)

        time.sleep(10)

@app.on_event("startup")
def start_background_thread():
    thread = threading.Thread(target=polling_loop, daemon=True)
    thread.start()
    print("🚀 Polling iniciado...")

# =============================================================
# ROTAS WEB
# =============================================================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
def health():
    return {"status": "ok", "service": "gooal-scanner"}

@app.post(f"/webhook/{TELEGRAM_BOT_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    print("📩 Mensagem recebida no webhook:", data)
    return {"ok": True}
