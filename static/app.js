async function loadFixtures() {
    try {
        const res = await fetch("/api/fixtures");
        const data = await res.json();

        const container = document.getElementById("fixtures");
        container.innerHTML = "";

        if (!data || data.length === 0) {
            container.innerHTML = "<p>Nenhum jogo ao vivo no momento.</p>";
            return;
        }

        data.forEach(m => {
            const div = document.createElement("div");
            div.className = "card";

            div.innerHTML = `
                <strong>Fixture:</strong> ${m.fixture_id}<br>
                <strong>Pressure:</strong> ${m.pressure}<br>
                <strong>D. Attacks:</strong> ${m.dangerous_attacks}<br>
                <strong>Shots on Target:</strong> ${m.shots_on_target}<br>
                <strong>xG:</strong> ${m.xg}
            `;

            container.appendChild(div);
        });
    } catch (err) {
        console.error("Erro ao carregar fixtures:", err);
    }
}

async function loadAlerts() {
    try {
        const res = await fetch("/api/last_alerts");
        const data = await res.json();

        const container = document.getElementById("alerts");
        container.innerHTML = "";

        if (!data || data.length === 0) {
            container.innerHTML = "<p>Nenhum alerta recente.</p>";
            return;
        }

        data.forEach(alert => {
            const div = document.createElement("div");
            div.className = "card";
            div.innerHTML = alert;
            container.appendChild(div);
        });
    } catch (err) {
        console.error("Erro ao carregar alertas:", err);
    }
}

// Botão "Rodar Scan Agora"
document.getElementById("manual-scan").onclick = async () => {
    await fetch("/api/scan", { method: "POST" });
    alert("Scan executado!");
};

// Atualização automática
loadFixtures();
loadAlerts();
setInterval(loadFixtures, 5000);
setInterval(loadAlerts, 7000);