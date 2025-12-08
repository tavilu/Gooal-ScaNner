# app.py – SMART POLLING PRO (Render Optimized)

import os
import logging
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from analyzer import Analyzer
from sources.apifootball import APIFootballSource
from sources.sofascore import SofaScoreSource
from sources.flashscore import FlashScoreSource
from sources.bet365 import Bet365Source
from sources.odds import OddsSource
from notifier import Notifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("goal_scanner")

POLL_NORMAL = 60
POLL_TURBO = 12
current_interval = POLL_NORMAL

# ---------------------------------------------------
# 1) CRIAÇÃO DO APP
# ---------------------------------------------------
app = FastAPI(title="Goal Scanner - Smart Polling PRO")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ---------------------------------------------------
# 2) SISTEMA INTERNO
# ---------------------------------------------------

# Initialize sources
apifoot = APIFootballSource()
sof = SofaScoreSource()
flash = FlashScoreSource()
bet = Bet365Source()
odds = OddsSource()

notifier = Notifier()
analyzer = Analyzer(
    sources=[apifoot, sof, flash, bet, odds],
    notifier=notifier
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------
# 3) NOVO SMART POLLING SEM APSCHEDULER
# ---------------------------------------------------

polling_task = None

async def polling_loop():
    global current_interval

    logger.info("SMART POLLING: loop iniciado!")

    while True:
        try:
            # roda análise
            analyzer.run_cycle()

            # detecta se há jogos ao vivo
            live_data, limited = apifoot.detect_live_games()

            if limited:
                current_interval = POLL_NORMAL
            else:
                current_interval = POLL_TURBO if (live_data and len(live_data) > 0) else POLL_NORMAL

            logger.info(f"[SMART POLLING] Intervalo atual: {current_interval}s")

        except Exception as e:
            logger.error(f"Erro no loop de polling: {e}")

        await asyncio.sleep(current_interval)


@app.on_event("startup")
async def startup_event():
    global polling_task
    logger.info("Iniciando SMART POLLING otimizado para Render...")

    # cria task assíncrona
    polling_task = asyncio.create_task(polling_loop())


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Encerrando loop...")
    if polling_task:
        polling_task.cancel()



# ---------------------------------------------------
# 4) ROTAS DE API
# ---------------------------------------------------

@app.get("/api/fixtures")
def fixtures():
    try:
        live_data, limited = apifoot.detect_live_games()

        if limited:
            return {"error": "API limit reached", "fixtures": []}

        if live_data is None:
            return []

        fixtures_list = []
        for m in live_data:
            try:
                fid = str(m["fixture"]["id"])
                stats = m.get("statistics", [])

                da = 0
                sot = 0
                pressure = 0.0
                xg = 0.0

                for block in stats:
                    for s in block.get("statistics", []):
                        t = s.get("type", "").lower()
                        v = s.get("value", 0)

                        if "dangerous attacks" in t:
                            da = max(da, int(v))
                        if "shots on target" in t or "shots on goal" in t:
                            sot = max(sot, int(v))
                        if "xg" in t:
                            try:
                                xg = max(xg, float(v))
                            except:
                                pass
                        if t == "attacks":
                            pressure = min(10, float(v) / 10)

                fixtures_list.append({
                    "fixture_id": fid,
                    "pressure": pressure,
                    "dangerous_attacks": da,
                    "shots_on_target": sot,
                    "xg": xg
                })

            except:
                continue

        return fixtures_list

    except Exception as e:
        return {"error": str(e)}


@app.get("/api/health")
def health():
    return {"status": "ok", "poll_interval": current_interval}


@app.post("/api/scan")
def scan():
    analyzer.run_cycle()
    return {"status": "scan_triggered"}


@app.get("/api/status")
def status():
    return analyzer.status_report()


@app.get("/api/last_alerts")
def last_alerts():
    return analyzer.get_alerts()

