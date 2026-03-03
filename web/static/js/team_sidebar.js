// Load team players and populate the sidebar
function loadTeamPlayers() {
    const playerNameEl = document.getElementById("player-name");
    if (!playerNameEl) return;

    const currentPlayer = playerNameEl.dataset.player;
    if (!currentPlayer) return;

    const playersList = document.getElementById("team-players-list");
    if (!playersList) return;

    fetch(`/api/team_players?player=${encodeURIComponent(currentPlayer)}`)
        .then(res => res.json())
        .then(data => {
            playersList.innerHTML = '';

            if (data.players && data.players.length > 0) {
                data.players.forEach(playerName => {
                    const item = document.createElement('div');
                    item.className = 'team-player-item';
                    if (playerName === currentPlayer) {
                        item.classList.add('active');
                    }

                    // Name — click navigates to that player
                    const nameSpan = document.createElement('span');
                    nameSpan.className = 'teammate-name';
                    nameSpan.textContent = playerName;
                    nameSpan.addEventListener('click', () => {
                        window.location.href = `/player?name=${encodeURIComponent(playerName)}`;
                    });
                    item.appendChild(nameSpan);

                    // C / S filter buttons (not shown for current player)
                    if (playerName !== currentPlayer) {
                        const btns = document.createElement('div');
                        btns.className = 'ww-btns';

                        const withBtn = document.createElement('button');
                        withBtn.className = 'ww-btn ww-with';
                        withBtn.textContent = '+';
                        withBtn.title = `Con ${playerName}`;
                        withBtn.addEventListener('click', (e) => {
                            e.stopPropagation();
                            if (typeof window.setTeammateFilter === 'function') {
                                window.setTeammateFilter(playerName, 'with');
                                updateSidebarActiveStates();
                            }
                        });

                        const withoutBtn = document.createElement('button');
                        withoutBtn.className = 'ww-btn ww-without';
                        withoutBtn.textContent = '−';
                        withoutBtn.title = `Sin ${playerName}`;
                        withoutBtn.addEventListener('click', (e) => {
                            e.stopPropagation();
                            if (typeof window.setTeammateFilter === 'function') {
                                window.setTeammateFilter(playerName, 'without');
                                updateSidebarActiveStates();
                            }
                        });

                        btns.appendChild(withBtn);
                        btns.appendChild(withoutBtn);
                        item.appendChild(btns);
                    }

                    playersList.appendChild(item);
                });
            }
        })
        .catch(err => console.error("Error loading team players:", err));
}

function updateSidebarActiveStates() {
    const filter = window.getTeammateFilter ? window.getTeammateFilter() : {};
    document.querySelectorAll('.ww-btn').forEach(btn => btn.classList.remove('active'));
    if (filter.withPlayer) {
        document.querySelectorAll('.ww-btn.ww-with').forEach(btn => {
            if (btn.title === `Con ${filter.withPlayer}`) btn.classList.add('active');
        });
    }
    if (filter.withoutPlayer) {
        document.querySelectorAll('.ww-btn.ww-without').forEach(btn => {
            if (btn.title === `Sin ${filter.withoutPlayer}`) btn.classList.add('active');
        });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadTeamPlayers();
});
