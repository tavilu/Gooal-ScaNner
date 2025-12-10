from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import threading
import time
import httpx
import os

app = FastAPI()

templates = Jinja2Templates(directory="templates")

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


# ======================================================
# SEND MESSAGE
# ======================================================
async def send_message(chat_id, text):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text},
        )


# ======================================================
# POLLING THREAD
# ======================================================
def polling_loop():
    while True:
        try:
            print("🔄 Polling ativo... buscando partidas")

            # Exemplo de envio de evento automático (test)
            # Depois substituímos pelos alertas reais de gols
            # await send_message(SEU_CHAT_ID, "evento encontrado!")

        except Exception as e:
            print("Erro no polling:", e)

        time.sleep(10)  # intervalo seguro para Render


@app.on_event("startup")
async def start_polling_thread():
    # 🟦 Thread
    thread = threading.Thread(target=polling_loop, daemon=True)
    thread.start()
    print("🚀 Thread de polling iniciada")

    # 🟦 Registrar webhook automaticamente
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{TELEGRAM_API}/setWebhook?url={WEBHOOK_URL}")
        print("🔗 Webhook registrado:", WEBHOOK_URL, "->", r.json())


# ======================================================
# WEBHOOK ENDPOINT
# ======================================================
@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]

        # Responde sempre que alguém falar com o bot
        await send_message(chat_id, f"Recebido: {text}")

    return {"ok": True}


# ======================================================
# ROTAS DO SITE
# ======================================================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok", "service": "gooal-scanner"}

