# sources/flashscore.py
import logging, os
logger = logging.getLogger("goal_scanner.flashscore")

class FlashScoreSource:
    def __init__(self):
        self.token = os.getenv("FLASHSCORE_KEY")  # optional

    def fetch_live_summary(self):
        # Return same shape as SofaScore
        logger.debug("FlashScore fetch placeholder")
        return []
