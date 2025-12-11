def get_live_matches():
    url = "https://v3.football.api-sports.io/fixtures?live=all"

    headers = {
        "x-apisports-key": API_KEY
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        print("STATUS:", response.status_code)
        print("HEADERS:", response.headers)
        print("CONTENT:", response.text[:300])

        response.raise_for_status()

        data = response.json()
        return data.get("response", [])
    except Exception as e:
        print("🔥 ERRO AO BUSCAR JOGOS:", e)
        return []
