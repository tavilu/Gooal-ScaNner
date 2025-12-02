# analyzer.py (API-Football aware, GPI 0-100)
import time
import logging
from collections import defaultdict, deque

logger = logging.getLogger("goal_scanner.analyzer")

# WINDOW: 3 minutes / polls at 8s => ~22 entries
WINDOW_SIZE = int(180 / 8)  # configurable if POLL_INTERVAL changes

# PROFESSIONAL WEIGHTS (tuneable via env in future)
W_PRESSURE = 2.5
W_DA = 2.8
W_SOT = 3.2
W_XG = 18.0
W_ODDS = 4.5
TREND_MULT = 3.0

MIN_EVENTS_REQUIRED = 1

class Analyzer:
    def __init__(self, sources, notifier):
        self.sources = sources
        self.notifier = notifier
        self.history = defaultdict(lambda: deque(maxlen=WINDOW_SIZE))
        self.alerts = []

    def _collect_from_sources(self):
        """
        Ask every source for their summaries and group results per fixture_id.
        Expect each source to return list of dicts with keys:
          fixture_id, pressure, dangerous_attacks, shots_on_target, xg, odds_delta (optional)
        """
        raw = []
        for s in self.sources:
            try:
                data = s.fetch_live_summary() or []
                # ensure list
                if isinstance(data, dict):
                    data = [data]
                raw.append(data)
            except Exception as e:
                logger.exception("Source fetch error: %s", e)
        # flatten
        flat = []
        for block in raw:
            if not isinstance(block, list):
                continue
            for item in block:
                if not isinstance(item, dict):
                    continue
                # normalize keys
                entry = {
                    "fixture_id": str(item.get("fixture_id") or item.get("id") or item.get("fixture")),
                    "pressure": float(item.get("pressure", 0.0)),
                    "dangerous_attacks": float(item.get("dangerous_attacks", 0.0)),
                    "shots_on_target": float(item.get("shots_on_target", 0.0)),
                    "xg": float(item.get("xg", 0.0)),
                    "odds_delta": float(item.get("odds_delta", 0.0)) if item.get("odds_delta") is not None else 0.0
                }
                flat.append(entry)
        # merge by fixture_id: keep maximum signals among sources (conservative merge)
        merged = {}
        for e in flat:
            fid = e["fixture_id"]
            if fid not in merged:
                merged[fid] = e.copy()
            else:
                for k in ["pressure","dangerous_attacks","shots_on_target","xg","odds_delta"]:
                    merged[fid][k] = max(merged[fid].get(k,0.0), e.get(k,0.0))
        return list(merged.values())

    def compute_gpi_from_history(self, hist):
        """
        hist: list of entries (dict) ordered oldest->newest
        returns dict {gpi, level}
        """
        if not hist or len(hist) < 1:
            return {"gpi": 0.0, "level": "VERDE"}

        # compute averages
        pressure = sum(h["pressure"] for h in hist)/len(hist)
        da = sum(h["dangerous_attacks"] for h in hist)/len(hist)
        sot = sum(h["shots_on_target"] for h in hist)/len(hist)
        xg = sum(h["xg"] for h in hist)/len(hist)
        odds = sum(h.get("odds_delta",0.0) for h in hist)/len(hist)

        # short-term trend: compare last vs 3-back
        trend = 0.0
        if len(hist) >= 4:
            short_now = hist[-1]["pressure"] + hist[-1]["dangerous_attacks"]
            short_before = hist[-4]["pressure"] + hist[-4]["dangerous_attacks"]
            trend = max(0.0, short_now - short_before)

        # raw score
        raw = (pressure * W_PRESSURE) + (da * W_DA) + (sot * W_SOT) + (xg * W_XG) + (odds * W_ODDS) + (trend * TREND_MULT)

        # normalize to 0..100 with a heuristic scale factor
        gpi = min(100.0, raw * 1.4)

        # levels
        if gpi >= 66:
            level = "VERMELHO"
        elif gpi >= 36:
            level = "AMARELO"
        else:
            level = "VERDE"

        return {"gpi": round(gpi,2), "level": level}

    def run_cycle(self):
        logger.info("Analyzer cycle started")
        try:
            merged = self._collect_from_sources()
            for item in merged:
                fid = item["fixture_id"]
                # push to history
                self.history[fid].append(item)

                # ignore fixtures with no informative data
                hist = list(self.history[fid])
                # require at least one non-zero indicator
                if all((h["pressure"]==0 and h["dangerous_attacks"]==0 and h["shots_on_target"]==0 and h.get("odds_delta",0)==0 and h["xg"]==0) for h in hist):
                    continue

                gpi_info = self.compute_gpi_from_history(hist)
                alert = {
                    "fixture": fid,
                    "gpi": gpi_info["gpi"],
                    "level": gpi_info["level"],
                    "merged": item,
                    "time": int(time.time())
                }

                # dedupe: avoid spamming same level frequently
                last = self.alerts[-1] if self.alerts else None
                if last and last["fixture"] == fid and last["level"] == alert["level"]:
                    # if same level within 30s, skip
                    if time.time() - last["time"] < 30:
                        continue

                # store alert and notify
                self.alerts.append(alert)
                if len(self.alerts) > 500:
                    self.alerts.pop(0)
                try:
                    # notifier should implement send_alert(alert)
                    self.notifier.send_alert(alert)
                except Exception:
                    logger.exception("Notifier failed")

            logger.info("Analyzer cycle completed")
        except Exception:
            logger.exception("Analyzer.run_cycle failed")

    def status_report(self):
        return {
            "sources": [type(s).__name__ for s in self.sources],
            "alerts_count": len(self.alerts)
        }

    def get_alerts(self):
        return list(reversed(self.alerts[-200:]))

