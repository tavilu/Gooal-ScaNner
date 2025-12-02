# app.py – SMART POLLING PRO
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from analyzer import Analyzer
from sources.apifootball import APIFootballSource
from sources.sofascore import SofaScoreSource
from sources.flashscore import FlashScoreSource
from sources.bet365 import Bet365Source
from sources.odds import OddsSource
from notifier import Notifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("goal_scanner")

POLL_NORMAL = 60       # sem jogos
POLL_TURBO = 12        # com jogos ao vivo
current_interval = POLL_NORMAL

# Initialize sources
apifoot = APIFootballSource()
sof = SofaScoreSource()
flash = FlashScoreSource()
bet = Bet365Source()
odds = OddsSource()

notifier = Notifier()
analyzer = Analyzer(sources=[apifoot, sof, flash, bet, odds], notifier=notifier)

app = FastAPI(title="Goal Scanner - Smart Polling PRO")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = BackgroundScheduler()
job = None


def update_polling_interval(has_live_games: bool, api_limited: bool):
    global current_interval, job

    if api_limited:
        new_interval = POLL_NORMAL
    else:
        new_interval = POLL_TURBO if has_live_games else POLL_NORMAL

    if new_interval != current_interval:
        current_interval = new_interval
        if job:
            scheduler.remove_job("main_job")
        scheduler.add_job(
            analyzer.run_cycle,
            "interval",
            seconds=current_interval,
            max_instances=1,
            id="main_job"
        )
        logger.info(f"SMART POLLING ALTERADO → {current_interval}s")


@app.on_event("startup")
def startup_event():
    global job
    logger.info("Iniciando scheduler em modo SMART POLLING...")
    job = scheduler.add_job(
        analyzer.run_cycle,
        "interval",
        seconds=current_interval,
        max_instances=1,
        id="main_job"
    )
    scheduler.start()


@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown(wait=False)


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


# Hook para receber sinais do APIFootball
@app.post("/api/smart_update")
def smart_update(has_live_games: bool, api_limited: bool):
    update_polling_interval(has_live_games, api_limited)
    return {"updated": True, "new_interval": current_interval}
