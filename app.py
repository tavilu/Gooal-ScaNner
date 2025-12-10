from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import threading
import time
import requests

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# ============================================
# POLLING THREAD (não trava o Render)
# ============================================

def polling_loop():
    while True:
        try:
            # Exemplo simples — depois substituímos pelos jogos reais
            print("🔄 Polling ativo... buscando partidas")
            
            # Aqui você chama suas APIs reais:
            # response = requests.get("https://api-football-url")
            # processa resposta...

        except Exception as e:
            print("Erro no polling:", e)

        time.sleep(10)  # intervalo seguro para Render


@app.on_event("startup")
def start_polling_thread():
    thread = threading.Thread(target=polling_loop, daemon=True)
    thread.start()
    print("🚀 Thread de polling iniciada com sucesso")


# ============================================
# ROTAS
# ============================================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok", "service": "gooal-scanner"}

