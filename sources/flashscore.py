import requests
import logging

logger = logging.getLogger("goal_scanner.flashscore")

class FlashScoreSource:
    def fetch_live_summary(self):
        # Mock simples para exemplo
        try:
            # Aqui você pode fazer scraping, API, etc
            return []
        except Exception as e:
            logger.error(f"Erro FlashScore: {e}")
            return []

    def detect_live_games(self):
        return [], True

