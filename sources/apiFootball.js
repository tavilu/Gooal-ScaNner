import fetch from "node-fetch";

const API_KEY = process.env.API_FOOTBALL_KEY;
const BASE_URL = "https://v3.football.api-sports.io";

async function safeFetch(url) {
    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 15000);

        const res = await fetch(url, {
            method: "GET",
            headers: {
                "x-apisports-key": API_KEY,
            },
            signal: controller.signal,
        });

        clearTimeout(timeout);

        if (res.status === 429) {
            console.log("⚠ API-Football: Rate limit atingido. Aguardando 60s...");
            await new Promise(r => setTimeout(r, 60000));
            return null;
        }

        if (res.status === 401) {
            console.log("❌ API-Football: Chave inválida.");
            return null;
        }

        if (res.status === 403) {
            console.log("❌ API-Football: Acesso bloqueado.");
            return null;
        }

        if (!res.ok) {
            console.log(`❌ API-Football Erro: ${res.status}`);
            return null;
        }

        const json = await res.json();
        return json;
    } catch (err) {
        console.log("❌ Erro API-Football:", err.message);
        return null;
    }
}

export async function getLiveMatch(fixtureId) {
    const url = `${BASE_URL}/fixtures?id=${fixtureId}&live=all`;
    const data = await safeFetch(url);

    if (!data || !data.response || data.response.length === 0) return null;

    const match = data.response[0];

    return {
        id: match.fixture.id,
        time: match.fixture.status.elapsed,
        status: match.fixture.status.short,
        league: match.league.name,
        goals: {
            home: match.goals.home,
            away: match.goals.away
        },
        home: {
            name: match.teams.home.name,
        },
        away: {
            name: match.teams.away.name,
        }
    };
}

