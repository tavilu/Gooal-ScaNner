# app.py
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from analyzer import Analyzer
from sources.sofascore import SofaScoreSource
from sources.flashscore import FlashScoreSource
from sources.bet365 import Bet365Source
from sources.odds import OddsSource
from sources.apifootball import APIFootballSource
from notifier import Notifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("goal_scanner")

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "8"))  # you chose 8s

# prepare sources (APIFootball prioritized)
apifoot = APIFootballSource()
sof = SofaScoreSource()
flash = FlashScoreSource()
bet = Bet365Source()
odds = OddsSource()

notifier = Notifier()
analyzer = Analyzer(sources=[apifoot, sof, flash, bet, odds], notifier=notifier)

app = FastAPI(title="Goal Scanner - Full Professional")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

scheduler = BackgroundScheduler()

@app.on_event("startup")
def startup_event():
    logger.info("Starting scheduler")
    scheduler.add_job(analyzer.run_cycle, "interval", seconds=POLL_INTERVAL, max_instances=1)
    scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown(wait=False)

@app.get("/api/health")
def health():
    return {"status":"ok"}

@app.post("/api/scan")
def scan():
    analyzer.run_cycle()
    return {"status":"scan_triggered"}

@app.get("/api/status")
def status():
    return analyzer.status_report()

@app.get("/api/last_alerts")
def last_alerts():
    return analyzer.get_alerts()


