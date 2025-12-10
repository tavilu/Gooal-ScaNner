from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import threading
import time
import requests
import json

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# =====================================================
# CONFIGURAÇÕES DO TELEGRAM
# =====================================================

TELEGRAM_BOT_TOKEN = 8263777761:AAH9mlZyc3eswgxxhpC6WGT-gQuqzXuEFOI
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
# FUNÇÃO PARA BUSCAR JOGOS AO VIVO
# =====================================================

def get_live_matches():
    """Busca todos os jogos ao vivo via SofaScore."""
    url = "https://api.sofascore.com/api/v1/sport/football/events/live"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        return data.get("events", [])
    except:
        return []


# =====================================================
# LÓGICA DE ANÁLISE DE MOMENTOS PERIGOSOS
# =====================================================

last_alert = {}  # evita spam de jogos repetidos

def analyze_match(match):
    """Analisa um jogo individual e dispara alerta."""
    global last_alert

    event_id = match["id"]
    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]
    score = match.get("homeScore", {}).get("current", 0), match.get("awayScore", {}).get("current", 0)

    stats = match.get("statistics", {})

    # Valores importantes
    attacks = stats.get("attacks")
    dangerous = stats.get("dangerousAttacks")
    on_target = stats.get("onTarget")
    corners = stats.get("corners")
    
    # Só alerta se tiver estatísticas
    if not attacks or not dangerous:
        return

    # ================================
    # LÓGICA PRINCIPAL DO GOL IMINENTE
    # ================================
    danger_total = dangerous.get("home", 0) + dangerous.get("away", 0)
    attacks_total = attacks.get("home", 0) + attacks.get("away", 0)

    # Critérios combinados (ajustado para ser assertivo)
    gol_iminente = (
        danger_total >= 18 or
        (dangerous.get("home", 0) >= 10) or
        (dangerous.get("away", 0) >= 10) or
        (attacks_total >= 35) or
        (on_target and (on_target.get("home", 0) >= 3 or on_target.get("away", 0) >= 3)) or
        (corners and (corners.get("home", 0) >= 5 or corners.get("away", 0) >= 5))
    )

    # Anti-spam: só 1 alerta por 3 minutos por jogo
    now = time.time()
    if gol_iminente:
        if event_id not in last_alert or now - last_alert[event_id] > 180:
            msg = (
                f"🔥 POSSÍVEL GOL IMINENTE!\n"
                f"{home} x {away}\n"
                f"Placar: {score[0]} - {score[1]}\n"
                f"Ataques perigosos totais: {danger_total}\n"
                f"Ataques: {attacks_total}"
            )
            send_telegram(msg)
            last_alert[event_id] = now


# =====================================================
# THREAD DE POLLING (EXECUÇÃO CONTÍNUA)
# =====================================================

def polling_loop():
    while True:
        try:
            matches = get_live_matches()

            print(f"🔄 {len(matches)} jogos ao vivo monitorados")

            for match in matches:
                analyze_match(match)

        except Exception as e:
            print("Erro no loop:", e)

        time.sleep(10)


@app.on_event("startup")
def start_thread():
    print("🚀 Polling iniciado...")
    thread = threading.Thread(target=polling_loop, daemon=True)
    thread.start()


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


