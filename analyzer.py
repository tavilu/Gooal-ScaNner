# analyzer.py – Smart Polling PRO compatible
import time
import logging
import requests

from collections import defaultdict, deque

logger = logging.getLogger("goal_scanner.analyzer")

WINDOW = 20  # ~3 minutos para TURBO (12s)

W_PRESSURE = 2.5
W_DA = 2.8
W_SOT = 3.2
W_XG = 18.0

class Analyzer:
    def __init__(self, sources, notifier):
        self.sources = sources
        self.notifier = notifier
        self.history = defaultdict(lambda: deque(maxlen=WINDOW))
        self.alerts = []

    def run_cycle(self):
        logger.info("→ Cycle Started")

        smart_has_live = False
        smart_limited = False

        merged = {}

        for s in self.sources:
            try:
                data = s.fetch_live_summary()

                # Smart Polling Feedback
                if isinstance(data, dict) and "__smart" in data:
                    smart_has_live = data["__smart"]["has_live"]
                    smart_limited = data["__smart"]["limited"]
                    data = data.get("data", [])

                for item in data:
                    fid = item["fixture_id"]

                    if fid not in merged:
                        merged[fid] = item
                    else:
                        for k in ["pressure", "dangerous_attacks", "shots_on_target", "xg"]:
                            merged[fid][k] = max(merged[fid][k], item[k])

            except:
                logger.exception("Falha source")

        # Enviar feedback SMART POLLING para app
        try:
            requests.post("http://localhost:8000/api/smart_update",
                          json={"has_live_games": smart_has_live,
                                "api_limited": smart_limited})
        except:
            pass

        # Process analyzer
        for fid, item in merged.items():
            self.history[fid].append(item)
            hist = list(self.history[fid])

            if not hist:
                continue

            pressure = sum(h["pressure"] for h in hist) / len(hist)
            da = sum(h["dangerous_attacks"] for h in hist) / len(hist)
            sot = sum(h["shots_on_target"] for h in hist) / len(hist)
            xg = sum(h["xg"] for h in hist) / len(hist)

            raw = (
                pressure * W_PRESSURE +
                da * W_DA +
                sot * W_SOT +
                xg * W_XG
            )

            gpi = min(100, raw * 1.4)

            level = "VERDE"
            if gpi >= 66:
                level = "VERMELHO"
            elif gpi >= 36:
                level = "AMARELO"

            alert = {
                "fixture": fid,
                "gpi": round(gpi, 2),
                "level": level,
                "data": item,
                "ts": int(time.time())
            }

            self.alerts.append(alert)
            if len(self.alerts) > 300:
                self.alerts.pop(0)

            try:
                self.notifier.send_alert(alert)
            except:
                pass

        logger.info("→ Cycle Finished")

    def get_alerts(self):
        return list(reversed(self.alerts[-200:]))

    def status_report(self):
        return {"sources": [type(s).__name__ for s in self.sources],
                "alerts": len(self.alerts)}


