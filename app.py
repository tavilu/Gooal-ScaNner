# app.py - FastAPI backend for Goal Scanner

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import httpx
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------------------------------------------
# CONFIGURAÇÕES DO PROJETO
# -------------------------------------------------------------
API_SOURCES = {
    "apifootball": "https://apifootball.com/demo/api/matches",
    "sofascore": "https://api.sofascore.com/api/v1/sport/football/events/live",
    "flashscore": "https://flashscore-api.example.com/live",
}

intervalo_atual_global = 20  # segundos
jogos_cache = []
ultima_atualizacao = None

# -------------------------------------------------------------
# FUNÇÃO PRINCIPAL DE COLETA (POLLING INTELIGENTE)
# -------------------------------------------------------------
async def fetch_all_sources():
    global jogos_cache, ultima_atualizacao

    resultados = []

    async with httpx.AsyncClient(timeout=10) as client:
        for nome, url in API_SOURCES.items():
            try:
                r = await client.get(url)
                resultados.append({
                    "fonte": nome,
                    "url": url,
                    "status": r.status_code,
                    "dados": r.json() if r.status_code == 200 else None
                })
            except Exception as e:
                resultados.append({
                    "fonte": nome,
                    "url": url,
                    "status": "erro",
                    "erro": str(e)
                })

    jogos_cache = resultados
    ultima_atualizacao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return resultados


# -------------------------------------------------------------
# ROTAS PRINCIPAIS
# -------------------------------------------------------------
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "intervalo": intervalo_atual_global,
        "ultima": ultima_atualizacao
    })


@app.get("/monitor")
def monitor(request: Request):
    return templates.TemplateResponse("monitor.html", {
        "request": request,
        "intervalo": intervalo_atual_global,
        "ultima": ultima_atualizacao
    })


# -------------------------------------------------------------
# ROTAS DE DADOS PARA O FRONT-END
# -------------------------------------------------------------
@app.get("/api/jogos")
async def api_jogos():
    await fetch_all_sources()
    return JSONResponse({
        "atualizado": ultima_atualizacao,
        "jogos": jogos_cache
    })


@app.post("/api/intervalo/{segundos}")
async def update_interval(segundos: int):
    global intervalo_atual_global
    intervalo_atual_global = segundos
    return {"novo_intervalo": segundos}


# -------------------------------------------------------------
# TASK BACKGROUND (POLLING AUTOMÁTICO)
# -------------------------------------------------------------
async def polling_task():
    while True:
        await fetch_all_sources()
        await asyncio.sleep(intervalo_atual_global)


@app.on_event("startup")
def start_background_task():
    asyncio.create_task(polling_task())



