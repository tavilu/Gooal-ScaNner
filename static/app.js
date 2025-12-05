async function loadFixtures() {
  try {
    const response = await fetch('/api/fixtures');
    if (!response.ok) throw new Error('Falha ao carregar jogos');
    const fixtures = await response.json();

    const container = document.getElementById('fixtures');
    container.innerHTML = ''; // limpa conteúdo

    if (fixtures.length === 0) {
      container.textContent = 'Nenhum jogo ao vivo no momento.';
      return;
    }

    fixtures.forEach(fixture => {
      const div = document.createElement('div');
      div.classList.add('fixture');
      div.textContent = `Jogo ID: ${fixture.fixture_id} — Pressão: ${fixture.pressure} — Ataques Perigosos: ${fixture.dangerous_attacks} — Chutes no Gol: ${fixture.shots_on_target} — xG: ${fixture.xg}`;
      container.appendChild(div);
    });
  } catch (e) {
    console.error(e);
    document.getElementById('fixtures').textContent = 'Erro ao carregar jogos.';
  }
}

async function runManualScan() {
  try {
    const res = await fetch('/api/scan', { method: 'POST' });
    if (!res.ok) throw new Error('Erro ao rodar scan');
    alert('Scan iniciado!');
    await loadFixtures(); // Atualiza a lista após o scan
  } catch (e) {
    alert('Erro: ' + e.message);
  }
}

document.getElementById('manual-scan').addEventListener('click', runManualScan);

// Carrega automaticamente ao abrir a página
loadFixtures();

// Opcional: Atualiza automaticamente a cada 60s
setInterval(loadFixtures, 60000);


