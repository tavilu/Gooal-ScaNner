import asyncio
analyzer = Analyzer(sources=[flash, apifoot])


polling_task = None


async def polling_loop():
global current_interval
logger.info("SMART POLLING: loop iniciado")


while True:
try:
analyzer.run_cycle()


# tentativa de detectar live via API/flash
has_live = apifoot.detect_live_games()[0] if hasattr(apifoot, 'detect_live_games') else None


if has_live:
current_interval = POLL_TURBO
else:
current_interval = POLL_NORMAL


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
logger.info("Encerrando polling...")
if polling_task:
polling_task.cancel()




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
