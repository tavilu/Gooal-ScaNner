# sources/sofascore.py
import os
import logging
import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any
import time

logger = logging.getLogger("goal_scanner.sofascore")

# Timeout / headers configuráveis via env
REQUEST_TIMEOUT = int(os.getenv("SOFASCORE_TIMEOUT", "8"))
USER_AGENT = os.getenv("SOFASCORE_UA",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36")

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

class SofaScoreSource:
    """
    Connector for SofaScore. This implementation:
    - Searches live matches page
    - For each match, tries to parse a summary of pressure/momentum/xG/shots
    Notes:
      - Sofascore changes layout from time to time.
      - If site blocks requests, migrate to Playwright/Selenium with real browser and proxies.
    """

    BASE_LIVE = "https://www.sofascore.com/football/live"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.cache = {}  # small cache for recently fetched fixtures

    def _get_live_matches_html(self) -> str:
        r = self.session.get(self.BASE_LIVE, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.text

    def _parse_fixture_list(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse the live page to obtain fixture URLs or IDs.
        Returns list of {'fixture_id': id, 'url': '/match/xxx'}
        """
        out = []
        soup = BeautifulSoup(html, "lxml")
        # Attempt to find links to live matches
        for a in soup.select("a[href*='/match/']"):
            href = a.get("href")
            # sofascore uses /sport/match/<id> or /<team>/match/...
            if not href:
                continue
            m = re.search(r"/match/([\w-]+)", href)
            if m:
                fixture_id = m.group(1)
                out.append({"fixture_id": fixture_id, "url": "https://www.sofascore.com" + href})
        # dedupe preserving order
        seen = set()
        unique = []
        for f in out:
            if f["fixture_id"] in seen:
                continue
            seen.add(f["fixture_id"])
            unique.append(f)
        return unique

    def _parse_match_page(self, html: str) -> Dict[str, Any]:
        """
        Try to extract:
          - pressure (0-10) estimated from momentum bars if available
          - dangerous_attacks (int)
          - shots_on_target (int)
          - xg (float) if displayed
        Returns a dict with keys used by analyzer.
        """
        soup = BeautifulSoup(html, "lxml")
        out = {"pressure": 0.0, "dangerous_attacks": 0.0, "shots_on_target": 0.0, "xg": 0.0}

        # Example approach: look for text like "Dangerous Attacks" or "Shots on target"
        # Sofascore organizes stats by rows; try a few heuristics.

        # 1) Try to parse statistics block
        try:
            # find stat rows
            stat_rows = soup.select(".statRow") or soup.select(".js-stat-row") or soup.select(".stat-row")
            for row in stat_rows:
                text = row.get_text(separator=" ").strip().lower()
                if "dangerous attacks" in text or "dangerous attacks" in text:
                    nums = re.findall(r"(\d+)", text)
                    if nums:
                        out["dangerous_attacks"] = float(nums[0])
                if "shots on target" in text or "on target" in text:
                    nums = re.findall(r"(\d+)", text)
                    if nums:
                        out["shots_on_target"] = float(nums[0])
                if "xg" in text:
                    # look for float like 0.45
                    m = re.search(r"([0-9]+\.[0-9]+)", text)
                    if m:
                        out["xg"] = float(m.group(1))
        except Exception:
            logger.debug("SofaScore stat parsing fallback", exc_info=True)

        # 2) Try to infer 'pressure' from momentum bars (if present)
        try:
            # momentum bars might be in svg or div widths
            # sum left/right momentum and normalize
            bars = soup.select(".momentum__bar .momentum__value") or soup.select(".momentumBar .value")
            if bars:
                vals = []
                for b in bars:
                    try:
                        v = float(b.get_text().strip().replace("%",""))
                        vals.append(v)
                    except:
                        continue
                if vals:
                    # map 0-100 to 0-10
                    avg = sum(vals)/len(vals)
                    out["pressure"] = round(min(10, avg/10), 2)
        except Exception:
            pass

        return out

    def fetch_live_summary(self) -> List[Dict[str, Any]]:
        """
        Returns list of dicts like:
          {"fixture_id": "...", "pressure": float, "dangerous_attacks": float, "shots_on_target": float, "xg": float}
        """
        try:
            html = self._get_live_matches_html()
            fixtures = self._parse_fixture_list(html)
            results = []
            # limit number of fixtures per run to avoid heavy load
            for f in fixtures[:25]:
                fid = f["fixture_id"]
                url = f["url"]
                try:
                    if fid in self.cache and (time.time() - self.cache[fid].get("ts",0) < 20):
                        results.append(self.cache[fid]["data"])
                        continue
                    r = self.session.get(url, timeout=REQUEST_TIMEOUT)
                    r.raise_for_status()
                    match_data = self._parse_match_page(r.text)
                    payload = {
                        "fixture_id": fid,
                        "pressure": float(match_data.get("pressure",0.0)),
                        "dangerous_attacks": float(match_data.get("dangerous_attacks",0.0)),
                        "shots_on_target": float(match_data.get("shots_on_target",0.0)),
                        "xg": float(match_data.get("xg",0.0)),
                    }
                    self.cache[fid] = {"ts": time.time(), "data": payload}
                    results.append(payload)
                except Exception as e:
                    logger.debug("SofaScore: failed to fetch match %s -> %s", url, e)
            return results
        except Exception as e:
            logger.exception("SofaScore fetch failed: %s", e)
            return []

