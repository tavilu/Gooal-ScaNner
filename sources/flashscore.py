# sources/flashscore.py
import os
import logging
import requests
from bs4 import BeautifulSoup
import re
import time

logger = logging.getLogger("goal_scanner.flashscore")

BASE_LIVE = "https://www.flashscore.com/"

REQUEST_TIMEOUT = int(os.getenv("FLASHSCORE_TIMEOUT", "8"))
USER_AGENT = os.getenv("FLASHSCORE_UA",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36")
HEADERS = {"User-Agent": USER_AGENT, "Accept": "text/html"}

class FlashScoreSource:
    """
    FlashScore scraper to extract:
      - dangerous_attacks
      - shots_on_target
      - pressure estimate
    Notes: Flashscore obfuscates HTML; may require Playwright for robust operation.
    """
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.cache = {}

    def _get_live_page(self):
        r = self.session.get(BASE_LIVE, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.text

    def _parse_match_page(self, html):
        soup = BeautifulSoup(html, "lxml")
        out = {"dangerous_attacks": 0.0, "shots_on_target": 0.0, "pressure": 0.0, "xg": 0.0}
        # heuristics
        try:
            # look for stat names or small boxes
            text = soup.get_text(" ", strip=True).lower()
            # attempts to find patterns
            m_shots = re.search(r"shots on target\s*(\d+)", text)
            if m_shots:
                out["shots_on_target"] = float(m_shots.group(1))
            m_danger = re.search(r"dangerous attacks\s*(\d+)", text)
            if m_danger:
                out["dangerous_attacks"] = float(m_danger.group(1))
            # pressure heuristic: count sequences of "attack" words near each other
            attacks = len(re.findall(r"\battack\b", text))
            out["pressure"] = min(10, attacks/5.0)
        except Exception:
            logger.debug("Flashscore parse fallback", exc_info=True)
        return out

    def fetch_live_summary(self):
        try:
            html = self._get_live_page()
            soup = BeautifulSoup(html, "lxml")
            # find match links (heuristic)
            results = []
            links = soup.select("a[href*='/match/']")
            seen = set()
            for a in links[:25]:
                href = a.get("href")
                if not href:
                    continue
                m = re.search(r"/match/([\w-]+)", href)
                if not m:
                    continue
                fid = m.group(1)
                if fid in seen:
                    continue
                seen.add(fid)
                url = "https://www.flashscore.com" + href
                try:
                    r = self.session.get(url, timeout=REQUEST_TIMEOUT)
                    r.raise_for_status()
                    parsed = self._parse_match_page(r.text)
                    payload = {
                        "fixture_id": fid,
                        "dangerous_attacks": float(parsed.get("dangerous_attacks",0)),
                        "shots_on_target": float(parsed.get("shots_on_target",0)),
                        "pressure": float(parsed.get("pressure",0)),
                        "xg": float(parsed.get("xg",0)),
                    }
                    results.append(payload)
                    self.cache[fid] = {"ts": time.time(), "data": payload}
                except Exception as e:
                    logger.debug("Flashscore fetch match fail %s -> %s", url, e)
            return results
        except Exception:
            logger.exception("Flashscore fetch failed")
            return []
