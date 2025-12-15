async def poll_matches():
    while True:
        try:
            matches = get_live_matches()
        except Exception as e:
            print("Erro ao buscar partidas:", e)
            # pausa maior para evitar loops rápidos em caso de falha
            await asyncio.sleep(600)
            continue

        # processa apenas se não houve erro
        for match in matches:
            state = get_state(match["id"])
            if has_changed(match, state):
                alerts = analyze(match, state)
                for alert in alerts:
                    send_telegram_message(alert["message"])
                    state["alerts_sent"].add(alert["key"])
                state["last_minute"] = match.get("minute")
                state["last_score"] = match.get("score")

        # espera entre polls para economizar requisições
        await asyncio.sleep(600)  # 10 minutos
