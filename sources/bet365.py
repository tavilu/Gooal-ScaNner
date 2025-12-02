# sources/bet365.py
import logging, os
logger = logging.getLogger("goal_scanner.bet365")

class Bet365Source:
    def __init__(self):
        # Ideally use an odds API provider (TheOddsAPI, Betradar etc)
        self.token = os.getenv("ODDS_API_KEY")  # if available

    def fetch_live_summary(self):
        """
        Should return odds_delta normalized to a scale (0-10).
        e.g. if market odds for home team fell significantly, odds_delta ~ 5-10.
        """
        logger.debug("Bet365 fetch placeholder")
        return []
