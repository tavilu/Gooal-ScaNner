import time
import logging
from collections import defaultdict, deque

logger = logging.getLogger("goal_scanner.analyzer")

# JANELA MÓVEL (3 minutos, com execução a cada 8s → ~22 ciclos)
WINDOW_SIZE = 22

# PESOS PROFISSIONAIS
W_PRESSURE = 2.5
W_DA = 2.8                # dangerous attacks
W_SOT = 3.2               # shots on target
W_XG = 18                 # xG é MUITO poderoso
W_ODDS = 4.5              # queda forte = risco alto

# Redução de ruído
MIN_EVENTS_REQUIRED = 1


class Analyzer:
    """
    Combina todas as fontes e calcula o GPI profissional (0–100)
    """

    def __init__(self, sources, notifier):
        self.sources = sources
        self.notifier = notifier

        # histórico por fixture
        self.history = defaultdict(lambda: deque(maxlen=WINDOW_SIZE))

        self.alerts = []  # últimos alertas enviados

    # ----------------------------- UTILIDADES -----------------------------

    def _merge_source_results(self, raw):
        """
        Une os dados de todas as fontes em um dict por fixture_id
        """
        merged = {}

        for src in raw:
            for entry in src:
                fid = entry["fixture_id"]
                if fid not in merged:
                    merged[fid] = {
                        "fixture_id": fid,
                        "pressure": 0.0,
                        "dangerous_attacks": 0.0,
                        "shots_on_target": 0.0,
                        "xg": 0.0,
                        "odds_delta": 0.0,
                    }

                for key in ["pressure", "dangerous_attacks", "shots_on_target", "xg", "odds_delta"]:
                    if key in entry:
                        merged[fid][key] = max(merged[fid][key], float(entry[key]))

        return merged

    # ----------------------------- GPI PROFISSIONAL -----------------------------

    def compute_gpi(self, data_list):
        """
        Calcula GPI (0–100) usando:
        - pressão
        - ataques perigosos
        - finalizações no alvo
        - xG
        - queda de odds
        - tendência (com janelas)

        output:
            {"gpi": 0..100, "level": "VERDE|AMARELO|VERMELHO"}
        """
        if not data_list:
            return {"gpi": 0, "level": "VERDE"}

        # média na janela
        pressure = sum(d["pressure"] for d in data_list) / len(data_list)
        da = sum(d["dangerous_attacks"] for d in data_list) / len(data_list)
        sot = sum(d["shots_on_target"] for d in data_list) / len(data_list)
        xg = sum(d["xg"] for d in data_list) / len(data_list)
        odds = sum(d["odds_delta"] for d in data_list) / len(data_list)

        # tendência temporal (últimos 3 ciclos)
        if len(data_list) > 3:
            trend = (
                (data_list[-1]["pressure"] + data_list[-1]["dangerous_attacks"])
                - (data_list[-3]["pressure"] + data_list[-3]["dangerous_attacks"])
            )
            trend = max(0, trend)
        else:
            trend = 0

        # GPI linear
        gpi_raw = (
            pressure * W_PRESSURE +
            da * W_DA +
            sot * W_SOT +
            xg * W_XG +
            odds * W_ODDS +
            trend * 3
        )

        # normalização para 0–100
        gpi = min(100, gpi_raw * 1.4)

        # nível
        if gpi >= 66:
            level = "VERMELHO"
        elif gpi >= 36:
            level = "AMARELO"
        else:
            level = "VERDE"

        return {"gpi": round(gpi, 2), "level": level}

    # ----------------------------- CICLO PRINCIPAL -----------------------------

    def run_cycle(self):
        logger.info("Analyzer cycle started...")

        raw_sources = []
        for src in self.sources:
            try:
                data = src.fetch_live_summary()
                raw_sources.append(data)
            except Exception as e:
                logger.error("Source error: %s", e)

        merged = self._merge_source_results(raw_sources)

        for fid, stats in merged.items():
            # gravar nos históricos
            self.history[fid].append(stats)

            # ignorar jogos sem eventos reais
            if stats["pressure"] == 0 and stats["dangerous_attacks"] == 0 and stats["shots_on_target"] == 0 and stats["odds_delta"] == 0:
                continue

            gpi_info = self.compute_gpi(list(self.history[fid]))

            alert = {
                "fixture": fid,
                "gpi": gpi_info["gpi"],
                "level": gpi_info["level"],
                "merged": stats,
                "time": time.time(),
            }

            # salvar últimos alertas
            self.alerts.append(alert)
            if len(self.alerts) > 200:
                self.alerts.pop(0)

            # enviar notificações
            try:
                self.notifier.send_alert(alert)
            except Exception as e:
                logger.error("Notifier error: %s", e)

        logger.info("Analyzer cycle completed.")

    # ----------------------------- API HELPERS -----------------------------

    def status_report(self):
        return {
            "sources": [type(s).__name__ for s in self.sources],
            "alerts_count": len(self.alerts),
        }

    def get_alerts(self):
        return list(reversed(self.alerts[-200:]))  # últimos 200
