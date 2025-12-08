up
"fixture_id": str,
"pressure": float,
"dangerous_attacks": int,
"shots_on_target": int,
"xg": float
}
"""
try:
time.sleep(random.uniform(0.5, 1.2))
headers = random.choice(HEADERS)
r = requests.get("https://d.flashscore.com/x/feed/news/notice/football", headers=headers, timeout=8)
# NOTE: se este endpoint específico mudar, a estratégia é buscar a página mobile e parsear JSON
if r.status_code != 200:
logger.warning(f"FlashScore retornou {r.status_code}")
return []


# tentativa genérica: parsear HTML e extrair blocos de jogo
soup = BeautifulSoup(r.text, "lxml")


matches = []
# busca blocos que possuam info de jogo — heurística segura
game_nodes = soup.select(".event, .match") or soup.select("div")[:40]


for node in game_nodes:
try:
# heurística para extrair ids e métricas
title = node.get_text(" ", strip=True)
fixture_id = str(abs(hash(title)))


# valores de fallback
pressure = 0.0
da = 0
sot = 0
xg = 0.0


matches.append({
"fixture_id": fixture_id,
"pressure": pressure,
"dangerous_attacks": da,
"shots_on_target": sot,
"xg": xg
})
except Exception:
continue


return matches


except Exception as e:
logger.error(f"Erro FlashScore: {e}")
return []
