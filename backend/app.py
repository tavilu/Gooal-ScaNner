# backend/app.py
import os, time, json, logging, re
from typing import Dict, Any, List
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
API_FOOTBALL_HOST = os.getenv("API_FOOTBALL_HOST", "v3.football.api-sports.io")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "12"))
STATE_FILE = os.getenv("STATE_FILE", "goal_bot_state.json")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID")
ONESIGNAL_API_KEY = os.getenv("ONESIGNAL_API_KEY")
ONESIGNAL_REST_URL = "https://onesignal.com/api/v1/notifications"
MIN_MATCH_MINUTE = int(os.getenv("MIN_MATCH_MINUTE", "8"))
MAX_MATCH_MINUTE = int(os.getenv("MAX_MATCH_MINUTE", "90"))
DELTA_SHOTS_OT_THRESHOLD = int(os.getenv("DELTA_SHOTS_OT_THRESHOLD", "2"))
DELTA_ATTACKS_THRESHOLD = int(os.getenv("DELTA_ATTACKS_THRESHOLD", "6"))
DELTA_SHOTS_TOTAL_THRESHOLD = int(os.getenv("DELTA_SHOTS_TOTAL_THRESHOLD", "3"))

logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper()), format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("goal_signal_bot")

HEADERS = {"x-apisports-key": API_FOOTBALL_KEY, "Accept": "application/json"}
BASE_API = f"https://{API_FOOTBALL_HOST}"

app = FastAPI()
scheduler = BackgroundScheduler()

state: Dict[str, Any] = {"last_stats": {}, "last_alerts": {}, "fixtures_meta": {}}

def load_state() -> Dict[str, Any]:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return state

def save_state():
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def api_get(path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    url = BASE_API.rstrip("/") + "/" + path.lstrip("/")
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"Erro API GET {url} params={params} -> {e}")
        return {}

def flatten_stats(stats_response: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    out = {}
    for team_stats in stats_response:
        team = team_stats.get("team", {})
        team_id = team.get("id")
        stats = team_stats.get("statistics", [])
        sdict = {}
        for s in stats:
            t = s.get("type")
            v = s.get("value")
            try:
                if isinstance(v, str):
                    m = re.search(r"(\d+)", v)
                    if m:
                        sdict[t] = int(m.group(1))
                    else:
                        sdict[t] = 0
                else:
                    sdict[t] = int(v)
            except:
                sdict[t] = 0
        out[str(team_id)] = sdict
    return out

def send_onesignal_notification(headline: str, message: str, data: Dict[str, Any] = None):
    if not ONESIGNAL_APP_ID or not ONESIGNAL_API_KEY:
        logger.warning("OneSignal não configurado")
        return False
    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["Subscribed Users"],
        "headings": {"en": headline},
        "contents": {"en": message},
    }
    if data:
        payload["data"] = data
    try:
        r = requests.post(ONESIGNAL_REST_URL, headers={"Authorization": f"Basic {ONESIGNAL_API_KEY}", "Content-Type": "application/json"}, json=payload, timeout=10)
        r.raise_for_status()
        logger.info("OneSignal push enviado: %s", r.json())
        return True
    except Exception as e:
        logger.error("Erro enviando OneSignal -> %s", e)
        return False

def get_live_fixtures():
    data = api_get("/fixtures", params={"live": "all"})
    if not data:
        return []
    return data.get("response", [])

def get_fixture_stats(fixture_id: int):
    data = api_get("/fixtures/statistics", params={"fixture": fixture_id})
    if not data:
        return []
    return data.get("response", [])

def compute_deltas(prev: Dict[str, Any], cur: Dict[str, Any]) -> Dict[str, Any]:
    deltas = {}
    for fixture_id, teams in cur.items():
        if fixture_id not in prev:
            deltas[fixture_id] = {}
            for team_id, stats in teams.items():
                deltas[fixture_id][team_id] = stats.copy()
        else:
            deltas[fixture_id] = {}
            for team_id, stats in teams.items():
                prev_stats = prev.get(fixture_id, {}).get(team_id, {})
                team_delta = {}
                for k, v in stats.items():
                    prev_v = prev_stats.get(k, 0)
                    try:
                        team_delta[k] = int(v) - int(prev_v)
                    except:
                        team_delta[k] = 0
                deltas[fixture_id][team_id] = team_delta
    return deltas

def poll_and_detect():
    try:
        fixtures = get_live_fixtures()
        if not fixtures:
            logger.debug("Nenhuma partida ao vivo encontrada")
            return

        cur_stats = {}

        for f in fixtures:
            fixture = f.get("fixture", {})
            fixture_id = str(fixture.get("id"))
            minute = fixture.get("status", {}).get("elapsed") or 0
            if minute < MIN_MATCH_MINUTE or minute > MAX_MATCH_MINUTE:
                continue
            stats_resp = get_fixture_stats(int(fixture_id))
            teams_stats = flatten_stats(stats_resp)
            if not teams_stats:
                continue
            cur_stats[fixture_id] = teams_stats
            state["fixtures_meta"][fixture_id] = {
                "home": f.get("teams", {}).get("home", {}).get("name"),
                "away": f.get("teams", {}).get("away", {}).get("name"),
                "minute": minute
            }

        deltas = compute_deltas(state.get("last_stats", {}), cur_stats)

        for fixture_id, teams in deltas.items():
            meta = state["fixtures_meta"].get(fixture_id, {})
            minute = meta.get("minute")
            for team_id, delta_stats in teams.items():
                shots_on_goal = delta_stats.get("Shots on Goal", 0) or delta_stats.get("Shots on target", 0) or 0
                attacks = delta_stats.get("Attacks", 0) or 0
                dangerous = delta_stats.get("Dangerous Attacks", 0) or 0
                shots_total = delta_stats.get("Shots", 0) or 0
                total_attack_delta = attacks + dangerous
                condition_shots_ot = shots_on_goal >= DELTA_SHOTS_OT_THRESHOLD
                condition_attacks = total_attack_delta >= DELTA_ATTACKS_THRESHOLD
                condition_shots_total = shots_total >= DELTA_SHOTS_TOTAL_THRESHOLD

                already_alerted = False
                alerts_for_fixture = state.get("last_alerts", {}).get(fixture_id, [])
                if alerts_for_fixture:
                    recent = alerts_for_fixture[-1]
                    if time.time() - recent.get("time", 0) < 60 and str(recent.get("team_id")) == str(team_id):
                        already_alerted = True

                if not already_alerted and ((condition_shots_ot and condition_attacks) or (condition_shots_ot and condition_shots_total)):
                    home = state["fixtures_meta"][fixture_id].get("home")
                    away = state["fixtures_meta"][fixture_id].get("away")
                    heading = "ALERTA: Oportunidade de gol"
                    message = f"{home} x {away} — minuto {minute} — pressão detectada. Shots on target Δ={shots_on_goal}, attacks Δ={total_attack_delta}"
                    logger.info("Sinal detectado: %s", message)
                    send_onesignal_notification(heading, message, data={"fixture_id": fixture_id, "minute": minute})
                    state.setdefault("last_alerts", {}).setdefault(fixture_id, []).append({"team_id": team_id, "time": int(time.time())})
        state["last_stats"] = cur_stats
        save_state()
    except Exception as e:
        logger.exception("Erro no poll_and_detect: %s", e)

scheduler.add_job(poll_and_detect, 'interval', seconds=POLL_INTERVAL)
scheduler.start()

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/api/health")
async def health():
    return JSONResponse({"status": "ok"})

@app.get("/api/fixtures")
async def api_fixtures():
    return JSONResponse({"fixtures": state.get("fixtures_meta", {}), "alerts": state.get("last_alerts", {})})

@app.post("/api/poll")
async def api_poll(background_tasks: BackgroundTasks):
    background_tasks.add_task(poll_and_detect)
    return JSONResponse({"status": "poll_started"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
