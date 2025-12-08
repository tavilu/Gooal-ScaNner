import requests
import logging

logger = logging.getLogger("goal_scanner.apifootball")

class ApiFootballSource:
    def __init__(self):
        self.api_key = "SUA_API_KEY_AQUI"  # configure via .env ou outro meio
        self.base_url = "https://api-football-v1.p.rapidapi.com/v3"

    def fetch_live_summary(self):
        # Exemplo básico - você pode ajustar conforme API real
        try:
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
            }
            resp = requests.get(f"{self.base_url}/fixtures?live=all", headers=headers, timeout=10)
            data = resp.json()

            results = []
            for fixture in data.get("response", []):
                results.append({
                    "fixture_id": str(fixture["fixture"]["id"]),
                    "pressure": 0.0,  # API não fornece diretamente, ajuste se quiser
                    "dangerous_attacks": 0,
                    "shots_on_target": 0,
                    "xg": 0.0
                })
            return results
        except Exception as e:
            logger.error(f"Erro ApiFootball: {e}")
            return []

    def detect_live_games(self):
        # Simples - retorna lista vazia e True para "limitado"
        return [], True


