# engine/analyzer.py

import logging
from datetime import datetime

logger = logging.getLogger("goal_scanner.analyzer")


class Analyzer:
    def __init__(self, sources=None, notifier=None):
        self.sources = sources or []
        self.notifier = notifier
        self.signals = []

    def fuse_data(self):
        """
        Junta os dados das fontes:
        - Flashscore
        - API Football
        """

        flash_src = next(
            (s for s in self.sources if "flash" in s.__class__.__name__.lower()),
            None
        )
        apifoot_src = next(
            (s for s in self.sources if s.__class__.__name__.lower().startswith("apifoot")),
            None
        )

        flash_data = flash_src.fetch_live_summary() if flash_src else []
        apifoot_live, limited = (
            apifoot_src.detect_live_games() if apifoot_src else ([], True)
        )

        merged = {}

        # Mescla FlashScore
        for item in flash_data:
            fid = item.get("fixture_id")
            if not fid:
                continue

            merged[fid] = merged.get(fid, {})
            merged[fid].update(item)

        # Mescla API Football
        for resp in apifoot_live or []:
            try:
                fid = str(resp.get("fixture", {}).get("id") or resp.get("id"))
                merged[fid] = merged.get(fid, {})

                merged[fid]["api_fixture"] = resp  # adiciona json completo do jogo
            except Exception:
                continue

        return merged, limited

    def score_fixture(self, fused):
        """
        Heurística simples (0-100)
        """

        pressure = fused.get("pressure", 0)
        da = fused.get("dangerous_attacks", 0)
        sot = fused.get("shots_on_target", 0)
        xg = fused.get("xg", 0)

        score = (pressure * 6) + (da * 4) + (sot * 7) + (xg * 10)
        return min(100, int(score))

    def run_cycle(self):
        """
        Executa um ciclo de análise:
        - junta tudo
        - calcula score
        - salva sinais
        - notifica (opcional)
        """

        merged, limited = self.fuse_data()
        now = datetime.utcnow().isoformat()

        signals = []

        for fid, data in merged.items():
            try:
                s = self.score_fixture(data)

                if s >= 70:  # threshold de alerta
                    signals.append(
                        {
                            "fixture_id": fid,
                            "score": s,
                            "data": data,
                            "ts": now,
                        }
                    )
            except Exception as e:
                logger.error(f"Erro scoring {e}")

        self.signals = signals

        # opcional: enviar via Telegram / Discord / email
        if self.notifier and signals:
            try:
                self.notifier.send(signals)
            except Exception as e:
                logger.error(f"Notifier falhou: {e}")

    def get_recent_signals(self):
        return self.signals


