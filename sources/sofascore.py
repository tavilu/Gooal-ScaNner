# sources/sofascore.py
import os
import logging
logger = logging.getLogger("goal_scanner.sofascore")

class SofaScoreSource:
    def __init__(self):
        # If you have a paid feed/API, put keys in env and implement here.
        # Otherwise implement a scraping/parsing method carefully respecting TOS.
        self.api_key = os.getenv("SOFASCORE_KEY")  # optional

    def fetch_live_summary(self):
        """
        Return list/dict with keys:
        {
          "fixture_id": "...",
          "pressure": 0-10,
          "dangerous_attacks": int,
          "shots_on_target": int,
          "xg": float,
        }
        You may implement scraping or use a paid feed.
        """
        # Placeholder: return empty to not break pipeline
        # Implement actual logic here
        logger.debug("SofaScore fetch placeholder")
        return []
