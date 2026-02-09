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
                    item.textContent = playerName;
                    item.style.cursor = 'pointer';
                    
                    item.addEventListener('click', () => {
                        // Buscar otro jugador del equipo
                        window.location.href = `/player?name=${encodeURIComponent(playerName)}`;
                    });
                    
                    playersList.appendChild(item);
                });
            }
        })
        .catch(err => console.error("Error loading team players:", err));
}

// Initialize when page loads
document.addEventListener("DOMContentLoaded", () => {
    loadTeamPlayers();
});
