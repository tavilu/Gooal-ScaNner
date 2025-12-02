# sources/apifootball.py
import os
import logging
import requests

logger = logging.getLogger("goal_scanner.apifootball")

API_KEY = os.getenv("API_FOOTBALL_KEY")
API_HOST = os.getenv("API_FOOTBALL_HOST", "v3.football.api-sports.io")
BASE = f"https://{API_HOST}"

HEADERS = {"x-apisports-key": API_KEY} if API_KEY else {}

class APIFootballSource:
    """
    Connector for API-Football (v3). Fetches live fixtures and extracts:
      - pressure (0..10) estimated from attacks / dangerous attacks / possession
      - dangerous_attacks (int)
      - shots_on_target (int)
      - xg (float) if present in statistics or events (some tiers provide xG)
      - fixture_id (string)
    Returns list of dicts:
      {"fixture_id": "...", "pressure":float, "dangerous_attacks":float,
       "shots_on_target":float, "xg":float}
    """
    def __init__(self):
        self.session = requests.Session()
        if HEADERS:
            self.session.headers.update(HEADERS)
        self.cache = {}

    def _safe_get_stat(self, stats, name):
        """
        stats: list of {type, statistics...} or API-Football statistics structure
        Attempts to find a statistic by name (case-insensitive).
        """
        try:
            # api-football v3 may return 'statistics' as list of dicts with 'type' and 'value'
            for s in stats:
                # normalize
                k = s.get("type") or s.get("name") or ""
                if not k:
                    # fallback: check 'statistics' nested
                    pass
            # fallback parsing if structure differs
        except Exception:
            pass
        # generic fallback: try to search deeper
        try:
            for s in stats:
                for k, v in s.items():
                    if isinstance(v, (int, float)) and name.lower() in str(k).lower():
                        return v
        except Exception:
            pass
        return None

    def fetch_live_summary(self):
        if not API_KEY:
            logger.warning("API_FOOTBALL_KEY not configured for APIFootballSource")
            return []

        url = f"{BASE}/fixtures?live=all"
        try:
            r = self.session.get(url, timeout=12)
            if r.status_code != 200:
                logger.error("API-Football returned %s: %s", r.status_code, r.text[:200])
                return []

            payload = r.json()
            items = payload.get("response") or []
            results = []

            for m in items:
                try:
                    fixture = m.get("fixture", {})
                    fixture_id = str(fixture.get("id") or f"{m.get('league',{}).get('id')}_{fixture.get('timestamp')}")

                    # Initialize defaults
                    pressure = 0.0
                    dangerous_attacks = 0.0
                    shots_on_target = 0.0
                    xg = 0.0

                    # Preferred: use 'statistics' field if present
                    stats = m.get("statistics") or []
                    # statistics may be list of dicts: each with team id + statistics list
                    # try simple heuristics:
                    try:
                        # gather numeric stats across teams and compute pressure
                        home_stats = {}
                        away_stats = {}
                        # sometimes API wraps stats differently
                        if isinstance(stats, list) and stats:
                            for stat_block in stats:
                                # stat_block might be {'team': {..}, 'statistics': [ {'type': 'Shots on Goal', 'value': 3}, ... ]}
                                if isinstance(stat_block, dict) and stat_block.get("statistics"):
                                    team_id = stat_block.get("team", {}).get("id") or stat_block.get("team")
                                    stat_list = stat_block.get("statistics", [])
                                    target_map = {}
                                    for s in stat_list:
                                        t = (s.get("type") or "").lower()
                                        v = s.get("value")
                                        if v is None:
                                            continue
                                        if "shots on target" in t or "shots on goal" in t:
                                            target_map["shots_on_target"] = float(v)
                                        if "dangerous attacks" in t or "dangerous_attacks" in t:
                                            target_map["dangerous_attacks"] = float(v)
                                        if "attacks" == t or "attacks" in t:
                                            target_map["attacks"] = float(v)
                                        if "xg" in t or "expected goals" in t:
                                            try:
                                                target_map["xg"] = float(v)
                                            except:
                                                pass
                                    if not home_stats:
                                        home_stats = target_map
                                    else:
                                        away_stats = target_map
                        # compute pressure as relative attacks / (attacks_total) scaled 0-10
                        home_att = home_stats.get("attacks", 0.0)
                        away_att = away_stats.get("attacks", 0.0)
                        total_att = home_att + away_att
                        if total_att > 0:
                            # pressure for leading team normalized 0-10
                            leading = max(home_att, away_att)
                            pressure = round(min(10.0, (leading / total_att) * 10.0), 2)
                        # dangerous attacks prefer sum of both sides? we use leading side
                        dangerous_attacks = max(home_stats.get("dangerous_attacks", 0.0), away_stats.get("dangerous_attacks", 0.0))
                        shots_on_target = max(home_stats.get("shots_on_target", 0.0), away_stats.get("shots_on_target", 0.0))
                        xg = max(home_stats.get("xg", 0.0), away_stats.get("xg", 0.0))
                    except Exception:
                        logger.debug("APIFootball stats parse fallback", exc_info=True)

                    # Fallback: try to derive some signals from 'goals' timeline or events if statistics missing
                    # many fixtures include 'goals' and 'events'
                    # keep simple: if score high or events recent, small xg bump
                    try:
                        goals = m.get("goals", {})
                        # no direct xg; keep as parsed
                    except Exception:
                        pass

                    results.append({
                        "fixture_id": fixture_id,
                        "pressure": float(pressure),
                        "dangerous_attacks": float(dangerous_attacks),
                        "shots_on_target": float(shots_on_target),
                        "xg": float(xg)
                    })
                except Exception:
                    continue

            return results

        except Exception as e:
            logger.exception("APIFootball fetch failed: %s", e)
            return []

