import asyncio
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from analisador import Analyzer
from fontes.apifootball import ApiFootballSource
from fontes.flashscore import FlashScoreSource

logger = logging.getLogger("goal_scanner")
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Inicializa suas fontes de dados
apifoot = ApiFootballSource()
flash = FlashScoreSource()

# Inicializa o analisador com as fontes
analyzer = Analyzer(sources=[flash, apifoot])

POLL_NORMAL = 15  # intervalo normal em segundos
POLL_TURBO = 5    # intervalo turbo (ao detectar jogo ao vivo)

current_interval = POLL_NORMAL
polling_task = None

async def polling_loop():
    global current_interval
    logger.info("SMART POLLING: loop iniciado")
    while True:
        try:
            analyzer.run_cycle()
            has_live = False
            if hasattr(apifoot, 'detect_live_games'):
                has_live = apifoot.detect_live_games()[0]
            current_interval = POLL_TURBO if has_live else POLL_NORMAL
            logger.info(f"Intervalo atual: {current_interval}s")
        except Exception as e:
            logger.error(f"Erro no loop de polling: {e}")
        await asyncio.sleep(current_interval)

@app.on_event("startup")
async def startup_event():
    global polling_task
    logger.info("Iniciando polling em background...")
    polling_task = asyncio.create_task(polling_loop())

@app.on_event("shutdown")
async def shutdown_event():
    global polling_task
    logger.info("Encerrando polling...")
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass

@app.get("/", response_class=JSONResponse)
async def home():
    return {"status": "Gooal Scanner online"}

@app.get("/api/health")
async def health():
    return {"status": "ok", "poll_interval": current_interval}

@app.get("/api/scan")
async def scan():
    analyzer.run_cycle()
    return {"status": "scan_triggered"}

@app.get("/api/live")
async def live():
    return analyzer.get_recent_signals()



