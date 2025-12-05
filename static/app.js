async function loadFixtures() {
    try {
        const res = await fetch("/fixtures");
        const data = await res.json();

        const container = document.getElementById("fixtures");
        container.innerHTML = "";

        if (!data || data.length === 0) {
            container.innerHTML = "<p>Nenhum jogo ao vivo no momento.</p>";
            return;
        }

        data.forEach(game => {
            const div = document.createElement("div");
            div.className = "fixture-card";

            div.innerHTML = `
                <strong>${game.league || "Liga Desconhecida"}</strong><br>
                ${game.home} ${game.score} ${game.away}<br>
                <small>${game.minute || "?"} min</small>
            `;

            container.appendChild(div);
        });

    } catch (err) {
        console.error("Erro ao carregar fixtures", err);
    }
}

async function loadAlerts() {
    try {
        const res = await fetch("/alerts");
        const alerts = await res.json();

        const container = document.getElementById("alerts");
        container.innerHTML = "";

        if (!alerts || alerts.length === 0) {
            container.innerHTML = "<p>Nenhum alerta recente.</p>";
            return;
        }

        alerts.forEach(alert => {
            const div = document.createElement("div");
            div.className = "alert-card";

            div.innerHTML = `
                <strong>${alert.game || "Jogo"}</strong><br>
                <p>${alert.message || "Sem detalhes"}</p>
                <small>${alert.time || ""}</small>
            `;

            container.appendChild(div);
        });

    } catch (err) {
        console.error("Erro ao carregar alerts", err);
    }
}

document.getElementById("manual-scan").addEventListener("click", async () => {
    await fetch("/scan");
    loadFixtures();
    loadAlerts();
});

loadFixtures();
loadAlerts();
setInterval(() => {
    loadFixtures();
    loadAlerts();
}, 15000);

