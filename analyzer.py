# analyzer.py
import os
import time
import logging
from typing import List, Dict, Any

logger = logging.getLogger("goal_scanner.analyzer")

# Weights / thresholds from env (tunable)
W_PRESSURE = float(os.getenv("W_PRESSURE", "2.0"))
W_DANGER = float(os.getenv("W_DANGER", "1.5"))
W_SHOTSOT = float(os.getenv("W_SHOTSOT", "1.8"))
W_ODDS = float(os.getenv("W_ODDS", "3.0"))
W_XG = float(os.getenv("W_XG", "2.0"))

GPI_GREEN = float(os.getenv("GPI_GREEN", "40"))
GPI_YELLOW = float(os.getenv("GPI_YELLOW", "70"))

STATE_FILE = os.getenv("STATE_FILE", "state_gpi.json")

import json
def _load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def _save_state(s):
    with open(STATE_FILE, "w") as f:
        json.dump(s, f, indent=2)

class Analyzer:
    def __init__(self, sources: List[Any], notifier):
        self.sources = sources
        self.notifier = notifier
        self.state = _load_state()
        self.alerts = []

    def compute_gpi(self, merged: Dict[str, Any]) -> float:
        # merged expected keys: pressure, dangerous_attacks, shots_ot, odds_delta, xg
        p = merged.get("pressure", 0)
        d = merged.get("dangerous_attacks", 0)
        s = merged.get("shots_on_target", 0)
        o = merged.get("odds_delta", 0)  # positive means odds moved in favor => stronger signal
        x = merged.get("xg", 0)
        gpi = (p * W_PRESSURE) + (d * W_DANGER) + (s * W_SHOTSOT) + (o * W_ODDS) + (x * W_XG)
        return max(0, min(100, gpi))

    def classify(self, gpi: float):
        if gpi >= GPI_YELLOW:
            return "VERMELHO"
        if gpi >= GPI_GREEN:
            return "AMARELO"
        return "VERDE"

    def merge_sources(self, raw_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        # naive merge: average / sum values; sources must normalize
        out = {"pressure":0,"dangerous_attacks":0,"shots_on_target":0,"odds_delta":0,"xg":0,"count":0}
        for r in raw_list:
            out["pressure"] += r.get("pressure",0)
            out["dangerous_attacks"] += r.get("dangerous_attacks",0)
            out["shots_on_target"] += r.get("shots_on_target",0)
            out["odds_delta"] += r.get("odds_delta",0)
            out["xg"] += r.get("xg",0)
            out["count"] += 1
        if out["count"]>0:
            for k in ["pressure","dangerous_attacks","shots_on_target","odds_delta","xg"]:
                out[k] = out[k] / out["count"]
        return out

    def run_cycle(self):
        logger.info("Analyzer cycle started")
        try:
            raws = []
            for src in self.sources:
                try:
                    data = src.fetch_live_summary()
                    if data:
                        raws.extend(data if isinstance(data,list) else [data])
                except Exception as e:
                    logger.exception("Source fetch failed: %s", e)
            # group by fixture id
            by_fixture = {}
            for item in raws:
                fid = str(item.get("fixture_id") or item.get("id") or item.get("fixture"))
                by_fixture.setdefault(fid, []).append(item)

            for fid, items in by_fixture.items():
                merged = self.merge_sources(items)
                gpi = self.compute_gpi(merged)
                level = self.classify(gpi)
                logger.info("Fixture %s -> GPI=%.1f Level=%s merged=%s", fid, gpi, level, merged)

                prev = self.state.get(fid, {})
                prev_level = prev.get("level")
                # create alert only on escalation or every N seconds
                if prev_level != level or (time.time() - prev.get("time",0) > 60):
                    alert = {
                        "fixture": fid,
                        "gpi": gpi,
                        "level": level,
                        "merged": merged,
                        "time": int(time.time())
                    }
                    self.alerts.append(alert)
                    self.notifier.notify_level(alert)
                    self.state[fid] = {"level": level, "time": int(time.time())}
            _save_state(self.state)
        except Exception:
            logger.exception("Analyzer failed")

    def get_alerts(self):
        return list(reversed(self.alerts[-200:]))

    def status_report(self):
        return {"sources": [type(s).__name__ for s in self.sources], "alerts_count": len(self.alerts)}
