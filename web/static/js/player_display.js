// Updates the quick stats display with current player statistics
function _fetchStatForRange(player, stat, range) {
    // If composite stat, fetch components and combine on client
    const compositeMap = {
        pa: ['points', 'assists'],
        pr: ['points', 'rebounds'],
        ra: ['rebounds', 'assists'],
        pra: ['points', 'rebounds', 'assists']
    };

    if (compositeMap[stat]) {
        const comps = compositeMap[stat];
        return Promise.all(comps.map(s => fetch(`/api/player_stats?player=${encodeURIComponent(player)}&stat=${s}&limit=${range}`).then(r => r.json())))
            .then(arr => {
                // arr is list of data objects for each component; combine
                const base = arr[0];
                const combined = { labels: base.labels || [], dates: base.dates || [], values: [], avg: 0 };
                const len = base.values ? base.values.length : 0;
                for (let i = 0; i < len; i++) {
                    let sum = 0;
                    arr.forEach(a => {
                        const v = a.values && a.values[i] ? a.values[i] : 0;
                        sum += (typeof v === 'number' && !isNaN(v)) ? v : 0;
                    });
                    combined.values.push(sum);
                }
                // average is sum of averages
                combined.avg = arr.reduce((acc, a) => acc + (a.avg || 0), 0);
                return combined;
            });
    }

    // Non-composite: fetch directly
    return fetch(`/api/player_stats?player=${encodeURIComponent(player)}&stat=${stat}&limit=${range}`).then(r => r.json());
}

function updateQuickStats() {
    const playerNameEl = document.getElementById("player-name");
    if (!playerNameEl) return;
    
    const currentPlayer = playerNameEl.dataset.player;
    if (!currentPlayer) return;

    // Fetch stats for different ranges (supports composite stats client-side)
    const stat = (document.querySelector('.stat-buttons-row button.active') || {}).dataset?.stat || 'points';
    Promise.all([
        _fetchStatForRange(currentPlayer, stat, 5),
        _fetchStatForRange(currentPlayer, stat, 10),
        _fetchStatForRange(currentPlayer, stat, 20),
        _fetchStatForRange(currentPlayer, stat, 'h2h')
    ]).then(([l5Data, l10Data, l20Data, h2hData]) => {
        // Update quick stats elements
        if (document.getElementById("qs-games")) {
            document.getElementById("qs-games").textContent = Math.round(l10Data.avg * 10) / 10;
        }
        if (document.getElementById("qs-h2h")) {
            document.getElementById("qs-h2h").textContent = Math.round(h2hData.avg * 10) / 10;
        }
        if (document.getElementById("qs-l5")) {
            document.getElementById("qs-l5").textContent = Math.round(l5Data.avg * 10) / 10;
        }
        if (document.getElementById("qs-l10")) {
            document.getElementById("qs-l10").textContent = Math.round(l10Data.avg * 10) / 10;
        }
        if (document.getElementById("qs-l20")) {
            document.getElementById("qs-l20").textContent = Math.round(l20Data.avg * 10) / 10;
        }
        if (document.getElementById("total-value")) {
            document.getElementById("total-value").textContent = Math.round(l10Data.avg * 10) / 10;
        }
    }).catch(err => console.error("Error loading quick stats:", err));
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    updateQuickStats();
});
